# Running the BoringTrade Dashboard Only

If you're encountering dependency issues or just want to see the web dashboard without running the full trading bot, you have two options:

## Option 1: Simple Dashboard (Minimal Dependencies)

This option requires only Flask, which is a common Python package.

### Prerequisites

1. Python 3.7 or higher
2. Flask (install with `pip install flask`)

### Steps to Run the Simple Dashboard

1. Make sure you have Flask installed:

```bash
pip install flask
```

2. Run the simple dashboard script:

```bash
python simple_dashboard.py
```

3. Open your web browser and navigate to http://localhost:5000

## Option 2: Full Dashboard (More Dependencies)

This option requires Flask and Flask-SocketIO for real-time updates.

### Prerequisites

1. Python 3.7 or higher
2. Flask and Flask-SocketIO (install with `pip install flask flask-socketio`)

### Steps to Run the Full Dashboard Only

1. Make sure you have the required dependencies installed:

```bash
pip install flask flask-socketio
```

2. Run the dashboard-only script:

```bash
python run_dashboard_only.py
```

3. Open your web browser and navigate to http://localhost:5000

## Features Available in Dashboard-Only Mode

In dashboard-only mode, you can:

- View the dashboard interface
- Navigate between different pages
- See the configuration settings

However, since the trading bot is not running, you won't be able to:

- Start or stop the bot
- See real-time trades
- See real-time price levels
- Receive notifications

## Next Steps

Once you've explored the dashboard, you may want to:

1. Install all the required dependencies to run the full bot:

```bash
pip install -r requirements.txt
```

2. Create a configuration file:

```bash
python create_config.py
```

3. Edit the configuration file to add your API keys and customize settings.

4. Run the full bot with the dashboard:

```bash
python run.py --dashboard
```

## Troubleshooting

If you encounter any issues with the dashboard, try:

1. Checking the console for error messages
2. Verifying that you have the required dependencies installed
3. Making sure no other application is using port 5000

If you need to use a different port, you can modify the `run_dashboard_only.py` script to change the port number.
