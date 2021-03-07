from src.data_handlers.historical_data_handler import HistoricalDataHandler
from src.data_handlers import request_handler
from src.backtest.backtest import Backtest, BacktestController
import config
import sys


# Main code
if __name__ == '__main__':

    # Application setup.
    config.logging_config()
    # Read command line argument to determine what environment URL to hit for the data access api.
    environment = str(sys.argv[1]) if len(sys.argv) == 2 else "prod"
    request_handler.set_environment(environment)

    # Download/update historical data.
    hist_data_mgr = HistoricalDataHandler(market_index="S&P500", max_threads=7)
    tickers = hist_data_mgr.grab_tickers()
    hist_data_mgr.threaded_data_download(tickers)

    # Initialise backtest.
    backtest = Backtest(start_balance=15000)
    backtest_controller = BacktestController(backtest)

    # Start backtest.
    backtest_controller.start_backtest()
