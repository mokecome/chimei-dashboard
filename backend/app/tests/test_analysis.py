"""
Analysis functionality tests.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..models.file import VoiceFile, FileStatus
from ..models.analysis import VoiceAnalysis, SentimentType
from ..models.user import User


class TestAnalysisCreation:
    """Analysis creation tests."""
    
    def test_create_analysis_success(self, client: TestClient, auth_headers: dict, completed_file: VoiceFile):
        """Test successful analysis creation."""
        analysis_data = {
            "file_id": str(completed_file.id),
            "transcript": "这是一段测试语音转文本",
            "sentiment": "positive",
            "feedback_category": "产品咨询",
            "feedback_summary": "客户询问产品信息",
            "product_names": ["测试产品A"]
        }
        
        response = client.post(
            "/api/analysis/",
            headers=auth_headers,
            json=analysis_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["file_id"] == str(completed_file.id)
        assert data["transcript"] == analysis_data["transcript"]
        assert data["sentiment"] == "positive"
        assert data["feedback_category"] == analysis_data["feedback_category"]
    
    def test_create_analysis_file_not_found(self, client: TestClient, auth_headers: dict):
        """Test analysis creation with non-existent file."""
        analysis_data = {
            "file_id": "nonexistent-id",
            "transcript": "测试文本",
            "sentiment": "neutral"
        }
        
        response = client.post(
            "/api/analysis/",
            headers=auth_headers,
            json=analysis_data
        )
        
        assert response.status_code == 404
    
    def test_create_analysis_no_auth(self, client: TestClient, completed_file: VoiceFile):
        """Test analysis creation without authentication."""
        analysis_data = {
            "file_id": str(completed_file.id),
            "transcript": "测试文本"
        }
        
        response = client.post(
            "/api/analysis/",
            json=analysis_data
        )
        
        assert response.status_code == 401
    
    def test_create_analysis_invalid_sentiment(self, client: TestClient, auth_headers: dict, completed_file: VoiceFile):
        """Test analysis creation with invalid sentiment."""
        analysis_data = {
            "file_id": str(completed_file.id),
            "transcript": "测试文本",
            "sentiment": "invalid_sentiment"
        }
        
        response = client.post(
            "/api/analysis/",
            headers=auth_headers,
            json=analysis_data
        )
        
        assert response.status_code == 422


class TestAnalysisRetrieval:
    """Analysis retrieval tests."""
    
    def test_get_analysis_success(self, client: TestClient, auth_headers: dict, test_analysis: VoiceAnalysis):
        """Test successful analysis retrieval."""
        response = client.get(
            f"/api/analysis/{test_analysis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(test_analysis.id)
        assert data["transcript"] == test_analysis.transcript
        assert data["sentiment"] == test_analysis.sentiment.value
    
    def test_get_analysis_not_found(self, client: TestClient, auth_headers: dict):
        """Test retrieval of non-existent analysis."""
        response = client.get(
            "/api/analysis/nonexistent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_analysis_by_file(self, client: TestClient, auth_headers: dict, test_analysis: VoiceAnalysis, completed_file: VoiceFile):
        """Test getting analysis by file ID."""
        response = client.get(
            f"/api/analysis/file/{completed_file.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["file_id"] == str(completed_file.id)
        assert data["id"] == str(test_analysis.id)
    
    def test_list_analyses_success(self, client: TestClient, auth_headers: dict, test_analysis: VoiceAnalysis):
        """Test successful analysis listing."""
        response = client.get(
            "/api/analysis/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
    
    def test_list_analyses_pagination(self, client: TestClient, auth_headers: dict, db_session: Session, completed_file: VoiceFile):
        """Test analysis listing pagination."""
        # Create multiple analyses
        for i in range(5):
            analysis = VoiceAnalysis(
                file_id=completed_file.id,
                transcript=f"测试转录文本 {i}",
                sentiment=SentimentType.NEUTRAL,
                feedback_category="测试分类",
                feedback_summary=f"测试摘要 {i}"
            )
            db_session.add(analysis)
        
        db_session.commit()
        
        response = client.get(
            "/api/analysis/?page=1&page_size=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2
    
    def test_filter_analyses_by_sentiment(self, client: TestClient, auth_headers: dict, test_analysis: VoiceAnalysis):
        """Test filtering analyses by sentiment."""
        response = client.get(
            f"/api/analysis/?sentiment={test_analysis.sentiment.value}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned analyses should have the specified sentiment
        for item in data["items"]:
            assert item["sentiment"] == test_analysis.sentiment.value
    
    def test_search_analyses(self, client: TestClient, auth_headers: dict, test_analysis: VoiceAnalysis):
        """Test searching analyses by text content."""
        search_term = test_analysis.transcript[:10]  # Use first 10 characters
        
        response = client.get(
            f"/api/analysis/search?q={search_term}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        # Should find the test analysis
        found = any(item["id"] == str(test_analysis.id) for item in data["items"])
        assert found


class TestAnalysisProcessing:
    """Analysis processing tests."""
    
    @patch('app.ai.speech_to_text.speech_service.speech_to_text')
    @patch('app.ai.llm_analyzer.analyze_feedback')
    def test_process_file_analysis_success(self, mock_llm, mock_stt, client: TestClient, auth_headers: dict, test_file: VoiceFile):
        """Test successful file analysis processing."""
        # Mock the AI services
        mock_stt.return_value = "这是一段测试语音转文本的结果"
        mock_llm.return_value = {
            "evaluation_tendency": "positive",
            "feedback_category": "产品咨询",
            "feedback_summary": "客户询问产品相关信息",
            "product_name": "测试产品A"
        }
        
        response = client.post(
            f"/api/analysis/process/{test_file.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "analysis_id" in data
        assert data["message"] == "Analysis completed successfully"
    
    @patch('app.ai.speech_to_text.speech_service.speech_to_text')
    def test_process_file_analysis_stt_failure(self, mock_stt, client: TestClient, auth_headers: dict, test_file: VoiceFile):
        """Test file analysis with speech-to-text failure."""
        # Mock STT failure
        mock_stt.return_value = None
        
        response = client.post(
            f"/api/analysis/process/{test_file.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "error" in data
        assert "Failed to transcribe audio" in data["error"]
    
    @patch('app.ai.speech_to_text.speech_service.speech_to_text')
    @patch('app.ai.llm_analyzer.analyze_feedback')
    def test_process_file_analysis_llm_failure(self, mock_llm, mock_stt, client: TestClient, auth_headers: dict, test_file: VoiceFile):
        """Test file analysis with LLM analysis failure."""
        # Mock successful STT but failed LLM
        mock_stt.return_value = "测试转录文本"
        mock_llm.return_value = {"error": "LLM analysis failed"}
        
        response = client.post(
            f"/api/analysis/process/{test_file.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "error" in data
        assert "Analysis failed" in data["error"]
    
    def test_process_file_already_analyzed(self, client: TestClient, auth_headers: dict, test_analysis: VoiceAnalysis, completed_file: VoiceFile):
        """Test processing file that already has analysis."""
        response = client.post(
            f"/api/analysis/process/{completed_file.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "error" in data
        assert "Analysis already exists" in data["error"]
    
    def test_process_nonexistent_file(self, client: TestClient, auth_headers: dict):
        """Test processing non-existent file."""
        response = client.post(
            "/api/analysis/process/nonexistent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "error" in data
        assert "File not found" in data["error"]


class TestAnalysisStatistics:
    """Analysis statistics tests."""
    
    def test_get_analysis_statistics(self, client: TestClient, auth_headers: dict, test_analysis: VoiceAnalysis):
        """Test getting analysis statistics."""
        response = client.get(
            "/api/analysis/statistics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_analyses" in data
        assert "sentiment_distribution" in data
        assert "product_distribution" in data
        assert "category_distribution" in data
        assert "daily_trend" in data
        assert "recent_analyses" in data
    
    def test_get_sentiment_distribution(self, client: TestClient, auth_headers: dict, db_session: Session, completed_file: VoiceFile):
        """Test getting sentiment distribution."""
        # Create analyses with different sentiments
        sentiments = [SentimentType.POSITIVE, SentimentType.NEGATIVE, SentimentType.NEUTRAL]
        
        for sentiment in sentiments:
            analysis = VoiceAnalysis(
                file_id=completed_file.id,
                transcript=f"测试文本 {sentiment.value}",
                sentiment=sentiment,
                feedback_category="测试分类",
                feedback_summary="测试摘要"
            )
            db_session.add(analysis)
        
        db_session.commit()
        
        response = client.get(
            "/api/analysis/statistics/sentiment",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have counts for different sentiments
        for sentiment in sentiments:
            assert sentiment.value in data
            assert isinstance(data[sentiment.value], int)
    
    def test_get_category_trends(self, client: TestClient, auth_headers: dict, test_analysis: VoiceAnalysis):
        """Test getting category trends."""
        response = client.get(
            "/api/analysis/trends/categories",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should have category information
        if data:
            assert "category" in data[0]
            assert "count" in data[0]


class TestAnalysisPermissions:
    """Analysis permission tests."""
    
    def test_admin_full_access(self, client: TestClient, admin_headers: dict, test_analysis: VoiceAnalysis):
        """Test admin has full access to analyses."""
        # Admin can view analysis
        response = client.get(
            f"/api/analysis/{test_analysis.id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Admin can view statistics
        response = client.get(
            "/api/analysis/statistics",
            headers=admin_headers
        )
        assert response.status_code == 200
    
    def test_manager_analysis_access(self, client: TestClient, manager_headers: dict, test_analysis: VoiceAnalysis):
        """Test manager can access analyses and statistics."""
        response = client.get(
            f"/api/analysis/{test_analysis.id}",
            headers=manager_headers
        )
        assert response.status_code == 200
        
        response = client.get(
            "/api/analysis/statistics",
            headers=manager_headers
        )
        assert response.status_code == 200
    
    def test_operator_analysis_access(self, client: TestClient, auth_headers: dict, test_analysis: VoiceAnalysis):
        """Test operator can view analyses."""
        response = client.get(
            f"/api/analysis/{test_analysis.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_viewer_readonly_analysis(self, client: TestClient, viewer_headers: dict, test_analysis: VoiceAnalysis):
        """Test viewer has read-only access to analyses."""
        # Viewer can view analysis
        response = client.get(
            f"/api/analysis/{test_analysis.id}",
            headers=viewer_headers
        )
        assert response.status_code == 200
        
        # Viewer should NOT be able to create analysis (if such endpoint exists)
        # This test depends on the actual permission implementation


class TestAnalysisValidation:
    """Analysis validation tests."""
    
    def test_create_analysis_missing_required_fields(self, client: TestClient, auth_headers: dict):
        """Test analysis creation with missing required fields."""
        # Missing file_id
        response = client.post(
            "/api/analysis/",
            headers=auth_headers,
            json={"transcript": "测试文本"}
        )
        assert response.status_code == 422
        
        # Missing transcript
        response = client.post(
            "/api/analysis/",
            headers=auth_headers,
            json={"file_id": "some-id"}
        )
        assert response.status_code == 422
    
    def test_analysis_text_length_validation(self, client: TestClient, auth_headers: dict, completed_file: VoiceFile):
        """Test analysis text length validation."""
        # Very long transcript
        long_transcript = "x" * 10000
        
        response = client.post(
            "/api/analysis/",
            headers=auth_headers,
            json={
                "file_id": str(completed_file.id),
                "transcript": long_transcript
            }
        )
        
        # Should either accept or reject with appropriate validation error
        assert response.status_code in [201, 422]
    
    def test_product_names_format_validation(self, client: TestClient, auth_headers: dict, completed_file: VoiceFile):
        """Test product names format validation."""
        response = client.post(
            "/api/analysis/",
            headers=auth_headers,
            json={
                "file_id": str(completed_file.id),
                "transcript": "测试文本",
                "product_names": ["产品A", "产品B", "产品C"]
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Product names should be stored correctly
        assert "product_names" in data