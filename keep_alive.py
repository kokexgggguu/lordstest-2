from flask import Flask, jsonify
from threading import Thread
import time
import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "✅ Bot is running!",
        "message": "Discord Bot Keep-Alive Server",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "uptime": time.time(),
        "bot_status": "running"
    })

@app.route('/ping')
def ping():
    return jsonify({"response": "pong", "timestamp": time.time()})

def run_flask():
    """Run Flask server"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def keep_alive():
    """Keep the bot alive by running Flask server"""
    logger.info("🔥 Starting Keep-Alive Flask server...")
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    logger.info("🚀 Keep-Alive server started on port 5000!")

def self_ping():
    """Self-ping to keep the service alive"""
    try:
        # Get the repl URL
        repl_url = os.getenv('REPLIT_DOMAINS', 'localhost:5000').split(',')[0]
        if not repl_url.startswith('http'):
            repl_url = f"https://{repl_url}"
        
        response = requests.get(f"{repl_url}/ping", timeout=10)
        if response.status_code == 200:
            logger.info("🏓 Self-ping successful!")
        else:
            logger.warning(f"⚠️ Self-ping returned status: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Self-ping failed: {e}")

def start_self_ping():
    """Start periodic self-ping in background"""
    def ping_loop():
        while True:
            time.sleep(300)  # Ping every 5 minutes
            self_ping()
    
    t = Thread(target=ping_loop)
    t.daemon = True
    t.start()
    logger.info("⏰ Self-ping scheduler started!")

if __name__ == "__main__":
    keep_alive()
    start_self_ping()
    
    # Keep the main thread alive
    while True:
        time.sleep(1)