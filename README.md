# BoringTrade - Break & Retest Trading Bot

A fully automated trading bot that implements the mechanical break and retest system from Jdub_Trades' strategy. The bot identifies key price levels, detects breakouts and retests, and automates entries/exits according to the strategy rules.

## Features

- Identifies key price levels (Opening Range, Previous Day High/Low, Order Blocks)
- Detects breakouts and retests of these levels
- Automates entries and exits based on strategy rules
- Manages risk according to user-defined parameters
- Provides real-time notifications of trades
- Tracks performance and generates reports
- Web dashboard for monitoring and configuration

## Supported Strategies

1. **Opening Range Break & Retest (ORB B&R)**
   - Uses the high and low of the first candle of the trading session
   - Enters trades when price breaks and retests these levels

2. **Previous Day High/Low (PDH/PDL) B&R**
   - Uses the previous trading day's high and low as key levels
   - Enters trades when price breaks and retests these levels

3. **Order Block (OB) B&R**
   - Uses order blocks as key levels
   - Enters trades when price retests these levels

## Supported Brokers

- Tastytrade API
- Charles Schwab API

## Project Structure

```
BoringTrade/
├── main.py                 # Main entry point
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── Strategy.md             # Strategy documentation
├── prd.md                  # Product Requirements Document
├── models/                 # Data models
│   ├── candle.py           # Candle data structure
│   ├── level.py            # Price level data structure
│   └── trade.py            # Trade data structure
├── strategies/             # Trading strategies
│   ├── base_strategy.py    # Base strategy class
│   ├── orb_strategy.py     # Opening Range Breakout strategy
│   ├── pdh_pdl_strategy.py # Previous Day High/Low strategy
│   └── order_block_strategy.py # Order Block strategy
├── brokers/                # Broker API integrations
│   ├── broker_interface.py # Abstract broker interface
│   ├── broker_factory.py   # Factory for creating brokers
│   ├── tastytrade.py       # Tastytrade API integration
│   └── schwab.py           # Charles Schwab API integration
├── data/                   # Market data handling
│   ├── data_feed.py        # Real-time market data feed
│   └── candle_builder.py   # Builds candles from tick data
├── utils/                  # Utility functions
│   ├── logger.py           # Logging functionality
│   ├── notification.py     # User notifications
│   └── risk_manager.py     # Risk management
├── web/                    # Web dashboard
│   ├── app.py              # Flask web application
│   ├── templates/          # HTML templates
│   └── static/             # CSS, JS, and other static files
└── tests/                  # Unit and integration tests
    └── test_orb_strategy.py # Tests for ORB strategy
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/BoringTrade.git
cd BoringTrade

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Edit the `config.py` file to set your preferences:

```python
# Example configuration
CONFIG = {
    "broker": "tastytrade",
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "assets": ["SPY", "QQQ", "AAPL"],
    "strategies": ["ORB", "PDH_PDL"],
    "risk_per_trade": 0.01,  # 1% of account
    "max_daily_loss": 0.03,  # 3% of account
    "max_trades_per_day": 3,
    "orb_timeframe": 5,  # minutes
    "execution_timeframe": 1,  # minutes
    "htf_filter": {
        "enabled": True,
        "timeframe": 60,  # minutes
        "ma_type": "EMA",
        "ma_period": 200
    }
}
```

## Usage

```bash
# Start the trading bot
python main.py

# Start the web dashboard
python web/app.py
```

Access the web dashboard at http://localhost:5000

## Running Tests

```bash
# Run all tests
python -m unittest discover tests

# Run a specific test
python -m unittest tests.test_orb_strategy
```

## Implementation Notes

- The bot is designed to be modular and extensible, allowing for easy addition of new strategies and broker integrations.
- The web dashboard provides real-time monitoring and control of the trading bot.
- The risk management system ensures that the bot adheres to user-defined risk parameters.
- The notification system keeps the user informed of important events.

## Future Enhancements

- Implement PDH/PDL and Order Block strategies
- Add backtesting functionality
- Improve order block detection
- Add more broker integrations
- Enhance the web dashboard with charts and analytics

## License

MIT
