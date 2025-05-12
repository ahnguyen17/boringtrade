"""
Tastytrade API integration for the BoringTrade trading bot.
"""
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable

import requests

# Try to import websocket, but continue if it's not available
try:
    from websocket import WebSocketApp
except ImportError:
    print("Warning: websocket-client not installed. WebSocket functionality will not be available.")
    # Define a dummy WebSocketApp class
    class WebSocketApp:
        def __init__(self, *args, **kwargs):
            pass

        def close(self):
            pass

from brokers.broker_interface import BrokerInterface
from models.candle import Candle
from models.trade import Trade, TradeDirection, TradeStatus


class TastytradeAPI(BrokerInterface):
    """
    Tastytrade API integration.
    """

    def __init__(self, api_key: str, api_secret: str, **kwargs: Any):
        """
        Initialize the Tastytrade API.

        Args:
            api_key: The API key
            api_secret: The API secret
            **kwargs: Additional parameters
        """
        super().__init__(api_key, api_secret)
        self.base_url = "https://api.tastytrade.com/v1"
        self.ws_url = "wss://streamer.tastytrade.com/v1"
        self.session_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.ws: Optional[WebSocketApp] = None
        self.subscriptions: Dict[str, Dict[str, Any]] = {}

    def connect(self) -> bool:
        """
        Connect to the Tastytrade API.

        Returns:
            bool: True if the connection was successful
        """
        self.logger.info("Connecting to Tastytrade API...")

        try:
            # Authenticate
            auth_url = f"{self.base_url}/sessions"
            auth_data = {
                "login": self.api_key,
                "password": self.api_secret
            }

            response = requests.post(auth_url, json=auth_data)
            response.raise_for_status()

            auth_result = response.json()
            self.session_token = auth_result.get("session-token")
            self.refresh_token = auth_result.get("refresh-token")

            if not self.session_token:
                self.logger.error("Failed to get session token")
                return False

            # Get account info
            self.get_account_info()

            # Connect to WebSocket
            self._connect_websocket()

            self.is_connected = True
            self.logger.info("Connected to Tastytrade API")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to Tastytrade API: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from the Tastytrade API.

        Returns:
            bool: True if the disconnection was successful
        """
        self.logger.info("Disconnecting from Tastytrade API...")

        try:
            # Close WebSocket
            if self.ws:
                self.ws.close()
                self.ws = None

            # Logout
            if self.session_token:
                logout_url = f"{self.base_url}/sessions"
                headers = {"Authorization": f"Bearer {self.session_token}"}

                response = requests.delete(logout_url, headers=headers)
                response.raise_for_status()

                self.session_token = None
                self.refresh_token = None

            self.is_connected = False
            self.logger.info("Disconnected from Tastytrade API")
            return True

        except Exception as e:
            self.logger.error(f"Failed to disconnect from Tastytrade API: {e}")
            return False

    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.

        Returns:
            Dict[str, Any]: Account information
        """
        self.logger.info("Getting account information...")

        try:
            # Get accounts
            accounts_url = f"{self.base_url}/customers/me/accounts"
            headers = {"Authorization": f"Bearer {self.session_token}"}

            response = requests.get(accounts_url, headers=headers)
            response.raise_for_status()

            accounts = response.json().get("items", [])

            if not accounts:
                self.logger.error("No accounts found")
                return {}

            # Use the first account
            account = accounts[0]
            account_number = account.get("account-number")

            # Get account balances
            balances_url = f"{self.base_url}/accounts/{account_number}/balances"

            response = requests.get(balances_url, headers=headers)
            response.raise_for_status()

            balances = response.json()

            # Combine account and balance information
            self.account_info = {
                "account_number": account_number,
                "account_type": account.get("account-type-name"),
                "equity": balances.get("equity"),
                "buying_power": balances.get("buying-power"),
                "cash": balances.get("cash"),
                "margin": balances.get("margin")
            }

            self.logger.info(f"Account information retrieved: {account_number}")
            return self.account_info

        except Exception as e:
            self.logger.error(f"Failed to get account information: {e}")
            return {}

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current positions.

        Returns:
            Dict[str, Dict[str, Any]]: Current positions
        """
        self.logger.info("Getting positions...")

        try:
            account_number = self.account_info.get("account_number")

            if not account_number:
                self.logger.error("No account number found")
                return {}

            # Get positions
            positions_url = f"{self.base_url}/accounts/{account_number}/positions"
            headers = {"Authorization": f"Bearer {self.session_token}"}

            response = requests.get(positions_url, headers=headers)
            response.raise_for_status()

            positions_data = response.json().get("items", [])

            # Process positions
            self.positions = {}
            for position in positions_data:
                symbol = position.get("symbol")

                if symbol:
                    self.positions[symbol] = {
                        "symbol": symbol,
                        "quantity": position.get("quantity", 0),
                        "average_price": position.get("average-open-price", 0),
                        "current_price": position.get("mark-price", 0),
                        "unrealized_pl": position.get("unrealized-gain-loss", 0),
                        "realized_pl": position.get("realized-gain-loss", 0),
                        "direction": "LONG" if position.get("quantity", 0) > 0 else "SHORT"
                    }

            self.logger.info(f"Retrieved {len(self.positions)} positions")
            return self.positions

        except Exception as e:
            self.logger.error(f"Failed to get positions: {e}")
            return {}

    def get_orders(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current orders.

        Returns:
            Dict[str, Dict[str, Any]]: Current orders
        """
        self.logger.info("Getting orders...")

        try:
            account_number = self.account_info.get("account_number")

            if not account_number:
                self.logger.error("No account number found")
                return {}

            # Get orders
            orders_url = f"{self.base_url}/accounts/{account_number}/orders"
            headers = {"Authorization": f"Bearer {self.session_token}"}

            response = requests.get(orders_url, headers=headers)
            response.raise_for_status()

            orders_data = response.json().get("items", [])

            # Process orders
            self.orders = {}
            for order in orders_data:
                order_id = order.get("id")

                if order_id:
                    self.orders[order_id] = {
                        "order_id": order_id,
                        "symbol": order.get("underlying-symbol"),
                        "quantity": order.get("quantity", 0),
                        "price": order.get("price", 0),
                        "type": order.get("order-type"),
                        "status": order.get("status"),
                        "direction": "BUY" if order.get("side") == "Buy" else "SELL",
                        "time_in_force": order.get("time-in-force"),
                        "created_at": order.get("created-at")
                    }

            self.logger.info(f"Retrieved {len(self.orders)} orders")
            return self.orders

        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            return {}

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
        self.logger.info(f"Placing market order: {symbol} {direction.value} {quantity}")

        try:
            account_number = self.account_info.get("account_number")

            if not account_number:
                return False, "No account number found", None

            # Create order
            order_url = f"{self.base_url}/accounts/{account_number}/orders"
            headers = {"Authorization": f"Bearer {self.session_token}"}

            order_data = {
                "account-number": account_number,
                "source": "API",
                "order-type": "Market",
                "time-in-force": "Day",
                "price-effect": "Debit",
                "underlying-symbol": symbol,
                "quantity": int(quantity),
                "side": "Buy" if direction == TradeDirection.LONG else "Sell"
            }

            response = requests.post(order_url, headers=headers, json=order_data)
            response.raise_for_status()

            order_result = response.json()
            order_id = order_result.get("order-id")

            if not order_id:
                return False, "Failed to get order ID", None

            # Create stop loss order if specified
            stop_loss_order_id = None
            if stop_loss:
                stop_order_data = {
                    "account-number": account_number,
                    "source": "API",
                    "order-type": "Stop",
                    "time-in-force": "GTC",
                    "price-effect": "Debit",
                    "underlying-symbol": symbol,
                    "quantity": int(quantity),
                    "side": "Sell" if direction == TradeDirection.LONG else "Buy",
                    "stop-price": stop_loss
                }

                stop_response = requests.post(order_url, headers=headers, json=stop_order_data)
                stop_response.raise_for_status()

                stop_result = stop_response.json()
                stop_loss_order_id = stop_result.get("order-id")

            # Create take profit order if specified
            take_profit_order_id = None
            if take_profit:
                limit_order_data = {
                    "account-number": account_number,
                    "source": "API",
                    "order-type": "Limit",
                    "time-in-force": "GTC",
                    "price-effect": "Debit",
                    "underlying-symbol": symbol,
                    "quantity": int(quantity),
                    "side": "Sell" if direction == TradeDirection.LONG else "Buy",
                    "price": take_profit
                }

                limit_response = requests.post(order_url, headers=headers, json=limit_order_data)
                limit_response.raise_for_status()

                limit_result = limit_response.json()
                take_profit_order_id = limit_result.get("order-id")

            # Get order details
            order_details = {
                "order_id": order_id,
                "symbol": symbol,
                "direction": direction.value,
                "quantity": quantity,
                "type": "MARKET",
                "status": "PENDING",
                "stop_loss_order_id": stop_loss_order_id,
                "take_profit_order_id": take_profit_order_id
            }

            self.logger.info(f"Market order placed: {order_id}")
            return True, f"Market order placed: {order_id}", order_details

        except Exception as e:
            error_msg = f"Failed to place market order: {e}"
            self.logger.error(error_msg)
            return False, error_msg, None

    # TODO: Implement remaining methods

    def test_connection(self, timeout: int = 10) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Test the connection to the Tastytrade API.

        Args:
            timeout: The timeout in seconds

        Returns:
            Tuple[bool, str, Dict[str, Any]]:
                - Success flag
                - Message
                - Additional details about the connection status
        """
        self.logger.info(f"Testing connection to Tastytrade API (timeout: {timeout}s)...")

        details = {
            "broker": "tastytrade",
            "api_url": self.base_url,
            "websocket_url": self.ws_url,
            "timeout": timeout,
            "connection_time": None,
            "authenticated": False,
            "account_info": {},
            "error": None
        }

        try:
            # Record start time
            start_time = time.time()

            # Authenticate
            auth_url = f"{self.base_url}/sessions"
            auth_data = {
                "login": self.api_key,
                "password": self.api_secret
            }

            response = requests.post(auth_url, json=auth_data, timeout=timeout)
            response.raise_for_status()

            auth_result = response.json()
            temp_session_token = auth_result.get("session-token")

            if not temp_session_token:
                error_msg = "Failed to get session token"
                self.logger.error(error_msg)
                details["error"] = error_msg
                return False, error_msg, details

            details["authenticated"] = True

            # Get accounts
            accounts_url = f"{self.base_url}/customers/me/accounts"
            headers = {"Authorization": f"Bearer {temp_session_token}"}

            response = requests.get(accounts_url, headers=headers, timeout=timeout)
            response.raise_for_status()

            accounts = response.json().get("items", [])

            if not accounts:
                error_msg = "No accounts found"
                self.logger.error(error_msg)
                details["error"] = error_msg
                return False, error_msg, details

            # Use the first account
            account = accounts[0]
            account_number = account.get("account-number")

            # Get account balances
            balances_url = f"{self.base_url}/accounts/{account_number}/balances"

            response = requests.get(balances_url, headers=headers, timeout=timeout)
            response.raise_for_status()

            balances = response.json()

            # Combine account and balance information
            account_info = {
                "account_number": account_number,
                "account_type": account.get("account-type-name"),
                "equity": balances.get("equity"),
                "buying_power": balances.get("buying-power"),
                "cash": balances.get("cash"),
                "margin": balances.get("margin")
            }

            details["account_info"] = account_info

            # Logout
            logout_url = f"{self.base_url}/sessions"
            response = requests.delete(logout_url, headers=headers, timeout=timeout)
            response.raise_for_status()

            # Calculate connection time
            end_time = time.time()
            connection_time = end_time - start_time
            details["connection_time"] = connection_time

            success_msg = f"Successfully connected to Tastytrade API in {connection_time:.2f} seconds"
            self.logger.info(success_msg)
            return True, success_msg, details

        except requests.exceptions.Timeout:
            error_msg = f"Connection to Tastytrade API timed out after {timeout} seconds"
            self.logger.error(error_msg)
            details["error"] = error_msg
            return False, error_msg, details

        except requests.exceptions.ConnectionError:
            error_msg = "Failed to connect to Tastytrade API: Connection error"
            self.logger.error(error_msg)
            details["error"] = error_msg
            return False, error_msg, details

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error occurred while connecting to Tastytrade API: {e}"
            self.logger.error(error_msg)
            details["error"] = error_msg
            return False, error_msg, details

        except Exception as e:
            error_msg = f"Failed to connect to Tastytrade API: {e}"
            self.logger.error(error_msg)
            details["error"] = error_msg
            return False, error_msg, details

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
        self.logger.info(f"Placing limit order: {symbol} {direction.value} {quantity} @ {price}")

        try:
            account_number = self.account_info.get("account_number")

            if not account_number:
                return False, "No account number found", None

            # Create order
            order_url = f"{self.base_url}/accounts/{account_number}/orders"
            headers = {"Authorization": f"Bearer {self.session_token}"}

            order_data = {
                "account-number": account_number,
                "source": "API",
                "order-type": "Limit",
                "time-in-force": "Day",
                "price-effect": "Debit",
                "underlying-symbol": symbol,
                "quantity": int(quantity),
                "price": price,
                "side": "Buy" if direction == TradeDirection.LONG else "Sell"
            }

            response = requests.post(order_url, headers=headers, json=order_data)
            response.raise_for_status()

            order_result = response.json()
            order_id = order_result.get("order-id")

            if not order_id:
                return False, "Failed to get order ID", None

            # Create stop loss order if specified
            stop_loss_order_id = None
            if stop_loss:
                stop_order_data = {
                    "account-number": account_number,
                    "source": "API",
                    "order-type": "Stop",
                    "time-in-force": "GTC",
                    "price-effect": "Debit",
                    "underlying-symbol": symbol,
                    "quantity": int(quantity),
                    "side": "Sell" if direction == TradeDirection.LONG else "Buy",
                    "stop-price": stop_loss
                }

                stop_response = requests.post(order_url, headers=headers, json=stop_order_data)
                stop_response.raise_for_status()

                stop_result = stop_response.json()
                stop_loss_order_id = stop_result.get("order-id")

            # Create take profit order if specified
            take_profit_order_id = None
            if take_profit:
                limit_order_data = {
                    "account-number": account_number,
                    "source": "API",
                    "order-type": "Limit",
                    "time-in-force": "GTC",
                    "price-effect": "Debit",
                    "underlying-symbol": symbol,
                    "quantity": int(quantity),
                    "side": "Sell" if direction == TradeDirection.LONG else "Buy",
                    "price": take_profit
                }

                limit_response = requests.post(order_url, headers=headers, json=limit_order_data)
                limit_response.raise_for_status()

                limit_result = limit_response.json()
                take_profit_order_id = limit_result.get("order-id")

            # Get order details
            order_details = {
                "order_id": order_id,
                "symbol": symbol,
                "direction": direction.value,
                "quantity": quantity,
                "price": price,
                "type": "LIMIT",
                "status": "PENDING",
                "stop_loss_order_id": stop_loss_order_id,
                "take_profit_order_id": take_profit_order_id
            }

            self.logger.info(f"Limit order placed: {order_id}")
            return True, f"Limit order placed: {order_id}", order_details

        except Exception as e:
            error_msg = f"Failed to place limit order: {e}"
            self.logger.error(error_msg)
            return False, error_msg, None

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
        self.logger.info(f"Modifying order: {order_id}")

        try:
            account_number = self.account_info.get("account_number")

            if not account_number:
                return False, "No account number found"

            # Get current order
            if order_id not in self.orders:
                self.get_orders()  # Refresh orders
                if order_id not in self.orders:
                    return False, f"Order {order_id} not found"

            current_order = self.orders[order_id]

            # For Tastytrade, we need to cancel the existing order and create a new one
            # First, cancel the existing order
            cancel_success, cancel_message = self.cancel_order(order_id)

            if not cancel_success:
                return False, f"Failed to cancel order for modification: {cancel_message}"

            # Create a new order with the updated parameters
            symbol = current_order["symbol"]
            direction = TradeDirection.LONG if current_order["direction"] == "BUY" else TradeDirection.SHORT
            quantity = new_quantity if new_quantity is not None else current_order["quantity"]
            price = new_price if new_price is not None else current_order.get("price")

            # Determine order type and place the appropriate order
            if current_order["type"] == "LIMIT" and price is not None:
                success, message, new_order = self.place_limit_order(
                    symbol=symbol,
                    direction=direction,
                    quantity=quantity,
                    price=price,
                    stop_loss=new_stop_loss,
                    take_profit=new_take_profit
                )
            else:
                success, message, new_order = self.place_market_order(
                    symbol=symbol,
                    direction=direction,
                    quantity=quantity,
                    stop_loss=new_stop_loss,
                    take_profit=new_take_profit
                )

            if not success:
                return False, f"Failed to create new order after cancellation: {message}"

            self.logger.info(f"Order modified: {order_id} -> {new_order['order_id']}")
            return True, f"Order modified: {order_id} -> {new_order['order_id']}"

        except Exception as e:
            error_msg = f"Failed to modify order: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """
        Cancel an order.

        Args:
            order_id: The order ID

        Returns:
            Tuple[bool, str]: Success flag and message
        """
        self.logger.info(f"Cancelling order: {order_id}")

        try:
            account_number = self.account_info.get("account_number")

            if not account_number:
                return False, "No account number found"

            # Cancel order
            cancel_url = f"{self.base_url}/accounts/{account_number}/orders/{order_id}"
            headers = {"Authorization": f"Bearer {self.session_token}"}

            response = requests.delete(cancel_url, headers=headers)
            response.raise_for_status()

            # Remove from orders dictionary
            if order_id in self.orders:
                del self.orders[order_id]

            self.logger.info(f"Order cancelled: {order_id}")
            return True, f"Order cancelled: {order_id}"

        except Exception as e:
            error_msg = f"Failed to cancel order: {e}"
            self.logger.error(error_msg)
            return False, error_msg

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
        self.logger.info(f"Closing position: {symbol}")

        try:
            # Get current positions
            self.get_positions()

            if symbol not in self.positions:
                return False, f"No position found for {symbol}", None

            position = self.positions[symbol]
            position_quantity = position["quantity"]
            position_direction = position["direction"]

            # Determine the quantity to close
            close_quantity = abs(position_quantity) if quantity is None else min(abs(quantity), abs(position_quantity))

            # Determine the direction for the closing order
            close_direction = TradeDirection.SHORT if position_direction == "LONG" else TradeDirection.LONG

            # Place a market order to close the position
            success, message, order_details = self.place_market_order(
                symbol=symbol,
                direction=close_direction,
                quantity=close_quantity
            )

            if not success:
                return False, f"Failed to close position: {message}", None

            self.logger.info(f"Position closed: {symbol} {close_quantity} shares")
            return True, f"Position closed: {symbol} {close_quantity} shares", order_details

        except Exception as e:
            error_msg = f"Failed to close position: {e}"
            self.logger.error(error_msg)
            return False, error_msg, None

    def flatten_all(self) -> Tuple[bool, str]:
        """
        Close all positions and cancel all orders.

        Returns:
            Tuple[bool, str]: Success flag and message
        """
        self.logger.info("Flattening all positions and cancelling all orders")

        try:
            # Get current positions and orders
            positions = self.get_positions()
            orders = self.get_orders()

            # Cancel all orders
            cancelled_orders = 0
            for order_id in list(orders.keys()):
                success, message = self.cancel_order(order_id)
                if success:
                    cancelled_orders += 1
                else:
                    self.logger.warning(f"Failed to cancel order {order_id}: {message}")

            # Close all positions
            closed_positions = 0
            for symbol in list(positions.keys()):
                success, message, _ = self.close_position(symbol)
                if success:
                    closed_positions += 1
                else:
                    self.logger.warning(f"Failed to close position {symbol}: {message}")

            result_message = f"Flattened {closed_positions}/{len(positions)} positions and cancelled {cancelled_orders}/{len(orders)} orders"
            self.logger.info(result_message)

            # Return success if all operations were successful
            if closed_positions == len(positions) and cancelled_orders == len(orders):
                return True, result_message
            else:
                return False, f"Partially completed: {result_message}"

        except Exception as e:
            error_msg = f"Failed to flatten all: {e}"
            self.logger.error(error_msg)
            return False, error_msg

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
        self.logger.info(f"Getting historical candles for {symbol} ({timeframe}m)")

        try:
            # Set end time to now if not provided
            if end_time is None:
                end_time = datetime.now()

            # Format dates for API
            start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            # Convert timeframe to a supported interval
            interval = self._convert_timeframe_to_interval(timeframe)

            # Build URL
            history_url = f"{self.base_url}/market-data/history"
            headers = {"Authorization": f"Bearer {self.session_token}"}

            params = {
                "symbol": symbol,
                "interval": interval,
                "start": start_str,
                "end": end_str
            }

            if limit is not None:
                params["limit"] = limit

            response = requests.get(history_url, headers=headers, params=params)
            response.raise_for_status()

            history_data = response.json().get("candles", [])

            # Convert to Candle objects
            candles = []
            for candle_data in history_data:
                timestamp = datetime.fromisoformat(candle_data.get("time").replace("Z", "+00:00"))
                candle = Candle(
                    symbol=symbol,
                    timestamp=timestamp,
                    open_price=float(candle_data.get("open", 0)),
                    high_price=float(candle_data.get("high", 0)),
                    low_price=float(candle_data.get("low", 0)),
                    close_price=float(candle_data.get("close", 0)),
                    volume=float(candle_data.get("volume", 0)),
                    timeframe=timeframe,
                    is_complete=True
                )
                candles.append(candle)

            self.logger.info(f"Retrieved {len(candles)} historical candles for {symbol}")
            return candles

        except Exception as e:
            error_msg = f"Failed to get historical candles: {e}"
            self.logger.error(error_msg)
            return []

    def _convert_timeframe_to_interval(self, timeframe: int) -> str:
        """
        Convert a timeframe in minutes to a Tastytrade API interval.

        Args:
            timeframe: The timeframe in minutes

        Returns:
            str: The Tastytrade API interval
        """
        # Map common timeframes to Tastytrade intervals
        if timeframe == 1:
            return "1min"
        elif timeframe == 5:
            return "5min"
        elif timeframe == 15:
            return "15min"
        elif timeframe == 30:
            return "30min"
        elif timeframe == 60:
            return "1hour"
        elif timeframe == 1440:  # 1 day
            return "1day"
        else:
            # Default to closest available timeframe
            if timeframe < 5:
                return "1min"
            elif timeframe < 15:
                return "5min"
            elif timeframe < 30:
                return "15min"
            elif timeframe < 60:
                return "30min"
            elif timeframe < 1440:
                return "1hour"
            else:
                return "1day"

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
        self.logger.info(f"Subscribing to market data for {symbol} ({timeframe}m)")

        try:
            # Create subscription key
            sub_key = f"{symbol}_{timeframe}"

            # Initialize subscription dictionary if it doesn't exist
            if sub_key not in self.subscriptions:
                self.subscriptions[sub_key] = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "callbacks": [],
                    "last_candle": None,
                    "current_candle": None
                }

            # Add callback to subscription
            if callback not in self.subscriptions[sub_key]["callbacks"]:
                self.subscriptions[sub_key]["callbacks"].append(callback)

            # Make sure WebSocket is connected
            if not self.ws:
                self._connect_websocket()

            # Subscribe to quotes via WebSocket
            if self.ws:
                # Create subscription message
                subscribe_msg = {
                    "action": "subscribe",
                    "value": {
                        "symbol": symbol,
                        "type": "quote"
                    }
                }

                # Send subscription message
                self.ws.send(json.dumps(subscribe_msg))

                self.logger.info(f"Subscribed to market data for {symbol}")
                return True
            else:
                self.logger.error("WebSocket not connected")
                return False

        except Exception as e:
            error_msg = f"Failed to subscribe to market data: {e}"
            self.logger.error(error_msg)
            return False

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
        self.logger.info(f"Unsubscribing from market data for {symbol} ({timeframe}m)")

        try:
            # Create subscription key
            sub_key = f"{symbol}_{timeframe}"

            # Check if subscription exists
            if sub_key not in self.subscriptions:
                self.logger.warning(f"No subscription found for {symbol} ({timeframe}m)")
                return False

            # Remove specific callback or all callbacks
            if callback is not None:
                if callback in self.subscriptions[sub_key]["callbacks"]:
                    self.subscriptions[sub_key]["callbacks"].remove(callback)
                    self.logger.info(f"Removed callback for {symbol} ({timeframe}m)")
                else:
                    self.logger.warning(f"Callback not found for {symbol} ({timeframe}m)")
                    return False
            else:
                self.subscriptions[sub_key]["callbacks"] = []
                self.logger.info(f"Removed all callbacks for {symbol} ({timeframe}m)")

            # If no callbacks left, unsubscribe from WebSocket
            if not self.subscriptions[sub_key]["callbacks"] and self.ws:
                # Create unsubscription message
                unsubscribe_msg = {
                    "action": "unsubscribe",
                    "value": {
                        "symbol": symbol,
                        "type": "quote"
                    }
                }

                # Send unsubscription message
                self.ws.send(json.dumps(unsubscribe_msg))

                # Remove subscription
                del self.subscriptions[sub_key]

                self.logger.info(f"Unsubscribed from market data for {symbol}")

            return True

        except Exception as e:
            error_msg = f"Failed to unsubscribe from market data: {e}"
            self.logger.error(error_msg)
            return False

    def _connect_websocket(self) -> None:
        """Connect to the WebSocket API."""
        try:
            # Import json here to avoid circular imports
            import json

            # Check if WebSocketApp is available
            if not hasattr(WebSocketApp, "__call__"):
                self.logger.error("WebSocket functionality not available. Please install websocket-client.")
                return

            # Close existing connection if any
            if self.ws:
                self.ws.close()

            # Create WebSocket URL with session token
            ws_url = f"{self.ws_url}?session-token={self.session_token}"

            # Create WebSocket connection
            self.ws = WebSocketApp(
                ws_url,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close,
                on_open=self._on_ws_open
            )

            # Start WebSocket connection in a separate thread
            import threading
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()

            self.logger.info("WebSocket connection started")

        except Exception as e:
            self.logger.error(f"Failed to connect to WebSocket: {e}")
            self.ws = None

    def _on_ws_message(self, ws: WebSocketApp, message: str) -> None:
        """Handle WebSocket messages."""
        try:
            # Parse message
            data = json.loads(message)

            # Check if it's a quote message
            if "data" in data and "quote" in data.get("type", ""):
                quote_data = data["data"]
                symbol = quote_data.get("symbol")

                # Process quote for each subscription with this symbol
                for sub_key, subscription in self.subscriptions.items():
                    if subscription["symbol"] == symbol:
                        self._process_quote(subscription, quote_data)

        except Exception as e:
            self.logger.error(f"Error processing WebSocket message: {e}")

    def _on_ws_error(self, ws: WebSocketApp, error: Exception) -> None:
        """Handle WebSocket errors."""
        self.logger.error(f"WebSocket error: {error}")

    def _on_ws_close(self, ws: WebSocketApp, close_status_code: int, close_msg: str) -> None:
        """Handle WebSocket close."""
        self.logger.info("WebSocket connection closed")

    def _on_ws_open(self, ws: WebSocketApp) -> None:
        """Handle WebSocket open."""
        self.logger.info("WebSocket connection opened")

    def _process_quote(self, subscription: Dict[str, Any], quote_data: Dict[str, Any]) -> None:
        """
        Process a quote and update candles.

        Args:
            subscription: The subscription data
            quote_data: The quote data from WebSocket
        """
        try:
            symbol = subscription["symbol"]
            timeframe = subscription["timeframe"]

            # Extract quote data
            timestamp = datetime.fromisoformat(quote_data.get("trade-time").replace("Z", "+00:00"))
            price = float(quote_data.get("last", 0))
            volume = float(quote_data.get("volume", 0))

            # Calculate candle timestamp (floor to timeframe)
            candle_timestamp = datetime(
                timestamp.year,
                timestamp.month,
                timestamp.day,
                timestamp.hour,
                (timestamp.minute // timeframe) * timeframe,
                0
            )

            # Get current candle or create a new one
            current_candle = subscription["current_candle"]

            if current_candle is None or current_candle.timestamp != candle_timestamp:
                # If we have a current candle, it's now complete
                if current_candle is not None:
                    current_candle.is_complete = True
                    subscription["last_candle"] = current_candle

                    # Notify callbacks
                    for callback in subscription["callbacks"]:
                        callback(current_candle)

                # Create a new candle
                current_candle = Candle(
                    symbol=symbol,
                    timestamp=candle_timestamp,
                    open_price=price,
                    high_price=price,
                    low_price=price,
                    close_price=price,
                    volume=volume,
                    timeframe=timeframe,
                    is_complete=False
                )
                subscription["current_candle"] = current_candle
            else:
                # Update current candle
                current_candle.high_price = max(current_candle.high_price, price)
                current_candle.low_price = min(current_candle.low_price, price)
                current_candle.close_price = price
                current_candle.volume += volume

        except Exception as e:
            self.logger.error(f"Error processing quote: {e}")
