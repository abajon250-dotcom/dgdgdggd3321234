import datetime
import json
from sqlalchemy import BigInteger, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, relationship, selectinload
from sqlalchemy import select, update, delete
from config import DATABASE_URL

Base = declarative_base()

# ---------- Модели ----------
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_user_id = Column(BigInteger, unique=True, nullable=False)   # ← изменено
    subscription_end = Column(DateTime, nullable=True)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)   # ← изменено
    phone = Column(String, nullable=False)
    country = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    registration_date = Column(DateTime)
    connected_at = Column(DateTime, default=datetime.datetime.utcnow)
    contacts_count = Column(Integer, default=0)
    spam_block = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    session_file = Column(String, nullable=True)
    session_string = Column(String, nullable=True)
    user = relationship("User", back_populates="accounts")
    campaigns = relationship("Campaign", back_populates="account")

class Template(Base):
    __tablename__ = 'templates'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)   # ← изменено
    name = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    delay = Column(Integer, default=0)
    user = relationship("User", back_populates="templates")

class Campaign(Base):
    __tablename__ = 'campaigns'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)   # ← изменено
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    name = Column(String)
    status = Column(String, default='pending')
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=True)
    custom_text = Column(Text, nullable=True)
    delay = Column(Integer, default=0)
    recipients_json = Column(Text)
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    started_at = Column(DateTime)
    last_sent_at = Column(DateTime)
    errors_log = Column(Text)
    user = relationship("User", back_populates="campaigns")
    account = relationship("Account", back_populates="campaigns")
    template = relationship("Template")

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)   # ← изменено
    amount = Column(Float)
    currency = Column(String, default='USD')
    payment_system = Column(String)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    external_id = Column(String)
    user = relationship("User")

class Setting(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=True)

class PromoCode(Base):
    __tablename__ = 'promo_codes'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    days = Column(Integer, nullable=False)
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    created_by = Column(BigInteger, ForeignKey('users.id'), nullable=True)   # ← изменено
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

# ---------- Engine и сессия ----------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ---------- Users ----------
async def get_user(tg_user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.tg_user_id == tg_user_id))
        return result.scalar_one_or_none()

async def create_user(tg_user_id: int):
    async with AsyncSessionLocal() as session:
        user = User(tg_user_id=tg_user_id)
        session.add(user)
        await session.commit()
        return user

async def update_subscription(tg_user_id: int, end_date: datetime.datetime):
    async with AsyncSessionLocal() as session:
        user = await get_user(tg_user_id)
        if user:
            user.subscription_end = end_date
            await session.commit()

async def ban_user(tg_user_id: int):
    async with AsyncSessionLocal() as session:
        user = await get_user(tg_user_id)
        if user:
            user.is_banned = True
            await session.commit()

async def unban_user(tg_user_id: int):
    async with AsyncSessionLocal() as session:
        user = await get_user(tg_user_id)
        if user:
            user.is_banned = False
            await session.commit()

async def get_all_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        return result.scalars().all()

# ---------- Accounts ----------
async def add_account(user_id: int, phone: str, country: str, first_name: str, last_name: str,
                      username: str, reg_date: datetime.datetime, contacts_count: int, spam_block: bool,
                      session_string: str = None, session_file: str = None):
    async with AsyncSessionLocal() as session:
        account = Account(
            user_id=user_id, phone=phone, country=country, first_name=first_name, last_name=last_name,
            username=username, registration_date=reg_date, contacts_count=contacts_count,
            spam_block=spam_block, session_string=session_string, session_file=session_file
        )
        session.add(account)
        await session.commit()
        return account

async def get_user_accounts(tg_user_id: int):
    user = await get_user(tg_user_id)
    if not user:
        return []
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Account).where(Account.user_id == user.id))
        return result.scalars().all()

async def get_account_by_id(account_id: int, tg_user_id: int):
    user = await get_user(tg_user_id)
    if not user:
        return None
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Account).where(Account.id == account_id, Account.user_id == user.id))
        return result.scalar_one_or_none()

async def update_account_active_status(account_id: int, is_active: bool):
    async with AsyncSessionLocal() as session:
        await session.execute(update(Account).where(Account.id == account_id).values(is_active=is_active))
        await session.commit()

async def update_account_spam_block(account_id: int, spam_block: bool):
    async with AsyncSessionLocal() as session:
        await session.execute(update(Account).where(Account.id == account_id).values(spam_block=spam_block))
        await session.commit()

async def get_all_accounts():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Account))
        return result.scalars().all()

# ---------- Templates ----------
async def add_template(user_id: int, name: str, text: str, delay: int):
    async with AsyncSessionLocal() as session:
        template = Template(user_id=user_id, name=name, text=text, delay=delay)
        session.add(template)
        await session.commit()
        return template

