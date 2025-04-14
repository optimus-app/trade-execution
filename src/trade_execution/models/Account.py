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
    
    def getPositions(self) -> List[Position]:
        """
        Retrieves all current positions in the account
        
        Returns:
            List[Position]: List of current positions
            
        Raises:
            Exception: If positions retrieval fails
        """
        ret, data = self.info.trade_context.position_list_query(refresh_cache=True)
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
            end=end_date.strftime("%Y-%m-%d")
        )
        if ret != RET_OK:
            raise Exception(f"Failed to get transaction history: {data}")
        return data.to_dict('records')