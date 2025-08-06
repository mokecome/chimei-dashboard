"""
Test configuration and fixtures for pytest.
"""
import pytest
import tempfile
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Import application components
from ..main import app
from ..core.database import get_db, Base
from ..config import settings
from ..core.security import create_access_token
from ..models.user import User, UserRole
from ..models.file import VoiceFile, FileStatus, FileFormat
from ..models.analysis import VoiceAnalysis, SentimentType
from ..models.label import ProductLabel, FeedbackCategory


# Test database URL - use SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite specific
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create a new session for the test
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        
        # Clean up all tables after each test
        for table in reversed(Base.metadata.sorted_tables):
            engine.execute(table.delete())


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Create test client with database session override."""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        name="Test User",
        email="test@example.com",
        role=UserRole.OPERATOR,
        is_active=True
    )
    user.set_password("testpassword123")
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Create a test admin user."""
    user = User(
        name="Admin User",
        email="admin@example.com",
        role=UserRole.ADMIN,
        is_active=True
    )
    user.set_password("adminpassword123")
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def manager_user(db_session: Session) -> User:
    """Create a test manager user."""
    user = User(
        name="Manager User",
        email="manager@example.com",
        role=UserRole.MANAGER,
        is_active=True
    )
    user.set_password("managerpassword123")
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def viewer_user(db_session: Session) -> User:
    """Create a test viewer user."""
    user = User(
        name="Viewer User",
        email="viewer@example.com",
        role=UserRole.VIEWER,
        is_active=True
    )
    user.set_password("viewerpassword123")
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def test_token(test_user: User) -> str:
    """Create JWT token for test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create JWT token for admin user."""
    return create_access_token(data={"sub": str(admin_user.id)})


@pytest.fixture
def manager_token(manager_user: User) -> str:
    """Create JWT token for manager user."""
    return create_access_token(data={"sub": str(manager_user.id)})


@pytest.fixture
def viewer_token(viewer_user: User) -> str:
    """Create JWT token for viewer user."""
    return create_access_token(data={"sub": str(viewer_user.id)})


@pytest.fixture
def auth_headers(test_token: str) -> dict:
    """Create authorization headers for test user."""
    return {"Authorization": f"Bearer {test_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Create authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def manager_headers(manager_token: str) -> dict:
    """Create authorization headers for manager user."""
    return {"Authorization": f"Bearer {manager_token}"}


@pytest.fixture
def viewer_headers(viewer_token: str) -> dict:
    """Create authorization headers for viewer user."""
    return {"Authorization": f"Bearer {viewer_token}"}


@pytest.fixture
def test_file(db_session: Session, test_user: User) -> VoiceFile:
    """Create a test voice file."""
    file = VoiceFile(
        filename="test_audio.wav",
        original_filename="test_audio.wav",
        file_path="/tmp/test_audio.wav",
        file_size=1024,
        file_format=FileFormat.WAV,
        status=FileStatus.PENDING,
        uploaded_by=test_user.id
    )
    
    db_session.add(file)
    db_session.commit()
    db_session.refresh(file)
    
    return file


@pytest.fixture
def completed_file(db_session: Session, test_user: User) -> VoiceFile:
    """Create a completed test voice file."""
    file = VoiceFile(
        filename="completed_audio.wav",
        original_filename="completed_audio.wav",
        file_path="/tmp/completed_audio.wav",
        file_size=2048,
        file_format=FileFormat.WAV,
        status=FileStatus.COMPLETED,
        uploaded_by=test_user.id,
        duration=30.5,
        processing_time=5.2
    )
    
    db_session.add(file)
    db_session.commit()
    db_session.refresh(file)
    
    return file


@pytest.fixture
def test_analysis(db_session: Session, completed_file: VoiceFile) -> VoiceAnalysis:
    """Create a test voice analysis."""
    analysis = VoiceAnalysis(
        file_id=completed_file.id,
        transcript="这是一段测试语音转文本的结果",
        sentiment=SentimentType.POSITIVE,
        feedback_category="产品咨询",
        feedback_summary="客户询问产品相关信息",
        product_names='["测试产品A", "测试产品B"]'
    )
    
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    
    return analysis


@pytest.fixture
def test_product_labels(db_session: Session) -> list[ProductLabel]:
    """Create test product labels."""
    labels = [
        ProductLabel(name="测试产品A", description="测试产品A的描述", is_active=True),
        ProductLabel(name="测试产品B", description="测试产品B的描述", is_active=True),
        ProductLabel(name="测试产品C", description="测试产品C的描述", is_active=False),
    ]
    
    for label in labels:
        db_session.add(label)
    
    db_session.commit()
    
    for label in labels:
        db_session.refresh(label)
    
    return labels


@pytest.fixture
def test_feedback_categories(db_session: Session) -> list[FeedbackCategory]:
    """Create test feedback categories."""
    categories = [
        FeedbackCategory(name="产品咨询", description="客户咨询产品相关问题", is_active=True),
        FeedbackCategory(name="投诉建议", description="客户投诉或建议", is_active=True),
        FeedbackCategory(name="售后服务", description="售后服务相关问题", is_active=True),
    ]
    
    for category in categories:
        db_session.add(category)
    
    db_session.commit()
    
    for category in categories:
        db_session.refresh(category)
    
    return categories


@pytest.fixture
def temp_file() -> Generator[str, None, None]:
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        # Write some dummy data
        tmp_file.write(b"dummy audio data for testing")
        tmp_file_path = tmp_file.name
    
    yield tmp_file_path
    
    # Cleanup
    if os.path.exists(tmp_file_path):
        os.unlink(tmp_file_path)


@pytest.fixture
def temp_upload_dir() -> Generator[str, None, None]:
    """Create a temporary upload directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override the upload directory setting
        original_upload_dir = settings.UPLOAD_DIR
        settings.UPLOAD_DIR = temp_dir
        
        yield temp_dir
        
        # Restore original setting
        settings.UPLOAD_DIR = original_upload_dir


@pytest.fixture(scope="function", autouse=True)
def reset_cache():
    """Reset cache before each test."""
    from ..utils.cache import cache
    cache.clear()
    yield
    cache.clear()


# Test utilities

def create_test_file_content() -> bytes:
    """Create dummy file content for testing."""
    return b"dummy audio file content for testing purposes"


def assert_error_response(response, status_code: int, error_message: str = None):
    """Assert error response format."""
    assert response.status_code == status_code
    
    if error_message:
        response_data = response.json()
        assert "detail" in response_data
        assert error_message in response_data["detail"]


def assert_success_response(response, status_code: int = 200):
    """Assert successful response."""
    assert response.status_code == status_code
    
    # Check that response is valid JSON
    response_data = response.json()
    assert isinstance(response_data, (dict, list))


class MockLLMResponse:
    """Mock LLM response for testing."""
    
    @staticmethod
    def success_response():
        return {
            "evaluation_tendency": "positive",
            "feedback_category": "产品咨询",
            "feedback_summary": "客户询问产品相关信息",
            "product_name": "测试产品A"
        }
    
    @staticmethod
    def error_response():
        return {"error": "LLM analysis failed"}


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection."""
    # Add markers to tests based on their location
    for item in items:
        # Mark tests in integration folders
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if "slow" in item.name.lower():
            item.add_marker(pytest.mark.slow)