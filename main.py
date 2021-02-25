from data_handlers.historical_data_handler import HistoricalDataManager
import logging


# Main code
if __name__ == '__main__':

    # Logging configuration.
    logFormatStr = "%(asctime)s [%(levelname)-7.7s]  %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=logFormatStr)

    hist_data_mgr = HistoricalDataManager(market_index="S&P500", max_threads=7)
    tickers = hist_data_mgr.grab_tickers()
    hist_data_mgr.threaded_data_download(tickers)
