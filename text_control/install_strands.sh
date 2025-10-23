#!/bin/bash

echo "🚀 Installing Strands Agents integration..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install strands-agents

# Create session directory
echo "📁 Creating agent sessions directory..."
mkdir -p agent_sessions

# Set permissions
chmod +x test_strands.py

echo "✅ Strands Agents integration installed!"
echo ""
echo "🔧 Available endpoints:"
echo "  📡 Streaming SSE: POST /api/talk"
echo "  🔄 Non-streaming: POST /xiaoice-chat-api-strands"
echo "  🌐 Original: POST /xiaoice-chat-api"
echo ""
echo "🧪 Test with: python test_strands.py"
echo "🏃 Run with: python app.py"
