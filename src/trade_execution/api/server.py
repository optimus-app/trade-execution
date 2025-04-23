from futu import SubType, RET_OK
from fastapi import APIRouter, FastAPI, Depends, HTTPException, Query, Path, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from trade_execution.models.Order import Order, OrderSide, OrderType
from trade_execution.models.Account import Account
from trade_execution.models.OrderBook import OrderBook
from trade_execution.models.Trade import Trade
from trade_execution.models.ConnectionManager import ConnectionManager
from trade_execution.handlers.order_status_handler import OrderStatusHandler
from trade_execution.handlers.order_handler import OrderHandler
from trade_execution.models.APIConnectInfo import APIConnectInfo

from trade_execution.strategies.moving_average import MovingAverageStrategy
from trade_execution.strategies.mean_reversion import MeanReversionStrategy
from trade_execution.handlers.order_book_handler import OrderBookHandler

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('trade_execution.api.server')
import asyncio

class BacktestRequest(BaseModel):
    symbol: str
    strategy_id: str
    start_date: datetime = Field(default_factory=lambda: datetime.now() - timedelta(days=365))
    end_date: datetime = Field(default_factory=lambda: datetime.now())
    initial_capital: float = 10000.0
    parameters: Dict[str, Any] = {}
class OrderRequest(BaseModel):
    code: str
    side: str
    qty: int
    price: Optional[float] = None
    order_type: OrderType = OrderType.LIMIT
    remark: Optional[str] = None

class OrderResponse(BaseModel):
    order_id: str
    code: str
    side: OrderSide
    qty: int
    price: Optional[float]
    order_type: OrderType
    status: str
    create_time: Optional[str]

class HistoryRequest(BaseModel):
    start_date: datetime = Field(default_factory=lambda: datetime.now() - timedelta(days=30))
    end_date: datetime = Field(default_factory=lambda: datetime.now())
    limit: int = 100

class StrategyRequest(BaseModel):
    code: str
    strategy_id: str
    is_backtest: bool = False
    parameters: Dict[str, Any] = {}

# Create router
router = APIRouter()

# Strategy mapping
STRATEGY_MAP = {
    "moving_average": MovingAverageStrategy(),
    "mean_reversion": MeanReversionStrategy(),
    # "momentum": MomentumStrategy()
}

