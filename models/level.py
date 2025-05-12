"""
Price level data model for the BoringTrade trading bot.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple


class LevelType(Enum):
    """Types of price levels."""
    OPENING_RANGE_HIGH = "ORH"
    OPENING_RANGE_LOW = "ORL"
    PREVIOUS_DAY_HIGH = "PDH"
    PREVIOUS_DAY_LOW = "PDL"
    BULLISH_ORDER_BLOCK = "BOB"
    BEARISH_ORDER_BLOCK = "BRB"
    SESSION_HIGH = "SH"
    SESSION_LOW = "SL"
    CUSTOM = "CUSTOM"


class Level:
    """
    Represents a key price level for trading decisions.
    """
    
    def __init__(
        self,
        symbol: str,
        price: float,
        level_type: LevelType,
        timestamp: datetime,
        description: Optional[str] = None,
        zone_high: Optional[float] = None,
        zone_low: Optional[float] = None,
        is_active: bool = True
    ):
        """
        Initialize a new price level.
        
        Args:
            symbol: The asset symbol (e.g., "SPY")
            price: The price level
            level_type: The type of level
            timestamp: When the level was created
            description: Optional description of the level
            zone_high: Optional upper bound for zone-based levels (e.g., order blocks)
            zone_low: Optional lower bound for zone-based levels
            is_active: Whether the level is currently active
        """
        self.symbol = symbol
        self.price = price
        self.level_type = level_type
        self.timestamp = timestamp
        self.description = description
        self.zone_high = zone_high if zone_high is not None else price
        self.zone_low = zone_low if zone_low is not None else price
        self.is_active = is_active
        self.breaks: List[Dict[str, Any]] = []
        self.retests: List[Dict[str, Any]] = []
    
    @property
    def is_zone(self) -> bool:
        """Check if this level is a zone (has width)."""
        return self.zone_high != self.zone_low
    
    @property
    def zone_width(self) -> float:
        """Get the width of the zone."""
        return self.zone_high - self.zone_low
    
    @property
    def has_been_broken(self) -> bool:
        """Check if this level has been broken."""
        return len(self.breaks) > 0
    
    @property
    def has_been_retested(self) -> bool:
        """Check if this level has been retested."""
        return len(self.retests) > 0
    
    @property
    def last_break(self) -> Optional[Dict[str, Any]]:
        """Get the most recent break of this level."""
        if not self.breaks:
            return None
        return self.breaks[-1]
    
    @property
    def last_retest(self) -> Optional[Dict[str, Any]]:
        """Get the most recent retest of this level."""
        if not self.retests:
            return None
        return self.retests[-1]
    
    def is_broken_above(self, price: float, threshold: float = 0.0) -> bool:
        """
        Check if the given price breaks this level from below.
        
        Args:
            price: The price to check
            threshold: The minimum distance required to consider it a break
            
        Returns:
            bool: True if the price breaks the level from below
        """
        if self.is_zone:
            return price > self.zone_high + threshold
        return price > self.price + threshold
    
    def is_broken_below(self, price: float, threshold: float = 0.0) -> bool:
        """
        Check if the given price breaks this level from above.
        
        Args:
            price: The price to check
            threshold: The minimum distance required to consider it a break
            
        Returns:
            bool: True if the price breaks the level from above
        """
        if self.is_zone:
            return price < self.zone_low - threshold
        return price < self.price - threshold
    
    def is_retesting_from_above(self, price: float, threshold: float = 0.0) -> bool:
        """
        Check if the given price is retesting this level from above.
        
        Args:
            price: The price to check
            threshold: The maximum distance to consider it a retest
            
        Returns:
            bool: True if the price is retesting the level from above
        """
        if self.is_zone:
            return (
                price >= self.zone_high - threshold and
                price <= self.zone_high + threshold
            )
        return (
            price >= self.price - threshold and
            price <= self.price + threshold
        )
    
    def is_retesting_from_below(self, price: float, threshold: float = 0.0) -> bool:
        """
        Check if the given price is retesting this level from below.
        
        Args:
            price: The price to check
            threshold: The maximum distance to consider it a retest
            
        Returns:
            bool: True if the price is retesting the level from below
        """
        if self.is_zone:
            return (
                price >= self.zone_low - threshold and
                price <= self.zone_low + threshold
            )
        return (
            price >= self.price - threshold and
            price <= self.price + threshold
        )
    
    def add_break(
        self,
        timestamp: datetime,
        price: float,
        direction: str,
        candle_index: Optional[int] = None
    ) -> None:
        """
        Record a break of this level.
        
        Args:
            timestamp: When the break occurred
            price: The price at which the break occurred
            direction: The direction of the break ("above" or "below")
            candle_index: Optional index of the candle that caused the break
        """
        self.breaks.append({
            "timestamp": timestamp,
            "price": price,
            "direction": direction,
            "candle_index": candle_index
        })
    
    def add_retest(
        self,
        timestamp: datetime,
        price: float,
        direction: str,
        candle_index: Optional[int] = None
    ) -> None:
        """
        Record a retest of this level.
        
        Args:
            timestamp: When the retest occurred
            price: The price at which the retest occurred
            direction: The direction of the retest ("above" or "below")
            candle_index: Optional index of the candle that caused the retest
        """
        self.retests.append({
            "timestamp": timestamp,
            "price": price,
            "direction": direction,
            "candle_index": candle_index
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the level to a dictionary.
        
        Returns:
            Dict[str, Any]: The level as a dictionary
        """
        return {
            "symbol": self.symbol,
            "price": self.price,
            "level_type": self.level_type.value,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "zone_high": self.zone_high,
            "zone_low": self.zone_low,
            "is_active": self.is_active,
            "breaks": self.breaks,
            "retests": self.retests
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Level':
        """
        Create a level from a dictionary.
        
        Args:
            data: The dictionary containing level data
            
        Returns:
            Level: A new level instance
        """
        level = cls(
            symbol=data["symbol"],
            price=data["price"],
            level_type=LevelType(data["level_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            description=data.get("description"),
            zone_high=data.get("zone_high"),
            zone_low=data.get("zone_low"),
            is_active=data.get("is_active", True)
        )
        
        # Add breaks and retests
        for break_data in data.get("breaks", []):
            level.breaks.append(break_data)
        
        for retest_data in data.get("retests", []):
            level.retests.append(retest_data)
        
        return level
    
    def __str__(self) -> str:
        """String representation of the level."""
        if self.is_zone:
            return (
                f"{self.symbol} {self.level_type.value} Zone: "
                f"{self.zone_low:.2f}-{self.zone_high:.2f} "
                f"({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
            )
        return (
            f"{self.symbol} {self.level_type.value}: {self.price:.2f} "
            f"({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
        )
    
    def __repr__(self) -> str:
        """Representation of the level."""
        return self.__str__()
