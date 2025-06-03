#!/bin/bash
set -e

echo "Setting up Visa Developer AI Agent Chat (for macOS/Linux)..."

# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install backend requirements
pip install --upgrade pip
pip install -r requirements.txt

# 3. Check for .env
if [ ! -f ".env" ]; then
    echo "❌ ERROR: Missing .env file. Please create one in the root directory."
    exit 1
fi

# 4. Start backend
echo "Starting FastAPI backend..."
cd backend
uvicorn app:app --reload &
BACKEND_PID=$!
cd ..

# 5. Start frontend
echo "Installing frontend and starting React app..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ App is running!"
echo "Frontend → http://localhost:5173"
echo "Backend  → http://localhost:8000"
echo "Please open your browser to the frontend URL to interact with the app."
echo ""
echo "To stop: kill $BACKEND_PID $FRONTEND_PID"