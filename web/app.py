"""
Web dashboard for the BoringTrade trading bot.
"""
# Import eventlet first and monkey patch before any other imports
import eventlet
eventlet.monkey_patch()

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
from config import CONFIG, update_config

# Import utilities
from utils.logger import setup_logger

# Create Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = "boringtrade-secret-key"
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Set up logger
logger = setup_logger(
    name="WebDashboard",
    level=CONFIG["logging"]["level"],
    log_file="web_dashboard.log"
)

# Global variables
bot_instance = None


@app.route("/")
def index():
    """Render the dashboard page."""
    return render_template("index.html", config=CONFIG)


@app.route("/config")
def config_page():
    """Render the configuration page."""
    return render_template("config.html", config=CONFIG)


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
    return jsonify(CONFIG)


@app.route("/api/config", methods=["POST"])
def update_config_api():
    """Update the configuration."""
    try:
        new_config = request.json
        update_config(new_config)
        return jsonify({"success": True, "config": CONFIG})
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/bot/start", methods=["POST"])
def start_bot():
    """Start the trading bot."""
    global bot_instance

    try:
        if bot_instance is None:
            # Import here to avoid circular imports
            from main import TradingBot
            bot_instance = TradingBot()

        if not bot_instance.is_running:
            bot_instance.start()
            return jsonify({"success": True, "message": "Bot started"})
        else:
            return jsonify({"success": False, "message": "Bot is already running"})
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/bot/stop", methods=["POST"])
def stop_bot():
    """Stop the trading bot."""
    global bot_instance

    try:
        if bot_instance is not None and bot_instance.is_running:
            bot_instance.stop()
            return jsonify({"success": True, "message": "Bot stopped"})
        else:
            return jsonify({"success": False, "message": "Bot is not running"})
    except Exception as e:
        logger.error(f"Failed to stop bot: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/bot/status", methods=["GET"])
def get_bot_status():
    """Get the status of the trading bot."""
    global bot_instance

    try:
        if bot_instance is None:
            return jsonify({"status": "not_initialized"})
        elif bot_instance.is_running:
            return jsonify({"status": "running"})
        else:
            return jsonify({"status": "stopped"})
    except Exception as e:
        logger.error(f"Failed to get bot status: {e}")
        return jsonify({"status": "error", "error": str(e)})


@app.route("/api/bot/flatten", methods=["POST"])
def flatten_all():
    """Flatten all positions."""
    global bot_instance

    try:
        if bot_instance is not None and bot_instance.is_running:
            bot_instance.flatten_all()
            return jsonify({"success": True, "message": "All positions flattened"})
        else:
            return jsonify({"success": False, "message": "Bot is not running"})
    except Exception as e:
        logger.error(f"Failed to flatten positions: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/trades", methods=["GET"])
def get_trades():
    """Get all trades."""
    global bot_instance

    try:
        if bot_instance is None:
            return jsonify([])

        # Get active trades
        active_trades = [
            trade.to_dict() for trade in bot_instance.active_trades.values()
        ]

        # Get completed trades
        completed_trades = [
            trade.to_dict() for trade in bot_instance.completed_trades
        ]

        return jsonify({
            "active_trades": active_trades,
            "completed_trades": completed_trades
        })
    except Exception as e:
        logger.error(f"Failed to get trades: {e}")
        return jsonify({"error": str(e)})


@app.route("/api/levels", methods=["GET"])
def get_levels():
    """Get all price levels."""
    global bot_instance

    try:
        if bot_instance is None:
            return jsonify([])

        # Get levels from all strategies
        all_levels = []
        for strategy in bot_instance.strategies:
            for symbol, levels in strategy.levels.items():
                all_levels.extend([level.to_dict() for level in levels])

        return jsonify(all_levels)
    except Exception as e:
        logger.error(f"Failed to get levels: {e}")
        return jsonify({"error": str(e)})


@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    """Get all notifications."""
    global bot_instance

    try:
        if bot_instance is None:
            return jsonify([])

        # Get notifications
        notifications = bot_instance.notifier.get_notifications()

        # Convert datetime objects to strings
        for notification in notifications:
            notification["timestamp"] = notification["timestamp"].isoformat()

        return jsonify(notifications)
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        return jsonify({"error": str(e)})


@app.route("/api/symbols", methods=["GET"])
def get_symbols():
    """Get all symbols."""
    global bot_instance

    try:
        if bot_instance is None:
            # Return default symbols from config if bot is not running
            return jsonify(CONFIG.get("assets", []))

        # Get symbols from bot
        symbols = list(bot_instance.symbols)
        return jsonify(symbols)
    except Exception as e:
        logger.error(f"Failed to get symbols: {e}")
        return jsonify({"error": str(e)})


@app.route("/api/candles", methods=["GET"])
def get_candles():
    """Get candles for a symbol and timeframe."""
    global bot_instance

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

        if bot_instance is None:
            # Return empty list if bot is not running
            return jsonify([])

        # Get candles from bot
        candles = bot_instance.get_historical_candles(symbol, timeframe)

        # Convert candles to dictionaries
        candle_dicts = []
        for candle in candles:
            candle_dict = {
                "symbol": candle.symbol,
                "timestamp": candle.timestamp.isoformat(),
                "open_price": candle.open_price,
                "high_price": candle.high_price,
                "low_price": candle.low_price,
                "close_price": candle.close_price,
                "volume": candle.volume,
                "timeframe": candle.timeframe,
                "is_complete": candle.is_complete
            }
            candle_dicts.append(candle_dict)

        return jsonify(candle_dicts)
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


def emit_notification(notification: Dict[str, Any]) -> None:
    """
    Emit a notification to connected clients.

    Args:
        notification: The notification to emit
    """
    # Convert datetime objects to strings
    notification_copy = notification.copy()
    notification_copy["timestamp"] = notification_copy["timestamp"].isoformat()

    # Emit notification
    socketio.emit("notification", notification_copy)


def emit_trade_update(trade: Dict[str, Any]) -> None:
    """
    Emit a trade update to connected clients.

    Args:
        trade: The trade to emit
    """
    socketio.emit("trade_update", trade)


def emit_level_update(level: Dict[str, Any]) -> None:
    """
    Emit a level update to connected clients.

    Args:
        level: The level to emit
    """
    socketio.emit("level_update", level)


def run_dashboard():
    """Run the web dashboard."""
    # Get dashboard configuration
    dashboard_config = CONFIG["web_dashboard"]

    if not dashboard_config["enabled"]:
        logger.info("Web dashboard is disabled")
        return

    host = dashboard_config["host"]
    port = dashboard_config["port"]

    logger.info(f"Starting web dashboard on {host}:{port}")
    print(f"Web dashboard started at http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_dashboard()
