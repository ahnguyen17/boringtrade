"""
Order Block strategy for the BoringTrade trading bot.
"""
import logging
from datetime import datetime, time, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple

from data.data_feed import DataFeed
from brokers.broker_interface import BrokerInterface
from models.candle import Candle
from models.level import Level, LevelType
from models.trade import Trade, TradeDirection, TradeStatus, TradeResult
from strategies.base_strategy import BaseStrategy
from utils.notification import Notifier
from utils.risk_manager import RiskManager


class OrderBlockStrategy(BaseStrategy):
    """
    Order Block (OB) strategy.

    This strategy:
    1. Identifies order blocks (last up/down candle before a strong move)
    2. Detects retests of these order blocks
    3. Enters trades when the retest holds
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
        Initialize the Order Block strategy.

        Args:
            data_feed: The data feed
            broker: The broker interface
            risk_manager: The risk manager
            notifier: The notifier
            config: The configuration
        """
        super().__init__(data_feed, broker, risk_manager, notifier, config)

        # Get OB-specific configuration
        ob_config = config["ob"]
        self.ob_enabled = ob_config["enabled"]
        self.lookback_period = ob_config["lookback_period"]
        self.significant_move_threshold = ob_config["significant_move_threshold"]
        self.retest_threshold = ob_config["retest_threshold"]
        self.confirmation_candles = ob_config["confirmation_candles"]
        self.manual_input = ob_config["manual_input"]

        # Initialize OB tracking
        self.order_blocks: Dict[str, List[Level]] = {}
        for symbol in self.assets:
            self.order_blocks[symbol] = []

        self.retests: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for symbol in self.assets:
            self.retests[symbol] = {}

        # Initialize stop loss and take profit settings
        self.stop_loss_type = config["stop_loss"]["type"]
        self.stop_loss_buffer = config["stop_loss"]["buffer"]
        self.take_profit_type = config["take_profit"]["type"]
        self.take_profit_ratio = config["take_profit"]["risk_reward_ratio"]

    def initialize(self) -> None:
        """Initialize strategy-specific components."""
        self.logger.info("Initializing Order Block strategy...")

        if not self.ob_enabled:
            self.logger.info("Order Block strategy is disabled")
            return

        # Identify order blocks for each asset
        for symbol in self.assets:
            self.identify_order_blocks(symbol)

        # Register for candle updates
        for symbol in self.assets:
            # Use the execution timeframe for order block identification
            self.data_feed.add_candle_callback(
                symbol=symbol,
                timeframe=self.execution_timeframe,
                callback=self._on_execution_candle
            )

    def cleanup(self) -> None:
        """Clean up strategy-specific components."""
        self.logger.info("Cleaning up Order Block strategy...")

        if not self.ob_enabled:
            return

        # Unregister from candle updates
        for symbol in self.assets:
            self.data_feed.remove_candle_callback(
                symbol=symbol,
                timeframe=self.execution_timeframe,
                callback=self._on_execution_candle
            )

    def on_candle(self, candle: Candle) -> None:
        """
        Handle a new candle.

        Args:
            candle: The new candle
        """
        symbol = candle.symbol

        # Check if OB is enabled
        if not self.ob_enabled:
            return

        # Check if we have order blocks for this symbol
        if symbol not in self.order_blocks or not self.order_blocks[symbol]:
            return

        # Check for retests
        self._check_for_retests(symbol, candle)

        # Check for trade entries
        self._check_for_entries(symbol, candle)

        # Check for trade exits
        self._check_for_exits(symbol, candle)

    def on_level_cross(self, level: Level, price: float) -> None:
        """
        Handle a price level crossing.

        Args:
            level: The price level
            price: The current price
        """
        symbol = level.symbol

        # Check if OB is enabled
        if not self.ob_enabled:
            return

        # Check if this is an order block level
        if level.level_type not in [LevelType.BULLISH_ORDER_BLOCK, LevelType.BEARISH_ORDER_BLOCK]:
            return

        # Check if we have retest tracking for this level
        if symbol not in self.retests or level.price not in self.retests[symbol]:
            # Initialize retest tracking for this level
            if symbol not in self.retests:
                self.retests[symbol] = {}

            self.retests[symbol][level.price] = {
                "in_progress": False,
                "confirmed": False,
                "candles": []
            }

        # Start retest tracking
        self.retests[symbol][level.price]["in_progress"] = True
        self.logger.info(f"Order block retest started for {symbol} at {price}")

    def identify_order_blocks(self, symbol: str) -> None:
        """
        Identify order blocks for a symbol.

        Args:
            symbol: The asset symbol
        """
        # Get historical candles
        candles = self.data_feed.get_candles(
            symbol=symbol,
            timeframe=self.execution_timeframe,
            count=self.lookback_period
        )

        if len(candles) < self.lookback_period:
            self.logger.warning(f"Not enough candles to identify order blocks for {symbol}")
            return

        # Find bullish order blocks (last down candle before a significant up move)
        for i in range(len(candles) - 3):
            # Check if this is a down candle
            if not candles[i].is_bearish:
                continue

            # Check if the next candles form a significant up move
            up_move = (candles[i+2].close_price - candles[i].close_price) / candles[i].close_price
            if up_move < self.significant_move_threshold:
                continue

            # This is a bullish order block
            ob_price = (candles[i].high_price + candles[i].low_price) / 2
            ob_high = candles[i].high_price
            ob_low = candles[i].low_price

            # Create level
            level = Level(
                symbol=symbol,
                price=ob_price,
                level_type=LevelType.BULLISH_ORDER_BLOCK,
                timestamp=candles[i].timestamp,
                description=f"Bullish Order Block ({candles[i].timestamp.strftime('%Y-%m-%d %H:%M')})",
                zone_high=ob_high,
                zone_low=ob_low,
                is_active=True
            )

            # Add level
            self.add_level(level)

            # Add to order blocks
            self.order_blocks[symbol].append(level)

            # Initialize retest tracking
            if symbol not in self.retests:
                self.retests[symbol] = {}

            self.retests[symbol][level.price] = {
                "in_progress": False,
                "confirmed": False,
                "candles": []
            }

            self.logger.info(f"Identified bullish order block for {symbol} at {ob_price:.2f}")

        # Find bearish order blocks (last up candle before a significant down move)
        for i in range(len(candles) - 3):
            # Check if this is an up candle
            if not candles[i].is_bullish:
                continue

            # Check if the next candles form a significant down move
            down_move = (candles[i].close_price - candles[i+2].close_price) / candles[i].close_price
            if down_move < self.significant_move_threshold:
                continue

            # This is a bearish order block
            ob_price = (candles[i].high_price + candles[i].low_price) / 2
            ob_high = candles[i].high_price
            ob_low = candles[i].low_price

            # Create level
            level = Level(
                symbol=symbol,
                price=ob_price,
                level_type=LevelType.BEARISH_ORDER_BLOCK,
                timestamp=candles[i].timestamp,
                description=f"Bearish Order Block ({candles[i].timestamp.strftime('%Y-%m-%d %H:%M')})",
                zone_high=ob_high,
                zone_low=ob_low,
                is_active=True
            )

            # Add level
            self.add_level(level)

            # Add to order blocks
            self.order_blocks[symbol].append(level)

            # Initialize retest tracking
            if symbol not in self.retests:
                self.retests[symbol] = {}

            self.retests[symbol][level.price] = {
                "in_progress": False,
                "confirmed": False,
                "candles": []
            }

            self.logger.info(f"Identified bearish order block for {symbol} at {ob_price:.2f}")

    def _on_execution_candle(self, candle: Candle) -> None:
        """
        Handle a new execution timeframe candle.

        Args:
            candle: The new candle
        """
        symbol = candle.symbol

        # Check if OB is enabled
        if not self.ob_enabled:
            return

        # Update order blocks periodically
        if candle.timestamp.minute % 15 == 0 and candle.timestamp.second == 0:
            self.identify_order_blocks(symbol)

        # Process the candle
        self.on_candle(candle)

    def _check_for_retests(self, symbol: str, candle: Candle) -> None:
        """
        Check for retests of order blocks.

        Args:
            symbol: The asset symbol
            candle: The current candle
        """
        # Check if we have order blocks for this symbol
        if symbol not in self.order_blocks or not self.order_blocks[symbol]:
            return

        # Check each order block
        for level in self.order_blocks[symbol]:
            # Skip inactive levels
            if not level.is_active:
                continue

            # Check if we have retest tracking for this level
            if level.price not in self.retests[symbol]:
                self.retests[symbol][level.price] = {
                    "in_progress": False,
                    "confirmed": False,
                    "candles": []
                }

            # Check for bullish order block retest
            if level.level_type == LevelType.BULLISH_ORDER_BLOCK:
                # Check if price is in the order block zone
                if (
                    candle.low_price <= level.zone_high and
                    candle.low_price >= level.zone_low
                ):
                    # Start or continue retest
                    if not self.retests[symbol][level.price]["in_progress"]:
                        self.retests[symbol][level.price]["in_progress"] = True
                        self.retests[symbol][level.price]["candles"] = [candle]
                        level.add_retest(
                            timestamp=candle.timestamp,
                            price=candle.low_price,
                            direction="above",
                            candle_index=None
                        )
                        self.logger.info(f"Bullish OB retest started for {symbol} at {candle.low_price}")
                    else:
                        self.retests[symbol][level.price]["candles"].append(candle)

                    # Check for confirmation
                    if len(self.retests[symbol][level.price]["candles"]) >= self.confirmation_candles:
                        # Check if the retest is confirmed (price bounced from the level)
                        last_candle = self.retests[symbol][level.price]["candles"][-1]
                        if last_candle.close_price > level.zone_high:
                            self.retests[symbol][level.price]["confirmed"] = True
                            self.logger.info(f"Bullish OB retest confirmed for {symbol}")
                else:
                    # Reset retest if price moved away from the level
                    if (
                        self.retests[symbol][level.price]["in_progress"] and
                        not self.retests[symbol][level.price]["confirmed"] and
                        candle.low_price < level.zone_low - (level.zone_low * self.retest_threshold)
                    ):
                        self.retests[symbol][level.price]["in_progress"] = False
                        self.retests[symbol][level.price]["candles"] = []
                        self.logger.info(f"Bullish OB retest cancelled for {symbol}")

            # Check for bearish order block retest
            elif level.level_type == LevelType.BEARISH_ORDER_BLOCK:
                # Check if price is in the order block zone
                if (
                    candle.high_price >= level.zone_low and
                    candle.high_price <= level.zone_high
                ):
                    # Start or continue retest
                    if not self.retests[symbol][level.price]["in_progress"]:
                        self.retests[symbol][level.price]["in_progress"] = True
                        self.retests[symbol][level.price]["candles"] = [candle]
                        level.add_retest(
                            timestamp=candle.timestamp,
                            price=candle.high_price,
                            direction="below",
                            candle_index=None
                        )
                        self.logger.info(f"Bearish OB retest started for {symbol} at {candle.high_price}")
                    else:
                        self.retests[symbol][level.price]["candles"].append(candle)

                    # Check for confirmation
                    if len(self.retests[symbol][level.price]["candles"]) >= self.confirmation_candles:
                        # Check if the retest is confirmed (price bounced from the level)
                        last_candle = self.retests[symbol][level.price]["candles"][-1]
                        if last_candle.close_price < level.zone_low:
                            self.retests[symbol][level.price]["confirmed"] = True
                            self.logger.info(f"Bearish OB retest confirmed for {symbol}")
                else:
                    # Reset retest if price moved away from the level
                    if (
                        self.retests[symbol][level.price]["in_progress"] and
                        not self.retests[symbol][level.price]["confirmed"] and
                        candle.high_price > level.zone_high + (level.zone_high * self.retest_threshold)
                    ):
                        self.retests[symbol][level.price]["in_progress"] = False
                        self.retests[symbol][level.price]["candles"] = []
                        self.logger.info(f"Bearish OB retest cancelled for {symbol}")

    def _check_for_entries(self, symbol: str, candle: Candle) -> None:
        """
        Check for trade entries.

        Args:
            symbol: The asset symbol
            candle: The current candle
        """
        # Check if we already have an active trade for this symbol
        if symbol in self.active_trades:
            return

        # Check if trading is allowed
        if not self.is_trading_allowed():
            return

        # Check if we have order blocks for this symbol
        if symbol not in self.order_blocks or not self.order_blocks[symbol]:
            return

        # Check each order block
        for level in self.order_blocks[symbol]:
            # Skip inactive levels
            if not level.is_active:
                continue

            # Check if we have retest tracking for this level
            if level.price not in self.retests[symbol]:
                continue

            # Check for long entry (bullish order block retest)
            if (
                level.level_type == LevelType.BULLISH_ORDER_BLOCK and
                self.retests[symbol][level.price]["confirmed"]
            ):
                # Check HTF trend if filter is enabled
                if self.htf_filter_enabled:
                    htf_trend = self.get_htf_trend(symbol)
                    if htf_trend == "DOWN":
                        self.logger.info(f"Skipping long entry for {symbol} due to HTF downtrend")
                        continue

                # Calculate stop loss
                if self.stop_loss_type == "level":
                    stop_loss = level.zone_low - (level.zone_low * self.stop_loss_buffer)
                else:  # "candle"
                    retest_candles = self.retests[symbol][level.price]["candles"]
                    retest_low = min(c.low_price for c in retest_candles)
                    stop_loss = retest_low - (retest_low * self.stop_loss_buffer)

                # Calculate take profit
                if self.take_profit_type == "risk_reward":
                    risk = candle.close_price - stop_loss
                    take_profit = candle.close_price + (risk * self.take_profit_ratio)
                else:  # "next_level"
                    # Find next resistance level (for simplicity, use a fixed multiple)
                    take_profit = candle.close_price + (candle.close_price - stop_loss) * 2

                # Create trade
                self.create_trade(
                    symbol=symbol,
                    direction=TradeDirection.LONG,
                    entry_price=candle.close_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    level=level
                )

                # Reset retest tracking
                self.retests[symbol][level.price]["confirmed"] = False

                # Mark level as inactive
                level.is_active = False

                # Only enter one trade at a time
                break

            # Check for short entry (bearish order block retest)
            elif (
                level.level_type == LevelType.BEARISH_ORDER_BLOCK and
                self.retests[symbol][level.price]["confirmed"]
            ):
                # Check HTF trend if filter is enabled
                if self.htf_filter_enabled:
                    htf_trend = self.get_htf_trend(symbol)
                    if htf_trend == "UP":
                        self.logger.info(f"Skipping short entry for {symbol} due to HTF uptrend")
                        continue

                # Calculate stop loss
                if self.stop_loss_type == "level":
                    stop_loss = level.zone_high + (level.zone_high * self.stop_loss_buffer)
                else:  # "candle"
                    retest_candles = self.retests[symbol][level.price]["candles"]
                    retest_high = max(c.high_price for c in retest_candles)
                    stop_loss = retest_high + (retest_high * self.stop_loss_buffer)

                # Calculate take profit
                if self.take_profit_type == "risk_reward":
                    risk = stop_loss - candle.close_price
                    take_profit = candle.close_price - (risk * self.take_profit_ratio)
                else:  # "next_level"
                    # Find next support level (for simplicity, use a fixed multiple)
                    take_profit = candle.close_price - (stop_loss - candle.close_price) * 2

                # Create trade
                self.create_trade(
                    symbol=symbol,
                    direction=TradeDirection.SHORT,
                    entry_price=candle.close_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    level=level
                )

                # Reset retest tracking
                self.retests[symbol][level.price]["confirmed"] = False

                # Mark level as inactive
                level.is_active = False

                # Only enter one trade at a time
                break

    def _check_for_exits(self, symbol: str, candle: Candle) -> None:
        """
        Check for trade exits.

        Args:
            symbol: The asset symbol
            candle: The current candle
        """
        # Check if we have an active trade for this symbol
        if symbol not in self.active_trades:
            return

        trade = self.active_trades[symbol]

        # Check for stop loss hit
        if trade.direction == TradeDirection.LONG:
            if candle.low_price <= trade.stop_loss:
                self.close_trade(
                    symbol=symbol,
                    exit_price=trade.stop_loss,
                    reason="Stop loss hit"
                )
                return
        else:  # SHORT
            if candle.high_price >= trade.stop_loss:
                self.close_trade(
                    symbol=symbol,
                    exit_price=trade.stop_loss,
                    reason="Stop loss hit"
                )
                return

        # Check for take profit hit
        if trade.direction == TradeDirection.LONG:
            if candle.high_price >= trade.take_profit:
                self.close_trade(
                    symbol=symbol,
                    exit_price=trade.take_profit,
                    reason="Take profit hit"
                )
                return
        else:  # SHORT
            if candle.low_price <= trade.take_profit:
                self.close_trade(
                    symbol=symbol,
                    exit_price=trade.take_profit,
                    reason="Take profit hit"
                )
                return

    def add_manual_order_block(
        self,
        symbol: str,
        price: float,
        zone_high: float,
        zone_low: float,
        direction: str
    ) -> Optional[Level]:
        """
        Add a manually defined order block.

        Args:
            symbol: The asset symbol
            price: The center price of the order block
            zone_high: The high price of the order block
            zone_low: The low price of the order block
            direction: The direction of the order block ("bullish" or "bearish")

        Returns:
            Optional[Level]: The created order block level
        """
        if not self.manual_input:
            self.logger.warning("Manual order block input is disabled")
            return None

        # Create level
        level_type = (
            LevelType.BULLISH_ORDER_BLOCK
            if direction.lower() == "bullish"
            else LevelType.BEARISH_ORDER_BLOCK
        )

        level = Level(
            symbol=symbol,
            price=price,
            level_type=level_type,
            timestamp=datetime.now(),
            description=f"Manual {direction} Order Block",
            zone_high=zone_high,
            zone_low=zone_low,
            is_active=True
        )

        # Add level
        self.add_level(level)

        # Add to order blocks
        if symbol not in self.order_blocks:
            self.order_blocks[symbol] = []

        self.order_blocks[symbol].append(level)

        # Initialize retest tracking
        if symbol not in self.retests:
            self.retests[symbol] = {}

        self.retests[symbol][level.price] = {
            "in_progress": False,
            "confirmed": False,
            "candles": []
        }

        self.logger.info(f"Added manual order block: {level}")
        return level
