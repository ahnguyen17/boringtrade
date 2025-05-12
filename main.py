"""
BoringTrade - Break & Retest Trading Bot
Main entry point for the application.
"""
import os
import sys
import time
import logging
import signal
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import configuration
from config import CONFIG, update_config

# Import utilities
from utils.logger import setup_logger
from utils.notification import Notifier

# Import broker interfaces
from brokers.broker_factory import BrokerFactory

# Import strategies
from strategies.strategy_factory import StrategyFactory

# Import market data
from data.data_feed import DataFeed

# Import risk manager
from utils.risk_manager import RiskManager

class TradingBot:
    """Main trading bot class."""
    
    def __init__(self, config=None):
        """Initialize the trading bot."""
        # Update configuration if provided
        if config:
            update_config(config)
        
        # Set up logger
        self.logger = setup_logger(
            name="TradingBot",
            level=CONFIG["logging"]["level"],
            log_file=CONFIG["logging"]["file"]
        )
        self.logger.info("Initializing BoringTrade trading bot...")
        
        # Initialize components
        self.notifier = Notifier(CONFIG["notifications"])
        self.broker = BrokerFactory.create_broker(
            broker_name=CONFIG["broker"],
            api_key=CONFIG["api_key"],
            api_secret=CONFIG["api_secret"]
        )
        self.risk_manager = RiskManager(
            risk_per_trade=CONFIG["risk_per_trade"],
            max_daily_loss=CONFIG["max_daily_loss"],
            max_daily_profit=CONFIG["max_daily_profit"],
            max_trades_per_day=CONFIG["max_trades_per_day"]
        )
        self.data_feed = DataFeed(
            broker=self.broker,
            assets=CONFIG["assets"],
            timeframes=[
                CONFIG["execution_timeframe"],
                CONFIG["htf_timeframe"],
                CONFIG["orb"]["timeframe"]
            ]
        )
        
        # Initialize strategies
        self.strategies = []
        for strategy_name in CONFIG["strategies"]:
            if CONFIG[strategy_name.lower()]["enabled"]:
                strategy = StrategyFactory.create_strategy(
                    strategy_name=strategy_name,
                    data_feed=self.data_feed,
                    broker=self.broker,
                    risk_manager=self.risk_manager,
                    notifier=self.notifier,
                    config=CONFIG
                )
                self.strategies.append(strategy)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        
        # Trading state
        self.is_running = False
        self.start_time = None
        
        self.logger.info("BoringTrade trading bot initialized successfully.")
    
    def start(self):
        """Start the trading bot."""
        self.logger.info("Starting BoringTrade trading bot...")
        self.is_running = True
        self.start_time = datetime.now()
        
        # Connect to broker
        self.broker.connect()
        
        # Start data feed
        self.data_feed.start()
        
        # Start strategies
        for strategy in self.strategies:
            strategy.start()
        
        # Send notification
        self.notifier.send_notification(
            "BoringTrade bot started",
            f"Trading bot started at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        self.logger.info("BoringTrade trading bot started successfully.")
        
        # Main loop
        try:
            while self.is_running:
                time.sleep(1)
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            self.stop()
    
    def stop(self):
        """Stop the trading bot."""
        self.logger.info("Stopping BoringTrade trading bot...")
        self.is_running = False
        
        # Stop strategies
        for strategy in self.strategies:
            strategy.stop()
        
        # Stop data feed
        self.data_feed.stop()
        
        # Disconnect from broker
        self.broker.disconnect()
        
        # Send notification
        end_time = datetime.now()
        duration = end_time - self.start_time if self.start_time else None
        duration_str = str(duration).split('.')[0] if duration else "Unknown"
        
        self.notifier.send_notification(
            "BoringTrade bot stopped",
            f"Trading bot stopped at {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Running duration: {duration_str}"
        )
        
        self.logger.info("BoringTrade trading bot stopped successfully.")
    
    def handle_exit(self, signum, frame):
        """Handle exit signals."""
        self.logger.info(f"Received signal {signum}. Exiting...")
        self.stop()
        sys.exit(0)
    
    def flatten_all(self):
        """Close all open positions."""
        self.logger.info("Flattening all positions...")
        self.broker.flatten_all()
        self.notifier.send_notification(
            "All positions flattened",
            "All open positions have been closed."
        )
        self.logger.info("All positions flattened successfully.")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="BoringTrade - Break & Retest Trading Bot")
    parser.add_argument("--config", type=str, help="Path to custom configuration file")
    parser.add_argument("--broker", type=str, choices=["tastytrade", "schwab"], help="Broker to use")
    parser.add_argument("--assets", type=str, nargs="+", help="Assets to trade")
    parser.add_argument("--strategies", type=str, nargs="+", help="Strategies to use")
    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level")
    return parser.parse_args()

if __name__ == "__main__":
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
    
    # Initialize and start the trading bot
    bot = TradingBot(config=custom_config)
    bot.start()
