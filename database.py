import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    language = Column(String(10), default="en")
    response_style = Column(String(50), default="professional")
    tone = Column(String(50), default="formal")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    notifications_enabled = Column(Boolean, default=True)
    auto_improve = Column(Boolean, default=False)
    max_response_length = Column(Integer, default=500)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RequestAnalysis(Base):
    __tablename__ = "request_analysis"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, index=True)
    user_input = Column(Text)
    score = Column(Float)
    risks = Column(Text)
    response = Column(Text)
    response_variant = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


# User CRUD operations
def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            session.commit()
            
            # Create default profile and settings
            profile = UserProfile(telegram_id=telegram_id, user_id=user.id)
            settings = UserSettings(telegram_id=telegram_id, user_id=user.id)
            session.add(profile)
            session.add(settings)
            session.commit()
        return user
    finally:
        session.close()


def get_user_profile(telegram_id: int) -> UserProfile:
    session = SessionLocal()
    try:
        profile = session.query(UserProfile).filter(UserProfile.telegram_id == telegram_id).first()
        return profile
    finally:
        session.close()


def update_user_profile(telegram_id: int, **kwargs) -> UserProfile:
    session = SessionLocal()
    try:
        profile = session.query(UserProfile).filter(UserProfile.telegram_id == telegram_id).first()
        if profile:
            for key, value in kwargs.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
            session.commit()
        return profile
    finally:
        session.close()


def get_user_settings(telegram_id: int) -> UserSettings:
    session = SessionLocal()
    try:
        settings = session.query(UserSettings).filter(UserSettings.telegram_id == telegram_id).first()
        return settings
    finally:
        session.close()


def update_user_settings(telegram_id: int, **kwargs) -> UserSettings:
    session = SessionLocal()
    try:
        settings = session.query(UserSettings).filter(UserSettings.telegram_id == telegram_id).first()
        if settings:
            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            settings.updated_at = datetime.utcnow()
            session.commit()
        return settings
    finally:
        session.close()


def save_analysis(telegram_id: int, user_input: str, score: float, risks: str, response: str) -> RequestAnalysis:
    session = SessionLocal()
    try:
        analysis = RequestAnalysis(
            telegram_id=telegram_id,
            user_input=user_input,
            score=score,
            risks=risks,
            response=response
        )
        session.add(analysis)
        session.commit()
        return analysis
    finally:
        session.close()


def get_user_history(telegram_id: int, limit: int = 10):
    session = SessionLocal()
    try:
        history = session.query(RequestAnalysis).filter(
            RequestAnalysis.telegram_id == telegram_id
        ).order_by(RequestAnalysis.created_at.desc()).limit(limit).all()
        return history
    finally:
        session.close()
