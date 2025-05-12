"""
Run the web dashboard for the BoringTrade trading bot.
"""
import os
import sys
import argparse

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the web dashboard
from web.app import run_dashboard


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the web dashboard for the BoringTrade trading bot")
    parser.add_argument("--host", type=str, help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to bind to")
    return parser.parse_args()


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Update configuration if needed
    from config import CONFIG
    if args.host:
        CONFIG["web_dashboard"]["host"] = args.host
    if args.port:
        CONFIG["web_dashboard"]["port"] = args.port
    
    # Run the web dashboard
    print(f"Starting web dashboard at http://{CONFIG['web_dashboard']['host']}:{CONFIG['web_dashboard']['port']}")
    run_dashboard()


if __name__ == "__main__":
    main()
