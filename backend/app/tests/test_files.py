"""
File management tests.
"""
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..models.file import VoiceFile, FileStatus, FileFormat
from ..models.user import User


class TestFileUpload:
    """File upload endpoint tests."""
    
    def test_upload_file_success(self, client: TestClient, auth_headers: dict, temp_upload_dir: str):
        """Test successful file upload."""
        # Create a test file
        test_content = b"test audio content"
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                response = client.post(
                    "/api/files/upload",
                    headers=auth_headers,
                    files={"file": ("test_audio.wav", f, "audio/wav")}
                )
            
            assert response.status_code == 201
            data = response.json()
            
            assert "id" in data
            assert data["filename"] == "test_audio.wav"
            assert data["original_filename"] == "test_audio.wav"
            assert data["file_size"] == len(test_content)
            assert data["file_format"] == "wav"
            assert data["status"] == "pending"
            
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def test_upload_file_no_auth(self, client: TestClient):
        """Test file upload without authentication."""
        test_content = b"test content"
        
        response = client.post(
            "/api/files/upload",
            files={"file": ("test.wav", test_content, "audio/wav")}
        )
        
        assert response.status_code == 401
    
    def test_upload_file_invalid_format(self, client: TestClient, auth_headers: dict):
        """Test upload with invalid file format."""
        test_content = b"test content"
        
        response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("test.xyz", test_content, "application/octet-stream")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid file format" in data["detail"]
    
    def test_upload_file_too_large(self, client: TestClient, auth_headers: dict):
        """Test upload with file too large."""
        # Create a large file content (exceeding MAX_FILE_SIZE)
        large_content = b"x" * (200 * 1024 * 1024)  # 200MB
        
        response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("large_file.wav", large_content, "audio/wav")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "File too large" in data["detail"]
    
    def test_upload_no_file(self, client: TestClient, auth_headers: dict):
        """Test upload without file."""
        response = client.post(
            "/api/files/upload",
            headers=auth_headers
        )
        
        assert response.status_code == 422


