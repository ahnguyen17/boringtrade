"""
Candle builder for the BoringTrade trading bot.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from models.candle import Candle


class CandleBuilder:
    """
    Builds candles from tick data or smaller timeframe candles.
    """
    
    def __init__(self, symbol: str, timeframe: int):
        """
        Initialize the candle builder.
        
        Args:
            symbol: The asset symbol
            timeframe: The candle timeframe in minutes
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.logger = logging.getLogger(f"CandleBuilder.{symbol}.{timeframe}m")
        self.current_candle: Optional[Candle] = None
        self.last_update: Optional[datetime] = None
    
    def update(self, candle: Candle) -> Optional[Candle]:
        """
        Update the current candle with new data.
        
        Args:
            candle: The new candle data
            
        Returns:
            Optional[Candle]: A complete candle if one was finished
        """
        # Check if the candle is for the correct symbol and timeframe
        if candle.symbol != self.symbol:
            self.logger.warning(
                f"Received candle for wrong symbol: {candle.symbol} (expected {self.symbol})"
            )
            return None
        
        # If the candle is already complete, just return it
        if candle.is_complete and candle.timeframe == self.timeframe:
            self.current_candle = None
            return candle
        
        # If the candle is for a smaller timeframe, use it to update the current candle
        if candle.timeframe < self.timeframe:
            return self._update_from_smaller_timeframe(candle)
        
        # If the candle is for a larger timeframe, ignore it
        if candle.timeframe > self.timeframe:
            self.logger.warning(
                f"Received candle for larger timeframe: {candle.timeframe}m (expected {self.timeframe}m)"
            )
            return None
        
        # If we get here, the candle is for the correct timeframe but is not complete
        self.current_candle = candle
        self.last_update = datetime.now()
        return None
    
    def _update_from_smaller_timeframe(self, candle: Candle) -> Optional[Candle]:
        """
        Update the current candle from a smaller timeframe candle.
        
        Args:
            candle: The smaller timeframe candle
            
        Returns:
            Optional[Candle]: A complete candle if one was finished
        """
        # Calculate the start time of the current timeframe candle
        candle_time = candle.timestamp
        minutes = candle_time.minute
        current_timeframe_start = candle_time.replace(
            minute=(minutes // self.timeframe) * self.timeframe,
            second=0,
            microsecond=0
        )
        
        # Check if we need to create a new candle
        if self.current_candle is None:
            self.current_candle = Candle(
                symbol=self.symbol,
                timestamp=current_timeframe_start,
                open_price=candle.open_price,
                high_price=candle.high_price,
                low_price=candle.low_price,
                close_price=candle.close_price,
                volume=candle.volume,
                timeframe=self.timeframe,
                is_complete=False
            )
            self.last_update = datetime.now()
            return None
        
        # Check if the candle belongs to the current timeframe
        if self.current_candle.timestamp == current_timeframe_start:
            # Update the current candle
            self.current_candle.high_price = max(
                self.current_candle.high_price,
                candle.high_price
            )
            self.current_candle.low_price = min(
                self.current_candle.low_price,
                candle.low_price
            )
            self.current_candle.close_price = candle.close_price
            self.current_candle.volume += candle.volume
            self.last_update = datetime.now()
            
            # Check if the current candle is complete
            next_timeframe_start = current_timeframe_start + timedelta(minutes=self.timeframe)
            if candle.timestamp >= next_timeframe_start:
                complete_candle = self.current_candle
                complete_candle.is_complete = True
                self.current_candle = None
                return complete_candle
            
            return None
        
        # If we get here, the candle belongs to a new timeframe
        complete_candle = self.current_candle
        complete_candle.is_complete = True
        
        # Create a new candle for the current timeframe
        self.current_candle = Candle(
            symbol=self.symbol,
            timestamp=current_timeframe_start,
            open_price=candle.open_price,
            high_price=candle.high_price,
            low_price=candle.low_price,
            close_price=candle.close_price,
            volume=candle.volume,
            timeframe=self.timeframe,
            is_complete=False
        )
        self.last_update = datetime.now()
        
        return complete_candle
