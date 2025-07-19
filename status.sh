#!/bin/bash

echo "=== DaoMed Services Status ==="

# Check Docker services
echo -e "\n🐳 Docker Services:"
if docker-compose ps | grep -q "Up"; then
    echo "✅ Docker services are running"
    docker-compose ps
else
    echo "❌ Docker services are not running"
fi

# Check Backend
echo -e "\n🐍 Backend (Port 5050):"
if lsof -i :5050 >/dev/null 2>&1; then
    echo "✅ Backend is running on port 5050"
    if curl -s http://localhost:5050/test-cors >/dev/null 2>&1; then
        echo "✅ Backend API is responding"
    else
        echo "❌ Backend API is not responding"
    fi
else
    echo "❌ Backend is not running"
fi

# Check Frontend
echo -e "\n⚛️  Frontend (Port 3000):"
if lsof -i :3000 >/dev/null 2>&1; then
    echo "✅ Frontend is running on port 3000"
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo "✅ Frontend is accessible"
    else
        echo "❌ Frontend is not accessible"
    fi
else
    echo "❌ Frontend is not running"
fi

# Check Proxy
echo -e "\n🔗 Proxy Status:"
if lsof -i :3000 >/dev/null 2>&1 && lsof -i :5050 >/dev/null 2>&1; then
    echo "✅ Both frontend and backend are running"
    echo "✅ Proxy should be working"
else
    echo "❌ Proxy cannot work - missing services"
fi

echo -e "\n=== End Status ===" 