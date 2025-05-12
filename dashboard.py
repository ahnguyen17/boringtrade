"""
Standalone dashboard for the BoringTrade trading bot.
"""
# Import eventlet first and monkey patch before any other imports
import eventlet
eventlet.monkey_patch()

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import random

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO

# Create Flask app
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.config["SECRET_KEY"] = "boringtrade-secret-key"
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Set up logger
logger = logging.getLogger("WebDashboard")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Sample data
SAMPLE_CONFIG = {
    "broker": "tastytrade",
    "assets": ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"],
    "orb": {"enabled": True},
    "pdh_pdl": {"enabled": True},
    "ob": {"enabled": True},
    "risk_per_trade": 0.01,
    "max_daily_loss": 0.03,
    "max_trades_per_day": 5,
    "position_size": 1,
    "execution_timeframe": 5,
    "htf_timeframe": 60
}

SAMPLE_TRADES = {
    "active_trades": [
        {
            "id": "trade_1",
            "symbol": "SPY",
            "direction": "LONG",
            "entry_time": (datetime.now() - timedelta(hours=2)).isoformat(),
            "entry_price": 500.25,
            "current_price": 502.75,
            "quantity": 1,
            "stop_loss": 498.50,
            "take_profit": 505.00,
            "strategy": "ORB"
        }
    ],
    "completed_trades": [
        {
            "id": "trade_2",
            "symbol": "AAPL",
            "direction": "LONG",
            "entry_time": (datetime.now() - timedelta(days=1)).isoformat(),
            "exit_time": (datetime.now() - timedelta(hours=4)).isoformat(),
            "entry_price": 180.50,
            "exit_price": 183.25,
            "quantity": 1,
            "result": "WIN",
            "strategy": "PDH_PDL"
        },
        {
            "id": "trade_3",
            "symbol": "TSLA",
            "direction": "SHORT",
            "entry_time": (datetime.now() - timedelta(days=2)).isoformat(),
            "exit_time": (datetime.now() - timedelta(days=1, hours=4)).isoformat(),
            "entry_price": 240.75,
            "exit_price": 235.50,
            "quantity": 1,
            "result": "WIN",
            "strategy": "OB"
        },
        {
            "id": "trade_4",
            "symbol": "QQQ",
            "direction": "LONG",
            "entry_time": (datetime.now() - timedelta(days=3)).isoformat(),
            "exit_time": (datetime.now() - timedelta(days=2, hours=6)).isoformat(),
            "entry_price": 420.25,
            "exit_price": 418.50,
            "quantity": 1,
            "result": "LOSS",
            "strategy": "ORB"
        }
    ]
}

SAMPLE_LEVELS = [
    {
        "id": "level_1",
        "symbol": "SPY",
        "level_type": "ORH",
        "price": 501.25,
        "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "has_been_broken": True,
        "has_been_retested": False,
        "description": "Opening Range High"
    },
    {
        "id": "level_2",
        "symbol": "SPY",
        "level_type": "ORL",
        "price": 498.75,
        "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "has_been_broken": False,
        "has_been_retested": False,
        "description": "Opening Range Low"
    },
    {
        "id": "level_3",
        "symbol": "AAPL",
        "level_type": "PDH",
        "price": 184.50,
        "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "has_been_broken": False,
        "has_been_retested": False,
        "description": "Previous Day High"
    },
    {
        "id": "level_4",
        "symbol": "AAPL",
        "level_type": "PDL",
        "price": 179.25,
        "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "has_been_broken": False,
        "has_been_retested": False,
        "description": "Previous Day Low"
    },
    {
        "id": "level_5",
        "symbol": "TSLA",
        "level_type": "OB_BULLISH",
        "price": 238.50,
        "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "has_been_broken": True,
        "has_been_retested": True,
        "description": "Bullish Order Block"
    }
]

