from src.data_handlers.historical_data_handler import HistoricalDataHandler
from src.data_handlers import request_handler
from src.backtest.backtest import Backtest, BacktestController
import config
import sys
import datetime as dt
import socketio
import logging as log

sio = socketio.Client()
config.logging_config()


@sio.event
def connect():
    log.info("Socket connected successfully")


@sio.event
def connect_error():
    log.error("Failed to connect to socket")


@sio.event
def disconnect():
    log.info("Socket disconnected")


# Main code
if __name__ == '__main__':

    sio.connect('http://localhost:8080')

    # Read command line argument to determine what environment URL to hit for the data access api.
    environment = str(sys.argv[1]) if len(sys.argv) == 2 else "prod"
    request_handler.set_environment(environment)

    # Download/update historical data.
    start_date = dt.datetime(2015, 1, 1)
    hist_data_mgr = HistoricalDataHandler(start_date=start_date, market_index="S&P500", max_threads=7)
    tickers = hist_data_mgr.get_tickers()
    # hist_data_mgr.threaded_data_download(tickers)

    # Initialise backtest.
    backtest = Backtest(start_balance=15000, start_date=start_date)
    backtest_controller = BacktestController(backtest, tickers)

    # Start backtest.
    backtest_controller.start_backtest(sio)