@router.websocket("/ws/orderbook")
async def websocket_orderbook_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time order book updates"""
    connection_manager = ConnectionManager.getInstance()
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive with ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await connection_manager.disconnect(websocket)

@router.websocket("/ws/orders")
async def websocket_order_updates(websocket: WebSocket):
    """WebSocket endpoint for real-time order status updates"""
    connection_manager = ConnectionManager.getInstance()
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive with ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await connection_manager.disconnect(websocket)

# Trade endpoints
@router.post("/trade/order", response_model=OrderResponse)
async def place_order(order_request: OrderRequest):
    """Place a new order"""
    try:
        order = Order(
            code=order_request.code,
            side=order_request.side,
            qty=order_request.qty,
            price=order_request.price,
            order_type=order_request.order_type,
            remark=order_request.remark
        )
        
        order_id = order.submit()

        await OrderStatusHandler.process_order_update({
            "order_id": order_id,
            "code": order.code,
            "order_status": "SUBMITTED",
            "qty": order.qty,
            "price": order.price,
            "trd_side": order.side,
        })
        
        return OrderResponse(
            order_id=order_id,
            code=order.code,
            side=order.side,
            qty=order.qty,
            price=order.price,
            order_type=order.order_type,
            status="SUBMITTED",
            create_time=datetime.now().isoformat()
        )

        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/trade/order/{order_id}")
async def cancel_order(order_id: str = Path(..., description="The ID of the order to cancel")):
    """Cancel an existing order"""
    try:
        order = Order.getOrderById(order_id)
        # TODO: Unlock trade first
        result = order.cancel()
        return {"message": "Order cancelled successfully", "order_id": order_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trade/order/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str = Path(..., description="The ID of the order to retrieve")):
    """Get order details by ID"""
    try:
        logger.debug(f"order_id: {order_id}")
        order = Order.getOrderById(order_id)
        return OrderResponse(
            order_id=order.order_id,
            code=order.code,
            side=order.side,
            qty=order.qty,
            price=order.price,
            order_type=order.order_type,
            status=order.status.value,
            create_time=order.create_time
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# TODO: Implement order history retrieval
# TODO: Check Orders Push Callback
# TODO: Get open orders
# TODO: Get trading account lists
# TODO: Test US market TrdMarket.US if available in a simulated environment

# Account endpoints
@router.get("/account/balance")
async def get_account_balance():
    """Get account balance and information"""
    try:
        logger.info("Fetching account balance...")
        account = Account()
        logger.info("Account() object created")
        balance = account.getBalance()
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MarketPositionRequest(BaseModel):
    acc_id: Optional[int] = None
    trd_mkt: Optional[str] = None  # HK, US, CN, etc.
    pl_ratio_min: Optional[float] = None
    pl_ratio_max: Optional[float] = None
    refresh_cache: bool = False

@router.post("/market/positions")
async def get_market_positions(request: MarketPositionRequest):
    """Get current positions in simulated market environment"""
    try:
        account = Account()
        # Force simulation environment
        positions = account.getPositions(
            trd_env="SIMULATE",
            trd_mkt=request.trd_mkt,
            pl_ratio_min=request.pl_ratio_min,
            pl_ratio_max=request.pl_ratio_max,
            refresh_cache=request.refresh_cache
        )
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/account/history")
async def get_transaction_history(request: HistoryRequest):
    """Get transaction history"""
    try:
        account = Account()
        history = account.getTransactionHistory(request.start_date, request.end_date)
        return {"transactions": history[:request.limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/account/historicalOrders")
async def get_historical_orders(request: HistoryRequest):
    try:
        account = Account()
        history = account.getHistoricalOrders(request.start_date, request.end_date)
        return {"orders": history[:request.limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Strategy endpoints
@router.post("/strategy/run")
async def run_strategy(request: StrategyRequest):
    """Run a trading strategy"""
    try:
        if request.strategy_id not in STRATEGY_MAP:
            raise HTTPException(status_code=404, detail=f"Strategy {request.strategy_id} not found")
            
        strategy = STRATEGY_MAP[request.strategy_id]
        result = strategy.run(
            code=request.code, 
            is_backtest=request.is_backtest,
            **request.parameters
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategy/list")
async def list_strategies():
    """List available trading strategies"""
    return {
        "strategies": [
            {"id": "moving_average", "name": "Moving Average Crossover", "description": "Strategy based on moving average crossovers"},
            {"id": "mean_reversion", "name": "Mean Reversion", "description": "Mean reversion strategy based on Bollinger Bands"},
            {"id": "momentum", "name": "RSI Momentum", "description": "Momentum trading strategy based on Relative Strength Index (RSI)"}
        ]
    }

# Market data endpoints
@router.get("/market/orderbook/{code}")
async def get_order_book(code: str = Path(..., description="The security code")):
    """Get order book for a security"""
    try:
        orderbook = OrderBook()
        data = orderbook.getOrderBook(code)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run a backtest with the specified strategy and parameters"""
    try:
        from trade_execution.services.backtest_service import BacktestService
        import math
        import numpy as np
        
        # Map the strategy_id from the request to an actual strategy
        strategy_mapping = {
            "moving_average": "sma_crossover",
            "mean_reversion": "mean_reversion"
            # Add more strategy mappings as they become available
        }
        
        if request.strategy_id not in strategy_mapping:
            raise HTTPException(
                status_code=404, 
                detail=f"Strategy {request.strategy_id} not found"
            )
            
        # Run the backtest
        result = BacktestService.run_backtest(
            strategy_id=strategy_mapping[request.strategy_id],
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            parameters=request.parameters
        )
        
        # Sanitize the result to handle special float values before JSON serialization
        def sanitize_json(obj):
            if isinstance(obj, dict):
                return {k: sanitize_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_json(item) for item in obj]
            elif isinstance(obj, (float, np.float64, np.float32)):
                if math.isnan(obj) or math.isinf(obj):
                    return None
                return float(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            return obj
        
        sanitized_result = sanitize_json(result)
        return sanitized_result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Main FastAPI application
def create_app():
    app = FastAPI(
        title="Trading Execution API",
        description="API for algorithmic and manual trading",
        version="0.1.0"
    )
    
    app.include_router(router, prefix="/api/v1")

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting up Trading Execution API...")
        api_info = APIConnectInfo.getInstance()
        
        # Get the current event loop
        loop = asyncio.get_running_loop()
        
        # Register the OrderHandler with the trade context
        order_status_handler = OrderStatusHandler()
        order_handler = OrderHandler(order_status_handler, loop=loop)
        api_info.trade_context.set_handler(order_handler)
        logger.info("Order status handlers registered with Futu API")
        
        # Subscribe to HK.00700 order book
        try:
            # Create order book handler
            order_book_handler = OrderBookHandler(loop=loop)
            api_info.quote_context.set_handler(order_book_handler)
            
            # Subscribe to order book for HK.00700
            ret, data = api_info.quote_context.subscribe(['HK.00700'], [SubType.ORDER_BOOK])
            if ret != RET_OK:
                logger.error(f"Failed to subscribe to HK.00700 order book: {data}")
            else:
                logger.info("Successfully subscribed to HK.00700 order book")
        except Exception as e:
            logger.error(f"Error setting up order book subscription: {str(e)}")
    
    @app.get("/")
    async def root():
        return {"message": "Trading Execution API is running. Visit /docs for documentation."}
    
    return app