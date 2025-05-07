import base64
import pytz
import random
import logging
import requests
from services.mailer_service import send_mail
from config import maya_key, maya_secret, maya_esim_api, maya_product_api, database_url
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, update
from logging.handlers import TimedRotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler
from models.esim import PaymentIntent, PaymentWebhook, UserOnboarding, EsimData, EsimDataPlanHistory


# Set up your database connection
engine = create_engine(database_url)
# Set timezone
lagos_tz = pytz.timezone('Africa/Lagos')


def get_authorization(key, secret):
    # Encode the API Key and Secret using base64
    credentials = f"{key}:{secret}"
    authorization = base64.b64encode(credentials.encode()).decode()
    return authorization


# generate random transaction id
def generate_transaction_id(db: Session):
    while True:
        # Generate a random 7-digit number
        generated_id = random.randint(1000000, 9999999)
        # Get current date and time
        now = datetime.now()
        # Format the date and time as a string
        formatted_date_time = now.strftime("%Y%m%d%H%M%S")

        reference = str(generated_id) + formatted_date_time

        existing_reference = db.query(EsimDataPlanHistory.transaction_id).filter(EsimDataPlanHistory.transaction_id == reference).first()
        if not existing_reference:
            return reference


def check_and_send_request():
    session = Session(bind=engine)

    try:
        print(f"User found")
        # Find matching intent_id between PaymentIntent and PaymentWebhook
        matching_records = (
            session.query(
                PaymentIntent.customer_id,
                PaymentIntent.data_plan_uid,
                PaymentWebhook.intent_id,
                PaymentWebhook.amount
            )
            .join(PaymentIntent, PaymentIntent.intent_id == PaymentWebhook.intent_id)
            .filter(PaymentWebhook.is_processed == 0, PaymentWebhook.status == 'succeeded')
            .all()
        )

        if not matching_records:
            print(f"Matching record not found")

        for record in matching_records:
            customer_id, data_plan_uid, intent_id, amount = record
            print(f"Processing for intent: {intent_id}, data plan: {data_plan_uid}")

            # Check if customer_id in PaymentIntent matches stripe_customer_id in UserOnboarding
            user = (
                session.query(UserOnboarding)
                .filter_by(stripe_customer_id=customer_id)
                .first()
            )

            if user:
                # Prepare payload for the request
                payload = {
                    "customer_id": user.customer_id,
                    "plan_type_id": data_plan_uid
                }

                authorization = get_authorization(maya_key, maya_secret)

                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Basic {authorization}"
                }

                # Send request to external API
                response = requests.post(maya_esim_api, json=payload, headers=headers)
                response_data = response.json()

                # Print or process the response
                print(f"API Esim Response: {response_data}")

                # Save response to database
                esim_record = EsimData(
                    apn=response_data['esim'].get('apn') if 'esim' in response_data else None,
                    tag=response_data['esim'].get('tag') if 'esim' in response_data else None,
                    uid=response_data['esim'].get('uid') if 'esim' in response_data else None,
                    iccid=response_data['esim'].get('iccid') if 'esim' in response_data else None,
                    state=response_data['esim'].get('state') if 'esim' in response_data else None,
                    auto_apn=response_data['esim'].get('auto_apn') if 'esim' in response_data else None,
                    manual_code=response_data['esim'].get('manual_code') if 'esim' in response_data else None,
                    smdp_address=response_data['esim'].get('smdp_address') if 'esim' in response_data else None,
                    date_assigned=datetime.strptime(response_data['esim'].get('date_assigned'), "%Y-%m-%d %H:%M:%S") if 'esim' in response_data else None,
                    network_status=response_data['esim'].get('network_status') if 'esim' in response_data else None,
                    service_status=response_data['esim'].get('service_status') if 'esim' in response_data else None,
                    activation_code=response_data['esim'].get('activation_code') if 'esim' in response_data else None,
                    request_id=response_data.get('request_id'),
                    payment_intent_id=intent_id,
                    customer=user.email_address
                )
                session.add(esim_record)

                # Fetch data plan details
                # Send request to external API
                plan_api_url = f"{maya_product_api}{data_plan_uid}"
                response = requests.get(plan_api_url, headers=headers)
                response_data = response.json()

                # Print or process the response
                print(f"API Product Response: {response_data}")

                transaction_id = generate_transaction_id(session)
                # Save response to database
                data_plan_record = EsimDataPlanHistory(
                    iccid=response_data['esim'].get('iccid') if 'esim' in response_data else None,
                    uid=response_data['product'].get('uid') if 'product' in response_data else None,
                    name=response_data['product'].get('name') if 'product' in response_data else None,
                    data_quota_mb=response_data['product'].get('data_quota_mb') if 'product' in response_data else None,
                    data_quota_bytes=response_data['product'].get('data_quota_bytes') if 'product' in response_data else None,
                    validity_days=response_data['product'].get('validity_days') if 'product' in response_data else None,
                    policy_id=response_data['product'].get('policy_id') if 'product' in response_data else None,
                    policy_name=response_data['product'].get('policy_name') if 'product' in response_data else None,
                    countries_enabled=",".join(response_data['product'].get('countries_enabled', [])) if 'product' in response_data else None,
                    intent_id=intent_id,
                    customer=user.email_address,
                    transaction_id=transaction_id
                )
                session.add(data_plan_record)

                # Update PaymentIntent table
                stmt = (
                    update(PaymentWebhook)
                    .where(PaymentWebhook.intent_id == intent_id)
                    .values(
                        is_processed=1,
                        processed_date=datetime.now(lagos_tz),
                        response_status=response_data.get("status"),
                        response_message=response_data.get("message")
                    )
                )
                session.execute(stmt)
            else:
                print(f"User not found")
        # Commit changes after processing
        session.commit()

    except Exception as e:
        session.rollback()
        print(f"Error during scheduled job: {e}")
    finally:
        session.close()


if __name__ == '__main__':
    # Set up a rotating log handler
    log_handler = TimedRotatingFileHandler(
        'logs/esim-plan.log', when='midnight', interval=1, backupCount=30
    )
    log_handler.suffix = "%Y-%m-%d"
    log_handler.setFormatter(logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s'))

    # Set up a logger with the rotating log handler
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)

    # Log application start
    logging.info('Application started')

    # Scheduler setup
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_send_request, 'interval', seconds=5)
    scheduler.start()

    # Keep the script running
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
