"""
Simple web dashboard for the BoringTrade trading bot.
This script doesn't require Flask-SocketIO, just Flask.
"""
import os
import sys
from flask import Flask, render_template, jsonify

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create Flask app
app = Flask(__name__,
            template_folder=os.path.join('web', 'templates'),
            static_folder=os.path.join('web', 'static'))

# Define routes
@app.route('/')
def index():
    """Render the dashboard page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BoringTrade - Simple Dashboard</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">BoringTrade</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link active" href="/">Dashboard</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <div class="container mt-4">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Simple Dashboard</h5>
                        </div>
                        <div class="card-body">
                            <p>This is a simple dashboard for the BoringTrade trading bot.</p>
                            <p>The full dashboard requires additional dependencies.</p>
                            <p>To run the full dashboard, install all dependencies with:</p>
                            <pre><code>pip install -r requirements.txt</code></pre>
                            <p>Then run the bot with:</p>
                            <pre><code>python run.py --dashboard</code></pre>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Supported Strategies</h5>
                        </div>
                        <div class="card-body">
                            <ul>
                                <li><strong>Opening Range Breakout (ORB)</strong> - Uses the high and low of the first candle of the trading session</li>
                                <li><strong>Previous Day High/Low (PDH/PDL)</strong> - Uses the previous day's high and low as key levels</li>
                                <li><strong>Order Block (OB)</strong> - Uses order blocks as key levels</li>
                            </ul>
                            <p class="mt-3"><strong>Supported Assets:</strong></p>
                            <ul>
                                <li><strong>Stocks</strong> - SPY, QQQ, AAPL, TSLA, NVDA, etc.</li>
                                <li><strong>Futures</strong> - ES (E-mini S&P 500), MES (Micro E-mini S&P 500)</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Features</h5>
                        </div>
                        <div class="card-body">
                            <ul>
                                <li>Identifies key price levels</li>
                                <li>Detects breakouts and retests</li>
                                <li>Automates entries and exits</li>
                                <li>Manages risk according to user-defined parameters</li>
                                <li>Supports futures trading (ES, MES)</li>
                                <li>Provides real-time notifications</li>
                                <li>Tracks performance and generates reports</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

@app.route('/docs/futures_trading')
def futures_trading_docs():
    """Render the futures trading documentation."""
    try:
        with open("docs/futures_trading.md", "r") as f:
            content = f.read()
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>BoringTrade - Futures Trading</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5.1.0/github-markdown.min.css">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container-fluid">
                    <a class="navbar-brand" href="/">BoringTrade</a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav">
                            <li class="nav-item">
                                <a class="nav-link" href="/">Dashboard</a>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>

            <div class="container mt-4">
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="mb-0">Futures Trading</h5>
                            </div>
                            <div class="card-body markdown-body">
                                <pre>{content}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """
    except FileNotFoundError:
        return "Documentation not found", 404


@app.route('/api/status')
def status():
    """Return the status of the bot."""
    return jsonify({
        "status": "not_running",
        "message": "This is a simple dashboard. The bot is not running."
    })

if __name__ == '__main__':
    print("Starting simple dashboard at http://localhost:5000")
    print("Note: This is a simplified dashboard. The full dashboard requires additional dependencies.")
    print("Press Ctrl+C to stop the dashboard.")
    app.run(host='127.0.0.1', port=5000)
