from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from trade_execution.models.Order import Order, OrderSide
from trade_execution.models.APIConnectInfo import APIConnectInfo
from futu import *
import pandas as pd
from datetime import datetime, timedelta

class StrategyBase(ABC):
    """
    Base abstract class for all trading strategies
    """
    def __init__(self, name: str):
        self.name = name
        self.info = APIConnectInfo.getInstance()
        self.parameters = {}
    
    @abstractmethod
    def setup(self, **kwargs):
        """
        Set up the strategy with parameters
        
        Args:
            **kwargs: Strategy-specific parameters
        """
        pass
    
    @abstractmethod
    def run(self, code: str, is_backtest: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Run the strategy
        
        Args:
            code: Security code to trade
            is_backtest: Whether to run in backtest mode
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Results of the strategy execution
        """
        pass
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Optional[OrderSide]:
        """
        Generate trading signals based on market data
        
        Args:
            data: Market data for analysis
            
        Returns:
            Optional[OrderSide]: Trading signal (BUY, SELL, or None for no action)
        """
        pass
    
    def get_historical_data(self, code: str, period: str, count: int = 100) -> pd.DataFrame:
        """
        Fetch historical k-line data
        
        Args:
            code: Security code
            period: K-line period (e.g., KLType.K_1M, KLType.K_DAY)
            count: Number of k-lines to fetch
            
        Returns:
            pd.DataFrame: Historical k-line data
        """
        ret, data = self.info.quote_context.get_cur_kline(code=code, num=count, ktype=period)
        if ret != RET_OK:
            raise Exception(f"Failed to get historical data: {data}")
        return data
    
    def place_order(self, code: str, side: OrderSide, qty: int, price: Optional[float] = None, is_backtest: Optional[bool] = True) -> Order:
        """
        Place an order based on the strategy signal
        
        Args:
            code: Security code
            side: Order side (BUY/SELL)
            qty: Order quantity
            price: Order price (None for market order)
            
        Returns:
            Order: The placed order
        """
        order = Order(
            code=code,
            side=side,
            qty=qty,
            price=price,
            order_type=OrderType.LIMIT if price else OrderType.MARKET
        )
        
        if not is_backtest:
            order.submit()
        
        return order
    
    def backtest(self, code: str, start_date: datetime, end_date: datetime, **kwargs) -> Dict[str, Any]:
        """
        Run a backtest for the strategy
        
        Args:
            code: Security code
            start_date: Start date for backtest
            end_date: End date for backtest
            **kwargs: Strategy-specific parameters
            
        Returns:
            Dict[str, Any]: Backtest results including performance metrics
        """
        # Set up the strategy with parameters
        self.setup(**kwargs)
        
        # Get historical data for the backtest period
        days_diff = (end_date - start_date).days
        ret, data = self.info.quote_context.get_history_kline(
            code=code, 
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            ktype=KLType.K_DAY
        )
        
        if ret != RET_OK:
            raise Exception(f"Failed to get historical data: {data}")
            
        # Initialize backtest variables
        initial_capital = kwargs.get('initial_capital', 100000)
        capital = initial_capital
        shares = 0
        trades = []
        equity_curve = []
        
        # Run the strategy on each day
        for i in range(len(data)):
            date = data.iloc[i]['time_key']
            price = data.iloc[i]['close']
            
            # Create a window of data for signal generation
            lookback = min(i, 50)  # Use up to 50 days of lookback
            window_data = data.iloc[i-lookback:i+1]
            
            # Generate signal
            signal = self.generate_signal(window_data)
            
            # Execute trades based on signals
            if signal == OrderSide.BUY and shares == 0:
                # Calculate shares to buy (use 90% of capital)
                buy_amount = capital * 0.9
                shares = int(buy_amount / price)
                trade_value = shares * price
                capital -= trade_value
                trades.append({
                    'date': date,
                    'action': 'BUY',
                    'price': price,
                    'shares': shares,
                    'value': trade_value,
                    'capital': capital
                })
            
            elif signal == OrderSide.SELL and shares > 0:
                # Sell all shares
                trade_value = shares * price
                capital += trade_value
                trades.append({
                    'date': date,
                    'action': 'SELL',
                    'price': price,
                    'shares': shares,
                    'value': trade_value,
                    'capital': capital
                })
                shares = 0
            
            # Update equity curve
            equity = capital + (shares * price)
            equity_curve.append({
                'date': date,
                'equity': equity,
                'price': price
            })
        
        # Calculate performance metrics
        final_equity = equity_curve[-1]['equity']
        total_return = (final_equity / initial_capital - 1) * 100
        
        # Calculate drawdown
        max_equity = initial_capital
        max_drawdown = 0
        for point in equity_curve:
            if point['equity'] > max_equity:
                max_equity = point['equity']
            drawdown = (max_equity - point['equity']) / max_equity * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'strategy': self.name,
            'code': code,
            'start_date': start_date.strftime("%Y-%m-%d"),
            'end_date': end_date.strftime("%Y-%m-%d"),
            'initial_capital': initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'trades': trades,
            'equity_curve': equity_curve,
            'parameters': self.parameters
        }