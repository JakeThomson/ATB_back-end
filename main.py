from data_managers.historical_data_manager import HistoricalDataManager
import logging
import os
import time


# Main code
if __name__ == '__main__':

    # Logging configuration.
    # TIP FOR FUTURE: Add [%(threadName)-12.12s] into log formatter to get thread name
    logFormatStr = "%(asctime)s [%(levelname)-5.5s]  %(message)s"
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"), format=logFormatStr)

    hist_data_mgr = HistoricalDataManager("S&P500")
    hist_data_mgr.grab_tickers()
