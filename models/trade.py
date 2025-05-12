"""
Trade data model for the BoringTrade trading bot.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from uuid import uuid4

from models.level import Level


class TradeDirection(Enum):
    """Trade directions."""
    LONG = "LONG"
    SHORT = "SHORT"


class TradeStatus(Enum):
    """Trade statuses."""
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class TradeResult(Enum):
    """Trade results."""
    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"
    UNKNOWN = "UNKNOWN"


class Trade:
    """
    Represents a trade with entry, exit, and performance details.
    """
    
    def __init__(
        self,
        symbol: str,
        direction: TradeDirection,
        strategy_name: str,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        quantity: float = 1.0,
        entry_time: Optional[datetime] = None,
        exit_price: Optional[float] = None,
        exit_time: Optional[datetime] = None,
        status: TradeStatus = TradeStatus.PENDING,
        result: TradeResult = TradeResult.UNKNOWN,
        level: Optional[Level] = None,
        trade_id: Optional[str] = None,
        broker_order_id: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """
        Initialize a new trade.
        
        Args:
            symbol: The asset symbol (e.g., "SPY")
            direction: The trade direction (LONG or SHORT)
            strategy_name: The name of the strategy that generated this trade
            entry_price: The entry price
            stop_loss: The stop loss price
            take_profit: The take profit price
            quantity: The trade quantity (contracts, shares, etc.)
            entry_time: When the trade was entered
            exit_price: The exit price
            exit_time: When the trade was exited
            status: The current status of the trade
            result: The result of the trade
            level: The price level that triggered this trade
            trade_id: A unique identifier for this trade
            broker_order_id: The broker's order ID
            notes: Additional notes about the trade
        """
        self.symbol = symbol
        self.direction = direction
        self.strategy_name = strategy_name
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.quantity = quantity
        self.entry_time = entry_time
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.status = status
        self.result = result
        self.level = level
        self.trade_id = trade_id if trade_id else str(uuid4())
        self.broker_order_id = broker_order_id
        self.notes = notes
        self.partial_exits: List[Dict[str, Any]] = []
    
    @property
    def is_open(self) -> bool:
        """Check if the trade is currently open."""
        return self.status == TradeStatus.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if the trade is closed."""
        return self.status == TradeStatus.CLOSED
    
    @property
    def risk(self) -> Optional[float]:
        """Calculate the risk per contract/share."""
        if self.entry_price is None or self.stop_loss is None:
            return None
        
        if self.direction == TradeDirection.LONG:
            return self.entry_price - self.stop_loss
        else:
            return self.stop_loss - self.entry_price
    
    @property
    def risk_amount(self) -> Optional[float]:
        """Calculate the total risk amount."""
        if self.risk is None:
            return None
        return abs(self.risk) * self.quantity
    
    @property
    def reward(self) -> Optional[float]:
        """Calculate the reward per contract/share."""
        if self.entry_price is None or self.take_profit is None:
            return None
        
        if self.direction == TradeDirection.LONG:
            return self.take_profit - self.entry_price
        else:
            return self.entry_price - self.take_profit
    
    @property
    def reward_amount(self) -> Optional[float]:
        """Calculate the total reward amount."""
        if self.reward is None:
            return None
        return abs(self.reward) * self.quantity
    
    @property
    def risk_reward_ratio(self) -> Optional[float]:
        """Calculate the risk-reward ratio."""
        if self.risk is None or self.reward is None or self.risk == 0:
            return None
        return abs(self.reward / self.risk)
    
    @property
    def profit_loss(self) -> Optional[float]:
        """Calculate the profit/loss per contract/share."""
        if self.entry_price is None or self.exit_price is None:
            return None
        
        if self.direction == TradeDirection.LONG:
            return self.exit_price - self.entry_price
        else:
            return self.entry_price - self.exit_price
    
    @property
    def profit_loss_amount(self) -> Optional[float]:
        """Calculate the total profit/loss amount."""
        if self.profit_loss is None:
            return None
        
        # Calculate P/L from partial exits
        partial_pl = sum(
            exit_data["quantity"] * (
                exit_data["price"] - self.entry_price if self.direction == TradeDirection.LONG
                else self.entry_price - exit_data["price"]
            )
            for exit_data in self.partial_exits
        )
        
        # Calculate P/L from final exit
        remaining_quantity = self.quantity - sum(exit_data["quantity"] for exit_data in self.partial_exits)
        final_pl = self.profit_loss * remaining_quantity
        
        return partial_pl + final_pl
    
    @property
    def profit_loss_r(self) -> Optional[float]:
        """Calculate the profit/loss in terms of R (risk multiples)."""
        if self.profit_loss is None or self.risk is None or self.risk == 0:
            return None
        return self.profit_loss / abs(self.risk)
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate the trade duration in seconds."""
        if self.entry_time is None or self.exit_time is None:
            return None
        return (self.exit_time - self.entry_time).total_seconds()
    
    def add_partial_exit(
        self,
        price: float,
        quantity: float,
        time: datetime,
        reason: Optional[str] = None
    ) -> None:
        """
        Record a partial exit.
        
        Args:
            price: The exit price
            quantity: The quantity exited
            time: When the exit occurred
            reason: The reason for the exit
        """
        self.partial_exits.append({
            "price": price,
            "quantity": quantity,
            "time": time,
            "reason": reason
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the trade to a dictionary.
        
        Returns:
            Dict[str, Any]: The trade as a dictionary
        """
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "direction": self.direction.value,
            "strategy_name": self.strategy_name,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "quantity": self.quantity,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "status": self.status.value,
            "result": self.result.value,
            "level": self.level.to_dict() if self.level else None,
            "broker_order_id": self.broker_order_id,
            "notes": self.notes,
            "partial_exits": [
                {
                    **exit_data,
                    "time": exit_data["time"].isoformat()
                }
                for exit_data in self.partial_exits
            ],
            "risk": self.risk,
            "reward": self.reward,
            "risk_reward_ratio": self.risk_reward_ratio,
            "profit_loss": self.profit_loss,
            "profit_loss_amount": self.profit_loss_amount,
            "profit_loss_r": self.profit_loss_r,
            "duration": self.duration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """
        Create a trade from a dictionary.
        
        Args:
            data: The dictionary containing trade data
            
        Returns:
            Trade: A new trade instance
        """
        trade = cls(
            symbol=data["symbol"],
            direction=TradeDirection(data["direction"]),
            strategy_name=data["strategy_name"],
            entry_price=data.get("entry_price"),
            stop_loss=data.get("stop_loss"),
            take_profit=data.get("take_profit"),
            quantity=data.get("quantity", 1.0),
            entry_time=datetime.fromisoformat(data["entry_time"]) if data.get("entry_time") else None,
            exit_price=data.get("exit_price"),
            exit_time=datetime.fromisoformat(data["exit_time"]) if data.get("exit_time") else None,
            status=TradeStatus(data["status"]),
            result=TradeResult(data["result"]),
            level=Level.from_dict(data["level"]) if data.get("level") else None,
            trade_id=data.get("trade_id"),
            broker_order_id=data.get("broker_order_id"),
            notes=data.get("notes")
        )
        
        # Add partial exits
        for exit_data in data.get("partial_exits", []):
            exit_data_copy = exit_data.copy()
            exit_data_copy["time"] = datetime.fromisoformat(exit_data["time"])
            trade.partial_exits.append(exit_data_copy)
        
        return trade
    
    def __str__(self) -> str:
        """String representation of the trade."""
        status_str = f"{self.status.value}"
        if self.is_closed:
            status_str += f" ({self.result.value})"
        
        entry_str = f"{self.entry_price:.2f}" if self.entry_price else "N/A"
        exit_str = f"{self.exit_price:.2f}" if self.exit_price else "N/A"
        pl_str = f"{self.profit_loss_amount:.2f}" if self.profit_loss_amount is not None else "N/A"
        
        return (
            f"Trade {self.trade_id[:8]}: {self.symbol} {self.direction.value} "
            f"({self.strategy_name}) - {status_str}\n"
            f"Entry: {entry_str}, Exit: {exit_str}, P/L: {pl_str}"
        )
    
    def __repr__(self) -> str:
        """Representation of the trade."""
        return self.__str__()
