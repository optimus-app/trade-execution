from pydantic import BaseModel
from typing import Optional
from futu import *
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('trade_execution.models.APIConnectInfo')

class APIConnectInfo():
    FUTU_OPEND_ADDRESS: Optional[str] = "127.0.0.1"
    FUTU_OPEND_PORT: Optional[int] = 11111

    TRADING_ENV: TrdEnv = TrdEnv.SIMULATE
    TRADING_MARKET: TrdMarket = TrdMarket.HK
    TRADING_PWD: str = "123456"
    TRADING_PERIOD: str = "1d"

    quote_context: Optional[OpenQuoteContext] = None
    trade_context: Optional[OpenSecTradeContext] = None

    _instance = None

    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info(f"Initializing APIConnectInfo with address={self.FUTU_OPEND_ADDRESS}, port={self.FUTU_OPEND_PORT}")
        
        if not self.quote_context:
            logger.info("Creating new QuoteContext connection")
            self.quote_context = OpenQuoteContext(
                host=self.FUTU_OPEND_ADDRESS, 
                port=self.FUTU_OPEND_PORT
            )
            
        if not self.trade_context:
            logger.info("Creating new TradeContext connection")
            self.trade_context = OpenSecTradeContext(
                host=self.FUTU_OPEND_ADDRESS, 
                port=self.FUTU_OPEND_PORT
            )
        
        logger.info(f"APIConnectInfo initialized with trading environment: {self.TRADING_ENV}")

    # Singleton pattern
    @classmethod
    def getInstance(cls, **kwargs):
        if not cls._instance:
            logger.info("Creating new APIConnectInfo instance")
            cls._instance = cls(**kwargs)
        else:
            logger.info("Returning existing APIConnectInfo instance")
            # Update instance if new kwargs provided
            if kwargs:
                logger.info(f"Updating existing instance with new parameters: {kwargs}")
                for key, value in kwargs.items():
                    setattr(cls._instance, key, value)
        
        return cls._instance