from src.data_handlers.historical_data_handler import HistoricalDataHandler
from src.data_handlers import request_handler
from src.backtest.backtest import BacktestController
import src.deadline_reminder as deadline_reminder
import config
import sys
import datetime as dt
import socketio
import logging as log
import time
from signal import signal, SIGABRT, SIGBREAK, SIGILL, SIGINT, SIGSEGV, SIGTERM
from threading import Thread
import json
import os

# Set up socket connection with the data-access api and the logging configurations.
sio = socketio.Client()
config.logging_config()
backtest_controller = None


@sio.event
def connect():
    """ Called when the socket connection is first made. """
    log.info("Socket connected successfully")
    sio.emit("sendIdentifier", "backtest")
    time.sleep(1)
    request_handler.patch("/backtest_settings/available", {"backtestOnline": 1})
    time.sleep(1)


@sio.event
def connect_error(e):
    """ Called when the socket connection has failed. """
    log.error("Failed to connect to socket")


@sio.event
def disconnect():
    """ Called when the socket connection has been terminated (when the backend is shutting down). """
    log.info("Socket disconnected")


@sio.on('getAnalysisModules')
def get_analysis_modules(req):
    """ Get a list of all available modules in the modules directory and the data for their configuration forms. """
    log.info("Server requested analysis modules")
    path = "./src/strategy/technical_analysis_modules/"

    # Get list of module names (the names of the module folders).
    analysis_modules = [item for item in os.listdir(path) if os.path.isdir(os.path.join(path, item))]
    # Initialise empty dictionary object to be sent to the UI.
    result = {}

    # Iterate through all the analysis modules and grab their configuration form data.
    for module in analysis_modules:
        with open(f'{path}/{module}/form_configuration.json') as f:
            data = json.load(f)
            # Save the module name and config form data as a key:value pair in the dict.
            result[module] = data

    # Return the dict to the data access api, which will be sent to the UI and cached in the DB.
    return result


def handle_exit(signum, frame):
    """ Called when the application is manually stopped (CTRL+C, PyCharm 'STOP', etc.). """
    if backtest_controller is not None:
        thread = Thread(target=backtest_controller.stop_backtest)
        thread.start()
        thread.join()

    request_handler.patch("/backtest_settings/available", {"backtestOnline": 0})
    time.sleep(0.5)
    sio.disconnect()
    log.info("Back-end shutting down")
    sys.exit()


# Main code
if __name__ == '__main__':

    # Signal handlers listen for events that attempt to kill the program (CTRL+C, PyCharm 'STOP', etc.).
    # IMPORTANT!! If using PyCharm, you must have 'kill.windows.processes.softly' set to true in the registry.
    for sig in (SIGABRT, SIGBREAK, SIGILL, SIGINT, SIGSEGV, SIGTERM):
        signal(sig, handle_exit)

    # Download/update historical data.
    start_date = dt.datetime(2009, 1, 1)
    hist_data_mgr = HistoricalDataHandler(start_date=start_date, market_index="S&P500", max_threads=7)
    tickers = hist_data_mgr.get_tickers()
    hist_data_mgr.multithreaded_data_download(tickers)

    # Read command line argument to determine what environment URL to hit for the data access api.
    environment = str(sys.argv[1]) if len(sys.argv) == 2 else "prod"
    request_handler.set_environment(sio, environment)

    # Set up backtest controller, which handles all backtest operations (restarts etc.)
    backtest_controller = BacktestController(sio, tickers)

    while 1:  # Forces main thread to stay alive, so that the signal handler still exists.
        time.sleep(1)
