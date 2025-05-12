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
