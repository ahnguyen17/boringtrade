# Getting Started with BoringTrade

Welcome to BoringTrade, a trading bot that implements the mechanical break and retest system from Jdub_Trades' strategy. This guide will help you get started with the bot.

## Quick Start

If you just want to see the dashboard without installing all dependencies:

```bash
pip install flask
python simple_dashboard.py
```

Then open your browser and go to http://localhost:5000

## Step 1: Check Dependencies

First, check if you have all the required dependencies installed:

```bash
python check_dependencies.py
```

This will show you which dependencies are installed and which are missing.

## Step 2: Install Dependencies

If you're missing dependencies, install them:

```bash
pip install -r requirements.txt
```

Note: Some dependencies like TA-Lib might require additional steps to install.

## Step 3: Create Configuration

Create a basic configuration file:

```bash
python create_config.py
```

This will create a `config.json` file that you can edit to customize the bot.

## Step 4: Run the Bot

There are several ways to run the bot:

### Dashboard Only (Minimal Dependencies)

```bash
python simple_dashboard.py
```

### Full Bot with Dashboard

```bash
python run.py --dashboard
```

### Bot Only (No Dashboard)

```bash
python run.py
```

### Dashboard Only (Full Features)

```bash
python run.py --dashboard-only
```

## Step 5: Explore the Code

The bot is organized into several modules:

- `models/` - Data models for candles, price levels, and trades
- `strategies/` - Trading strategies (ORB, PDH/PDL, Order Block)
- `brokers/` - Broker API integrations
- `data/` - Market data handling
- `utils/` - Utility functions
- `web/` - Web dashboard

## Step 6: Customize the Bot

You can customize the bot by:

1. Editing the configuration file
2. Implementing new strategies
3. Adding new broker integrations
4. Enhancing the web dashboard

## Troubleshooting

If you encounter issues:

1. Check the logs in `boringtrade.log`
2. Run `python check_dependencies.py` to verify dependencies
3. Try running with just the simple dashboard: `python simple_dashboard.py`
4. Check the console for error messages

## Additional Resources

- `README.md` - Overview of the project
- `Strategy.md` - Detailed description of the trading strategy
- `IMPLEMENTATION_STATUS.md` - Current status of the implementation
- `DASHBOARD_ONLY.md` - Instructions for running just the dashboard

## Next Steps

1. Complete the broker API integrations
2. Implement the PDH/PDL and Order Block strategies
3. Add backtesting functionality
4. Enhance the web dashboard with charts and analytics

Happy trading!