class TestFileRetrieval:
    """File retrieval tests."""
    
    def test_get_file_success(self, client: TestClient, auth_headers: dict, test_file: VoiceFile):
        """Test successful file retrieval."""
        response = client.get(
            f"/api/files/{test_file.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(test_file.id)
        assert data["filename"] == test_file.filename
        assert data["file_size"] == test_file.file_size
    
    def test_get_file_not_found(self, client: TestClient, auth_headers: dict):
        """Test retrieval of non-existent file."""
        response = client.get(
            "/api/files/nonexistent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_file_no_auth(self, client: TestClient, test_file: VoiceFile):
        """Test file retrieval without authentication."""
        response = client.get(f"/api/files/{test_file.id}")
        
        assert response.status_code == 401
    
    def test_list_files_success(self, client: TestClient, auth_headers: dict, test_file: VoiceFile):
        """Test successful file listing."""
        response = client.get(
            "/api/files/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["items"]) >= 1
    
    def test_list_files_pagination(self, client: TestClient, auth_headers: dict, db_session: Session, test_user: User):
        """Test file listing pagination."""
        # Create multiple files
        for i in range(5):
            file = VoiceFile(
                filename=f"test_file_{i}.wav",
                original_filename=f"test_file_{i}.wav",
                file_path=f"/tmp/test_file_{i}.wav",
                file_size=1024,
                file_format=FileFormat.WAV,
                status=FileStatus.PENDING,
                uploaded_by=test_user.id
            )
            db_session.add(file)
        
        db_session.commit()
        
        # Test pagination
        response = client.get(
            "/api/files/?page=1&page_size=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2
    
    def test_list_files_filter_by_status(self, client: TestClient, auth_headers: dict, completed_file: VoiceFile):
        """Test file listing with status filter."""
        response = client.get(
            "/api/files/?status=completed",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned files should have completed status
        for item in data["items"]:
            assert item["status"] == "completed"
    
    def test_search_files(self, client: TestClient, auth_headers: dict, test_file: VoiceFile):
        """Test file search functionality."""
        response = client.get(
            f"/api/files/search?q={test_file.filename[:5]}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        # Should find the test file
        found = any(item["id"] == str(test_file.id) for item in data["items"])
        assert found


class TestFileManagement:
    """File management tests."""
    
    def test_delete_file_success(self, client: TestClient, auth_headers: dict, test_file: VoiceFile):
        """Test successful file deletion."""
        response = client.delete(
            f"/api/files/{test_file.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "File deleted successfully"
    
    def test_delete_file_not_found(self, client: TestClient, auth_headers: dict):
        """Test deletion of non-existent file."""
        response = client.delete(
            "/api/files/nonexistent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_file_no_permission(self, client: TestClient, viewer_headers: dict, test_file: VoiceFile):
        """Test file deletion without permission."""
        response = client.delete(
            f"/api/files/{test_file.id}",
            headers=viewer_headers
        )
        
        assert response.status_code == 403
    
    def test_update_file_metadata(self, client: TestClient, auth_headers: dict, test_file: VoiceFile):
        """Test updating file metadata."""
        update_data = {
            "filename": "updated_filename.wav"
        }
        
        response = client.put(
            f"/api/files/{test_file.id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "updated_filename.wav"


class TestFileProcessing:
    """File processing tests."""
    
    def test_start_analysis(self, client: TestClient, auth_headers: dict, test_file: VoiceFile):
        """Test starting file analysis."""
        response = client.post(
            f"/api/files/{test_file.id}/analyze",
            headers=auth_headers
        )
        
        # This might return 202 (accepted) for async processing
        # or 200 for immediate processing, depending on implementation
        assert response.status_code in [200, 202]
    
    def test_get_processing_status(self, client: TestClient, auth_headers: dict, test_file: VoiceFile):
        """Test getting file processing status."""
        response = client.get(
            f"/api/files/{test_file.id}/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["pending", "processing", "completed", "failed"]
    
    def test_get_file_statistics(self, client: TestClient, auth_headers: dict):
        """Test getting file statistics."""
        response = client.get(
            "/api/files/statistics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_files" in data
        assert "status_distribution" in data
        assert "format_distribution" in data


class TestFilePermissions:
    """File permission tests."""
    
    def test_admin_can_access_all_files(self, client: TestClient, admin_headers: dict, test_file: VoiceFile):
        """Test admin can access all files."""
        response = client.get(
            f"/api/files/{test_file.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
    
    def test_manager_can_manage_files(self, client: TestClient, manager_headers: dict, test_file: VoiceFile):
        """Test manager can manage files."""
        # Manager should be able to view files
        response = client.get(
            f"/api/files/{test_file.id}",
            headers=manager_headers
        )
        assert response.status_code == 200
        
        # Manager should be able to delete files
        response = client.delete(
            f"/api/files/{test_file.id}",
            headers=manager_headers
        )
        assert response.status_code == 200
    
    def test_operator_can_upload_and_view(self, client: TestClient, auth_headers: dict, test_file: VoiceFile):
        """Test operator can upload and view files."""
        # Operator should be able to view files
        response = client.get(
            f"/api/files/{test_file.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Operator should be able to upload files (tested in upload tests)
    
    def test_viewer_readonly_access(self, client: TestClient, viewer_headers: dict, test_file: VoiceFile):
        """Test viewer has read-only access."""
        # Viewer should be able to view files
        response = client.get(
            f"/api/files/{test_file.id}",
            headers=viewer_headers
        )
        assert response.status_code == 200
        
        # Viewer should NOT be able to delete files
        response = client.delete(
            f"/api/files/{test_file.id}",
            headers=viewer_headers
        )
        assert response.status_code == 403


class TestFileValidation:
    """File validation tests."""
    
    def test_file_size_validation(self, client: TestClient, auth_headers: dict):
        """Test file size validation."""
        # Test with very small file (should pass if there's a minimum size requirement)
        small_content = b"x"
        
        response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("small.wav", small_content, "audio/wav")}
        )
        
        # Should either succeed or fail with specific validation error
        assert response.status_code in [201, 400]
    
    def test_filename_validation(self, client: TestClient, auth_headers: dict):
        """Test filename validation."""
        test_content = b"test content"
        
        # Test with invalid characters in filename
        response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("test<>file.wav", test_content, "audio/wav")}
        )
        
        # Should handle invalid filename gracefully
        assert response.status_code in [201, 400]
    
    def test_file_format_detection(self, client: TestClient, auth_headers: dict):
        """Test file format detection."""
        test_content = b"test content"
        
        # Test with mismatched extension and content type
        response = client.post(
            "/api/files/upload",
            headers=auth_headers,
            files={"file": ("test.wav", test_content, "audio/mp3")}
        )
        
        # Should handle format mismatch appropriately
        assert response.status_code in [201, 400]