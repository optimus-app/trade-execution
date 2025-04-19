import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger('trade_execution.services.backtest_service')

class BacktestService:
    @staticmethod
    def fetch_data(symbol: str, start_date: datetime, end_date: datetime) -> pd.Series:
        """Fetch historical price data for a symbol"""
        logger.info(f"Fetching data for {symbol} from {start_date} to {end_date}")
        data = yf.download(symbol, start=start_date.strftime('%Y-%m-%d'), 
                          end=end_date.strftime('%Y-%m-%d'), auto_adjust=False)
        if isinstance(data.columns, pd.MultiIndex):
            return data['Adj Close', symbol]
        else:
            return data['Adj Close']

    @staticmethod
    def calculate_sma(data: pd.Series, window: int) -> pd.Series:
        """Calculate simple moving average"""
        return data.rolling(window=window).mean()

    @staticmethod
    def generate_signals(short_sma: pd.Series, long_sma: pd.Series) -> pd.DataFrame:
        """Generate buy/sell signals based on SMA crossover"""
        signals = pd.DataFrame(index=short_sma.index)
        signals['signal'] = 0.0
        signals.loc[short_sma > long_sma, 'signal'] = 1.0
        signals['positions'] = signals['signal'].diff()
        signals['positions'].iloc[0] = signals['signal'].iloc[0]
        return signals

    @staticmethod
    def simulate_trades(data: pd.Series, signals: pd.DataFrame, initial_capital: float) -> pd.DataFrame:
        """Simulate trades based on signals"""
        positions = signals['positions']
        price = data
        
        cash = initial_capital
        shares = 0
        portfolio = pd.DataFrame(index=data.index)
        portfolio['holdings'] = 0.0
        portfolio['cash'] = 0.0
        portfolio['total'] = 0.0
        
        for t in data.index:
            if positions[t] == 1:  # buy
                shares = cash / price[t]
                cash = 0
            elif positions[t] == -1:  # sell
                cash = shares * price[t]
                shares = 0
            holdings = shares * price[t]
            portfolio.loc[t, 'holdings'] = holdings
            portfolio.loc[t, 'cash'] = cash
            portfolio.loc[t, 'total'] = cash + holdings
        
        return portfolio

    @staticmethod
    def calculate_metrics(data: pd.Series, signals: pd.DataFrame, portfolio: pd.DataFrame, 
                          initial_capital: float) -> Dict[str, Any]:
        """Calculate comprehensive backtesting metrics"""
        # Calculate returns
        portfolio['returns'] = portfolio['total'].pct_change()
        
        # Net performance
        net_performance = (portfolio['total'][-1] - initial_capital) / initial_capital
        
        # Number of trades
        num_trades = len(signals[signals['positions'] != 0])
        
        # Trading period in years
        trading_days = len(portfolio)
        years = trading_days / 252  # Assuming 252 trading days per year
        
        # Annualized return
        annualized_return = (1 + net_performance) ** (1 / years) - 1 if years > 0 else 0
        
        # Volatility (annualized)
        volatility = portfolio['returns'].std() * np.sqrt(252) if len(portfolio) > 1 else 0
        
        # Sharpe ratio (assuming risk-free rate of 0 for simplicity)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        cumulative_returns = (1 + portfolio['returns'].fillna(0)).cumprod()
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns / peak) - 1
        max_drawdown = drawdown.min()
        
        # Win rate and average profit
        trades = signals[signals['positions'] != 0]
        if num_trades > 0:
            portfolio_at_trades = portfolio.loc[trades.index, 'total']
            trade_returns = portfolio_at_trades.pct_change().fillna(0)
            win_rate = len(trade_returns[trade_returns > 0]) / len(trade_returns)
            avg_profit_per_trade = net_performance / num_trades
        else:
            win_rate = 0
            avg_profit_per_trade = 0
        
        return {
            'net_performance': float(net_performance),
            'annualized_return': float(annualized_return),
            'volatility': float(volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'win_rate': float(win_rate),
            'avg_profit_per_trade': float(avg_profit_per_trade),
            'num_trades': int(num_trades),
            'final_value': float(portfolio['total'][-1]),
            'initial_value': float(initial_capital)
        }

    @staticmethod
    def prepare_graph_data(data: pd.Series, short_sma: pd.Series, long_sma: pd.Series, 
                          signals: pd.DataFrame, portfolio: pd.DataFrame) -> List[Dict[str, Any]]:
        """Prepare data for visualization"""
        graph_data = pd.DataFrame(index=data.index)
        graph_data['date'] = graph_data.index.strftime('%Y-%m-%d')
        graph_data['price'] = data
        graph_data['short_sma'] = short_sma
        graph_data['long_sma'] = long_sma
        
        # Add portfolio value
        graph_data['portfolio_value'] = portfolio['total']
        
        # Calculate percentage change from initial
        initial_value = portfolio['total'].iloc[0]
        graph_data['portfolio_performance'] = (portfolio['total'] / initial_value - 1) * 100
        
        # Initialize trade marker columns with null values
        graph_data['buyPrice'] = np.nan
        graph_data['sellPrice'] = np.nan
        
        # Mark buy and sell points
        buy_dates = signals[signals['positions'] == 1].index
        sell_dates = signals[signals['positions'] == -1].index
        
        graph_data.loc[buy_dates, 'buyPrice'] = data.loc[buy_dates]
        graph_data.loc[sell_dates, 'sellPrice'] = data.loc[sell_dates]
        
        # Convert to records format for frontend visualization
        return graph_data.reset_index().to_dict(orient='records')

    @staticmethod
    def backtest_sma_strategy(symbol: str, start_date: datetime, end_date: datetime, 
                             short_window: int, long_window: int, 
                             initial_capital: float = 10000.0) -> Dict[str, Any]:
        """Run a complete SMA crossover strategy backtest"""
        data = BacktestService.fetch_data(symbol, start_date, end_date)
        short_sma = BacktestService.calculate_sma(data, short_window)
        long_sma = BacktestService.calculate_sma(data, long_window)
        
        # Slice from where both SMAs are defined
        start_idx = max(short_window, long_window) - 1
        if start_idx >= len(data):
            raise ValueError("Window sizes are too large for the data")
        
        data = data.iloc[start_idx:]
        short_sma = short_sma.iloc[start_idx:]
        long_sma = long_sma.iloc[start_idx:]
        
        signals = BacktestService.generate_signals(short_sma, long_sma)
        portfolio = BacktestService.simulate_trades(data, signals, initial_capital)
        metrics = BacktestService.calculate_metrics(data, signals, portfolio, initial_capital)
        graph_data = BacktestService.prepare_graph_data(data, short_sma, long_sma, signals, portfolio)
        
        return {
            'metrics': metrics,
            'graph_data': graph_data
        }

    @staticmethod
    def run_backtest(strategy_id: str, symbol: str, start_date: datetime, end_date: datetime, 
                    initial_capital: float = 10000.0, parameters: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Run a backtest with the specified strategy"""
        if strategy_id == "sma_crossover":
            short_window = parameters.get('short_window', 20)
            long_window = parameters.get('long_window', 50)
            return BacktestService.backtest_sma_strategy(
                symbol, start_date, end_date, short_window, long_window, initial_capital
            )
        elif strategy_id == "mean_reversion":
            # Add implementation for mean reversion strategy
            window = parameters.get('window', 20)
            num_std = parameters.get('num_std', 2.0)
            # Placeholder for mean reversion implementation
            raise NotImplementedError("Mean reversion backtesting not yet implemented")
        else:
            raise ValueError(f"Unknown strategy: {strategy_id}")