"""
Asset data model for the BoringTrade trading bot.
"""
from enum import Enum
from typing import Optional, Dict, Any, List


class AssetType(Enum):
    """Types of tradable assets."""
    STOCK = "STOCK"
    FUTURES = "FUTURES"
    OPTION = "OPTION"
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"


class Asset:
    """
    Represents a tradable asset with its properties.
    """
    
    def __init__(
        self,
        symbol: str,
        asset_type: AssetType,
        description: Optional[str] = None,
        exchange: Optional[str] = None,
        tick_size: float = 0.01,
        contract_size: float = 1.0,
        margin_requirement: Optional[float] = None,
        trading_hours: Optional[Dict[str, Any]] = None,
        expiration_date: Optional[str] = None,
        underlying: Optional[str] = None,
        multiplier: float = 1.0,
        additional_properties: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new asset.
        
        Args:
            symbol: The asset symbol (e.g., "SPY", "ES", "MES")
            asset_type: The type of asset
            description: Optional description of the asset
            exchange: The exchange where the asset is traded
            tick_size: The minimum price movement
            contract_size: The size of one contract
            margin_requirement: The margin requirement for trading this asset
            trading_hours: The trading hours for this asset
            expiration_date: The expiration date for futures and options
            underlying: The underlying asset for derivatives
            multiplier: The price multiplier (e.g., for futures)
            additional_properties: Additional asset-specific properties
        """
        self.symbol = symbol
        self.asset_type = asset_type
        self.description = description
        self.exchange = exchange
        self.tick_size = tick_size
        self.contract_size = contract_size
        self.margin_requirement = margin_requirement
        self.trading_hours = trading_hours or {}
        self.expiration_date = expiration_date
        self.underlying = underlying
        self.multiplier = multiplier
        self.additional_properties = additional_properties or {}
    
    @property
    def is_futures(self) -> bool:
        """Check if the asset is a futures contract."""
        return self.asset_type == AssetType.FUTURES
    
    @property
    def is_stock(self) -> bool:
        """Check if the asset is a stock."""
        return self.asset_type == AssetType.STOCK
    
    @property
    def is_option(self) -> bool:
        """Check if the asset is an option."""
        return self.asset_type == AssetType.OPTION
    
    @property
    def is_forex(self) -> bool:
        """Check if the asset is a forex pair."""
        return self.asset_type == AssetType.FOREX
    
    @property
    def is_crypto(self) -> bool:
        """Check if the asset is a cryptocurrency."""
        return self.asset_type == AssetType.CRYPTO
    
    @property
    def display_name(self) -> str:
        """Get a human-readable name for the asset."""
        if self.description:
            return f"{self.symbol} ({self.description})"
        return self.symbol
    
    @property
    def value_per_point(self) -> float:
        """Get the dollar value per point movement."""
        return self.contract_size * self.multiplier
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the asset to a dictionary.
        
        Returns:
            Dict[str, Any]: The asset as a dictionary
        """
        return {
            "symbol": self.symbol,
            "asset_type": self.asset_type.value,
            "description": self.description,
            "exchange": self.exchange,
            "tick_size": self.tick_size,
            "contract_size": self.contract_size,
            "margin_requirement": self.margin_requirement,
            "trading_hours": self.trading_hours,
            "expiration_date": self.expiration_date,
            "underlying": self.underlying,
            "multiplier": self.multiplier,
            "additional_properties": self.additional_properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Asset':
        """
        Create an asset from a dictionary.
        
        Args:
            data: The dictionary containing asset data
            
        Returns:
            Asset: A new asset instance
        """
        return cls(
            symbol=data["symbol"],
            asset_type=AssetType(data["asset_type"]),
            description=data.get("description"),
            exchange=data.get("exchange"),
            tick_size=data.get("tick_size", 0.01),
            contract_size=data.get("contract_size", 1.0),
            margin_requirement=data.get("margin_requirement"),
            trading_hours=data.get("trading_hours"),
            expiration_date=data.get("expiration_date"),
            underlying=data.get("underlying"),
            multiplier=data.get("multiplier", 1.0),
            additional_properties=data.get("additional_properties")
        )


# Common futures contracts
ES_FUTURES = Asset(
    symbol="ES",
    asset_type=AssetType.FUTURES,
    description="E-mini S&P 500 Futures",
    exchange="CME",
    tick_size=0.25,
    contract_size=1,
    multiplier=50.0,  # $50 per point
    trading_hours={
        "regular": {
            "start": "09:30",
            "end": "16:15",
        },
        "extended": {
            "start": "18:00",
            "end": "17:00",  # Next day
        }
    }
)

MES_FUTURES = Asset(
    symbol="MES",
    asset_type=AssetType.FUTURES,
    description="Micro E-mini S&P 500 Futures",
    exchange="CME",
    tick_size=0.25,
    contract_size=1,
    multiplier=5.0,  # $5 per point
    trading_hours={
        "regular": {
            "start": "09:30",
            "end": "16:15",
        },
        "extended": {
            "start": "18:00",
            "end": "17:00",  # Next day
        }
    }
)

# Dictionary of common assets
COMMON_ASSETS = {
    "ES": ES_FUTURES,
    "MES": MES_FUTURES,
}
