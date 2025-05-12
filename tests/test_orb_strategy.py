"""
Tests for the Opening Range Breakout strategy.
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from models.candle import Candle
from models.level import Level, LevelType
from strategies.orb_strategy import ORBStrategy


class TestORBStrategy(unittest.TestCase):
    """Test cases for the ORB strategy."""
    
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
            "orb": {
                "enabled": True,
                "session_start_time": "09:30",
                "timeframe": 5,
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
        self.strategy = ORBStrategy(
            data_feed=self.data_feed,
            broker=self.broker,
            risk_manager=self.risk_manager,
            notifier=self.notifier,
            config=self.config
        )
        
        # Set up is_trading_allowed to always return True for testing
        self.strategy.is_trading_allowed = MagicMock(return_value=True)
    
    def test_identify_opening_range(self):
        """Test identifying the opening range."""
        # Create opening candle
        opening_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open_price=100.0,
            high_price=101.0,
            low_price=99.0,
            close_price=100.5,
            volume=1000.0,
            timeframe=5,
            is_complete=True
        )
        
        # Call the method
        self.strategy._identify_opening_range("SPY", opening_candle)
        
        # Check if levels were added
        self.assertEqual(len(self.strategy.levels["SPY"]), 2)
        
        # Check if opening range was identified
        self.assertTrue(self.strategy.opening_ranges["SPY"]["identified"])
        
        # Check high level
        high_level = self.strategy.opening_ranges["SPY"]["high_level"]
        self.assertEqual(high_level.symbol, "SPY")
        self.assertEqual(high_level.price, 101.0)
        self.assertEqual(high_level.level_type, LevelType.OPENING_RANGE_HIGH)
        
        # Check low level
        low_level = self.strategy.opening_ranges["SPY"]["low_level"]
        self.assertEqual(low_level.symbol, "SPY")
        self.assertEqual(low_level.price, 99.0)
        self.assertEqual(low_level.level_type, LevelType.OPENING_RANGE_LOW)
    
    def test_check_for_breakouts(self):
        """Test checking for breakouts."""
        # Create opening candle
        opening_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open_price=100.0,
            high_price=101.0,
            low_price=99.0,
            close_price=100.5,
            volume=1000.0,
            timeframe=5,
            is_complete=True
        )
        
        # Identify opening range
        self.strategy._identify_opening_range("SPY", opening_candle)
        
        # Create breakout candle (above high)
        breakout_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 9, 35),
            open_price=100.5,
            high_price=102.0,
            low_price=100.0,
            close_price=101.5,
            volume=1000.0,
            timeframe=5,
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
        # Create opening candle
        opening_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open_price=100.0,
            high_price=101.0,
            low_price=99.0,
            close_price=100.5,
            volume=1000.0,
            timeframe=5,
            is_complete=True
        )
        
        # Identify opening range
        self.strategy._identify_opening_range("SPY", opening_candle)
        
        # Create breakout candle (above high)
        breakout_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 9, 35),
            open_price=100.5,
            high_price=102.0,
            low_price=100.0,
            close_price=101.5,
            volume=1000.0,
            timeframe=5,
            is_complete=True
        )
        
        # Check for breakouts
        self.strategy._check_for_breakouts("SPY", breakout_candle)
        
        # Create retest candle
        retest_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 9, 36),
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
            timestamp=datetime(2023, 1, 1, 9, 37),
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
    
    def test_check_for_entries(self):
        """Test checking for entries."""
        # Create opening candle
        opening_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open_price=100.0,
            high_price=101.0,
            low_price=99.0,
            close_price=100.5,
            volume=1000.0,
            timeframe=5,
            is_complete=True
        )
        
        # Identify opening range
        self.strategy._identify_opening_range("SPY", opening_candle)
        
        # Create breakout candle (above high)
        breakout_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 9, 35),
            open_price=100.5,
            high_price=102.0,
            low_price=100.0,
            close_price=101.5,
            volume=1000.0,
            timeframe=5,
            is_complete=True
        )
        
        # Check for breakouts
        self.strategy._check_for_breakouts("SPY", breakout_candle)
        
        # Create retest candle
        retest_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 9, 36),
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
        
        # Create confirmation candle
        confirmation_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 9, 37),
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
        
        # Mock create_trade method
        self.strategy.create_trade = MagicMock(return_value=None)
        
        # Check for entries
        self.strategy._check_for_entries("SPY", confirmation_candle)
        
        # Check if create_trade was called
        self.strategy.create_trade.assert_called_once()
        
        # Check call arguments
        args, kwargs = self.strategy.create_trade.call_args
        self.assertEqual(kwargs["symbol"], "SPY")
        self.assertEqual(kwargs["entry_price"], 101.7)
        self.assertLess(kwargs["stop_loss"], 101.0)
        self.assertGreater(kwargs["take_profit"], 101.7)


if __name__ == "__main__":
    unittest.main()
