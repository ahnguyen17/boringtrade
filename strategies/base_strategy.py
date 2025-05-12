"""
Base strategy for the BoringTrade trading bot.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime, time
from typing import Dict, Any, List, Optional, Set, Tuple

from brokers.broker_interface import BrokerInterface
from data.data_feed import DataFeed
from models.candle import Candle
from models.level import Level, LevelType
from models.trade import Trade, TradeDirection, TradeStatus, TradeResult
from utils.notification import Notifier
from utils.risk_manager import RiskManager


class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    """
    
    def __init__(
        self,
        data_feed: DataFeed,
        broker: BrokerInterface,
        risk_manager: RiskManager,
        notifier: Notifier,
        config: Dict[str, Any]
    ):
        """
        Initialize the strategy.
        
        Args:
            data_feed: The data feed
            broker: The broker interface
            risk_manager: The risk manager
            notifier: The notifier
            config: The configuration
        """
        self.data_feed = data_feed
        self.broker = broker
        self.risk_manager = risk_manager
        self.notifier = notifier
        self.config = config
        self.logger = logging.getLogger(f"Strategy.{self.__class__.__name__}")
        
        # Initialize strategy state
        self.is_running = False
        self.assets = config["assets"]
        self.levels: Dict[str, List[Level]] = {}
        for symbol in self.assets:
            self.levels[symbol] = []
        
        # Initialize trade tracking
        self.active_trades: Dict[str, Trade] = {}
        self.completed_trades: List[Trade] = []
        
        # Initialize timeframes
        self.execution_timeframe = config["execution_timeframe"]
        self.htf_timeframe = config["htf_timeframe"]
        
        # Initialize HTF filter
        self.htf_filter_enabled = config["htf_filter"]["enabled"]
        self.htf_ma_type = config["htf_filter"]["ma_type"]
        self.htf_ma_period = config["htf_filter"]["ma_period"]
        
        # Initialize trading hours
        self.trading_hours_start = self._parse_time(config["trading_hours"]["start"])
        self.trading_hours_end = self._parse_time(config["trading_hours"]["end"])
        self.trading_days = config["trading_hours"]["days"]
    
    def start(self) -> None:
        """Start the strategy."""
        if self.is_running:
            self.logger.warning("Strategy is already running")
            return
        
        self.logger.info("Starting strategy...")
        self.is_running = True
        
        # Register candle callbacks
        for symbol in self.assets:
            # Register execution timeframe callback
            self.data_feed.add_candle_callback(
                symbol=symbol,
                timeframe=self.execution_timeframe,
                callback=self.on_candle
            )
            
            # Register HTF callback if filter is enabled
            if self.htf_filter_enabled:
                self.data_feed.add_candle_callback(
                    symbol=symbol,
                    timeframe=self.htf_timeframe,
                    callback=self.on_htf_candle
                )
        
        # Initialize strategy-specific components
        self.initialize()
        
        self.logger.info("Strategy started")
    
    def stop(self) -> None:
        """Stop the strategy."""
        if not self.is_running:
            self.logger.warning("Strategy is not running")
            return
        
        self.logger.info("Stopping strategy...")
        self.is_running = False
        
        # Unregister candle callbacks
        for symbol in self.assets:
            # Unregister execution timeframe callback
            self.data_feed.remove_candle_callback(
                symbol=symbol,
                timeframe=self.execution_timeframe,
                callback=self.on_candle
            )
            
            # Unregister HTF callback if filter is enabled
            if self.htf_filter_enabled:
                self.data_feed.remove_candle_callback(
                    symbol=symbol,
                    timeframe=self.htf_timeframe,
                    callback=self.on_htf_candle
                )
        
        # Clean up strategy-specific components
        self.cleanup()
        
        self.logger.info("Strategy stopped")
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize strategy-specific components."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up strategy-specific components."""
        pass
    
    @abstractmethod
    def on_candle(self, candle: Candle) -> None:
        """
        Handle a new candle.
        
        Args:
            candle: The new candle
        """
        pass
    
    def on_htf_candle(self, candle: Candle) -> None:
        """
        Handle a new higher timeframe candle.
        
        Args:
            candle: The new candle
        """
        pass
    
    def is_trading_allowed(self) -> bool:
        """
        Check if trading is allowed based on time and day.
        
        Returns:
            bool: True if trading is allowed
        """
        now = datetime.now()
        current_time = now.time()
        current_day = now.strftime("%A")
        
        # Check if current day is a trading day
        if current_day not in self.trading_days:
            return False
        
        # Check if current time is within trading hours
        if current_time < self.trading_hours_start or current_time > self.trading_hours_end:
            return False
        
        return True
    
    def get_htf_trend(self, symbol: str) -> Optional[str]:
        """
        Get the higher timeframe trend.
        
        Args:
            symbol: The asset symbol
            
        Returns:
            Optional[str]: The trend direction ("UP", "DOWN", or None)
        """
        if not self.htf_filter_enabled:
            return None
        
        # Get HTF candles
        candles = self.data_feed.get_candles(
            symbol=symbol,
            timeframe=self.htf_timeframe,
            count=self.htf_ma_period + 1
        )
        
        if len(candles) < self.htf_ma_period:
            return None
        
        # Calculate MA
        if self.htf_ma_type == "SMA":
            ma = sum(c.close_price for c in candles[-self.htf_ma_period:]) / self.htf_ma_period
        elif self.htf_ma_type == "EMA":
            # Simple EMA calculation
            alpha = 2 / (self.htf_ma_period + 1)
            ma = candles[-self.htf_ma_period].close_price
            for i in range(-self.htf_ma_period + 1, 0):
                ma = candles[i].close_price * alpha + ma * (1 - alpha)
        else:
            return None
        
        # Determine trend
        current_price = candles[-1].close_price
        if current_price > ma:
            return "UP"
        elif current_price < ma:
            return "DOWN"
        
        return None
    
    def add_level(self, level: Level) -> None:
        """
        Add a price level.
        
        Args:
            level: The price level
        """
        symbol = level.symbol
        
        if symbol not in self.levels:
            self.levels[symbol] = []
        
        # Check if level already exists
        for existing_level in self.levels[symbol]:
            if (
                existing_level.level_type == level.level_type and
                abs(existing_level.price - level.price) < 0.0001
            ):
                self.logger.debug(f"Level already exists: {level}")
                return
        
        # Add level
        self.levels[symbol].append(level)
        self.logger.info(f"Added level: {level}")
        
        # Add level callback
        if level.is_zone:
            # Add callbacks for zone boundaries
            self.data_feed.add_level_callback(
                symbol=symbol,
                level=level.zone_high,
                callback=lambda price: self.on_level_cross(level, price)
            )
            self.data_feed.add_level_callback(
                symbol=symbol,
                level=level.zone_low,
                callback=lambda price: self.on_level_cross(level, price)
            )
        else:
            # Add callback for single level
            self.data_feed.add_level_callback(
                symbol=symbol,
                level=level.price,
                callback=lambda price: self.on_level_cross(level, price)
            )
    
    def remove_level(self, level: Level) -> None:
        """
        Remove a price level.
        
        Args:
            level: The price level
        """
        symbol = level.symbol
        
        if symbol not in self.levels:
            return
        
        # Remove level
        if level in self.levels[symbol]:
            self.levels[symbol].remove(level)
            self.logger.info(f"Removed level: {level}")
        
        # Remove level callback
        if level.is_zone:
            # Remove callbacks for zone boundaries
            self.data_feed.remove_level_callback(
                symbol=symbol,
                level=level.zone_high
            )
            self.data_feed.remove_level_callback(
                symbol=symbol,
                level=level.zone_low
            )
        else:
            # Remove callback for single level
            self.data_feed.remove_level_callback(
                symbol=symbol,
                level=level.price
            )
    
    def on_level_cross(self, level: Level, price: float) -> None:
        """
        Handle a price level crossing.
        
        Args:
            level: The price level
            price: The current price
        """
        # This method should be overridden by subclasses
        pass
    
    def create_trade(
        self,
        symbol: str,
        direction: TradeDirection,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        level: Optional[Level] = None
    ) -> Optional[Trade]:
        """
        Create a new trade.
        
        Args:
            symbol: The asset symbol
            direction: The trade direction
            entry_price: The entry price
            stop_loss: The stop loss price
            take_profit: The take profit price
            level: The price level that triggered the trade
            
        Returns:
            Optional[Trade]: The created trade
        """
        # Check if trading is allowed
        if not self.is_trading_allowed():
            self.logger.warning("Trading is not allowed at this time")
            return None
        
        # Check if we already have an active trade for this symbol
        if symbol in self.active_trades:
            self.logger.warning(f"Already have an active trade for {symbol}")
            return None
        
        # Calculate position size
        position_size, risk_amount = self.risk_manager.calculate_position_size(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            max_contracts=self.config["position_size"]
        )
        
        # Check if trade can be placed
        can_place, reason = self.risk_manager.can_place_trade(
            symbol=symbol,
            risk_amount=risk_amount,
            strategy_name=self.__class__.__name__
        )
        
        if not can_place:
            self.logger.warning(f"Cannot place trade: {reason}")
            return None
        
        # Create trade
        trade = Trade(
            symbol=symbol,
            direction=direction,
            strategy_name=self.__class__.__name__,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=position_size,
            entry_time=datetime.now(),
            status=TradeStatus.PENDING,
            level=level
        )
        
        # Register trade with risk manager
        self.risk_manager.register_trade(trade)
        
        # Place order
        success, message, order_details = self.broker.place_market_order(
            symbol=symbol,
            direction=direction,
            quantity=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        if not success:
            self.logger.error(f"Failed to place order: {message}")
            trade.status = TradeStatus.REJECTED
            trade.notes = message
            self.risk_manager.update_trade(trade)
            return None
        
        # Update trade with order details
        if order_details:
            trade.broker_order_id = order_details.get("order_id")
            trade.status = TradeStatus.OPEN
        
        # Add to active trades
        self.active_trades[symbol] = trade
        
        # Send notification
        self.notifier.send_trade_entry_notification(
            symbol=symbol,
            direction=direction.value,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=position_size,
            strategy_name=self.__class__.__name__,
            risk_reward=trade.risk_reward_ratio
        )
        
        self.logger.info(f"Created trade: {trade}")
        return trade
    
    def close_trade(
        self,
        symbol: str,
        exit_price: float,
        reason: str = "Manual close"
    ) -> Optional[Trade]:
        """
        Close a trade.
        
        Args:
            symbol: The asset symbol
            exit_price: The exit price
            reason: The reason for closing the trade
            
        Returns:
            Optional[Trade]: The closed trade
        """
        # Check if we have an active trade for this symbol
        if symbol not in self.active_trades:
            self.logger.warning(f"No active trade for {symbol}")
            return None
        
        trade = self.active_trades[symbol]
        
        # Close position
        success, message, order_details = self.broker.close_position(symbol)
        
        if not success:
            self.logger.error(f"Failed to close position: {message}")
            return None
        
        # Update trade
        trade.exit_price = exit_price
        trade.exit_time = datetime.now()
        trade.status = TradeStatus.CLOSED
        trade.notes = reason
        
        # Calculate profit/loss
        if trade.direction == TradeDirection.LONG:
            pl = exit_price - trade.entry_price
        else:
            pl = trade.entry_price - exit_price
        
        pl_amount = pl * trade.quantity
        
        # Determine result
        if pl > 0:
            trade.result = TradeResult.WIN
        elif pl < 0:
            trade.result = TradeResult.LOSS
        else:
            trade.result = TradeResult.BREAKEVEN
        
        # Update risk manager
        self.risk_manager.update_trade(trade)
        
        # Remove from active trades
        del self.active_trades[symbol]
        
        # Add to completed trades
        self.completed_trades.append(trade)
        
        # Send notification
        self.notifier.send_trade_exit_notification(
            symbol=symbol,
            direction=trade.direction.value,
            entry_price=trade.entry_price,
            exit_price=exit_price,
            quantity=trade.quantity,
            profit_loss=pl_amount,
            profit_loss_r=trade.profit_loss_r,
            exit_reason=reason
        )
        
        self.logger.info(f"Closed trade: {trade}")
        return trade
    
    def _parse_time(self, time_str: str) -> time:
        """
        Parse a time string.
        
        Args:
            time_str: The time string (HH:MM)
            
        Returns:
            time: The parsed time
        """
        hour, minute = map(int, time_str.split(":"))
        return time(hour, minute)
