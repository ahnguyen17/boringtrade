"""
Notification utility for the BoringTrade trading bot.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional


class Notifier:
    """
    Handles notifications for the trading bot.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the notifier.
        
        Args:
            config: Notification configuration
        """
        self.config = config
        self.logger = logging.getLogger("Notifier")
        self.notifications: List[Dict[str, Any]] = []
    
    def send_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a notification.
        
        Args:
            title: The notification title
            message: The notification message
            notification_type: The type of notification (info, warning, error, trade)
            data: Additional data to include with the notification
        """
        # Create notification
        notification = {
            "title": title,
            "message": message,
            "type": notification_type,
            "timestamp": datetime.now(),
            "data": data
        }
        
        # Log notification
        log_message = f"{title}: {message}"
        if notification_type == "error":
            self.logger.error(log_message)
        elif notification_type == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Store notification
        self.notifications.append(notification)
        
        # TODO: Implement additional notification methods (email, SMS, push, etc.)
    
    def send_trade_entry_notification(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        quantity: float,
        strategy_name: str,
        risk_reward: Optional[float] = None
    ) -> None:
        """
        Send a notification for a trade entry.
        
        Args:
            symbol: The asset symbol
            direction: The trade direction (LONG or SHORT)
            entry_price: The entry price
            stop_loss: The stop loss price
            take_profit: The take profit price
            quantity: The trade quantity
            strategy_name: The name of the strategy
            risk_reward: The risk-reward ratio
        """
        if not self.config.get("trade_entry", True):
            return
        
        # Format risk-reward ratio
        rr_str = f" [{risk_reward:.2f}R]" if risk_reward is not None else ""
        
        # Create message
        message = (
            f"Entered {direction} {quantity} {symbol} at {entry_price:.2f}\n"
            f"Stop Loss: {stop_loss:.2f}\n"
            f"Take Profit: {take_profit:.2f}{rr_str}\n"
            f"Strategy: {strategy_name}"
        )
        
        # Send notification
        self.send_notification(
            title=f"Trade Entry: {symbol} {direction}",
            message=message,
            notification_type="trade",
            data={
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "quantity": quantity,
                "strategy_name": strategy_name,
                "risk_reward": risk_reward
            }
        )
    
    def send_trade_exit_notification(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        profit_loss: float,
        profit_loss_r: Optional[float] = None,
        exit_reason: str = "Unknown"
    ) -> None:
        """
        Send a notification for a trade exit.
        
        Args:
            symbol: The asset symbol
            direction: The trade direction (LONG or SHORT)
            entry_price: The entry price
            exit_price: The exit price
            quantity: The trade quantity
            profit_loss: The profit/loss amount
            profit_loss_r: The profit/loss in R multiples
            exit_reason: The reason for the exit
        """
        if not self.config.get("trade_exit", True):
            return
        
        # Determine if the trade was a win or loss
        result = "WIN" if profit_loss > 0 else "LOSS" if profit_loss < 0 else "BREAKEVEN"
        
        # Format profit/loss in R multiples
        r_str = f" [{profit_loss_r:.2f}R]" if profit_loss_r is not None else ""
        
        # Create message
        message = (
            f"Exited {direction} {quantity} {symbol} at {exit_price:.2f}\n"
            f"Entry: {entry_price:.2f}\n"
            f"P/L: {profit_loss:.2f}{r_str}\n"
            f"Reason: {exit_reason}"
        )
        
        # Send notification
        self.send_notification(
            title=f"Trade Exit: {symbol} {direction} - {result}",
            message=message,
            notification_type="trade",
            data={
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "quantity": quantity,
                "profit_loss": profit_loss,
                "profit_loss_r": profit_loss_r,
                "exit_reason": exit_reason,
                "result": result
            }
        )
    
    def send_daily_summary_notification(
        self,
        date: datetime,
        total_trades: int,
        winning_trades: int,
        losing_trades: int,
        breakeven_trades: int,
        total_profit_loss: float,
        win_rate: float
    ) -> None:
        """
        Send a notification with a daily trading summary.
        
        Args:
            date: The date of the summary
            total_trades: The total number of trades
            winning_trades: The number of winning trades
            losing_trades: The number of losing trades
            breakeven_trades: The number of breakeven trades
            total_profit_loss: The total profit/loss
            win_rate: The win rate
        """
        if not self.config.get("daily_summary", True):
            return
        
        # Create message
        message = (
            f"Date: {date.strftime('%Y-%m-%d')}\n"
            f"Total Trades: {total_trades}\n"
            f"Winning Trades: {winning_trades}\n"
            f"Losing Trades: {losing_trades}\n"
            f"Breakeven Trades: {breakeven_trades}\n"
            f"Total P/L: {total_profit_loss:.2f}\n"
            f"Win Rate: {win_rate:.2%}"
        )
        
        # Send notification
        self.send_notification(
            title=f"Daily Trading Summary: {date.strftime('%Y-%m-%d')}",
            message=message,
            notification_type="summary",
            data={
                "date": date.isoformat(),
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "breakeven_trades": breakeven_trades,
                "total_profit_loss": total_profit_loss,
                "win_rate": win_rate
            }
        )
    
    def send_error_notification(
        self,
        error_message: str,
        error_type: str = "Error",
        error_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a notification for an error.
        
        Args:
            error_message: The error message
            error_type: The type of error
            error_details: Additional error details
        """
        if not self.config.get("error_alerts", True):
            return
        
        # Send notification
        self.send_notification(
            title=f"{error_type} Alert",
            message=error_message,
            notification_type="error",
            data=error_details
        )
    
    def get_notifications(
        self,
        notification_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get notifications.
        
        Args:
            notification_type: Filter by notification type
            limit: Maximum number of notifications to return
            
        Returns:
            List[Dict[str, Any]]: The notifications
        """
        # Filter by type if specified
        if notification_type:
            filtered = [n for n in self.notifications if n["type"] == notification_type]
        else:
            filtered = self.notifications
        
        # Sort by timestamp (newest first)
        sorted_notifications = sorted(
            filtered,
            key=lambda n: n["timestamp"],
            reverse=True
        )
        
        # Apply limit if specified
        if limit:
            return sorted_notifications[:limit]
        
        return sorted_notifications
