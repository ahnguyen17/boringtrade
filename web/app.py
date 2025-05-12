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


@app.route("/trading")
def trading_page():
    """Render the trading page."""
    return render_template("trading.html")


@app.route("/docs/futures_trading")
def futures_trading_docs():
    """Render the futures trading documentation."""
    try:
        with open("docs/futures_trading.md", "r") as f:
            content = f.read()
        return render_template("markdown.html", title="Futures Trading", content=content)
    except FileNotFoundError:
        return "Documentation not found", 404


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


@app.route("/api/trades/place", methods=["POST"])
def place_trade():
    """Place a new trade."""
    global bot_instance

    try:
        # Check if bot is running
        if bot_instance is None:
            return jsonify({
                "success": False,
                "message": "Trading bot is not running"
            }), 400

        # Get request data
        data = request.json
        symbol = data.get("symbol")
        direction_str = data.get("direction")
        quantity = data.get("quantity")
        entry_price = data.get("entry_price")
        stop_loss = data.get("stop_loss")
        take_profit = data.get("take_profit")

        # Validate inputs
        if not all([symbol, direction_str, quantity, entry_price, stop_loss, take_profit]):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Convert direction string to enum
        from models.trade import TradeDirection
        direction = TradeDirection.LONG if direction_str == "LONG" else TradeDirection.SHORT

        # Place order through broker
        success, message, order_details = bot_instance.broker.place_market_order(
            symbol=symbol,
            direction=direction,
            quantity=float(quantity),
            stop_loss=float(stop_loss),
            take_profit=float(take_profit)
        )

        if not success:
            return jsonify({
                "success": False,
                "message": message
            }), 400

        # Create trade object
        from models.trade import Trade, TradeStatus
        trade = Trade(
            symbol=symbol,
            direction=direction,
            strategy_name="Manual",
            entry_price=float(entry_price),
            stop_loss=float(stop_loss),
            take_profit=float(take_profit),
            quantity=float(quantity),
            entry_time=datetime.now(),
            status=TradeStatus.PENDING,
            broker_order_id=order_details.get("order_id") if order_details else None
        )

        # Update trade with order details
        if order_details:
            trade = bot_instance.broker.update_trade_from_order(trade, order_details)

        # Add to active trades
        bot_instance.active_trades[symbol] = trade

        # Register trade with risk manager
        bot_instance.risk_manager.register_trade(trade)

        # Send notification
        bot_instance.notifier.send_trade_entry_notification(
            symbol=symbol,
            direction=direction.value,
            entry_price=float(entry_price),
            stop_loss=float(stop_loss),
            take_profit=float(take_profit),
            quantity=float(quantity),
            strategy_name="Manual",
            risk_reward=trade.risk_reward_ratio
        )

        # Emit trade update event
        socketio.emit("trade_update", trade.to_dict())

        return jsonify({
            "success": True,
            "message": "Trade placed successfully",
            "trade": trade.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to place trade: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/trades/close", methods=["POST"])
def close_trade():
    """Close an existing trade."""
    global bot_instance

    try:
        # Check if bot is running
        if bot_instance is None:
            return jsonify({
                "success": False,
                "message": "Trading bot is not running"
            }), 400

        # Get request data
        data = request.json
        symbol = data.get("symbol")

        # Validate inputs
        if not symbol:
            return jsonify({
                "success": False,
                "message": "Symbol is required"
            }), 400

        # Check if trade exists
        if symbol not in bot_instance.active_trades:
            return jsonify({
                "success": False,
                "message": f"No active trade found for {symbol}"
            }), 404

        # Get current price
        current_price = bot_instance.get_current_price(symbol)

        # Close trade
        trade = bot_instance.close_trade(symbol, current_price, "Manual close")

        if not trade:
            return jsonify({
                "success": False,
                "message": f"Failed to close trade for {symbol}"
            }), 500

        # Emit trade update event
        socketio.emit("trade_update", trade.to_dict())

        return jsonify({
            "success": True,
            "message": "Trade closed successfully",
            "trade": trade.to_dict()
        })

    except Exception as e:
        logger.error(f"Failed to close trade: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/debug/test_broker_connection", methods=["POST"])
def test_broker_connection():
    """Test the connection to the broker API."""
    try:
        # Get request data
        data = request.json
        broker_name = data.get("broker", CONFIG["broker"])
        api_key = data.get("api_key", CONFIG["api_key"])
        api_secret = data.get("api_secret", CONFIG["api_secret"])
        timeout = data.get("timeout", CONFIG["debug"]["connection_timeout"])

        # Import broker factory
        from brokers.broker_factory import BrokerFactory

        # Create broker instance
        broker = BrokerFactory.create_broker(
            broker_name=broker_name,
            api_key=api_key,
            api_secret=api_secret
        )

        # Test connection
        success, message, details = broker.test_connection(timeout=timeout)

        # Return result
        return jsonify({
            "success": success,
            "message": message,
            "details": details
        })
    except Exception as e:
        error_msg = f"Failed to test broker connection: {e}"
        logger.error(error_msg)
        return jsonify({
            "success": False,
            "message": error_msg,
            "details": {
                "error": str(e)
            }
        })


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
