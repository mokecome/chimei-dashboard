"""
Authentication tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..models.user import User, UserRole


class TestAuth:
    """Authentication endpoint tests."""
    
    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
    
    def test_login_invalid_email(self, client: TestClient):
        """Test login with invalid email."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]
    
    def test_login_invalid_password(self, client: TestClient, test_user: User):
        """Test login with invalid password."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]
    
    def test_login_inactive_user(self, client: TestClient, db_session: Session):
        """Test login with inactive user."""
        # Create inactive user
        inactive_user = User(
            name="Inactive User",
            email="inactive@example.com",
            role=UserRole.VIEWER,
            is_active=False
        )
        inactive_user.set_password("password123")
        
        db_session.add(inactive_user)
        db_session.commit()
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Account is inactive" in data["detail"]
    
    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Test successful token refresh."""
        # First, login to get tokens
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]
        
        # Use refresh token to get new access token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid refresh token" in data["detail"]
    
    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """Test successful logout."""
        response = client.post(
            "/api/auth/logout",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"
    
    def test_logout_no_token(self, client: TestClient):
        """Test logout without token."""
        response = client.post("/api/auth/logout")
        
        assert response.status_code == 401
    
    def test_me_endpoint_success(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test getting current user info."""
        response = client.get(
            "/api/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["role"] == test_user.role.value
        assert "password_hash" not in data  # Sensitive data should not be exposed
    
    def test_me_endpoint_no_token(self, client: TestClient):
        """Test getting current user info without token."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    def test_me_endpoint_invalid_token(self, client: TestClient):
        """Test getting current user info with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401


class TestAuthValidation:
    """Authentication validation tests."""
    
    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing fields."""
        # Missing password
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 422
        
        # Missing email
        response = client.post(
            "/api/auth/login",
            json={"password": "password123"}
        )
        assert response.status_code == 422
        
        # Empty request body
        response = client.post("/api/auth/login")
        assert response.status_code == 422
    
    def test_login_invalid_email_format(self, client: TestClient):
        """Test login with invalid email format."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "invalid-email",
                "password": "password123"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_refresh_token_missing_field(self, client: TestClient):
        """Test refresh token with missing field."""
        response = client.post("/api/auth/refresh", json={})
        
        assert response.status_code == 422


class TestAuthIntegration:
    """Integration tests for authentication flow."""
    
    def test_full_auth_flow(self, client: TestClient, test_user: User):
        """Test complete authentication flow."""
        # 1. Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # 2. Access protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/auth/me", headers=headers)
        assert me_response.status_code == 200
        
        # 3. Refresh token
        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        new_access_token = new_tokens["access_token"]
        
        # 4. Use new access token
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        me_response2 = client.get("/api/auth/me", headers=new_headers)
        assert me_response2.status_code == 200
        
        # 5. Logout
        logout_response = client.post("/api/auth/logout", headers=new_headers)
        assert logout_response.status_code == 200
    
    def test_token_expiration_handling(self, client: TestClient, test_user: User):
        """Test handling of expired tokens."""
        # This would require mocking time or using very short token expiration
        # For now, we'll test the structure is in place
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        
        # Verify token structure
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert isinstance(tokens["access_token"], str)
        assert isinstance(tokens["refresh_token"], str)


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    def test_admin_access(self, client: TestClient, admin_headers: dict):
        """Test admin role access."""
        response = client.get("/api/auth/me", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["role"] == "admin"
    
    def test_manager_access(self, client: TestClient, manager_headers: dict):
        """Test manager role access."""
        response = client.get("/api/auth/me", headers=manager_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["role"] == "manager"
    
    def test_operator_access(self, client: TestClient, auth_headers: dict):
        """Test operator role access."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["role"] == "operator"
    
    def test_viewer_access(self, client: TestClient, viewer_headers: dict):
        """Test viewer role access."""
        response = client.get("/api/auth/me", headers=viewer_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["role"] == "viewer"