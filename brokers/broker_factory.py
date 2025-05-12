"""
Broker factory for the BoringTrade trading bot.
"""
import logging
from typing import Dict, Any, Optional

from brokers.broker_interface import BrokerInterface
from brokers.tastytrade import TastytradeAPI
from brokers.schwab import SchwabAPI


class BrokerFactory:
    """
    Factory for creating broker instances.
    """
    
    @staticmethod
    def create_broker(
        broker_name: str,
        api_key: str,
        api_secret: str,
        **kwargs: Any
    ) -> BrokerInterface:
        """
        Create a broker instance.
        
        Args:
            broker_name: The name of the broker
            api_key: The API key
            api_secret: The API secret
            **kwargs: Additional broker-specific parameters
            
        Returns:
            BrokerInterface: The broker instance
            
        Raises:
            ValueError: If the broker is not supported
        """
        logger = logging.getLogger("BrokerFactory")
        
        # Create broker instance based on name
        if broker_name.lower() == "tastytrade":
            logger.info("Creating Tastytrade broker")
            return TastytradeAPI(api_key, api_secret, **kwargs)
        elif broker_name.lower() == "schwab":
            logger.info("Creating Schwab broker")
            return SchwabAPI(api_key, api_secret, **kwargs)
        else:
            error_msg = f"Unsupported broker: {broker_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
