from data_managers.historical_data_manager import HistoricalDataManager
import logging


# Main code
if __name__ == '__main__':

    # Logging configuration.
    logFormatStr = "%(asctime)s [%(levelname)-5.5s]  %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=logFormatStr)

    hist_data_mgr = HistoricalDataManager(market_index="S&P500", max_threads=7)
    tickers = hist_data_mgr.grab_tickers()
    hist_data_mgr.threaded_data_download(tickers)