SAMPLE_NOTIFICATIONS = [
    {
        "id": "notif_1",
        "timestamp": datetime.now().isoformat(),
        "type": "info",
        "title": "Bot Started",
        "message": "BoringTrade trading bot started successfully."
    },
    {
        "id": "notif_2",
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        "type": "trade",
        "title": "Trade Opened",
        "message": "Long position opened in SPY at 500.25"
    },
    {
        "id": "notif_3",
        "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
        "type": "trade",
        "title": "Trade Closed",
        "message": "Long position closed in AAPL at 183.25 (Win)"
    }
]

# Routes
@app.route("/")
def index():
    """Render the dashboard page."""
    return render_template("index.html", config=SAMPLE_CONFIG)


@app.route("/config")
def config_page():
    """Render the configuration page."""
    return render_template("config.html", config=SAMPLE_CONFIG)


@app.route("/trades")
def trades_page():
    """Render the trades page."""
    return render_template("trades.html")


@app.route("/levels")
def levels_page():
    """Render the levels page."""
    return render_template("levels.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    """Get the current configuration."""
    return jsonify(SAMPLE_CONFIG)


@app.route("/api/config", methods=["POST"])
def update_config_api():
    """Update the configuration."""
    try:
        new_config = request.json
        # In a real implementation, we would update the config here
        return jsonify({"success": True, "config": SAMPLE_CONFIG})
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/bot/status", methods=["GET"])
def get_bot_status():
    """Get the status of the trading bot."""
    return jsonify({"status": "running"})


@app.route("/api/bot/start", methods=["POST"])
def start_bot():
    """Start the trading bot."""
    return jsonify({"success": True, "message": "Bot started"})


@app.route("/api/bot/stop", methods=["POST"])
def stop_bot():
    """Stop the trading bot."""
    return jsonify({"success": True, "message": "Bot stopped"})


@app.route("/api/bot/flatten", methods=["POST"])
def flatten_all():
    """Flatten all positions."""
    return jsonify({"success": True, "message": "All positions flattened"})


@app.route("/api/trades", methods=["GET"])
def get_trades():
    """Get all trades."""
    return jsonify(SAMPLE_TRADES)


@app.route("/api/levels", methods=["GET"])
def get_levels():
    """Get all price levels."""
    return jsonify(SAMPLE_LEVELS)


@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    """Get all notifications."""
    return jsonify(SAMPLE_NOTIFICATIONS)


@app.route("/api/symbols", methods=["GET"])
def get_symbols():
    """Get all symbols."""
    return jsonify(SAMPLE_CONFIG["assets"])


@app.route("/api/candles", methods=["GET"])
def get_candles():
    """Get candles for a symbol and timeframe."""
    try:
        # Get query parameters
        symbol = request.args.get("symbol")
        timeframe = request.args.get("timeframe")
        
        if not symbol or not timeframe:
            return jsonify({"error": "Symbol and timeframe are required"}), 400
        
        # Convert timeframe to integer
        try:
            timeframe = int(timeframe)
        except ValueError:
            return jsonify({"error": "Timeframe must be an integer"}), 400
        
        # Generate sample candles
        candles = []
        end_time = datetime.now()
        
        for i in range(100):
            timestamp = end_time - timedelta(minutes=timeframe * i)
            open_price = random.uniform(100, 200)
            close_price = random.uniform(100, 200)
            high_price = max(open_price, close_price) + random.uniform(0, 5)
            low_price = min(open_price, close_price) - random.uniform(0, 5)
            
            candle = {
                "symbol": symbol,
                "timestamp": timestamp.isoformat(),
                "open_price": open_price,
                "high_price": high_price,
                "low_price": low_price,
                "close_price": close_price,
                "volume": random.uniform(1000, 10000),
                "timeframe": timeframe,
                "is_complete": True
            }
            candles.append(candle)
        
        return jsonify(candles)
    except Exception as e:
        logger.error(f"Failed to get candles: {e}")
        return jsonify({"error": str(e)})


@socketio.on("connect")
def handle_connect():
    """Handle WebSocket connection."""
    logger.info("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection."""
    logger.info("Client disconnected")


def run_dashboard(host="127.0.0.1", port=5000):
    """Run the web dashboard."""
    logger.info(f"Starting web dashboard on {host}:{port}")
    print(f"Web dashboard started at http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_dashboard()
