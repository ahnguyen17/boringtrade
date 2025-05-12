"""
Previous Day High/Low strategy for the BoringTrade trading bot.
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


class PDHPDLStrategy(BaseStrategy):
    """
    Previous Day High/Low (PDH/PDL) strategy.

    This strategy:
    1. Identifies the previous day's high and low
    2. Detects breakouts above/below these levels
    3. Looks for retests of the broken level
    4. Enters trades when the retest holds
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
        Initialize the PDH/PDL strategy.

        Args:
            data_feed: The data feed
            broker: The broker interface
            risk_manager: The risk manager
            notifier: The notifier
            config: The configuration
        """
        super().__init__(data_feed, broker, risk_manager, notifier, config)

        # Get PDH/PDL-specific configuration
        pdh_pdl_config = config["pdh_pdl"]
        self.pdh_pdl_enabled = pdh_pdl_config["enabled"]
        self.breakout_threshold = pdh_pdl_config["breakout_threshold"]
        self.retest_threshold = pdh_pdl_config["retest_threshold"]
        self.confirmation_candles = pdh_pdl_config["confirmation_candles"]

        # Initialize PDH/PDL tracking
        self.previous_day_levels: Dict[str, Dict[str, Any]] = {}
        self.breakouts: Dict[str, Dict[str, Any]] = {}
        self.retests: Dict[str, Dict[str, Any]] = {}

        # Initialize data structures for each asset
        for symbol in self.assets:
            self.previous_day_levels[symbol] = {
                "identified": False,
                "high_level": None,
                "low_level": None,
                "date": None
            }
            self.breakouts[symbol] = {
                "high": False,
                "low": False,
                "high_candle": None,
                "low_candle": None
            }
            self.retests[symbol] = {
                "high": {
                    "in_progress": False,
                    "confirmed": False,
                    "candles": []
                },
                "low": {
                    "in_progress": False,
                    "confirmed": False,
                    "candles": []
                }
            }

        # Initialize stop loss and take profit settings
        self.stop_loss_type = config["stop_loss"]["type"]
        self.stop_loss_buffer = config["stop_loss"]["buffer"]
        self.take_profit_type = config["take_profit"]["type"]
        self.take_profit_ratio = config["take_profit"]["risk_reward_ratio"]

    def initialize(self) -> None:
        """Initialize strategy-specific components."""
        self.logger.info("Initializing PDH/PDL strategy...")

        if not self.pdh_pdl_enabled:
            self.logger.info("PDH/PDL strategy is disabled")
            return

        # Identify previous day high/low for each asset
        for symbol in self.assets:
            self._identify_previous_day_levels(symbol)

        # Register for daily candles to update PDH/PDL
        for symbol in self.assets:
            # Use the highest timeframe available for daily tracking
            self.data_feed.add_candle_callback(
                symbol=symbol,
                timeframe=self.htf_timeframe,
                callback=self._on_daily_candle
            )

    def cleanup(self) -> None:
        """Clean up strategy-specific components."""
        self.logger.info("Cleaning up PDH/PDL strategy...")

        if not self.pdh_pdl_enabled:
            return

        # Unregister from daily candles
        for symbol in self.assets:
            self.data_feed.remove_candle_callback(
                symbol=symbol,
                timeframe=self.htf_timeframe,
                callback=self._on_daily_candle
            )

    def on_candle(self, candle: Candle) -> None:
        """
        Handle a new candle.

        Args:
            candle: The new candle
        """
        symbol = candle.symbol

        # Check if PDH/PDL is enabled
        if not self.pdh_pdl_enabled:
            return

        # Check if we have previous day levels for this symbol
        if (
            symbol not in self.previous_day_levels or
            not self.previous_day_levels[symbol]["identified"]
        ):
            return

        # Check for breakouts
        self._check_for_breakouts(symbol, candle)

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

        # Check if PDH/PDL is enabled
        if not self.pdh_pdl_enabled:
            return

        # Check if this is a PDH/PDL level
        if level.level_type not in [LevelType.PREVIOUS_DAY_HIGH, LevelType.PREVIOUS_DAY_LOW]:
            return

        # Check if we have breakout tracking for this symbol
        if symbol not in self.breakouts:
            return

        # Handle PDH crossing
        if level.level_type == LevelType.PREVIOUS_DAY_HIGH:
            if not self.breakouts[symbol]["high"]:
                # Record breakout
                self.breakouts[symbol]["high"] = True
                self.breakouts[symbol]["high_candle"] = self.data_feed.get_current_candle(
                    symbol=symbol,
                    timeframe=self.execution_timeframe
                )
                level.add_break(
                    timestamp=datetime.now(),
                    price=price,
                    direction="above"
                )
                self.logger.info(f"PDH breakout detected for {symbol} at {price}")

        # Handle PDL crossing
        elif level.level_type == LevelType.PREVIOUS_DAY_LOW:
            if not self.breakouts[symbol]["low"]:
                # Record breakout
                self.breakouts[symbol]["low"] = True
                self.breakouts[symbol]["low_candle"] = self.data_feed.get_current_candle(
                    symbol=symbol,
                    timeframe=self.execution_timeframe
                )
                level.add_break(
                    timestamp=datetime.now(),
                    price=price,
                    direction="below"
                )
                self.logger.info(f"PDL breakout detected for {symbol} at {price}")

    def _on_daily_candle(self, candle: Candle) -> None:
        """
        Handle a new daily candle.

        Args:
            candle: The new candle
        """
        # Check if this is a new day
        symbol = candle.symbol
        candle_date = candle.timestamp.date()

        if (
            symbol in self.previous_day_levels and
            self.previous_day_levels[symbol]["identified"] and
            self.previous_day_levels[symbol]["date"] == candle_date
        ):
            # Same day, no need to update
            return

        # New day, update previous day levels
        self._identify_previous_day_levels(symbol)

    def _identify_previous_day_levels(self, symbol: str) -> None:
        """
        Identify previous day high and low for a symbol.

        Args:
            symbol: The asset symbol
        """
        # Get daily candles
        candles = self.data_feed.get_candles(
            symbol=symbol,
            timeframe=self.htf_timeframe,
            count=2  # We need at least 2 candles (today and yesterday)
        )

        if len(candles) < 2:
            self.logger.warning(f"Not enough candles to identify previous day levels for {symbol}")
            return

        # Get previous day candle (second to last)
        prev_day_candle = candles[-2]
        current_day = candles[-1].timestamp.date()

        # Create PDH level
        pdh_level = Level(
            symbol=symbol,
            price=prev_day_candle.high_price,
            level_type=LevelType.PREVIOUS_DAY_HIGH,
            timestamp=prev_day_candle.timestamp,
            description=f"Previous Day High ({prev_day_candle.timestamp.date()})"
        )

        # Create PDL level
        pdl_level = Level(
            symbol=symbol,
            price=prev_day_candle.low_price,
            level_type=LevelType.PREVIOUS_DAY_LOW,
            timestamp=prev_day_candle.timestamp,
            description=f"Previous Day Low ({prev_day_candle.timestamp.date()})"
        )

        # Add levels
        self.add_level(pdh_level)
        self.add_level(pdl_level)

        # Update previous day levels tracking
        self.previous_day_levels[symbol] = {
            "identified": True,
            "high_level": pdh_level,
            "low_level": pdl_level,
            "date": current_day
        }

        # Reset breakout tracking
        self.breakouts[symbol] = {
            "high": False,
            "low": False,
            "high_candle": None,
            "low_candle": None
        }

        # Reset retest tracking
        self.retests[symbol] = {
            "high": {
                "in_progress": False,
                "confirmed": False,
                "candles": []
            },
            "low": {
                "in_progress": False,
                "confirmed": False,
                "candles": []
            }
        }

        self.logger.info(
            f"Previous day levels identified for {symbol}: "
            f"High={pdh_level.price:.2f}, Low={pdl_level.price:.2f}"
        )

    def _check_for_breakouts(self, symbol: str, candle: Candle) -> None:
        """
        Check for breakouts of the previous day high/low.

        Args:
            symbol: The asset symbol
            candle: The current candle
        """
        # Check if previous day levels are identified
        if (
            symbol not in self.previous_day_levels or
            not self.previous_day_levels[symbol]["identified"]
        ):
            return

        # Get previous day levels
        pdh_level = self.previous_day_levels[symbol]["high_level"]
        pdl_level = self.previous_day_levels[symbol]["low_level"]

        # Check for high breakout
        if (
            not self.breakouts[symbol]["high"] and
            candle.close_price > pdh_level.price + (pdh_level.price * self.breakout_threshold)
        ):
            # Record breakout
            self.breakouts[symbol]["high"] = True
            self.breakouts[symbol]["high_candle"] = candle
            pdh_level.add_break(
                timestamp=candle.timestamp,
                price=candle.close_price,
                direction="above",
                candle_index=None
            )
            self.logger.info(f"PDH breakout detected for {symbol} at {candle.close_price}")

        # Check for low breakout
        if (
            not self.breakouts[symbol]["low"] and
            candle.close_price < pdl_level.price - (pdl_level.price * self.breakout_threshold)
        ):
            # Record breakout
            self.breakouts[symbol]["low"] = True
            self.breakouts[symbol]["low_candle"] = candle
            pdl_level.add_break(
                timestamp=candle.timestamp,
                price=candle.close_price,
                direction="below",
                candle_index=None
            )
            self.logger.info(f"PDL breakout detected for {symbol} at {candle.close_price}")

    def _check_for_retests(self, symbol: str, candle: Candle) -> None:
        """
        Check for retests of the previous day high/low.

        Args:
            symbol: The asset symbol
            candle: The current candle
        """
        # Check if previous day levels are identified
        if (
            symbol not in self.previous_day_levels or
            not self.previous_day_levels[symbol]["identified"]
        ):
            return

        # Get previous day levels
        pdh_level = self.previous_day_levels[symbol]["high_level"]
        pdl_level = self.previous_day_levels[symbol]["low_level"]

        # Check for high retest
        if (
            self.breakouts[symbol]["high"] and
            not self.retests[symbol]["high"]["confirmed"]
        ):
            # Check if price is near the high level
            if abs(candle.low_price - pdh_level.price) <= (pdh_level.price * self.retest_threshold):
                # Start or continue retest
                if not self.retests[symbol]["high"]["in_progress"]:
                    self.retests[symbol]["high"]["in_progress"] = True
                    self.retests[symbol]["high"]["candles"] = [candle]
                    pdh_level.add_retest(
                        timestamp=candle.timestamp,
                        price=candle.low_price,
                        direction="above",
                        candle_index=None
                    )
                    self.logger.info(f"PDH retest started for {symbol} at {candle.low_price}")
                else:
                    self.retests[symbol]["high"]["candles"].append(candle)

                # Check for confirmation
                if len(self.retests[symbol]["high"]["candles"]) >= self.confirmation_candles:
                    # Check if the retest is confirmed (price bounced from the level)
                    last_candle = self.retests[symbol]["high"]["candles"][-1]
                    if last_candle.close_price > pdh_level.price:
                        self.retests[symbol]["high"]["confirmed"] = True
                        self.logger.info(f"PDH retest confirmed for {symbol}")
            else:
                # Reset retest if price moved away from the level
                if (
                    self.retests[symbol]["high"]["in_progress"] and
                    not self.retests[symbol]["high"]["confirmed"] and
                    candle.low_price < pdh_level.price - (pdh_level.price * self.retest_threshold * 2)
                ):
                    self.retests[symbol]["high"]["in_progress"] = False
                    self.retests[symbol]["high"]["candles"] = []
                    self.logger.info(f"PDH retest cancelled for {symbol}")

        # Check for low retest
        if (
            self.breakouts[symbol]["low"] and
            not self.retests[symbol]["low"]["confirmed"]
        ):
            # Check if price is near the low level
            if abs(candle.high_price - pdl_level.price) <= (pdl_level.price * self.retest_threshold):
                # Start or continue retest
                if not self.retests[symbol]["low"]["in_progress"]:
                    self.retests[symbol]["low"]["in_progress"] = True
                    self.retests[symbol]["low"]["candles"] = [candle]
                    pdl_level.add_retest(
                        timestamp=candle.timestamp,
                        price=candle.high_price,
                        direction="below",
                        candle_index=None
                    )
                    self.logger.info(f"PDL retest started for {symbol} at {candle.high_price}")
                else:
                    self.retests[symbol]["low"]["candles"].append(candle)

                # Check for confirmation
                if len(self.retests[symbol]["low"]["candles"]) >= self.confirmation_candles:
                    # Check if the retest is confirmed (price bounced from the level)
                    last_candle = self.retests[symbol]["low"]["candles"][-1]
                    if last_candle.close_price < pdl_level.price:
                        self.retests[symbol]["low"]["confirmed"] = True
                        self.logger.info(f"PDL retest confirmed for {symbol}")
            else:
                # Reset retest if price moved away from the level
                if (
                    self.retests[symbol]["low"]["in_progress"] and
                    not self.retests[symbol]["low"]["confirmed"] and
                    candle.high_price > pdl_level.price + (pdl_level.price * self.retest_threshold * 2)
                ):
                    self.retests[symbol]["low"]["in_progress"] = False
                    self.retests[symbol]["low"]["candles"] = []
                    self.logger.info(f"PDL retest cancelled for {symbol}")

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

        # Check if previous day levels are identified
        if (
            symbol not in self.previous_day_levels or
            not self.previous_day_levels[symbol]["identified"]
        ):
            return

        # Get previous day levels
        pdh_level = self.previous_day_levels[symbol]["high_level"]
        pdl_level = self.previous_day_levels[symbol]["low_level"]

        # Check for long entry (PDH breakout and retest)
        if (
            self.breakouts[symbol]["high"] and
            self.retests[symbol]["high"]["confirmed"]
        ):
            # Check HTF trend if filter is enabled
            if self.htf_filter_enabled:
                htf_trend = self.get_htf_trend(symbol)
                if htf_trend == "DOWN":
                    self.logger.info(f"Skipping long entry for {symbol} due to HTF downtrend")
                    return

            # Calculate stop loss
            if self.stop_loss_type == "level":
                stop_loss = pdh_level.price - (pdh_level.price * self.stop_loss_buffer)
            else:  # "candle"
                retest_candles = self.retests[symbol]["high"]["candles"]
                retest_low = min(c.low_price for c in retest_candles)
                stop_loss = retest_low - (retest_low * self.stop_loss_buffer)

            # Calculate take profit
            if self.take_profit_type == "risk_reward":
                risk = candle.close_price - stop_loss
                take_profit = candle.close_price + (risk * self.take_profit_ratio)
            else:  # "next_level"
                # Find next resistance level
                # For simplicity, we'll use a fixed multiple of the range
                range_size = pdh_level.price - pdl_level.price
                take_profit = pdh_level.price + range_size

            # Create trade
            self.create_trade(
                symbol=symbol,
                direction=TradeDirection.LONG,
                entry_price=candle.close_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                level=pdh_level
            )

            # Reset retest tracking
            self.retests[symbol]["high"]["confirmed"] = False

        # Check for short entry (PDL breakout and retest)
        elif (
            self.breakouts[symbol]["low"] and
            self.retests[symbol]["low"]["confirmed"]
        ):
            # Check HTF trend if filter is enabled
            if self.htf_filter_enabled:
                htf_trend = self.get_htf_trend(symbol)
                if htf_trend == "UP":
                    self.logger.info(f"Skipping short entry for {symbol} due to HTF uptrend")
                    return

            # Calculate stop loss
            if self.stop_loss_type == "level":
                stop_loss = pdl_level.price + (pdl_level.price * self.stop_loss_buffer)
            else:  # "candle"
                retest_candles = self.retests[symbol]["low"]["candles"]
                retest_high = max(c.high_price for c in retest_candles)
                stop_loss = retest_high + (retest_high * self.stop_loss_buffer)

            # Calculate take profit
            if self.take_profit_type == "risk_reward":
                risk = stop_loss - candle.close_price
                take_profit = candle.close_price - (risk * self.take_profit_ratio)
            else:  # "next_level"
                # Find next support level
                # For simplicity, we'll use a fixed multiple of the range
                range_size = pdh_level.price - pdl_level.price
                take_profit = pdl_level.price - range_size

            # Create trade
            self.create_trade(
                symbol=symbol,
                direction=TradeDirection.SHORT,
                entry_price=candle.close_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                level=pdl_level
            )

            # Reset retest tracking
            self.retests[symbol]["low"]["confirmed"] = False

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
