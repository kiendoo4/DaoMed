#!/bin/bash

echo "Stopping DaoMed services..."

# Stop Docker services
echo "Stopping Docker services..."
docker-compose down

# Kill any remaining Python processes
echo "Stopping backend processes..."
pkill -f "python3 run.py"
pkill -f "python run.py"
pkill -f "run.py"
pkill -f "flask"

# Kill any remaining Node processes
echo "Stopping frontend processes..."
pkill -f "react-scripts start"
pkill -f "node.*3000"

# Force kill any processes on the ports
echo "Force killing processes on ports 3000 and 5050..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:5050 | xargs kill -9 2>/dev/null || true

echo "All services stopped!" 