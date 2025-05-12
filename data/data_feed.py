"""
Market data feed for the BoringTrade trading bot.
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set, Tuple

from brokers.broker_interface import BrokerInterface
from models.candle import Candle
from data.candle_builder import CandleBuilder


class DataFeed:
    """
    Handles market data for the trading bot.
    """
    
    def __init__(
        self,
        broker: BrokerInterface,
        assets: List[str],
        timeframes: List[int]
    ):
        """
        Initialize the data feed.
        
        Args:
            broker: The broker interface
            assets: The assets to track
            timeframes: The timeframes to track (in minutes)
        """
        self.broker = broker
        self.assets = assets
        self.timeframes = timeframes
        self.logger = logging.getLogger("DataFeed")
        
        # Initialize candle builders
        self.candle_builders: Dict[str, Dict[int, CandleBuilder]] = {}
        for symbol in assets:
            self.candle_builders[symbol] = {}
            for timeframe in timeframes:
                self.candle_builders[symbol][timeframe] = CandleBuilder(
                    symbol=symbol,
                    timeframe=timeframe
                )
        
        # Initialize candle history
        self.candle_history: Dict[str, Dict[int, List[Candle]]] = {}
        for symbol in assets:
            self.candle_history[symbol] = {}
            for timeframe in timeframes:
                self.candle_history[symbol][timeframe] = []
        
        # Initialize callbacks
        self.candle_callbacks: Dict[str, Dict[int, List[Callable[[Candle], None]]]] = {}
        for symbol in assets:
            self.candle_callbacks[symbol] = {}
            for timeframe in timeframes:
                self.candle_callbacks[symbol][timeframe] = []
        
        # Initialize level callbacks
        self.level_callbacks: Dict[str, List[Callable[[float], None]]] = {}
        for symbol in assets:
            self.level_callbacks[symbol] = []
        
        # Initialize price levels
        self.price_levels: Dict[str, Set[float]] = {}
        for symbol in assets:
            self.price_levels[symbol] = set()
        
        # Initialize running state
        self.is_running = False
        self.update_thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start the data feed."""
        if self.is_running:
            self.logger.warning("Data feed is already running")
            return
        
        self.logger.info("Starting data feed...")
        self.is_running = True
        
        # Load historical data
        self._load_historical_data()
        
        # Subscribe to market data
        for symbol in self.assets:
            for timeframe in self.timeframes:
                self.broker.subscribe_to_market_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    callback=self._on_candle_update
                )
        
        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        self.logger.info("Data feed started")
    
    def stop(self) -> None:
        """Stop the data feed."""
        if not self.is_running:
            self.logger.warning("Data feed is not running")
            return
        
        self.logger.info("Stopping data feed...")
        self.is_running = False
        
        # Unsubscribe from market data
        for symbol in self.assets:
            for timeframe in self.timeframes:
                self.broker.unsubscribe_from_market_data(
                    symbol=symbol,
                    timeframe=timeframe
                )
        
        # Wait for update thread to stop
        if self.update_thread:
            self.update_thread.join(timeout=5.0)
            self.update_thread = None
        
        self.logger.info("Data feed stopped")
    
    def add_candle_callback(
        self,
        symbol: str,
        timeframe: int,
        callback: Callable[[Candle], None]
    ) -> None:
        """
        Add a callback for candle updates.
        
        Args:
            symbol: The asset symbol
            timeframe: The candle timeframe in minutes
            callback: The callback function
        """
        if symbol not in self.candle_callbacks:
            self.candle_callbacks[symbol] = {}
        
        if timeframe not in self.candle_callbacks[symbol]:
            self.candle_callbacks[symbol][timeframe] = []
        
        self.candle_callbacks[symbol][timeframe].append(callback)
        self.logger.debug(f"Added candle callback for {symbol} {timeframe}m")
    
    def remove_candle_callback(
        self,
        symbol: str,
        timeframe: int,
        callback: Callable[[Candle], None]
    ) -> None:
        """
        Remove a callback for candle updates.
        
        Args:
            symbol: The asset symbol
            timeframe: The candle timeframe in minutes
            callback: The callback function
        """
        if (
            symbol in self.candle_callbacks and
            timeframe in self.candle_callbacks[symbol] and
            callback in self.candle_callbacks[symbol][timeframe]
        ):
            self.candle_callbacks[symbol][timeframe].remove(callback)
            self.logger.debug(f"Removed candle callback for {symbol} {timeframe}m")
    
    def add_level_callback(
        self,
        symbol: str,
        level: float,
        callback: Callable[[float], None]
    ) -> None:
        """
        Add a callback for price level crossings.
        
        Args:
            symbol: The asset symbol
            level: The price level
            callback: The callback function
        """
        if symbol not in self.level_callbacks:
            self.level_callbacks[symbol] = []
        
        if symbol not in self.price_levels:
            self.price_levels[symbol] = set()
        
        self.level_callbacks[symbol].append(callback)
        self.price_levels[symbol].add(level)
        self.logger.debug(f"Added level callback for {symbol} at {level}")
    
    def remove_level_callback(
        self,
        symbol: str,
        level: Optional[float] = None,
        callback: Optional[Callable[[float], None]] = None
    ) -> None:
        """
        Remove a callback for price level crossings.
        
        Args:
            symbol: The asset symbol
            level: The price level (None to remove all levels)
            callback: The callback function (None to remove all callbacks)
        """
        if symbol not in self.level_callbacks:
            return
        
        if callback is None and level is None:
            # Remove all callbacks and levels
            self.level_callbacks[symbol] = []
            self.price_levels[symbol] = set()
            self.logger.debug(f"Removed all level callbacks for {symbol}")
        elif callback is None:
            # Remove specific level
            if level in self.price_levels[symbol]:
                self.price_levels[symbol].remove(level)
                self.logger.debug(f"Removed level {level} for {symbol}")
        elif level is None:
            # Remove specific callback
            if callback in self.level_callbacks[symbol]:
                self.level_callbacks[symbol].remove(callback)
                self.logger.debug(f"Removed level callback for {symbol}")
        else:
            # Remove specific callback and level
            if callback in self.level_callbacks[symbol]:
                self.level_callbacks[symbol].remove(callback)
            if level in self.price_levels[symbol]:
                self.price_levels[symbol].remove(level)
            self.logger.debug(f"Removed level callback for {symbol} at {level}")
    
    def get_candles(
        self,
        symbol: str,
        timeframe: int,
        count: Optional[int] = None
    ) -> List[Candle]:
        """
        Get historical candles.
        
        Args:
            symbol: The asset symbol
            timeframe: The candle timeframe in minutes
            count: The number of candles to return (None for all)
            
        Returns:
            List[Candle]: The historical candles
        """
        if (
            symbol not in self.candle_history or
            timeframe not in self.candle_history[symbol]
        ):
            return []
        
        candles = self.candle_history[symbol][timeframe]
        
        if count is None:
            return candles
        
        return candles[-count:]
    
    def get_current_candle(self, symbol: str, timeframe: int) -> Optional[Candle]:
        """
        Get the current (incomplete) candle.
        
        Args:
            symbol: The asset symbol
            timeframe: The candle timeframe in minutes
            
        Returns:
            Optional[Candle]: The current candle
        """
        if (
            symbol not in self.candle_builders or
            timeframe not in self.candle_builders[symbol]
        ):
            return None
        
        return self.candle_builders[symbol][timeframe].current_candle
    
    def get_last_complete_candle(self, symbol: str, timeframe: int) -> Optional[Candle]:
        """
        Get the last complete candle.
        
        Args:
            symbol: The asset symbol
            timeframe: The candle timeframe in minutes
            
        Returns:
            Optional[Candle]: The last complete candle
        """
        candles = self.get_candles(symbol, timeframe, 1)
        if not candles:
            return None
        
        return candles[0]
    
    def _load_historical_data(self) -> None:
        """Load historical data for all assets and timeframes."""
        self.logger.info("Loading historical data...")
        
        # Calculate start time (1 day ago)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        # Load historical data for each asset and timeframe
        for symbol in self.assets:
            for timeframe in self.timeframes:
                candles = self.broker.get_historical_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=start_time,
                    end_time=end_time
                )
                
                if candles:
                    self.candle_history[symbol][timeframe] = candles
                    self.logger.info(
                        f"Loaded {len(candles)} historical candles for {symbol} {timeframe}m"
                    )
                else:
                    self.logger.warning(
                        f"No historical candles found for {symbol} {timeframe}m"
                    )
        
        self.logger.info("Historical data loaded")
    
    def _on_candle_update(self, candle: Candle) -> None:
        """
        Handle candle updates from the broker.
        
        Args:
            candle: The updated candle
        """
        symbol = candle.symbol
        timeframe = candle.timeframe
        
        # Update candle builder
        if (
            symbol in self.candle_builders and
            timeframe in self.candle_builders[symbol]
        ):
            builder = self.candle_builders[symbol][timeframe]
            complete_candle = builder.update(candle)
            
            # If a complete candle was returned, add it to history
            if complete_candle:
                if (
                    symbol in self.candle_history and
                    timeframe in self.candle_history[symbol]
                ):
                    self.candle_history[symbol][timeframe].append(complete_candle)
                    
                    # Notify callbacks
                    if (
                        symbol in self.candle_callbacks and
                        timeframe in self.candle_callbacks[symbol]
                    ):
                        for callback in self.candle_callbacks[symbol][timeframe]:
                            try:
                                callback(complete_candle)
                            except Exception as e:
                                self.logger.error(
                                    f"Error in candle callback: {e}"
                                )
        
        # Check price levels
        if symbol in self.price_levels and self.price_levels[symbol]:
            current_price = candle.close_price
            
            # Get last price
            last_candle = self.get_last_complete_candle(symbol, timeframe)
            last_price = last_candle.close_price if last_candle else None
            
            if last_price is not None:
                # Check each level
                for level in self.price_levels[symbol]:
                    # Check if price crossed the level
                    if (
                        (last_price < level and current_price >= level) or
                        (last_price > level and current_price <= level)
                    ):
                        # Notify callbacks
                        if symbol in self.level_callbacks:
                            for callback in self.level_callbacks[symbol]:
                                try:
                                    callback(level)
                                except Exception as e:
                                    self.logger.error(
                                        f"Error in level callback: {e}"
                                    )
    
    def _update_loop(self) -> None:
        """Update loop for the data feed."""
        while self.is_running:
            try:
                # Sleep for 1 second
                time.sleep(1)
                
                # TODO: Implement additional update logic if needed
                
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                time.sleep(5)  # Sleep longer on error
