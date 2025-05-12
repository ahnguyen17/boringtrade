"""
Strategy factory for the BoringTrade trading bot.
"""
import logging
from typing import Dict, Any, Optional

from brokers.broker_interface import BrokerInterface
from data.data_feed import DataFeed
from strategies.base_strategy import BaseStrategy
from strategies.orb_strategy import ORBStrategy
from strategies.pdh_pdl_strategy import PDHPDLStrategy
from strategies.order_block_strategy import OrderBlockStrategy
from utils.notification import Notifier
from utils.risk_manager import RiskManager


class StrategyFactory:
    """
    Factory for creating strategy instances.
    """
    
    @staticmethod
    def create_strategy(
        strategy_name: str,
        data_feed: DataFeed,
        broker: BrokerInterface,
        risk_manager: RiskManager,
        notifier: Notifier,
        config: Dict[str, Any]
    ) -> BaseStrategy:
        """
        Create a strategy instance.
        
        Args:
            strategy_name: The name of the strategy
            data_feed: The data feed
            broker: The broker interface
            risk_manager: The risk manager
            notifier: The notifier
            config: The configuration
            
        Returns:
            BaseStrategy: The strategy instance
            
        Raises:
            ValueError: If the strategy is not supported
        """
        logger = logging.getLogger("StrategyFactory")
        
        # Create strategy instance based on name
        if strategy_name.upper() == "ORB":
            logger.info("Creating Opening Range Breakout strategy")
            return ORBStrategy(
                data_feed=data_feed,
                broker=broker,
                risk_manager=risk_manager,
                notifier=notifier,
                config=config
            )
        elif strategy_name.upper() == "PDH_PDL":
            logger.info("Creating Previous Day High/Low strategy")
            return PDHPDLStrategy(
                data_feed=data_feed,
                broker=broker,
                risk_manager=risk_manager,
                notifier=notifier,
                config=config
            )
        elif strategy_name.upper() == "OB":
            logger.info("Creating Order Block strategy")
            return OrderBlockStrategy(
                data_feed=data_feed,
                broker=broker,
                risk_manager=risk_manager,
                notifier=notifier,
                config=config
            )
        else:
            error_msg = f"Unsupported strategy: {strategy_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
