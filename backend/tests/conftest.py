import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set environment before loading app
os.environ["USE_SQLITE_FALLBACK"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test_bizpulse.db"

from app.api.deps import get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.auth import Organization, User, UserRole
from app.models.base import Base

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bizpulse.db"
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_bizpulse.db"):
        os.remove("./test_bizpulse.db")


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_organization(db) -> Organization:
    org = Organization(name="Acme Corporation")
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.fixture
def test_admin_user(db, test_organization) -> User:
    user = User(
        organization_id=test_organization.id,
        name="Admin User",
        email="admin@acme.com",
        password_hash=get_password_hash("AdminSecret123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_viewer_user(db, test_organization) -> User:
    user = User(
        organization_id=test_organization.id,
        name="Viewer User",
        email="viewer@acme.com",
        password_hash=get_password_hash("ViewerSecret123!"),
        role=UserRole.VIEWER.value,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_auth_headers(test_admin_user) -> dict:
    token = create_access_token(subject=test_admin_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_auth_headers(test_viewer_user) -> dict:
    token = create_access_token(subject=test_viewer_user.id)
    return {"Authorization": f"Bearer {token}"}

