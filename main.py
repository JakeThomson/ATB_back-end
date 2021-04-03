from src.data_handlers.historical_data_handler import HistoricalDataHandler
from src.data_handlers import request_handler
from src.backtest.backtest import Backtest, BacktestController
import config
import sys
import datetime as dt
import socketio
import logging as log
import time
import atexit
from signal import signal, SIGABRT, SIGBREAK, SIGILL, SIGINT, SIGSEGV, SIGTERM
from threading import Thread

# Set up socket connection with the data-access api and the logging configurations.
sio = socketio.Client()
config.logging_config()
backtest_controller = None


@sio.event
def connect():
    """ Called when the socket connection is first made. """
    log.info("Socket connected successfully")
    time.sleep(1)
    request_handler.patch("/backtest_properties/available", {"backtestOnline": 1})
    time.sleep(1)


@sio.event
def connect_error(e):
    """ Called when the socket connection has failed. """
    log.error("Failed to connect to socket")


@sio.event
def disconnect():
    """ Called when the socket connection has been terminated (when the backend is shutting down). """
    log.info("Socket disconnected")


def handle_exit(signum, frame):
    """ Called when the application is manually stopped (CTRL+C, PyCharm 'STOP', etc.). """
    if backtest_controller is not None:
        thread = Thread(target=backtest_controller.stop_backtest)
        thread.start()
        thread.join()

    request_handler.patch("/backtest_properties/available", {"backtestOnline": 0})
    time.sleep(0.5)
    sio.disconnect()
    log.info("Back-end shutting down")
    sys.exit()


# Main code
if __name__ == '__main__':

    # Signal handlers listen for events that attempt to kill the program (CTRL+C, PyCharm 'STOP', etc.).
    # You must have 'kill.windows.processes.softly' set to true in PyCharm registry.
    for sig in (SIGABRT, SIGBREAK, SIGILL, SIGINT, SIGSEGV, SIGTERM):
        signal(sig, handle_exit)

    # Read command line argument to determine what environment URL to hit for the data access api.
    environment = str(sys.argv[1]) if len(sys.argv) == 2 else "prod"
    request_handler.set_environment(sio, environment)

    # Download/update historical data.
    start_date = dt.datetime(2009, 1, 1)
    hist_data_mgr = HistoricalDataHandler(start_date=start_date, market_index="S&P500", max_processes=7)
    tickers = hist_data_mgr.get_tickers()
    hist_data_mgr.multiprocess_data_download(tickers)

    backtest_controller = BacktestController(sio, tickers)

    while 1:  # Forces main thread to stay alive, so that the signal handler still exists.
        time.sleep(1)
