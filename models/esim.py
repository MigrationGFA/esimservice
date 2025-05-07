import pytz
from datetime import datetime
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Float, Text

Base = declarative_base()


# Set the timezone to Africa/Lagos
lagos_tz = pytz.timezone('Africa/Lagos')


class UserOnboarding(Base):
    __tablename__ = "onboarding_user"

    user_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(50), nullable=True, index=True)
    stripe_customer_id = Column(String(50), nullable=True, index=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    email_address = Column(String(100), nullable=True, index=True)
    country_of_residence = Column(String(50), nullable=True)
    password = Column(String(200))
    phone_number = Column(String(20), nullable=True)
    is_email_verified = Column(Integer)
    is_active = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    intent_id = Column(String(100), unique=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    customer_id = Column(String(50))
    data_plan_uid = Column(String(50))
    status = Column(String(100), nullable=False)
    client_secret = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(lagos_tz))


class PaymentWebhook(Base):
    __tablename__ = "payment_webhook"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Auto-incrementing ID
    intent_id = Column(String(100), unique=True, index=True)  # Stripe PaymentIntent ID
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    customer_name = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)  # Store error message in case of failure
    last4_card_digits = Column(String(20), nullable=True)  # Last 4 digits of card
    card_brand = Column(String(50), nullable=True)  # Brand of the card (e.g., Visa)
    is_processed = Column(Integer)
    processed_date = Column(DateTime(timezone=True))
    response_status = Column(Integer)
    response_message = Column(String(500))


class EsimData(Base):
    __tablename__ = 'esim_data'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    apn = Column(String(100))
    tag = Column(String(100), nullable=True)
    uid = Column(String(100), unique=True, index=True)
    iccid = Column(String(50), index=True)
    state = Column(String(50))
    auto_apn = Column(Integer)
    manual_code = Column(String(100))
    smdp_address = Column(String(100))
    date_assigned = Column(DateTime)
    network_status = Column(String(50))
    service_status = Column(String(50))
    activation_code = Column(String(255))
    request_id = Column(String(100), nullable=True)
    payment_intent_id = Column(String(100), unique=True, index=True)
    customer = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(lagos_tz))


class EsimDataPlanHistory(Base):
    __tablename__ = 'esim_data_plan_history'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    iccid = Column(String(50), index=True)
    uid = Column(String(100), primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    data_quota_mb = Column(String(100), nullable=True)
    data_quota_bytes = Column(String(100), nullable=True)
    validity_days = Column(Integer, nullable=True)
    policy_id = Column(Integer, nullable=True)
    policy_name = Column(String(100), nullable=True)
    wholesale_price_usd = Column(Float, nullable=True)
    rrp_usd = Column(Float, nullable=True)
    rrp_eur = Column(Float, nullable=True)
    rrp_gbp = Column(Float, nullable=True)
    rrp_cad = Column(Float, nullable=True)
    rrp_aud = Column(Float, nullable=True)
    rrp_jpy = Column(Float, nullable=True)
    countries_enabled = Column(Text, nullable=True)
    intent_id = Column(String(100), nullable=False, unique=True)
    transaction_id = Column(String(100), nullable=False, unique=True)
    customer = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(lagos_tz))
