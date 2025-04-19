from trade_execution.strategies.base import StrategyBase
from trade_execution.models.Order import OrderSide
import pandas as pd
from typing import Optional, Dict, Any
from futu import KLType, RET_OK
from datetime import datetime, timedelta

class MovingAverageStrategy(StrategyBase):
    """
    Strategy based on moving average crossovers.
    When the short-term moving average crosses above the long-term moving average,
    it generates a buy signal. When it crosses below, it generates a sell signal.
    """
    
    def __init__(self, name: str = "Moving Average Crossover"):
        super().__init__(name)
        self.short_window = 20
        self.long_window = 50
    
    def setup(self, short_window: int = 20, long_window: int = 50, **kwargs):
        """
        Set up the strategy with parameters
        
        Args:
            short_window: Period for short-term moving average
            long_window: Period for long-term moving average
        """
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")
            
        self.short_window = short_window
        self.long_window = long_window
        self.parameters = {
            'short_window': short_window,
            'long_window': long_window
        }
    
    def generate_signal(self, data: pd.DataFrame) -> Optional[OrderSide]:
        """
        Generate trading signals based on moving average crossovers
        
        Args:
            data: Market data with price history
            
        Returns:
            Optional[OrderSide]: BUY when short MA crosses above long MA, 
                               SELL when short MA crosses below long MA,
                               None otherwise
        """
        # Check if we have enough data
        if len(data) < self.long_window:
            return None
        
        # Calculate moving averages
        short_ma = data['close'].rolling(window=self.short_window).mean()
        long_ma = data['close'].rolling(window=self.long_window).mean()
        
        # Check for crossover
        if len(short_ma) < 2 or len(long_ma) < 2:
            return None
            
        # Current situation
        current_short = short_ma.iloc[-1]
        current_long = long_ma.iloc[-1]
        
        # Previous situation
        prev_short = short_ma.iloc[-2]
        prev_long = long_ma.iloc[-2]
        
        # Generate signals
        if prev_short < prev_long and current_short > current_long:
            return OrderSide.BUY
        elif prev_short > prev_long and current_short < current_long:
            return OrderSide.SELL
            
        return None
    
    def run(self, code: str, is_backtest: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Run the moving average strategy
        
        Args:
            code: Security code
            is_backtest: Whether to run in backtest mode
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Results of the strategy execution
        """
        # Set up the strategy
        short_window = kwargs.get('short_window', self.short_window)
        long_window = kwargs.get('long_window', self.long_window)
        self.setup(short_window=short_window, long_window=long_window)
        
        # If backtest mode, run the backtest
        if is_backtest:
            from datetime import datetime
            start_date = kwargs.get('start_date', datetime.now() - timedelta(days=365))
            end_date = kwargs.get('end_date', datetime.now())
            return self.backtest(code, start_date, end_date, **kwargs)
        
        # For live trading
        # Get recent data
        data = self.get_historical_data(code, KLType.K_DAY, count=self.long_window + 10)
        
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