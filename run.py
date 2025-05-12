"""
Run script for the BoringTrade trading bot.
"""
import os
import sys
import argparse
import threading
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the trading bot
from main import TradingBot
from web.app import run_dashboard


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="BoringTrade - Break & Retest Trading Bot")
    parser.add_argument("--config", type=str, help="Path to custom configuration file")
    parser.add_argument("--broker", type=str, choices=["tastytrade", "schwab"], help="Broker to use")
    parser.add_argument("--assets", type=str, nargs="+", help="Assets to trade")
    parser.add_argument("--strategies", type=str, nargs="+", help="Strategies to use")
    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level")
    parser.add_argument("--dashboard", action="store_true", help="Run the web dashboard")
    parser.add_argument("--dashboard-only", action="store_true", help="Run only the web dashboard")
    return parser.parse_args()


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Create custom configuration from arguments
    custom_config = {}
    if args.broker:
        custom_config["broker"] = args.broker
    if args.assets:
        custom_config["assets"] = args.assets
    if args.strategies:
        custom_config["strategies"] = args.strategies
    if args.log_level:
        custom_config["logging"] = {"level": args.log_level}
    
    # Run dashboard in a separate thread if requested
    dashboard_thread = None
    if args.dashboard or args.dashboard_only:
        dashboard_thread = threading.Thread(target=run_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()
        print(f"Web dashboard started at http://localhost:5000")
    
    # Run the trading bot if not dashboard-only
    if not args.dashboard_only:
        # Initialize and start the trading bot
        bot = TradingBot(config=custom_config)
        
        try:
            print(f"Starting BoringTrade trading bot at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            bot.start()
            
            # Keep the main thread alive
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
            bot.stop()
            print(f"BoringTrade trading bot stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        # Keep the main thread alive for dashboard-only mode
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
    
    # Wait for dashboard thread to finish if it was started
    if dashboard_thread and dashboard_thread.is_alive():
        dashboard_thread.join(timeout=5.0)


if __name__ == "__main__":
    main()
