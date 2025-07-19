#!/bin/bash

echo "🚀 Khởi động DaoMed..."

# Khởi động Docker services
docker-compose up -d

echo "⏳ Chờ services khởi động..."
sleep 5

echo "🐍 Khởi động Backend..."
cd backend
source ../.venv/bin/activate
python3 run.py &
BACKEND_PID=$!
cd ..

echo "🌐 Khởi động Frontend..."
cd frontend
npm start &
FRONTEND_PID=$!

echo "✅ Hệ thống đã sẵn sàng!"
echo ""
echo "📋 Truy cập:"
echo "   Frontend: http://localhost:3000"
echo "   Backend: http://localhost:5050"
echo ""
echo "🛑 Dừng: ./stop.sh hoặc Ctrl+C"

# Đợi người dùng nhấn Ctrl+C
trap "echo ''; echo '🛑 Đang dừng...'; kill $FRONTEND_PID; kill $BACKEND_PID; docker-compose down; echo '✅ Đã dừng.'; exit 0" INT

wait 