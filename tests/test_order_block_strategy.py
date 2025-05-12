"""
Tests for the Order Block strategy.
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from models.candle import Candle
from models.level import Level, LevelType
from strategies.order_block_strategy import OrderBlockStrategy


class TestOrderBlockStrategy(unittest.TestCase):
    """Test cases for the Order Block strategy."""

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
            "ob": {
                "enabled": True,
                "lookback_period": 20,
                "significant_move_threshold": 0.005,
                "retest_threshold": 0.0002,
                "confirmation_candles": 1,
                "manual_input": True
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
        self.strategy = OrderBlockStrategy(
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

    def test_identify_order_blocks(self):
        """Test identifying order blocks."""
        # Create candles with a bullish order block pattern
        candles = []

        # Create a series of candles
        for i in range(20):
            if i == 5:
                # Down candle (potential bullish order block)
                candle = Candle(
                    symbol="SPY",
                    timestamp=datetime(2023, 1, 1, 9, 30) + timedelta(minutes=i),
                    open_price=100.5,
                    high_price=100.8,
                    low_price=99.5,
                    close_price=99.8,
                    volume=1000.0,
                    timeframe=1,
                    is_complete=True
                )
            elif i > 5 and i < 8:
                # Strong up move after the down candle
                candle = Candle(
                    symbol="SPY",
                    timestamp=datetime(2023, 1, 1, 9, 30) + timedelta(minutes=i),
                    open_price=99.8 + (i - 5) * 0.5,
                    high_price=100.0 + (i - 5) * 0.5,
                    low_price=99.7 + (i - 5) * 0.5,
                    close_price=100.0 + (i - 5) * 0.5,
                    volume=1000.0,
                    timeframe=1,
                    is_complete=True
                )
            else:
                # Normal candles
                candle = Candle(
                    symbol="SPY",
                    timestamp=datetime(2023, 1, 1, 9, 30) + timedelta(minutes=i),
                    open_price=100.0,
                    high_price=100.5,
                    low_price=99.5,
                    close_price=100.2,
                    volume=1000.0,
                    timeframe=1,
                    is_complete=True
                )

            candles.append(candle)

        # Mock data_feed.get_candles to return our test candles
        self.data_feed.get_candles.return_value = candles

        # Call the method
        self.strategy.identify_order_blocks("SPY")

        # Check if order blocks were added
        self.strategy.add_level.assert_called()

        # Check if at least one order block was identified
        self.assertGreater(len(self.strategy.order_blocks["SPY"]), 0)

        # Check if the identified order block is a bullish order block
        ob = self.strategy.order_blocks["SPY"][0]
        self.assertEqual(ob.level_type, LevelType.BULLISH_ORDER_BLOCK)

    def test_add_manual_order_block(self):
        """Test adding a manual order block."""
        # Call the method
        level = self.strategy.add_manual_order_block(
            symbol="SPY",
            price=100.0,
            zone_high=100.5,
            zone_low=99.5,
            direction="bullish"
        )

        # Check if the level was created correctly
        self.assertIsNotNone(level)
        self.assertEqual(level.symbol, "SPY")
        self.assertEqual(level.price, 100.0)
        self.assertEqual(level.level_type, LevelType.BULLISH_ORDER_BLOCK)
        self.assertEqual(level.zone_high, 100.5)
        self.assertEqual(level.zone_low, 99.5)

        # Check if the level was added
        self.strategy.add_level.assert_called_once()

        # Check if the level was added to order blocks
        self.assertIn(level, self.strategy.order_blocks["SPY"])

        # Check if retest tracking was initialized
        self.assertIn(level.price, self.strategy.retests["SPY"])

    def test_check_for_retests(self):
        """Test checking for retests."""
        # Create a bullish order block
        ob = Level(
            symbol="SPY",
            price=100.0,
            level_type=LevelType.BULLISH_ORDER_BLOCK,
            timestamp=datetime(2023, 1, 1, 9, 30),
            description="Bullish Order Block",
            zone_high=100.5,
            zone_low=99.5,
            is_active=True
        )

        # Add the order block
        self.strategy.order_blocks["SPY"] = [ob]

        # Initialize retest tracking
        self.strategy.retests["SPY"] = {
            ob.price: {
                "in_progress": False,
                "confirmed": False,
                "candles": []
            }
        }

        # Create a retest candle
        retest_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 10, 0),
            open_price=100.2,
            high_price=100.3,
            low_price=99.8,
            close_price=100.1,
            volume=1000.0,
            timeframe=1,
            is_complete=True
        )

        # Check for retests
        self.strategy._check_for_retests("SPY", retest_candle)

        # Check if retest was detected
        self.assertTrue(self.strategy.retests["SPY"][ob.price]["in_progress"])
        self.assertEqual(len(self.strategy.retests["SPY"][ob.price]["candles"]), 1)

        # Create a confirmation candle
        confirmation_candle = Candle(
            symbol="SPY",
            timestamp=datetime(2023, 1, 1, 10, 1),
            open_price=100.1,
            high_price=101.0,
            low_price=100.0,
            close_price=100.8,
            volume=1000.0,
            timeframe=1,
            is_complete=True
        )

        # Check for retests again
        self.strategy._check_for_retests("SPY", confirmation_candle)

        # Check if retest was confirmed
        self.assertTrue(self.strategy.retests["SPY"][ob.price]["confirmed"])


if __name__ == "__main__":
    unittest.main()
