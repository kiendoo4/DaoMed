# DoctorQA - Vietnamese Medical Question Answering System

A medical question answering system with knowledge base management and user authentication features.

## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Node.js 16+

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd DoctorQA
```

### 2. Pull Vietnamese Embedding Model

```bash
# Download the Vietnamese bi-encoder model
git lfs install
git clone https://huggingface.co/bkai-foundation-models/vietnamese-bi-encoder models/vietnamese-bi-encoder
```

### 3. Start Services

```bash
# Option 1: Using startup script (Recommended)
chmod +x start.sh
./start.sh

# Option 2: Manual setup
docker-compose up -d
cd backend
python init_db.py
python run.py

# In another terminal:
cd frontend
npm install
npm start
```

### 4. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5050
- **Qdrant**: http://localhost:6333
- **MinIO Console**: http://localhost:9101

## Services & Credentials

### Services
- **Frontend**: React.js application with Ant Design
- **Backend**: Flask with PostgreSQL database
- **Qdrant**: Vector database for embeddings (local Docker instance)
- **MinIO**: Object storage for files
- **PostgreSQL**: Primary database for user sessions and chat data

### Database Credentials
- **MinIO Console**:
  - Username: `daomed`
  - Password: `daomed_secret`
- **PostgreSQL**:
  - Database: `daomed_db`
  - Username: `daomed`
  - Password: `daomed_pass`
  - Host: `localhost`
  - Port: `5432`

## Database Schema

### Tables
- **dialogs**: Stores user dialogs/conversations
  - `id`: Primary key
  - `name`: Dialog name
  - `user_id`: User identifier
  - `created_at`: Creation timestamp
  - `updated_at`: Last update timestamp

- **messages**: Stores chat messages
  - `id`: Primary key
  - `dialog_id`: Foreign key to dialogs table
  - `sender`: Message sender ('user' or 'assistant')
  - `content`: Message content
  - `timestamp`: Message timestamp

- **users**: User authentication (managed by Flask-Session)
- **sessions**: User sessions (managed by Flask-Session)

## Features

- User authentication (login/register)
- Knowledge base management with file upload
- Medical traditional Q&A using RAG
- Dialog-based conversation system
- Persistent chat history across sessions
- File upload and management via MinIO
- Vector search using Qdrant
- RAG evaluation

## Stop Services

```bash
# Option 1: Using stop script (Recommended)
./stop.sh

# Option 2: Manual stop
docker-compose down
pkill -f "python run.py"
pkill -f "react-scripts start"
```

## Development

### Backend
```bash
cd backend
pip install -r requirements.txt
python run.py
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Troubleshooting

### Proxy Error
If you see "Proxy error: Could not proxy request":
1. Make sure the backend is running on port 5050
2. Check that the virtual environment is activated
3. Verify all dependencies are installed

### Port Already in Use
If ports are already in use:
1. Stop existing services: `./stop.sh`
2. Check for running processes: `lsof -i :3000` or `lsof -i :5050`
3. Kill conflicting processes if needed

### Database Issues
If messages disappear after restart:
1. Ensure PostgreSQL container is running: `docker ps`
2. Check database connectivity
3. Verify database schema is properly initialized

## API Endpoints

### Authentication
- `POST /api/chat/login` - User login
- `POST /api/chat/register` - User registration
- `POST /api/chat/logout` - User logout

### Chat & Dialogs
- `POST /api/chat/send` - Send chat message
- `GET /api/chat/history/<dialog_id>` - Get chat history for specific dialog
- `GET /api/chat/dialogs` - Get user's dialogs list
- `POST /api/chat/dialogs` - Create new dialog
- `PUT /api/chat/dialogs/<dialog_id>` - Update dialog name
- `DELETE /api/chat/dialogs/<dialog_id>` - Delete dialog

### Knowledge Base
- `GET /api/kb/files` - Get uploaded files
- `POST /api/kb/upload` - Upload file to knowledge base
- `DELETE /api/kb/files/<filename>` - Delete file from knowledge base

### Health Check
- `GET /api/health` - Backend health status

## Recent Changes

- **Database Migration**: Switched from SQLite to PostgreSQL for better scalability
- **Schema Update**: Removed `conversations` table, simplified to `dialogs` and `messages` tables
- **Session Management**: Implemented persistent sessions using Flask-Session with PostgreSQL
- **UI Improvements**: Enhanced dialog creation flow and chat window scrolling
- **API Enhancements**: Improved error handling and response consistency
