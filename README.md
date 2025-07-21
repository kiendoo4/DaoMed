## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Node.js 16+
- **Git LFS** (for model download)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
```

### 2. Download Vietnamese Embedding Model (Bắt buộc)

**Chạy script tự động (bắt buộc, không dùng git clone/git lfs):**

```bash
cd backend/models
python download_embedding_model.py
cd ../..
```

> **Lưu ý:**
> - Phải chạy script này trước khi build Docker hoặc chạy backend.
> - Nếu chạy trên Docker, model phải có sẵn trong thư mục `backend/models/vietnamese-bi-encoder` trước khi build Docker image.
> - Nếu chạy local, cũng phải pull model về đúng thư mục này.

### 3. Setup Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install Node.js dependencies  
cd frontend
npm install
cd ..
```

### 4. Initialize Database

```bash
cd backend
source ../.venv/bin/activate
python init_db.py
cd ..
```

### 5. Build Docker image (nếu dùng Docker)

```bash
docker-compose build backend
```

### 6. Start Services

**Option 1: Using startup script (Recommended)**
```bash
chmod +x start.sh
./start.sh
```

**Option 2: Manual setup**
```bash
docker-compose up -d
cd backend
python run.py
# In another terminal:
cd frontend
npm start
```

### 7. Access Application
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
