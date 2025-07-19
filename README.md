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
- **Frontend**: React.js application
- **Backend**: FastAPI with SQLite database
- **Qdrant**: Vector database for embeddings (local Docker instance)
- **MinIO**: Object storage for files

### Database Credentials
- **MinIO Console**:
  - Username: `daomed`
  - Password: `daomed_secret`
- **PostgreSQL**:
  - Database: `daomed_db`
  - Username: `daomed`
  - Password: `daomed_pass`

## Features

- User authentication (login/register)
- Knowledge base management
- Vietnamese medical Q&A
- Conversation history
- File upload and management

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

## API Endpoints

- `POST /api/chat/login` - User login
- `POST /api/chat/register` - User registration
- `POST /api/chat/logout` - User logout
- `POST /api/chat/send` - Send chat message
- `GET /api/chat/history` - Get chat history
- `GET /api/chat/conversations` - Get conversations list
- `GET /api/chat/dialogs` - Get dialogs list
