#!/bin/bash

echo "🚀 Aurora Web Scraper Setup"
echo "============================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install playwright selenium requests beautifulsoup4 openai pandas fake-useragent python-dotenv aiohttp flask fastapi uvicorn undetected-chromedriver selenium-stealth webdriver-manager lxml

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install

# Create downloads directory
echo "📁 Creating downloads directory..."
mkdir -p downloads

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# OpenAI API Configuration (REQUIRED)
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Proxy Configuration (for anonymity)
# PROXY_URL=http://username:password@proxy-server:port

# Optional: Browser Configuration
HEADLESS=true
USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36

# Optional: Rate Limiting
REQUEST_DELAY=2
MAX_RETRIES=3

# Optional: Output Configuration
OUTPUT_FORMAT=json
SAVE_SCREENSHOTS=false

# Optional: Backend Proxy Configuration
BACKEND_PROXY_URL=http://localhost:8000
EOF
    echo "⚠️  IMPORTANT: Please edit .env file and add your OpenAI API key!"
else
    echo "✅ .env file already exists"
fi

# Test installation
echo "🧪 Testing installation..."
python3 -c "import playwright, selenium, requests, bs4, openai, pandas, flask, fastapi, uvicorn; print('✅ All dependencies installed successfully!')"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Run: python3 start_aurora.py"
echo "3. Open http://localhost:8080 in your browser"
echo ""
echo "🔑 Get your OpenAI API key from: https://platform.openai.com/api-keys" 