"""
Create a minimal configuration file for the BoringTrade trading bot.
"""
import os
import json

# Define the minimal configuration
minimal_config = {
    "broker": "tastytrade",
    "api_key": "",
    "api_secret": "",
    "assets": ["SPY", "QQQ", "AAPL"],
    "strategies": ["ORB"],
    "risk_per_trade": 0.01,
    "max_daily_loss": 0.03,
    "max_trades_per_day": 3,
    "orb": {
        "enabled": True,
        "session_start_time": "09:30",
        "timeframe": 5,
        "breakout_threshold": 0.0001,
        "retest_threshold": 0.0002,
        "confirmation_candles": 1
    },
    "pdh_pdl": {
        "enabled": False,
        "breakout_threshold": 0.0001,
        "retest_threshold": 0.0002,
        "confirmation_candles": 1
    },
    "ob": {
        "enabled": False,
        "lookback_period": 20,
        "significant_move_threshold": 0.005,
        "retest_threshold": 0.0002,
        "confirmation_candles": 1,
        "manual_input": True
    },
    "execution_timeframe": 1,
    "htf_timeframe": 60,
    "htf_filter": {
        "enabled": False,
        "ma_type": "EMA",
        "ma_period": 200
    },
    "stop_loss": {
        "type": "level",
        "buffer": 0.001
    },
    "take_profit": {
        "type": "risk_reward",
        "risk_reward_ratio": 2.0
    },
    "trading_hours": {
        "start": "09:30",
        "end": "16:00",
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    },
    "notifications": {
        "trade_entry": True,
        "trade_exit": True,
        "daily_summary": True,
        "error_alerts": True
    },
    "logging": {
        "level": "INFO",
        "file": "boringtrade.log"
    },
    "web_dashboard": {
        "enabled": True,
        "host": "127.0.0.1",
        "port": 5000
    }
}

# Create the configuration file
def create_config_file(config_path="config.json"):
    """Create a configuration file."""
    with open(config_path, "w") as f:
        json.dump(minimal_config, f, indent=4)
    
    print(f"Configuration file created: {config_path}")
    print("Please edit this file to add your API keys and customize settings.")

if __name__ == "__main__":
    create_config_file()
