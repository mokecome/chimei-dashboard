# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Chime Dashboard (奇美食品客服語音分析系統) - a full-stack voice analysis system for customer service feedback. The system consists of a FastAPI backend and Vue 3 frontend that together provide ASR (Automatic Speech Recognition), AI-powered analysis of customer calls, and a dashboard for managing and visualizing the results.

**Key Components:**
- **Backend**: FastAPI Python API with MySQL database, JWT authentication, and AI integration
- **Frontend**: Vue 3 TypeScript SPA with Element Plus UI framework
- **AI Processing**: Whisper for speech-to-text, Ollama/Qwen for content analysis
- **Architecture**: Full-stack with role-based permissions (admin/manager/operator/viewer)

## Development Commands

### Backend Development
```bash
# Navigate to backend directory first
cd backend

# Setup virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database (creates tables and default admin user)
python scripts/init_db.py

# Reset database (WARNING: deletes all data)
python scripts/init_db.py --reset

# Start development server (runs on http://localhost:8100)
python run_server.py

# Run all API tests
python app/tests/test_api.py

# Test specific functionality
python app/tests/test_api.py --test login
python app/tests/test_api.py --test file_upload

# Run pytest for more detailed testing
pytest app/tests/ -v
pytest app/tests/test_auth.py -v  # Specific test file
pytest -k "test_login" -v         # Specific test by name

# Create new user via script
python scripts/create_user.py

# Database migrations (if needed)
alembic upgrade head    # Apply migrations
alembic downgrade -1    # Rollback one migration
alembic history         # View migration history

# Production deployment
uvicorn app.main:app --host 0.0.0.0 --port 8100 --workers 4
```

### Frontend Development
```bash
# Navigate to frontend directory first
cd frontend

# Install dependencies
npm install

# Start development server (runs on http://localhost:3000)
# Automatically proxies /api requests to backend on port 8100
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting with auto-fix
npm run lint

# TypeScript type checking
npm run type-check

# Test backend API connectivity (requires backend running)
node test-api.js
```

### Docker Development
```bash
# From project root, start both services
docker-compose up

# Build and start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Architecture Overview

### System Architecture
The application follows a modern full-stack architecture with clear separation of concerns:

**Backend (FastAPI)**
- **Layered Architecture**: API → Service → Repository → Model layers
- **Authentication**: JWT-based with role-based access control (RBAC)
- **Database**: MySQL 8.0 with SQLAlchemy 2.0 ORM
- **AI Integration**: Async processing for Whisper (speech-to-text) and Ollama/Qwen (analysis)
- **File Processing**: Multi-format support (WAV, MP3, TXT) with async upload handling

**Frontend (Vue 3)**
- **Modern Vue**: Composition API with TypeScript
- **State Management**: Pinia for global state
- **UI Framework**: Element Plus with auto-import
- **Charts**: ECharts integration for data visualization
- **Build Tool**: Vite with optimized chunking

### Key Design Patterns

**Backend Patterns:**
- **Repository Pattern**: Clean data access abstraction
- **Service Pattern**: Business logic encapsulation  
- **Dependency Injection**: Database sessions and user context via FastAPI dependencies
- **DTO Pattern**: Pydantic models for request/response validation
- **Async Processing**: Background tasks for AI operations

**Frontend Patterns:**
- **Composition API**: Modern Vue 3 reactive patterns
- **Store Pattern**: Centralized state with Pinia
- **Component Architecture**: Organized by feature and reusability
- **Route Guards**: Authentication and permission-based navigation

### Authentication & Authorization System

**Four-Tier Role System:**
- **admin**: Full access to all features including user management
- **manager**: Can manage files, labels, and view all data
- **operator**: Can upload files and view dashboard/analysis
- **viewer**: Read-only access to dashboard and data

**Security Implementation:**
- JWT access/refresh tokens with automatic renewal
- Password hashing using bcrypt
- Route guards on both frontend and backend
- Permission decorators for API endpoints
- Secure token storage and automatic logout on token expiry

### Data Flow Architecture

**File Processing Flow:**
1. Frontend uploads files via drag-drop or file picker
2. Backend validates file types and stores in `/storage/uploads/`
3. Async background task processes files through AI pipeline
4. Whisper model converts speech to text
5. Ollama/Qwen model analyzes content for insights
6. Results stored in database with metadata
7. Frontend displays results in dashboard and analysis views

**API Request Flow:**
1. Frontend sends request with JWT Bearer token
2. FastAPI validates token and extracts user permissions
3. Route handler checks required permissions via decorators
4. Service layer processes business logic
5. Repository layer handles database operations
6. Response formatted via Pydantic schemas and returned

### Database Schema Design

**Core Entities:**
- **User**: Authentication and role management
- **VoiceFile**: Uploaded audio/text files with metadata
- **VoiceAnalysis**: AI analysis results linked to files
- **ProductLabel**: Classification labels for products
- **FeedbackCategory**: Categorization of customer feedback types

**Key Relationships:**
- User → VoiceFile (many-to-many through analysis)
- VoiceFile → VoiceAnalysis (one-to-many)
- Analysis results linked to labels and categories
- Audit fields (created_at, updated_at) on all models

## Development Considerations

### Performance Optimizations
- **Backend**: Database connection pooling, async I/O operations, Redis caching support
- **Frontend**: Code splitting, lazy loading, optimized build chunks
- **AI Processing**: Background task queues to prevent blocking requests
- **Database**: Proper indexing on query fields, pagination on list endpoints

### Security Best Practices
- All passwords hashed with bcrypt
- SQL injection prevention via ORM
- CORS properly configured for frontend integration
- Input validation on all endpoints
- Secrets managed via environment variables
- Default credentials should be changed in production

### Error Handling Strategy
- Global exception handlers with consistent error response format
- Detailed logging for debugging without exposing sensitive data
- Graceful degradation when AI services are unavailable
- Client-side error boundaries and user-friendly error messages

### Testing Strategy
- **Backend**: pytest with async support, SQLite test database, comprehensive fixtures
- **Frontend**: Component testing setup available, API integration testing
- **Integration**: End-to-end testing between frontend and backend
- **Test Data**: Factory pattern for creating test objects

## Important Notes

### Default Credentials
- **Admin User**: `admin@chimei.com` / `admin123`
- **MySQL Root**: `123456`
- **Database**: `chime_dashboard`
- **⚠️ Change these in production environments**

### Environment Configuration
Both frontend and backend support environment-specific configuration:
- **Backend**: `.env` files with database URLs, secret keys, AI service endpoints
- **Frontend**: Vite environment variables for API base URLs and app settings
- **Docker**: Environment variables configured in docker-compose.yml

### AI Service Dependencies
The system integrates with external AI services:
- **Whisper Model**: For speech-to-text conversion
- **Ollama/Qwen**: For content analysis and insights
- **Configuration**: LLM_API_URL should point to running Ollama instance
- **Fallback**: System handles AI service unavailability gracefully

### File Storage
- **Development**: Local storage in `backend/storage/uploads/`
- **Production**: Configure appropriate file storage solution
- **Formats**: WAV, MP3 for audio; TXT for text files
- **Processing**: Async handling prevents blocking during large file uploads