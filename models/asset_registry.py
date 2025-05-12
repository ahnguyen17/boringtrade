"""
Asset registry for the BoringTrade trading bot.
"""
import logging
from typing import Dict, List, Optional, Any

from models.asset import Asset, AssetType, COMMON_ASSETS


class AssetRegistry:
    """
    Registry for managing tradable assets.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the asset registry.
        
        Args:
            config: The configuration dictionary
        """
        self.logger = logging.getLogger("AssetRegistry")
        self.config = config
        self.assets: Dict[str, Asset] = {}
        
        # Initialize with common assets
        self.assets.update(COMMON_ASSETS)
        
        # Load assets from configuration
        self._load_assets_from_config()
    
    def _load_assets_from_config(self) -> None:
        """Load assets from the configuration."""
        # Load futures contracts if enabled
        if self.config.get("futures", {}).get("enabled", False):
            self._load_futures_contracts()
        
        # Add stock assets (assuming all non-futures assets are stocks)
        for symbol in self.config.get("assets", []):
            if symbol not in self.assets:
                self.assets[symbol] = Asset(
                    symbol=symbol,
                    asset_type=AssetType.STOCK,
                    description=f"{symbol} Stock",
                    exchange="NYSE/NASDAQ",  # Default exchange
                    tick_size=0.01,
                    contract_size=1.0,
                    multiplier=1.0
                )
                self.logger.debug(f"Added stock asset: {symbol}")
    
    def _load_futures_contracts(self) -> None:
        """Load futures contracts from the configuration."""
        futures_config = self.config.get("futures", {})
        contracts_config = futures_config.get("contracts", {})
        
        for symbol, contract_config in contracts_config.items():
            # Skip if already loaded from common assets
            if symbol in self.assets:
                # Update with config values
                asset = self.assets[symbol]
                for key, value in contract_config.items():
                    if hasattr(asset, key):
                        setattr(asset, key, value)
                self.logger.debug(f"Updated futures contract: {symbol}")
            else:
                # Create new asset
                self.assets[symbol] = Asset(
                    symbol=symbol,
                    asset_type=AssetType.FUTURES,
                    description=contract_config.get("description", f"{symbol} Futures"),
                    exchange=contract_config.get("exchange", "CME"),
                    tick_size=contract_config.get("tick_size", 0.01),
                    contract_size=contract_config.get("contract_size", 1.0),
                    margin_requirement=contract_config.get("margin_requirement"),
                    multiplier=contract_config.get("multiplier", 1.0),
                    trading_hours=contract_config.get("trading_hours", {})
                )
                self.logger.debug(f"Added futures contract: {symbol}")
    
    def get_asset(self, symbol: str) -> Optional[Asset]:
        """
        Get an asset by symbol.
        
        Args:
            symbol: The asset symbol
            
        Returns:
            Optional[Asset]: The asset, or None if not found
        """
        return self.assets.get(symbol)
    
    def get_all_assets(self) -> List[Asset]:
        """
        Get all assets.
        
        Returns:
            List[Asset]: All assets
        """
        return list(self.assets.values())
    
    def get_assets_by_type(self, asset_type: AssetType) -> List[Asset]:
        """
        Get assets by type.
        
        Args:
            asset_type: The asset type
            
        Returns:
            List[Asset]: Assets of the specified type
        """
        return [asset for asset in self.assets.values() if asset.asset_type == asset_type]
    
    def get_futures_contracts(self) -> List[Asset]:
        """
        Get all futures contracts.
        
        Returns:
            List[Asset]: All futures contracts
        """
        return self.get_assets_by_type(AssetType.FUTURES)
    
    def get_stocks(self) -> List[Asset]:
        """
        Get all stocks.
        
        Returns:
            List[Asset]: All stocks
        """
        return self.get_assets_by_type(AssetType.STOCK)
    
    def is_futures_contract(self, symbol: str) -> bool:
        """
        Check if a symbol is a futures contract.
        
        Args:
            symbol: The asset symbol
            
        Returns:
            bool: True if the symbol is a futures contract
        """
        asset = self.get_asset(symbol)
        return asset is not None and asset.is_futures
    
    def is_stock(self, symbol: str) -> bool:
        """
        Check if a symbol is a stock.
        
        Args:
            symbol: The asset symbol
            
        Returns:
            bool: True if the symbol is a stock
        """
        asset = self.get_asset(symbol)
        return asset is not None and asset.is_stock
    
    def get_value_per_point(self, symbol: str) -> float:
        """
        Get the dollar value per point movement for an asset.
        
        Args:
            symbol: The asset symbol
            
        Returns:
            float: The dollar value per point
        """
        asset = self.get_asset(symbol)
        if asset:
            return asset.value_per_point
        return 1.0  # Default for stocks
    
    def get_tick_size(self, symbol: str) -> float:
        """
        Get the tick size for an asset.
        
        Args:
            symbol: The asset symbol
            
        Returns:
            float: The tick size
        """
        asset = self.get_asset(symbol)
        if asset:
            return asset.tick_size
        return 0.01  # Default tick size
