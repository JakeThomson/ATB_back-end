from data_handlers.historical_data_handler import HistoricalDataHandler
from data_handlers import request_handler
from backtest.backtest import Backtest, BacktestController
import config


# Main code
if __name__ == '__main__':

    # Application setup.
    config.logging_config()
    request_handler.set_environment("LOCAL")

    # Download/update historical data.
    hist_data_mgr = HistoricalDataHandler(market_index="S&P500", max_threads=7)
    tickers = hist_data_mgr.grab_tickers()
    hist_data_mgr.threaded_data_download(tickers)

    # Initialise backtest.
    backtest = Backtest(start_balance=15000)
    backtest_controller = BacktestController(backtest)

    # Start backtest.
    backtest_controller.start_backtest()
