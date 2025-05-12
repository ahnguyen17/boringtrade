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

# Import asset models
from models.asset import Asset, AssetType
from models.asset_registry import AssetRegistry

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

        # Initialize asset registry
        self.asset_registry = AssetRegistry(CONFIG)

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
                    asset_registry=self.asset_registry,
                    config=CONFIG
                )
                self.strategies.append(strategy)

        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)

        # Trading state
        self.is_running = False
        self.start_time = None
        self.active_trades = {}
        self.completed_trades = []

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

    def get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a symbol.

        Args:
            symbol: The asset symbol

        Returns:
            float: The current price
        """
        self.logger.info(f"Getting current price for {symbol}")

        # Get the latest candle for the symbol
        candles = self.get_historical_candles(symbol, CONFIG["execution_timeframe"], limit=1)

        if not candles:
            self.logger.warning(f"No candles found for {symbol}")
            return 0.0

        # Return the close price of the latest candle
        return candles[0].close_price

    def get_historical_candles(self, symbol: str, timeframe: int, limit: int = 100):
        """
        Get historical candles for a symbol and timeframe.

        Args:
            symbol: The asset symbol
            timeframe: The candle timeframe in minutes
            limit: The maximum number of candles to return

        Returns:
            List[Candle]: The historical candles
        """
        self.logger.info(f"Getting historical candles for {symbol} {timeframe}m (limit: {limit})")

        # Get candles from data feed
        candles = self.data_feed.get_candles(symbol, timeframe)

        # Limit the number of candles
        if limit > 0 and len(candles) > limit:
            candles = candles[:limit]

        return candles

    def close_trade(self, symbol: str, exit_price: float, reason: str = "Manual close"):
        """
        Close a trade.

        Args:
            symbol: The asset symbol
            exit_price: The exit price
            reason: The reason for closing the trade

        Returns:
            Optional[Trade]: The closed trade
        """
        self.logger.info(f"Closing trade for {symbol} at {exit_price} ({reason})")

        # Check if we have an active trade for this symbol
        if symbol not in self.active_trades:
            self.logger.warning(f"No active trade found for {symbol}")
            return None

        trade = self.active_trades[symbol]

        # Close position through broker
        success, message, order_details = self.broker.close_position(symbol)

        if not success:
            self.logger.error(f"Failed to close position: {message}")
            return None

        # Update trade with exit details
        trade.exit_price = exit_price
        trade.exit_time = datetime.now()
        trade.status = "CLOSED"

        # Calculate profit/loss
        if trade.direction == "LONG":
            trade.profit_loss_amount = (exit_price - trade.entry_price) * trade.quantity
        else:  # SHORT
            trade.profit_loss_amount = (trade.entry_price - exit_price) * trade.quantity

        # Determine result
        if trade.profit_loss_amount > 0:
            trade.result = "WIN"
        elif trade.profit_loss_amount < 0:
            trade.result = "LOSS"
        else:
            trade.result = "BREAKEVEN"

        # Update trade with order details
        if order_details:
            trade.broker_order_id = order_details.get("order_id", trade.broker_order_id)

        # Remove from active trades
        del self.active_trades[symbol]

        # Add to completed trades
        if not hasattr(self, 'completed_trades'):
            self.completed_trades = []
        self.completed_trades.append(trade)

        # Update risk manager
        self.risk_manager.update_trade(trade)

        # Send notification
        self.notifier.send_trade_exit_notification(
            symbol=symbol,
            direction=trade.direction,
            entry_price=trade.entry_price,
            exit_price=exit_price,
            profit_loss=trade.profit_loss_amount,
            result=trade.result,
            strategy_name=trade.strategy_name
        )

        self.logger.info(f"Closed trade: {trade}")
        return trade

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
