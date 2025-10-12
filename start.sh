#!/bin/bash

# Quick start script for Discord MQTT Bot

echo "🤖 Discord MQTT Bot - Setup"
echo "================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📋 Copying .env.example to .env..."
    cp .env.example .env
    echo "✅ Please edit .env with your credentials before running the bot."
    echo ""
    echo "Required variables:"
    echo "  - DISCORD_TOKEN"
    echo "  - MQTT_BROKER"
    echo "  - MQTT_USERNAME (if required)"
    echo "  - MQTT_PASSWORD (if required)"
    exit 1
fi

echo "✅ .env file found"
echo ""

# Check if running with Docker
if [ "$1" == "docker" ]; then
    echo "🐳 Starting with Docker Compose..."
    docker-compose up -d
    echo ""
    echo "✅ Bot is running in the background"
    echo "📋 View logs with: docker-compose logs -f"
    echo "🛑 Stop with: docker-compose down"
else
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "🔧 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
    
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    
    echo ""
    echo "🚀 Starting bot..."
    python bot.py
fi
