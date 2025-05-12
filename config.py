"""
Configuration settings for the BoringTrade trading bot.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default configuration
DEFAULT_CONFIG = {
    # Broker settings
    "broker": "tastytrade",  # Options: "tastytrade", "schwab"
    "api_key": os.getenv("API_KEY", ""),
    "api_secret": os.getenv("API_SECRET", ""),

    # Trading assets
    "assets": ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"],

    # Enabled strategies
    "strategies": ["ORB", "PDH_PDL", "OB"],

    # Risk management
    "risk_per_trade": 0.01,  # 1% of account
    "max_daily_loss": 0.03,  # 3% of account
    "max_daily_profit": None,  # Optional, set to None for unlimited
    "max_trades_per_day": 3,
    "position_size": 1,  # Number of contracts/shares

    # Opening Range Breakout settings
    "orb": {
        "enabled": True,
        "session_start_time": "09:30",  # Market open (EST)
        "timeframe": 5,  # minutes (1, 5, or 15)
        "breakout_threshold": 0.0001,  # 0.01% above/below level
        "retest_threshold": 0.0002,  # How close price must come to level for retest
        "confirmation_candles": 1,  # Number of candles to confirm retest
    },

    # Previous Day High/Low settings
    "pdh_pdl": {
        "enabled": True,
        "breakout_threshold": 0.0001,  # 0.01% above/below level
        "retest_threshold": 0.0002,  # How close price must come to level for retest
        "confirmation_candles": 1,  # Number of candles to confirm retest
    },

    # Order Block settings
    "ob": {
        "enabled": True,
        "lookback_period": 20,  # Candles to look back for order blocks
        "significant_move_threshold": 0.005,  # 0.5% move to qualify as significant
        "retest_threshold": 0.0002,  # How close price must come to level for retest
        "confirmation_candles": 1,  # Number of candles to confirm retest
        "manual_input": True,  # Allow manual input of order blocks
    },

    # Timeframes
    "execution_timeframe": 1,  # minutes (1 or 5)
    "htf_timeframe": 60,  # minutes (15, 30, 60)

    # Higher Timeframe filter
    "htf_filter": {
        "enabled": True,
        "ma_type": "EMA",  # Options: "SMA", "EMA"
        "ma_period": 200,
    },

    # Stop loss settings
    "stop_loss": {
        "type": "level",  # Options: "level", "candle"
        "buffer": 0.001,  # 0.1% buffer below/above level or candle
    },

    # Take profit settings
    "take_profit": {
        "type": "risk_reward",  # Options: "risk_reward", "next_level"
        "risk_reward_ratio": 2.0,  # 1:2 risk-reward ratio
        "partial_tp": {
            "enabled": False,
            "levels": [1.0, 2.0],  # Take partial profits at 1R and 2R
            "percentages": [0.5, 0.5],  # 50% at each level
        },
    },

    # Trading hours
    "trading_hours": {
        "start": "09:30",  # EST
        "end": "16:00",  # EST
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    },

    # Notification settings
    "notifications": {
        "trade_entry": True,
        "trade_exit": True,
        "daily_summary": True,
        "error_alerts": True,
    },

    # Logging settings
    "logging": {
        "level": "INFO",  # Options: "DEBUG", "INFO", "WARNING", "ERROR"
        "file": "boringtrade.log",
    },

    # Web dashboard settings
    "web_dashboard": {
        "enabled": True,
        "host": "127.0.0.1",
        "port": 5000,
    },

    # Debug settings
    "debug": {
        "enabled": False,
        "test_broker_connection": False,
        "connection_timeout": 10,  # seconds
        "verbose_logging": False,
    },
}

# User configuration (override with user settings)
USER_CONFIG = {}

# Merge default and user configurations
CONFIG = {**DEFAULT_CONFIG, **USER_CONFIG}

def get_config():
    """Get the current configuration."""
    return CONFIG

def update_config(new_config):
    """Update the configuration with new settings."""
    global CONFIG
    CONFIG.update(new_config)
    return CONFIG
