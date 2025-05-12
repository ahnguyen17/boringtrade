"""
Opening Range Breakout strategy for the BoringTrade trading bot.
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


class ORBStrategy(BaseStrategy):
    """
    Opening Range Breakout (ORB) strategy.

    This strategy:
    1. Identifies the opening range (first candle of the session)
    2. Detects breakouts above/below the opening range
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
        Initialize the ORB strategy.

        Args:
            data_feed: The data feed
            broker: The broker interface
            risk_manager: The risk manager
            notifier: The notifier
            config: The configuration
        """
        super().__init__(data_feed, broker, risk_manager, notifier, config)

        # Get ORB-specific configuration
        orb_config = config["orb"]
        self.orb_enabled = orb_config["enabled"]
        self.orb_session_start = self._parse_time(orb_config["session_start_time"])
        self.orb_timeframe = orb_config["timeframe"]
        self.breakout_threshold = orb_config["breakout_threshold"]
        self.retest_threshold = orb_config["retest_threshold"]
        self.confirmation_candles = orb_config["confirmation_candles"]

        # Initialize ORB tracking
        self.opening_ranges: Dict[str, Dict[str, Any]] = {}
        self.breakouts: Dict[str, Dict[str, Any]] = {}
        self.retests: Dict[str, Dict[str, Any]] = {}

        # Initialize data structures for each asset
        for symbol in self.assets:
            self.opening_ranges[symbol] = {
                "identified": False,
                "high_level": None,
                "low_level": None,
                "candle": None
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
        self.logger.info("Initializing ORB strategy...")

        # Initialize opening ranges for each asset
        for symbol in self.assets:
            self.opening_ranges[symbol] = {
                "identified": False,
                "high_level": None,
                "low_level": None,
                "candle": None
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

        # Register for ORB timeframe candles
        for symbol in self.assets:
            self.data_feed.add_candle_callback(
                symbol=symbol,
                timeframe=self.orb_timeframe,
                callback=self.on_orb_candle
            )

    def cleanup(self) -> None:
        """Clean up strategy-specific components."""
        self.logger.info("Cleaning up ORB strategy...")

        # Unregister from ORB timeframe candles
        for symbol in self.assets:
            self.data_feed.remove_candle_callback(
                symbol=symbol,
                timeframe=self.orb_timeframe,
                callback=self.on_orb_candle
            )

    def on_candle(self, candle: Candle) -> None:
        """
        Handle a new candle.

        Args:
            candle: The new candle
        """
        symbol = candle.symbol

        # Check if we have an opening range for this symbol
        if (
            symbol not in self.opening_ranges or
            not self.opening_ranges[symbol]["identified"]
        ):
            return

        # Check if we have a breakout for this symbol
        if (
            symbol not in self.breakouts or
            (not self.breakouts[symbol]["high"] and not self.breakouts[symbol]["low"])
        ):
            return

        # Check for retests
        self._check_for_retests(symbol, candle)

        # Check for trade entries
        self._check_for_entries(symbol, candle)

        # Check for trade exits
        self._check_for_exits(symbol, candle)

    def on_orb_candle(self, candle: Candle) -> None:
        """
        Handle a new ORB timeframe candle.

        Args:
            candle: The new candle
        """
        symbol = candle.symbol

        # Check if this is the opening candle
        candle_time = candle.timestamp.time()
        if candle_time == self.orb_session_start:
            self._identify_opening_range(symbol, candle)

        # Check for breakouts
        self._check_for_breakouts(symbol, candle)

    def on_level_cross(self, level: Level, price: float) -> None:
        """
        Handle a price level crossing.

        Args:
            level: The price level
            price: The current price
        """
        symbol = level.symbol

        # Check if this is an ORB level
        if level.level_type not in [LevelType.OPENING_RANGE_HIGH, LevelType.OPENING_RANGE_LOW]:
            return

        # Check if we have a breakout for this symbol
        if symbol not in self.breakouts:
            return

        # Handle ORH crossing
        if level.level_type == LevelType.OPENING_RANGE_HIGH:
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
                self.logger.info(f"ORH breakout detected for {symbol} at {price}")

        # Handle ORL crossing
        elif level.level_type == LevelType.OPENING_RANGE_LOW:
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
                self.logger.info(f"ORL breakout detected for {symbol} at {price}")

    def _identify_opening_range(self, symbol: str, candle: Candle) -> None:
        """
        Identify the opening range for a symbol.

        Args:
            symbol: The asset symbol
            candle: The opening candle
        """
        # Check if opening range is already identified
        if (
            symbol in self.opening_ranges and
            self.opening_ranges[symbol]["identified"]
        ):
            return

        # Create opening range levels
        orh_level = Level(
            symbol=symbol,
            price=candle.high_price,
            level_type=LevelType.OPENING_RANGE_HIGH,
            timestamp=candle.timestamp,
            description=f"Opening Range High ({self.orb_timeframe}m)"
        )

        orl_level = Level(
            symbol=symbol,
            price=candle.low_price,
            level_type=LevelType.OPENING_RANGE_LOW,
            timestamp=candle.timestamp,
            description=f"Opening Range Low ({self.orb_timeframe}m)"
        )

        # Add levels
        self.add_level(orh_level)
        self.add_level(orl_level)

        # Update opening range tracking
        self.opening_ranges[symbol] = {
            "identified": True,
            "high_level": orh_level,
            "low_level": orl_level,
            "candle": candle
        }

        self.logger.info(
            f"Opening range identified for {symbol}: "
            f"High={orh_level.price:.2f}, Low={orl_level.price:.2f}"
        )

    def _check_for_breakouts(self, symbol: str, candle: Candle) -> None:
        """
        Check for breakouts of the opening range.

        Args:
            symbol: The asset symbol
            candle: The current candle
        """
        # Check if opening range is identified
        if (
            symbol not in self.opening_ranges or
            not self.opening_ranges[symbol]["identified"]
        ):
            return

        # Get opening range levels
        orh_level = self.opening_ranges[symbol]["high_level"]
        orl_level = self.opening_ranges[symbol]["low_level"]

        # Check for high breakout
        if (
            not self.breakouts[symbol]["high"] and
            candle.close_price > orh_level.price + (orh_level.price * self.breakout_threshold)
        ):
            # Record breakout
            self.breakouts[symbol]["high"] = True
            self.breakouts[symbol]["high_candle"] = candle
            orh_level.add_break(
                timestamp=candle.timestamp,
                price=candle.close_price,
                direction="above",
                candle_index=None
            )
            self.logger.info(f"ORH breakout detected for {symbol} at {candle.close_price}")

        # Check for low breakout
        if (
            not self.breakouts[symbol]["low"] and
            candle.close_price < orl_level.price - (orl_level.price * self.breakout_threshold)
        ):
            # Record breakout
            self.breakouts[symbol]["low"] = True
            self.breakouts[symbol]["low_candle"] = candle
            orl_level.add_break(
                timestamp=candle.timestamp,
                price=candle.close_price,
                direction="below",
                candle_index=None
            )
            self.logger.info(f"ORL breakout detected for {symbol} at {candle.close_price}")

    def _check_for_retests(self, symbol: str, candle: Candle) -> None:
        """
        Check for retests of the opening range.

        Args:
            symbol: The asset symbol
            candle: The current candle
        """
        # Check if opening range is identified
        if (
            symbol not in self.opening_ranges or
            not self.opening_ranges[symbol]["identified"]
        ):
            return

        # Get opening range levels
        orh_level = self.opening_ranges[symbol]["high_level"]
        orl_level = self.opening_ranges[symbol]["low_level"]

        # Check for high retest
        if (
            self.breakouts[symbol]["high"] and
            not self.retests[symbol]["high"]["confirmed"]
        ):
            # Check if price is near the high level
            if abs(candle.low_price - orh_level.price) <= (orh_level.price * self.retest_threshold):
                # Start or continue retest
                if not self.retests[symbol]["high"]["in_progress"]:
                    self.retests[symbol]["high"]["in_progress"] = True
                    self.retests[symbol]["high"]["candles"] = [candle]
                    orh_level.add_retest(
                        timestamp=candle.timestamp,
                        price=candle.low_price,
                        direction="above",
                        candle_index=None
                    )
                    self.logger.info(f"ORH retest started for {symbol} at {candle.low_price}")
                else:
                    self.retests[symbol]["high"]["candles"].append(candle)

                # Check for confirmation
                if len(self.retests[symbol]["high"]["candles"]) >= self.confirmation_candles:
                    # Check if the retest is confirmed (price bounced from the level)
                    last_candle = self.retests[symbol]["high"]["candles"][-1]
                    if last_candle.close_price > orh_level.price:
                        self.retests[symbol]["high"]["confirmed"] = True
                        self.logger.info(f"ORH retest confirmed for {symbol}")
            else:
                # Reset retest if price moved away from the level
                if (
                    self.retests[symbol]["high"]["in_progress"] and
                    not self.retests[symbol]["high"]["confirmed"] and
                    candle.low_price < orh_level.price - (orh_level.price * self.retest_threshold * 2)
                ):
                    self.retests[symbol]["high"]["in_progress"] = False
                    self.retests[symbol]["high"]["candles"] = []
                    self.logger.info(f"ORH retest cancelled for {symbol}")

        # Check for low retest
        if (
            self.breakouts[symbol]["low"] and
            not self.retests[symbol]["low"]["confirmed"]
        ):
            # Check if price is near the low level
            if abs(candle.high_price - orl_level.price) <= (orl_level.price * self.retest_threshold):
                # Start or continue retest
                if not self.retests[symbol]["low"]["in_progress"]:
                    self.retests[symbol]["low"]["in_progress"] = True
                    self.retests[symbol]["low"]["candles"] = [candle]
                    orl_level.add_retest(
                        timestamp=candle.timestamp,
                        price=candle.high_price,
                        direction="below",
                        candle_index=None
                    )
                    self.logger.info(f"ORL retest started for {symbol} at {candle.high_price}")
                else:
                    self.retests[symbol]["low"]["candles"].append(candle)

                # Check for confirmation
                if len(self.retests[symbol]["low"]["candles"]) >= self.confirmation_candles:
                    # Check if the retest is confirmed (price bounced from the level)
                    last_candle = self.retests[symbol]["low"]["candles"][-1]
                    if last_candle.close_price < orl_level.price:
                        self.retests[symbol]["low"]["confirmed"] = True
                        self.logger.info(f"ORL retest confirmed for {symbol}")
            else:
                # Reset retest if price moved away from the level
                if (
                    self.retests[symbol]["low"]["in_progress"] and
                    not self.retests[symbol]["low"]["confirmed"] and
                    candle.high_price > orl_level.price + (orl_level.price * self.retest_threshold * 2)
                ):
                    self.retests[symbol]["low"]["in_progress"] = False
                    self.retests[symbol]["low"]["candles"] = []
                    self.logger.info(f"ORL retest cancelled for {symbol}")

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

        # Check if opening range is identified
        if (
            symbol not in self.opening_ranges or
            not self.opening_ranges[symbol]["identified"]
        ):
            return

        # Get opening range levels
        orh_level = self.opening_ranges[symbol]["high_level"]
        orl_level = self.opening_ranges[symbol]["low_level"]

        # Check for long entry (ORH breakout and retest)
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
                stop_loss = orh_level.price - (orh_level.price * self.stop_loss_buffer)
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
                range_size = orh_level.price - orl_level.price
                take_profit = orh_level.price + range_size

            # Create trade
            self.create_trade(
                symbol=symbol,
                direction=TradeDirection.LONG,
                entry_price=candle.close_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                level=orh_level
            )

            # Reset retest tracking
            self.retests[symbol]["high"]["confirmed"] = False

        # Check for short entry (ORL breakout and retest)
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
                stop_loss = orl_level.price + (orl_level.price * self.stop_loss_buffer)
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
                range_size = orh_level.price - orl_level.price
                take_profit = orl_level.price - range_size

            # Create trade
            self.create_trade(
                symbol=symbol,
                direction=TradeDirection.SHORT,
                entry_price=candle.close_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                level=orl_level
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
