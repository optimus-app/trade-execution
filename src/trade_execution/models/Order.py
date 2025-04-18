from futu import *
from trade_execution.models.APIConnectInfo import APIConnectInfo
from pydantic import BaseModel
from typing import Optional, Dict, List
from enum import Enum

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"

class OrderStatus(str, Enum):
    UNSUBMITTED = "UNSUBMITTED"
    WAITING_SUBMIT = "WAITING_SUBMIT"
    SUBMITTED = "SUBMITTED"
    FILLED_PART = "FILLED_PART"
    FILLED_ALL = "FILLED_ALL"
    CANCELLED_PART = "CANCELLED_PART"
    CANCELLED_ALL = "CANCELLED_ALL"
    FAILED = "FAILED"
    DISABLED = "DISABLED"
    DELETED = "DELETED"

class Order:
    """
    Represents a trading order with execution details
    """
    info: APIConnectInfo = APIConnectInfo.getInstance()
    code: str
    side: OrderSide
    qty: int
    price: Optional[float] = None
    order_type: OrderType = OrderType.LIMIT
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.UNSUBMITTED
    create_time: Optional[str] = None
    update_time: Optional[str] = None
    remark: Optional[str] = None

    def __init__(
        self,
        code: str,
        side: OrderSide,
        qty: int,
        price: Optional[float] = None,
        order_type: OrderType = OrderType.LIMIT,
        order_id: Optional[str] = None,
        status: OrderStatus = OrderStatus.UNSUBMITTED,
        create_time: Optional[str] = None,
        update_time: Optional[str] = None,
        remark: Optional[str] = None
        ):
        self.code = code
        self.side = side
        self.qty = qty
        self.price = price
        self.order_type = order_type
        self.order_id = order_id
        self.status = status
        self.create_time = create_time
        self.update_time = update_time
        self.remark = remark
        self.info = APIConnectInfo.getInstance()
    
    def submit(self) -> str:
        """
        Submits the order to the market
        
        Returns:
            str: Order ID if successful
            
        Raises:
            Exception: If order submission fails
        """
        if self.order_type == OrderType.MARKET:
            ret, data = self.info.trade_context.place_order(
                price=0.0,
                qty=self.qty,
                code=self.code,
                trd_side=TrdSide.BUY if self.side == OrderSide.BUY else TrdSide.SELL,
                trd_env=TrdEnv.SIMULATE
            )
        else:
            if not self.price:
                raise ValueError("Price must be specified for limit orders")
                
            ret, data = self.info.trade_context.place_order(
                price=self.price,
                qty=self.qty,
                code=self.code,
                trd_side=TrdSide.BUY if self.side == OrderSide.BUY else TrdSide.SELL,
                trd_env=TrdEnv.SIMULATE
            )
            
        if ret != RET_OK:
            raise Exception(f"Failed to place order: {data}")
            
        self.order_id = data['order_id'][0]
        self.status = OrderStatus.SUBMITTED
        return self.order_id
    
    def cancel(self) -> bool:
        """
        Cancels the order if possible
        
        Returns:
            bool: True if successful
            
        Raises:
            Exception: If order cancellation fails
        """
        if not self.order_id:
            raise ValueError("Cannot cancel order without order_id")
        
        ret, data = self.info.trade_context.modify_order(
            modify_order_op=ModifyOrderOp.CANCEL,
            order_id=self.order_id,
            qty=self.qty,
            price=self.price or 0.0
        )
        
        if ret != RET_OK:
            raise Exception(f"Failed to cancel order: {data}")
        
        self.status = OrderStatus.CANCELLED_ALL
        return True
    
    def modifyOrder(self, new_price: Optional[float] = None, new_qty: Optional[int] = None) -> bool:
        """
        Modifies the order with new price or quantity
        
        Args:
            new_price: New price for the order
            new_qty: New quantity for the order
            
        Returns:
            bool: True if successful
            
        Raises:
            Exception: If order modification fails
        """
        if not self.order_id:
            raise ValueError("Cannot modify order without order_id")
        
        ret, data = self.info.trade_context.modify_order(
            modify_order_op=ModifyOrderOp.NORMAL,
            order_id=self.order_id,
            qty=new_qty or self.qty,
            price=new_price or self.price or 0.0
        )
        
        if ret != RET_OK:
            raise Exception(f"Failed to modify order: {data}")
        
        if new_price:
            self.price = new_price
        if new_qty:
            self.qty = new_qty
            
        return True
    
    @classmethod
    def getOrderById(cls, order_id: str) -> 'Order':
        """
        Retrieves an order by its ID
        
        Args:
            order_id: The order ID to retrieve
            
        Returns:
            Order: The retrieved order
            
        Raises:
            Exception: If order retrieval fails
        """
        info = APIConnectInfo.getInstance()
        ret, data = info.trade_context.order_list_query(order_id=order_id, trd_env=info.TRADING_ENV)
        
        if ret != RET_OK:
            raise Exception(f"Failed to get order: {data}")
        
        if len(data) == 0:
            raise ValueError(f"Order with ID {order_id} not found")
        
        order_data = data.iloc[0]
        
        return cls(
            code=order_data['code'],
            side=OrderSide.BUY if order_data['trd_side'] == TrdSide.BUY else OrderSide.SELL,
            qty=order_data['qty'],
            price=order_data['price'],
            order_type=OrderType.LIMIT if order_data['order_type'] == OrderType.LIMIT else OrderType.MARKET,
            order_id=order_id,
            status=OrderStatus(order_data['order_status']),
            create_time=order_data['create_time'],
        )