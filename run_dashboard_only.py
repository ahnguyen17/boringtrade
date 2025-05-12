"""
Run only the web dashboard for the BoringTrade trading bot.
This script doesn't import the main bot, so it avoids dependency issues.
"""
import os
import sys
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import only the web dashboard
from web.app import app, socketio

if __name__ == "__main__":
    print(f"Starting web dashboard at http://localhost:5000")
    print("Note: The trading bot is not running, only the dashboard.")
    print("Press Ctrl+C to stop the dashboard.")
    
    # Run the Flask app
    socketio.run(app, host="127.0.0.1", port=5000)
