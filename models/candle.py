"""
Candle data model for the BoringTrade trading bot.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any


class Candle:
    """
    Represents a price candle (OHLCV) for a specific asset and timeframe.
    """
    
    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
        timeframe: int,  # in minutes
        is_complete: bool = False
    ):
        """
        Initialize a new candle.
        
        Args:
            symbol: The asset symbol (e.g., "SPY")
            timestamp: The candle's timestamp (start time)
            open_price: The opening price
            high_price: The highest price
            low_price: The lowest price
            close_price: The closing price
            volume: The trading volume
            timeframe: The candle's timeframe in minutes
            is_complete: Whether the candle is complete
        """
        self.symbol = symbol
        self.timestamp = timestamp
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.timeframe = timeframe
        self.is_complete = is_complete
    
    @property
    def is_bullish(self) -> bool:
        """Check if the candle is bullish (close > open)."""
        return self.close_price > self.open_price
    
    @property
    def is_bearish(self) -> bool:
        """Check if the candle is bearish (close < open)."""
        return self.close_price < self.open_price
    
    @property
    def is_doji(self) -> bool:
        """Check if the candle is a doji (open ≈ close)."""
        return abs(self.close_price - self.open_price) < 0.0001 * self.open_price
    
    @property
    def body_size(self) -> float:
        """Get the size of the candle body."""
        return abs(self.close_price - self.open_price)
    
    @property
    def upper_wick(self) -> float:
        """Get the size of the upper wick."""
        return self.high_price - max(self.open_price, self.close_price)
    
    @property
    def lower_wick(self) -> float:
        """Get the size of the lower wick."""
        return min(self.open_price, self.close_price) - self.low_price
    
    @property
    def range(self) -> float:
        """Get the total range of the candle."""
        return self.high_price - self.low_price
    
    def is_engulfing(self, previous_candle: 'Candle') -> bool:
        """
        Check if this candle engulfs the previous candle.
        
        Args:
            previous_candle: The previous candle to compare with
            
        Returns:
            bool: True if this candle engulfs the previous candle
        """
        if self.is_bullish and previous_candle.is_bearish:
            # Bullish engulfing
            return (
                self.open_price <= previous_candle.close_price and
                self.close_price >= previous_candle.open_price
            )
        elif self.is_bearish and previous_candle.is_bullish:
            # Bearish engulfing
            return (
                self.open_price >= previous_candle.close_price and
                self.close_price <= previous_candle.open_price
            )
        return False
    
    def is_hammer(self) -> bool:
        """
        Check if this candle is a hammer.
        
        Returns:
            bool: True if this candle is a hammer
        """
        if self.range == 0:
            return False
        
        body_ratio = self.body_size / self.range
        lower_wick_ratio = self.lower_wick / self.range
        
        return (
            body_ratio < 0.3 and
            lower_wick_ratio > 0.6 and
            self.upper_wick / self.range < 0.1
        )
    
    def is_shooting_star(self) -> bool:
        """
        Check if this candle is a shooting star.
        
        Returns:
            bool: True if this candle is a shooting star
        """
        if self.range == 0:
            return False
        
        body_ratio = self.body_size / self.range
        upper_wick_ratio = self.upper_wick / self.range
        
        return (
            body_ratio < 0.3 and
            upper_wick_ratio > 0.6 and
            self.lower_wick / self.range < 0.1
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the candle to a dictionary.
        
        Returns:
            Dict[str, Any]: The candle as a dictionary
        """
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "close": self.close_price,
            "volume": self.volume,
            "timeframe": self.timeframe,
            "is_complete": self.is_complete
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Candle':
        """
        Create a candle from a dictionary.
        
        Args:
            data: The dictionary containing candle data
            
        Returns:
            Candle: A new candle instance
        """
        return cls(
            symbol=data["symbol"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            open_price=data["open"],
            high_price=data["high"],
            low_price=data["low"],
            close_price=data["close"],
            volume=data["volume"],
            timeframe=data["timeframe"],
            is_complete=data.get("is_complete", True)
        )
    
    def __str__(self) -> str:
        """String representation of the candle."""
        return (
            f"{self.symbol} {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} "
            f"({self.timeframe}m): O={self.open_price:.2f}, H={self.high_price:.2f}, "
            f"L={self.low_price:.2f}, C={self.close_price:.2f}, V={self.volume:.2f}"
        )
    
    def __repr__(self) -> str:
        """Representation of the candle."""
        return self.__str__()
