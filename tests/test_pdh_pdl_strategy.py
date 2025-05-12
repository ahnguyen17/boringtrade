"""
Tests for the Previous Day High/Low strategy.
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from models.candle import Candle
from models.level import Level, LevelType
from strategies.pdh_pdl_strategy import PDHPDLStrategy


class TestPDHPDLStrategy(unittest.TestCase):
    """Test cases for the PDH/PDL strategy."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects
        self.data_feed = MagicMock()
        self.broker = MagicMock()
        self.risk_manager = MagicMock()
        self.notifier = MagicMock()

        # Create configuration
        self.config = {
            "assets": ["SPY"],
            "execution_timeframe": 1,
            "htf_timeframe": 60,
            "htf_filter": {
                "enabled": False,
                "ma_type": "EMA",
                "ma_period": 200
            },
            "trading_hours": {
                "start": "09:30",
                "end": "16:00",
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            },
            "pdh_pdl": {
                "enabled": True,
                "breakout_threshold": 0.0001,
                "retest_threshold": 0.0002,
                "confirmation_candles": 1
            },
            "stop_loss": {
                "type": "level",
                "buffer": 0.001
            },
            "take_profit": {
                "type": "risk_reward",
                "risk_reward_ratio": 2.0
            },
            "position_size": 1
        }

        # Create strategy
        self.strategy = PDHPDLStrategy(
            data_feed=self.data_feed,
            broker=self.broker,
            risk_manager=self.risk_manager,
            notifier=self.notifier,
            config=self.config
        )

        # Set up is_trading_allowed to always return True for testing
        self.strategy.is_trading_allowed = MagicMock(return_value=True)

        # Mock the add_level method
        self.strategy.add_level = MagicMock()

    def test_identify_previous_day_levels(self):
        """Test identifying previous day high and low."""
        # Create previous day candle
        prev_day_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open_price=100.0,
            high_price=101.0,
            low_price=99.0,
            close_price=100.5,
            volume=1000.0,
            timeframe=60,
            is_complete=True
        )

        # Create current day candle
        current_day_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 2, 9, 30),
            open_price=100.5,
            high_price=102.0,
            low_price=100.0,
            close_price=101.5,
            volume=1000.0,
            timeframe=60,
            is_complete=True
        )

        # Mock data_feed.get_candles to return our test candles
        self.data_feed.get_candles.return_value = [prev_day_candle, current_day_candle]

        # Call the method
        self.strategy._identify_previous_day_levels("SPY")

        # Check if levels were added
        self.strategy.add_level.assert_called()
        self.assertEqual(self.strategy.add_level.call_count, 2)

        # Check if previous day levels were identified
        self.assertTrue(self.strategy.previous_day_levels["SPY"]["identified"])

        # Check high level
        high_level = self.strategy.previous_day_levels["SPY"]["high_level"]
        self.assertEqual(high_level.symbol, "SPY")
        self.assertEqual(high_level.price, 101.0)
        self.assertEqual(high_level.level_type, LevelType.PREVIOUS_DAY_HIGH)

        # Check low level
        low_level = self.strategy.previous_day_levels["SPY"]["low_level"]
        self.assertEqual(low_level.symbol, "SPY")
        self.assertEqual(low_level.price, 99.0)
        self.assertEqual(low_level.level_type, LevelType.PREVIOUS_DAY_LOW)

    def test_check_for_breakouts(self):
        """Test checking for breakouts."""
        # Create previous day levels
        pdh_level = Level(
            symbol="SPY",
            price=101.0,
            level_type=LevelType.PREVIOUS_DAY_HIGH,
            timestamp=datetime(2023, 1, 1, 9, 30),
            description="Previous Day High (2023-01-01)"
        )

        pdl_level = Level(
            symbol="SPY",
            price=99.0,
            level_type=LevelType.PREVIOUS_DAY_LOW,
            timestamp=datetime(2023, 1, 1, 9, 30),
            description="Previous Day Low (2023-01-01)"
        )

        # Set up previous day levels
        self.strategy.previous_day_levels["SPY"] = {
            "identified": True,
            "high_level": pdh_level,
            "low_level": pdl_level,
            "date": datetime(2023, 1, 2).date()
        }

        # Create breakout candle (above high)
        breakout_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 2, 9, 35),
            open_price=100.5,
            high_price=102.0,
            low_price=100.0,
            close_price=101.5,
            volume=1000.0,
            timeframe=1,
            is_complete=True
        )

        # Check for breakouts
        self.strategy._check_for_breakouts("SPY", breakout_candle)

        # Check if high breakout was detected
        self.assertTrue(self.strategy.breakouts["SPY"]["high"])
        self.assertEqual(self.strategy.breakouts["SPY"]["high_candle"], breakout_candle)

        # Check if low breakout was not detected
        self.assertFalse(self.strategy.breakouts["SPY"]["low"])

    def test_check_for_retests(self):
        """Test checking for retests."""
        # Create previous day levels
        pdh_level = Level(
            symbol="SPY",
            price=101.0,
            level_type=LevelType.PREVIOUS_DAY_HIGH,
            timestamp=datetime(2023, 1, 1, 9, 30),
            description="Previous Day High (2023-01-01)"
        )

        # Set up previous day levels
        self.strategy.previous_day_levels["SPY"] = {
            "identified": True,
            "high_level": pdh_level,
            "low_level": None,
            "date": datetime(2023, 1, 2).date()
        }

        # Set up breakout
        self.strategy.breakouts["SPY"]["high"] = True

        # Create retest candle
        retest_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 2, 9, 36),
            open_price=101.5,
            high_price=101.5,
            low_price=101.0,
            close_price=101.2,
            volume=1000.0,
            timeframe=1,
            is_complete=True
        )

        # Check for retests
        self.strategy._check_for_retests("SPY", retest_candle)

        # Check if retest was detected
        self.assertTrue(self.strategy.retests["SPY"]["high"]["in_progress"])
        self.assertEqual(len(self.strategy.retests["SPY"]["high"]["candles"]), 1)

        # Create confirmation candle
        confirmation_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 2, 9, 37),
            open_price=101.2,
            high_price=101.8,
            low_price=101.1,
            close_price=101.7,
            volume=1000.0,
            timeframe=1,
            is_complete=True
        )

        # Check for retests again
        self.strategy._check_for_retests("SPY", confirmation_candle)

        # Check if retest was confirmed
        self.assertTrue(self.strategy.retests["SPY"]["high"]["confirmed"])


if __name__ == "__main__":
    unittest.main()
