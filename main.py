from src.data_handlers.historical_data_handler import HistoricalDataHandler
from src.data_handlers import request_handler
from src.backtest.backtest import Backtest, BacktestController
import config
import sys
import datetime as dt
import socketio
import logging as log
import atexit
import signal

# Set up socket connection with the data-access api and the logging configurations.
sio = socketio.Client()
config.logging_config()


@sio.event
def connect():
    """ Called when the socket connection is first made. """
    log.info("Socket connected successfully")


@sio.event
def connect_error():
    """ Called when the socket connection has failed. """
    log.error("Failed to connect to socket")


@sio.event
def disconnect():
    """ Called when the socket connection has been terminated (when the backend is shutting down). """
    log.info("Socket disconnected")
    log.info("Back-end shutting down")


def handle_exit(signum, frame):
    """ Called when the application is manually stopped (CTRL+C, PyCharm 'STOP', etc.). """
    sio.disconnect()
    exit()


# Listen for events that attempt to kill the program (CTRL+C, PyCharm 'STOP', etc.).
atexit.register(handle_exit, None, None)
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)


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

    properties = {"start_balance": 15000, "start_date": start_date, "max_cap_pct_per_trade": 0.25, "tp_limit": 1.02,
                  "sl_limit": 0.99}

    backtest_controller = BacktestController(sio, tickers, properties)

