"""
Risk management utility for the BoringTrade trading bot.
"""
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple

from models.trade import Trade, TradeStatus, TradeResult
from models.asset import Asset, AssetType


class RiskManager:
    """
    Manages risk for the trading bot.
    """

    def __init__(
        self,
        risk_per_trade: float = 0.01,
        max_daily_loss: float = 0.03,
        max_daily_profit: Optional[float] = None,
        max_trades_per_day: int = 3
    ):
        """
        Initialize the risk manager.

        Args:
            risk_per_trade: Maximum risk per trade as a percentage of account equity
            max_daily_loss: Maximum daily loss as a percentage of account equity
            max_daily_profit: Maximum daily profit as a percentage of account equity
            max_trades_per_day: Maximum number of trades per day
        """
        self.risk_per_trade = risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.max_daily_profit = max_daily_profit
        self.max_trades_per_day = max_trades_per_day
        self.logger = logging.getLogger("RiskManager")

        # Track trades by date
        self.trades_by_date: Dict[date, List[Trade]] = {}

        # Track account equity
        self.initial_equity: Optional[float] = None
        self.current_equity: Optional[float] = None

    def set_account_equity(self, equity: float) -> None:
        """
        Set the current account equity.

        Args:
            equity: The current account equity
        """
        if self.initial_equity is None:
            self.initial_equity = equity

        self.current_equity = equity
        self.logger.info(f"Account equity updated: {equity:.2f}")

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        max_contracts: Optional[int] = None,
        asset: Optional[Asset] = None
    ) -> Tuple[int, float]:
        """
        Calculate the appropriate position size based on risk parameters.

        Args:
            symbol: The asset symbol
            entry_price: The entry price
            stop_loss: The stop loss price
            max_contracts: Maximum number of contracts to trade
            asset: Optional asset information

        Returns:
            Tuple[int, float]: The position size (contracts) and risk amount
        """
        if self.current_equity is None:
            self.logger.warning("Account equity not set. Using default position size of 1.")
            return 1, abs(entry_price - stop_loss)

        # Calculate risk per contract
        price_difference = abs(entry_price - stop_loss)

        # Apply multiplier for futures contracts
        multiplier = 1.0
        if asset and asset.is_futures:
            multiplier = asset.multiplier
            self.logger.debug(f"Using futures multiplier: {multiplier} for {symbol}")

        risk_per_contract = price_difference * multiplier

        # Calculate maximum risk amount
        max_risk_amount = self.current_equity * self.risk_per_trade

        # Calculate position size
        if risk_per_contract > 0:
            position_size = max_risk_amount / risk_per_contract
            position_size = int(position_size)  # Round down to nearest integer
        else:
            self.logger.warning("Risk per contract is zero. Using default position size of 1.")
            position_size = 1

        # Apply maximum contracts limit if specified
        if max_contracts is not None and position_size > max_contracts:
            position_size = max_contracts

        # Ensure position size is at least 1
        position_size = max(1, position_size)

        # Calculate actual risk amount
        risk_amount = position_size * risk_per_contract

        self.logger.info(
            f"Position size for {symbol}: {position_size} contracts "
            f"(risk: {risk_amount:.2f}, {(risk_amount / self.current_equity):.2%} of equity)"
        )

        return position_size, risk_amount

    def can_place_trade(
        self,
        symbol: str,
        risk_amount: float,
        strategy_name: str
    ) -> Tuple[bool, str]:
        """
        Check if a trade can be placed based on risk parameters.

        Args:
            symbol: The asset symbol
            risk_amount: The risk amount for the trade
            strategy_name: The name of the strategy

        Returns:
            Tuple[bool, str]: Whether the trade can be placed and the reason if not
        """
        today = datetime.now().date()

        # Check if we have trades for today
        if today not in self.trades_by_date:
            self.trades_by_date[today] = []

        # Get today's trades
        today_trades = self.trades_by_date[today]

        # Check maximum trades per day
        if len(today_trades) >= self.max_trades_per_day:
            reason = f"Maximum trades per day ({self.max_trades_per_day}) reached"
            self.logger.warning(f"Cannot place trade: {reason}")
            return False, reason

        # Check if account equity is set
        if self.current_equity is None:
            self.logger.warning("Account equity not set. Allowing trade with caution.")
            return True, ""

        # Calculate today's P/L
        today_pl = sum(
            trade.profit_loss_amount or 0
            for trade in today_trades
            if trade.is_closed
        )

        # Check maximum daily loss
        max_loss_amount = self.current_equity * self.max_daily_loss
        if today_pl < -max_loss_amount:
            reason = f"Maximum daily loss ({self.max_daily_loss:.2%}) reached"
            self.logger.warning(f"Cannot place trade: {reason}")
            return False, reason

        # Check maximum daily profit if set
        if self.max_daily_profit is not None:
            max_profit_amount = self.current_equity * self.max_daily_profit
            if today_pl > max_profit_amount:
                reason = f"Maximum daily profit ({self.max_daily_profit:.2%}) reached"
                self.logger.warning(f"Cannot place trade: {reason}")
                return False, reason

        # Check risk per trade
        max_risk_amount = self.current_equity * self.risk_per_trade
        if risk_amount > max_risk_amount:
            reason = f"Risk amount ({risk_amount:.2f}) exceeds maximum risk per trade ({max_risk_amount:.2f})"
            self.logger.warning(f"Cannot place trade: {reason}")
            return False, reason

        self.logger.info(
            f"Trade allowed for {symbol} ({strategy_name}): "
            f"risk amount {risk_amount:.2f}, today's P/L {today_pl:.2f}"
        )

        return True, ""

    def register_trade(self, trade: Trade) -> None:
        """
        Register a trade with the risk manager.

        Args:
            trade: The trade to register
        """
        # Get the trade date
        trade_date = (trade.entry_time or datetime.now()).date()

        # Initialize the date entry if it doesn't exist
        if trade_date not in self.trades_by_date:
            self.trades_by_date[trade_date] = []

        # Add the trade to the list
        self.trades_by_date[trade_date].append(trade)

        self.logger.info(f"Trade registered: {trade}")

    def update_trade(self, trade: Trade) -> None:
        """
        Update a registered trade.

        Args:
            trade: The updated trade
        """
        # Find the trade in the registry
        for date_trades in self.trades_by_date.values():
            for i, registered_trade in enumerate(date_trades):
                if registered_trade.trade_id == trade.trade_id:
                    # Update the trade
                    date_trades[i] = trade
                    self.logger.info(f"Trade updated: {trade}")
                    return

        # If the trade wasn't found, register it
        self.register_trade(trade)

    def get_daily_summary(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of trades for a specific date.

        Args:
            date_str: The date string (YYYY-MM-DD) or None for today

        Returns:
            Dict[str, Any]: The daily summary
        """
        # Parse date or use today
        if date_str:
            summary_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            summary_date = datetime.now().date()

        # Get trades for the date
        trades = self.trades_by_date.get(summary_date, [])

        # Calculate statistics
        total_trades = len(trades)
        closed_trades = [trade for trade in trades if trade.is_closed]
        winning_trades = [
            trade for trade in closed_trades
            if trade.result == TradeResult.WIN
        ]
        losing_trades = [
            trade for trade in closed_trades
            if trade.result == TradeResult.LOSS
        ]
        breakeven_trades = [
            trade for trade in closed_trades
            if trade.result == TradeResult.BREAKEVEN
        ]

        # Calculate P/L
        total_pl = sum(
            trade.profit_loss_amount or 0
            for trade in closed_trades
        )

        # Calculate win rate
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0

        # Create summary
        summary = {
            "date": summary_date.isoformat(),
            "total_trades": total_trades,
            "closed_trades": len(closed_trades),
            "open_trades": total_trades - len(closed_trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "breakeven_trades": len(breakeven_trades),
            "total_profit_loss": total_pl,
            "win_rate": win_rate,
            "trades": [trade.to_dict() for trade in trades]
        }

        return summary

    def get_all_trades(self) -> List[Trade]:
        """
        Get all registered trades.

        Returns:
            List[Trade]: All registered trades
        """
        all_trades = []
        for date_trades in self.trades_by_date.values():
            all_trades.extend(date_trades)

        return all_trades
