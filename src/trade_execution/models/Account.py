from futu import *
from trade_execution.models.APIConnectInfo import APIConnectInfo
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('trade_execution.models.APIConnectInfo')

class Position(BaseModel):
    """Model representing a position in a security"""
    code: str
    quantity: float
    avg_price: float
    market_value: float
    unrealized_pl: float
    pl_ratio: float
    
class Account():
    """
    Represents a trading account with balance and positions information
    """
    def __init__(self):
        self.info: APIConnectInfo = APIConnectInfo.getInstance()
        self.account_id: Optional[str] = None
    
    def getBalance(self) -> Dict:
        """
        Retrieves the current account balance and related information
        
        Returns:
            Dict: Account balance information
            
        Raises:
            Exception: If balance retrieval fails
        """
        logger.info("Fet")
        ret, data = self.info.trade_context.accinfo_query()
        if ret != RET_OK:
            raise Exception(f"Failed to get account info: {data}")
        return data
    

    def getPositions(self, trd_env=None, acc_id=None, trd_mkt=None, pl_ratio_min=None, pl_ratio_max=None, refresh_cache=True) -> List[Position]:
        """
        Retrieves all current positions in the account
        
        Args:
            trd_env (str, optional): Trading environment. Default is None (uses APIConnectInfo default)
            acc_id (int, optional): Account ID. Default is None (uses default account)
            trd_mkt (str, optional): Trading market. Default is None (all markets)
            pl_ratio_min (float, optional): Minimum P/L ratio filter. Default is None
            pl_ratio_max (float, optional): Maximum P/L ratio filter. Default is None
            refresh_cache (bool, optional): Whether to refresh cache. Default is True
            
        Returns:
            List[Position]: List of current positions
            
        Raises:
            Exception: If positions retrieval fails
        """
        # Use default trading environment from APIConnectInfo if not specified
        if trd_env is None:
            trd_env = self.info.TRADING_ENV
            
        # Build query parameters
        query_params = {'refresh_cache': refresh_cache, 'trd_env': trd_env}
        
        # Add optional filters if provided
        if acc_id is not None:
            query_params['acc_id'] = acc_id
        if trd_mkt is not None:
            query_params['position_market'] = trd_mkt
        if pl_ratio_min is not None:
            query_params['pl_ratio_min'] = pl_ratio_min
        if pl_ratio_max is not None:
            query_params['pl_ratio_max'] = pl_ratio_max
        
        ret, data = self.info.trade_context.position_list_query(**query_params)
        if ret != RET_OK:
            raise Exception(f"Failed to get positions: {data}")
            
        positions = []
        for pos in data.itertuples():
            positions.append(Position(
                code=pos.code,
                quantity=pos.qty,
                avg_price=pos.cost_price,
                market_value=pos.market_val,
                unrealized_pl=pos.pl_val,
                pl_ratio=pos.pl_ratio
            ))
        return positions
    
    def getTransactionHistory(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Retrieves transaction history for a given date range
        
        Args:
            start_date: Start date for transaction history
            end_date: End date for transaction history
            
        Returns:
            List[Dict]: List of transactions
            
        Raises:
            Exception: If transaction history retrieval fails
        """
        ret, data = self.info.trade_context.history_deal_list_query(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            trd_env=self.info.TRADING_ENV
        )
        if ret != RET_OK:
            raise Exception(f"Failed to get transaction history: {data}")
        return data.to_dict('records')
    
    def getHistoricalOrders(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        ret, data = self.info.trade_context.history_order_list_query(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            trd_env=self.info.TRADING_ENV
        )
        if ret != RET_OK:
            raise Exception(f"Failed to get historical orders: {data}")
        return data.to_dict('records')