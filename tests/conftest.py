import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.consent import Consent
from app.security.authentication import hash_password, create_session_token

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def student_user(db_session):
    user = User(
        user_ref="STU-TEST",
        email="test_student@campus.edu",
        full_name="Test Student",
        hashed_password=hash_password("Password123!"),
        role="student",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    consent = Consent(
        user_id=user.id,
        general_consent=True,
        consent_sleep_tracking=True,
        consent_activity_tracking=True,
        consent_mood_tracking=True,
        consent_social_tracking=True,
        consent_counsellor_review=True
    )
    db_session.add(consent)
    db_session.commit()
    return user

@pytest.fixture
def counsellor_user(db_session):
    user = User(
        user_ref="CNS-TEST",
        email="test_counsellor@campus.edu",
        full_name="Test Counsellor",
        hashed_password=hash_password("Password123!"),
        role="counsellor",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_user(db_session):
    user = User(
        user_ref="ADM-TEST",
        email="test_admin@campus.edu",
        full_name="Test Admin",
        hashed_password=hash_password("Password123!"),
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
