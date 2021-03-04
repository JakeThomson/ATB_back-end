from data_handlers.historical_data_handler import HistoricalDataHandler
from simulator.simulator import Backtest, BacktestController
import config


# Main code
if __name__ == '__main__':

    config.logging_config()

    hist_data_mgr = HistoricalDataHandler(market_index="S&P500", max_threads=7)
    tickers = hist_data_mgr.grab_tickers()
    hist_data_mgr.threaded_data_download(tickers)

    simulator = TradeSimulator(start_balance=15000)