async def get_user_templates(tg_user_id: int):
    user = await get_user(tg_user_id)
    if not user:
        return []
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Template).where(Template.user_id == user.id))
        return result.scalars().all()

async def get_template_by_id(template_id: int, tg_user_id: int):
    user = await get_user(tg_user_id)
    if not user:
        return None
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Template).where(Template.id == template_id, Template.user_id == user.id))
        return result.scalar_one_or_none()

async def update_template(template_id: int, name: str, text: str, delay: int):
    async with AsyncSessionLocal() as session:
        await session.execute(update(Template).where(Template.id == template_id).values(name=name, text=text, delay=delay))
        await session.commit()

async def delete_template(template_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Template).where(Template.id == template_id))
        await session.commit()

# ---------- Campaigns ----------
async def add_campaign(user_id: int, account_id: int, name: str, template_id: int, custom_text: str,
                       delay: int, recipients: list):
    recipients_json = json.dumps(recipients)
    total = len(recipients)
    async with AsyncSessionLocal() as session:
        campaign = Campaign(
            user_id=user_id, account_id=account_id, name=name, template_id=template_id,
            custom_text=custom_text, delay=delay, recipients_json=recipients_json,
            total_recipients=total, status='pending'
        )
        session.add(campaign)
        await session.commit()
        return campaign

async def get_user_campaigns(tg_user_id: int):
    user = await get_user(tg_user_id)
    if not user:
        return []
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Campaign)
            .where(Campaign.user_id == user.id)
            .order_by(Campaign.id.desc())
            .options(selectinload(Campaign.account))
        )
        return result.scalars().all()

async def get_campaign_by_id(campaign_id: int, tg_user_id: int):
    user = await get_user(tg_user_id)
    if not user:
        return None
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Campaign)
            .where(Campaign.id == campaign_id, Campaign.user_id == user.id)
            .options(selectinload(Campaign.account))
        )
        return result.scalar_one_or_none()

async def update_campaign_status(campaign_id: int, status: str):
    async with AsyncSessionLocal() as session:
        await session.execute(update(Campaign).where(Campaign.id == campaign_id).values(status=status))
        await session.commit()

async def update_campaign_sent_count(campaign_id: int, sent_count: int, last_sent_at: datetime.datetime):
    async with AsyncSessionLocal() as session:
        await session.execute(update(Campaign).where(Campaign.id == campaign_id).values(sent_count=sent_count, last_sent_at=last_sent_at))
        await session.commit()

async def update_campaign_errors_log(campaign_id: int, errors_log: list):
    async with AsyncSessionLocal() as session:
        await session.execute(update(Campaign).where(Campaign.id == campaign_id).values(errors_log=json.dumps(errors_log)))
        await session.commit()

async def get_all_campaigns(limit: int = 100):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Campaign)
            .order_by(Campaign.id.desc())
            .limit(limit)
            .options(selectinload(Campaign.account))
        )
        return result.scalars().all()

# ---------- Payments ----------
async def add_payment(user_id: int, amount: float, payment_system: str, external_id: str):
    async with AsyncSessionLocal() as session:
        payment = Payment(user_id=user_id, amount=amount, payment_system=payment_system, external_id=external_id)
        session.add(payment)
        await session.commit()
        return payment

async def update_payment_status(external_id: str, status: str):
    async with AsyncSessionLocal() as session:
        await session.execute(update(Payment).where(Payment.external_id == external_id).values(status=status))
        await session.commit()

async def get_all_payments(limit: int = 100):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Payment).order_by(Payment.id.desc()).limit(limit))
        return result.scalars().all()

# ---------- Settings ----------
async def get_setting(key: str, default: str = None):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        return setting.value if setting else default

async def set_setting(key: str, value: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            session.add(setting)
        await session.commit()

# ---------- PromoCodes ----------
async def create_promo(code: str, days: int, max_uses: int = 1, expires_at: datetime.datetime = None, created_by: int = None):
    async with AsyncSessionLocal() as session:
        promo = PromoCode(code=code, days=days, max_uses=max_uses, expires_at=expires_at, created_by=created_by)
        session.add(promo)
        await session.commit()
        return promo

async def get_promo(code: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PromoCode).where(PromoCode.code == code))
        return result.scalar_one_or_none()

async def use_promo(code: str):
    async with AsyncSessionLocal() as session:
        promo = await get_promo(code)
        if not promo:
            return None
        if promo.max_uses <= promo.used_count:
            return None
        if promo.expires_at and promo.expires_at < datetime.datetime.utcnow():
            return None
        promo.used_count += 1
        await session.commit()
        return promo.days

async def get_all_promos():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PromoCode).order_by(PromoCode.id.desc()))
        return result.scalars().all()