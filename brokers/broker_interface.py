"""
Abstract broker interface for the BoringTrade trading bot.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable

from models.candle import Candle
from models.trade import Trade, TradeDirection, TradeStatus
from models.asset import Asset, AssetType


class BrokerInterface(ABC):
    """
    Abstract base class for broker interfaces.
    """

    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize the broker interface.

        Args:
            api_key: The API key
            api_secret: The API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logging.getLogger(f"Broker.{self.__class__.__name__}")
        self.is_connected = False
        self.account_info: Dict[str, Any] = {}
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.market_data_callbacks: Dict[str, List[Callable]] = {}

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the broker API.

        Returns:
            bool: True if the connection was successful
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the broker API.

        Returns:
            bool: True if the disconnection was successful
        """
        pass

    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.

        Returns:
            Dict[str, Any]: Account information
        """
        pass

    @abstractmethod
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current positions.

        Returns:
            Dict[str, Dict[str, Any]]: Current positions
        """
        pass

    @abstractmethod
    def get_orders(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current orders.

        Returns:
            Dict[str, Dict[str, Any]]: Current orders
        """
        pass

    @abstractmethod
    def place_market_order(
        self,
        symbol: str,
        direction: TradeDirection,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Place a market order.

        Args:
            symbol: The asset symbol
            direction: The trade direction
            quantity: The quantity to trade
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: Success flag, message, and order details
        """
        pass

    @abstractmethod
    def place_limit_order(
        self,
        symbol: str,
        direction: TradeDirection,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Place a limit order.

        Args:
            symbol: The asset symbol
            direction: The trade direction
            quantity: The quantity to trade
            price: The limit price
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: Success flag, message, and order details
        """
        pass

    @abstractmethod
    def modify_order(
        self,
        order_id: str,
        new_price: Optional[float] = None,
        new_quantity: Optional[float] = None,
        new_stop_loss: Optional[float] = None,
        new_take_profit: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Modify an existing order.

        Args:
            order_id: The order ID
            new_price: The new price
            new_quantity: The new quantity
            new_stop_loss: The new stop loss price
            new_take_profit: The new take profit price

        Returns:
            Tuple[bool, str]: Success flag and message
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """
        Cancel an order.

        Args:
            order_id: The order ID

        Returns:
            Tuple[bool, str]: Success flag and message
        """
        pass

    @abstractmethod
    def close_position(
        self,
        symbol: str,
        quantity: Optional[float] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Close a position.

        Args:
            symbol: The asset symbol
            quantity: The quantity to close (None for all)

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: Success flag, message, and order details
        """
        pass

    @abstractmethod
    def flatten_all(self) -> Tuple[bool, str]:
        """
        Close all positions and cancel all orders.

        Returns:
            Tuple[bool, str]: Success flag and message
        """
        pass

    @abstractmethod
    def get_historical_candles(
        self,
        symbol: str,
        timeframe: int,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Candle]:
        """
        Get historical candles.

        Args:
            symbol: The asset symbol
            timeframe: The candle timeframe in minutes
            start_time: The start time
            end_time: The end time (None for now)
            limit: The maximum number of candles to return

        Returns:
            List[Candle]: The historical candles
        """
        pass

    @abstractmethod
    def subscribe_to_market_data(
        self,
        symbol: str,
        timeframe: int,
        callback: Callable[[Candle], None]
    ) -> bool:
        """
        Subscribe to market data.

        Args:
            symbol: The asset symbol
            timeframe: The candle timeframe in minutes
            callback: The callback function to call when new data is available

        Returns:
            bool: True if the subscription was successful
        """
        pass

    @abstractmethod
    def unsubscribe_from_market_data(
        self,
        symbol: str,
        timeframe: int,
        callback: Optional[Callable[[Candle], None]] = None
    ) -> bool:
        """
        Unsubscribe from market data.

        Args:
            symbol: The asset symbol
            timeframe: The candle timeframe in minutes
            callback: The callback function to unsubscribe (None for all)

        Returns:
            bool: True if the unsubscription was successful
        """
        pass

    def trade_to_order_params(self, trade: Trade) -> Dict[str, Any]:
        """
        Convert a trade to order parameters.

        Args:
            trade: The trade to convert

        Returns:
            Dict[str, Any]: The order parameters
        """
        return {
            "symbol": trade.symbol,
            "direction": trade.direction,
            "quantity": trade.quantity,
            "price": trade.entry_price,
            "stop_loss": trade.stop_loss,
            "take_profit": trade.take_profit
        }

    def update_trade_from_order(
        self,
        trade: Trade,
        order: Dict[str, Any]
    ) -> Trade:
        """
        Update a trade from an order.

        Args:
            trade: The trade to update
            order: The order data

        Returns:
            Trade: The updated trade
        """
        # Update trade with order information
        trade.broker_order_id = order.get("order_id")

        # Update entry details if filled
        if order.get("status") == "FILLED":
            trade.entry_price = order.get("filled_price", trade.entry_price)
            trade.entry_time = order.get("filled_time", datetime.now())
            trade.status = TradeStatus.OPEN

        return trade

    @abstractmethod
    def test_connection(self, timeout: int = 10) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Test the connection to the broker API.

        Args:
            timeout: The timeout in seconds

        Returns:
            Tuple[bool, str, Dict[str, Any]]:
                - Success flag
                - Message
                - Additional details about the connection status
        """
        pass

    def get_asset_type(self, symbol: str) -> AssetType:
        """
        Get the asset type for a symbol.

        Args:
            symbol: The asset symbol

        Returns:
            AssetType: The asset type
        """
        # Default implementation - override in subclasses for more accurate detection
        if symbol in ["ES", "MES"]:
            return AssetType.FUTURES
        return AssetType.STOCK

    def is_futures_contract(self, symbol: str) -> bool:
        """
        Check if a symbol is a futures contract.

        Args:
            symbol: The asset symbol

        Returns:
            bool: True if the symbol is a futures contract
        """
        return self.get_asset_type(symbol) == AssetType.FUTURES

    def get_futures_expiration(self, symbol: str) -> Optional[str]:
        """
        Get the expiration date for a futures contract.

        Args:
            symbol: The futures symbol

        Returns:
            Optional[str]: The expiration date in YYYY-MM-DD format, or None if not applicable
        """
        # Default implementation - override in subclasses
        return None

    def get_futures_contracts(self, root_symbol: str) -> List[Dict[str, Any]]:
        """
        Get available futures contracts for a root symbol.

        Args:
            root_symbol: The root symbol (e.g., "ES" for E-mini S&P 500)

        Returns:
            List[Dict[str, Any]]: List of available contracts with details
        """
        # Default implementation - override in subclasses
        return []
