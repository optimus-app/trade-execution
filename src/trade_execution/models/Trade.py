from futu import *
from trade_execution.models.APIConnectInfo import APIConnectInfo
from trade_execution.models.Order import OrderSide
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class Trade:
    """
    Represents an executed trade
    """
    info: APIConnectInfo = APIConnectInfo.getInstance()
    code: str
    trade_id: str
    order_id: str
    side: OrderSide
    qty: int
    price: float
    trade_time: datetime
    counterparty: Optional[str] = None
    
    @classmethod
    def getTradesByOrderId(cls, order_id: str) -> List['Trade']:
        """
        Retrieves all trades associated with an order ID
        
        Args:
            order_id: The order ID to query
            
        Returns:
            List[Trade]: List of trades for the specified order
            
        Raises:
            Exception: If trade retrieval fails
        """
        info = APIConnectInfo.getInstance()
        ret, data = info.trade_context.deal_list_query(order_id=order_id)
        
        if ret != RET_OK:
            raise Exception(f"Failed to get trades for order {order_id}: {data}")
        
        trades = []
        for trade_data in data.itertuples():
            trades.append(cls(
                code=trade_data.code,
                trade_id=trade_data.deal_id,
                order_id=order_id,
                side=OrderSide.BUY if trade_data.trd_side == TrdSide.BUY else OrderSide.SELL,
                qty=trade_data.qty,
                price=trade_data.price,
                trade_time=datetime.strptime(trade_data.create_time, "%Y-%m-%d %H:%M:%S"),
                counterparty=trade_data.counterparty if hasattr(trade_data, 'counterparty') else None
            ))
        return trades
    
    @classmethod
    def getDailyTrades(cls, date: Optional[datetime] = None) -> List['Trade']:
        """
        Retrieves all trades for a specific date
        
        Args:
            date: The date to query (defaults to today)
            
        Returns:
            List[Trade]: List of trades for the specified date
            
        Raises:
            Exception: If trade retrieval fails
        """
        info = APIConnectInfo.getInstance()
        
        if date is None:
            date = datetime.now()
            
        date_str = date.strftime("%Y-%m-%d")
        
        ret, data = info.trade_context.history_deal_list_query(
            start=date_str,
            end=date_str
        )
        
        if ret != RET_OK:
            raise Exception(f"Failed to get trades for date {date_str}: {data}")
        
        trades = []
        for trade_data in data.itertuples():
            trades.append(cls(
                code=trade_data.code,
                trade_id=trade_data.deal_id,
                order_id=trade_data.order_id,
                side=OrderSide.BUY if trade_data.trd_side == TrdSide.BUY else OrderSide.SELL,
                qty=trade_data.qty,
                price=trade_data.price,
                trade_time=datetime.strptime(trade_data.create_time, "%Y-%m-%d %H:%M:%S"),
                counterparty=trade_data.counterparty if hasattr(trade_data, 'counterparty') else None
            ))
        return trades