from trade_execution.strategies.base import StrategyBase
from trade_execution.models.Order import OrderSide
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from futu import KLType, RET_OK
from datetime import datetime, timedelta

class MeanReversionStrategy(StrategyBase):
    """
    Mean reversion strategy based on Bollinger Bands.
    
    Buy when price goes below lower band (oversold) and 
    sell when price goes above upper band (overbought).
    """
    
    def __init__(self, name: str = "Mean Reversion"):
        super().__init__(name)
        self.window = 20
        self.num_std = 2.0
    
    def setup(self, window: int = 20, num_std: float = 2.0, **kwargs):
        """
        Set up the strategy with parameters
        
        Args:
            window: Lookback period for calculating mean and standard deviation
            num_std: Number of standard deviations for the bands
        """
        self.window = window
        self.num_std = num_std
        self.parameters = {
            'window': window,
            'num_std': num_std
        }
    
    def generate_signal(self, data: pd.DataFrame) -> Optional[OrderSide]:
        """
        Generate trading signals based on Bollinger Bands
        
        Args:
            data: Market data with price history
            
        Returns:
            Optional[OrderSide]: BUY when price crosses below lower band, 
                               SELL when price crosses above upper band,
                               None otherwise
        """
        # Check if we have enough data
        if len(data) < self.window:
            return None
        
        # Calculate moving average
        data['ma'] = data['close'].rolling(window=self.window).mean()
        
        # Calculate standard deviation
        data['std'] = data['close'].rolling(window=self.window).std()
        
        # Calculate Bollinger Bands
        data['upper_band'] = data['ma'] + (data['std'] * self.num_std)
        data['lower_band'] = data['ma'] - (data['std'] * self.num_std)
        
        # Current price
        current_price = data['close'].iloc[-1]
        
        # Previous price
        prev_price = data['close'].iloc[-2]
        
        # Current bands
        current_lower = data['lower_band'].iloc[-1]
        current_upper = data['upper_band'].iloc[-1]
        
        # Previous bands
        prev_lower = data['lower_band'].iloc[-2]
        prev_upper = data['upper_band'].iloc[-2]
        
        # Generate signals
        if prev_price >= prev_lower and current_price < current_lower:
            return OrderSide.BUY
        elif prev_price <= prev_upper and current_price > current_upper:
            return OrderSide.SELL
            
        return None
    
    def run(self, code: str, is_backtest: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Run the mean reversion strategy
        
        Args:
            code: Security code
            is_backtest: Whether to run in backtest mode
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Results of the strategy execution
        """
        # Set up the strategy
        window = kwargs.get('window', self.window)
        num_std = kwargs.get('num_std', self.num_std)
        self.setup(window=window, num_std=num_std)
        
        # If backtest mode, run the backtest
        if is_backtest:
            from datetime import datetime
            start_date = kwargs.get('start_date', datetime.now() - timedelta(days=365))
            end_date = kwargs.get('end_date', datetime.now())
            return self.backtest(code, start_date, end_date, **kwargs)
        
        # For live trading
        # Get recent data
        data = self.get_historical_data(code, KLType.K_DAY, count=self.window + 10)
        
        # Generate signal
        signal = self.generate_signal(data)
        
        # Execute trade based on signal
        if signal:
            qty = kwargs.get('qty', 100)
            price = kwargs.get('price', None)
            order = self.place_order(code, signal, qty, price)
            return {
                "strategy": self.name,
                "signal": signal.value,
                "order_id": order.order_id,
                "parameters": self.parameters,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "strategy": self.name,
                "signal": "HOLD",
                "parameters": self.parameters,
                "timestamp": datetime.now().isoformat()
            }