import math
import threading
import datetime as dt
import pandas as pd
import pandas_datareader as web
import requests
import bs4
from exceptions.custom_exceptions import InvalidMarketIndexError
import logging as log
import os
import re
import pickle
import time

log.getLogger("urllib3").setLevel(log.WARNING)


class HistoricalDataManager:

    num_tickers = 0

    def __init__(self, market_index="S&P500", max_threads=4, start_date=dt.datetime(2000, 1, 1),
                 end_date=dt.datetime.today().date()):
        """ Constructor class that instantiates the historical data manager.

        :param market_index: Label for the market index to be used in the backtest.
            Currently supported index labels: 'S&P500'.
        """
        self.market_index = market_index
        self.max_threads = max_threads
        self.start_date = start_date
        self.end_date = end_date

    def grab_tickers(self):
        """ Returns a list of tickers that are a part of the index stated in self.index.

        :return tickers: A list of company tickers.
        """

        tickers = []
        log.debug(f"Looking for tickers in the market index '{self.market_index}'")

        # Determining the source of the list of tickers.
        if self.market_index == "S&P500":

            # Look for ticker list in cache.
            pattern = re.compile(f"^S&P500_(.*)\\.pickle")
            filepath = "historical_data/market_index_lists/"
            for filename in os.listdir(filepath):
                match = pattern.match(filename)
                if match:
                    # Use cache if it is up to date.
                    if dt.datetime.strptime(match.group(1), "%Y-%m-%d").date() == dt.datetime.today().date():
                        with open(filepath + filename, "rb") as f:
                            tickers = pickle.load(f)
                        self.num_tickers = len(tickers)
                        log.info(f"Successfully obtained list of {self.num_tickers} tickers in "
                                 f"market index '{self.market_index}' from cache")
                        return tickers
                    # Remove cache file if it is not up to date, and proceed to re-download from Wikipedia.
                    else:
                        log.debug(f"Updating cache file for market index '{self.market_index}'")
                        os.remove(filepath + filename)

            # Scrape list of S&P500 companies from Wikipedia.
            resp = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
            soup = bs4.BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"id": "constituents"})

            # Extract tickers from Wikipedia table.
            for row in table.findAll("tr")[1:]:
                ticker = row.findAll("td")[0].text.replace('\n', '')
                if "." in ticker:
                    ticker = ticker.replace('.', '-')
                tickers.append(ticker)

            filename = self.market_index + "_" + str(dt.datetime.today().date()) + ".pickle"
            with open(filepath + filename, "wb") as f:
                pickle.dump(tickers, f)

            log.info(f"Successfully obtained list of {len(tickers)} tickers in market index '{self.market_index}' "
                     f"from Wikipedia")
        else:
            # Raise an error if the provided index is not recognised.
            raise InvalidMarketIndexError(self.market_index)

        self.num_tickers = len(tickers)
        return tickers

    def download_historical_data_to_csv(self, tickers, thread_id):
        """ Gets historical data from Yahoo using a slice of the tickers provided in the tickers list.

        :param tickers: A list of company tickers.
        :param thread_id: The ID of the thread that called this function.
        :return: none
        """

        # Get a portion of tickers for this thread to work with.
        tickers = split_list(tickers, self.max_threads, thread_id)

        # Iterate through ticker list and download historical data into a CSV if it does not already exist.
        for ticker in tickers:
            if not os.path.exists(f"historical_data/{self.market_index}/{ticker}.csv"):
                df = web.DataReader(ticker, "yahoo", self.start_date, self.end_date)
                df = df.reindex(columns=["Open", "High", "Low", "Close", "Volume", "Adj Close"])
                df.columns = ["open", "high", "low", "close", "volume", "adj close"]
                df.to_csv(f"historical_data/{self.market_index}/{ticker}.csv", mode="a", header=False)
                percentage = round(len(os.listdir(f'./historical_data/{self.market_index}')) / self.num_tickers * 100,
                                   2)
                log.debug(f"Saved {(ticker + ' data').ljust(13)} ({len(os.listdir(f'historical_data/{self.market_index}'))}"
                          f"/{self.num_tickers} - {percentage}%)")

    def threaded_data_download(self, tickers):
        """ Downloads historical data using multiple threads, max threads are set in the class attributes.

        :param tickers: A list of company tickers.
        :return: none
        """

        download_threads = []
        start_time = time.time()

        if not os.path.exists(f"historical_data/{self.market_index}"):
            os.makedirs(f"historical_data/{self.market_index}")

        # Create a number of threads to download data concurrently, to speed up the process.
        for thread_id in range(0, self.max_threads):
            download_thread = threading.Thread(target=self.download_historical_data_to_csv,
                                               args=(tickers, thread_id))
            download_threads.append(download_thread)
            download_thread.start()

        # Wait for all threads to finish downloading data before continuing.
        for download_thread in download_threads:
            download_thread.join()
        total_time = dt.timedelta(seconds=(time.time() - start_time))
        log.info(f"Downloads completed in: {total_time}")


def split_list(tickers, num_portions, portion_id):
    """ Splits a list into equal sections, returns the portion of the list needed by that thread.

    :param tickers: A list of company tickers.
    :param num_portions: The total number of portions to split the list between.
    :param portion_id: The portion of the split to be returned.
    :return: The required section of a list.
    """

    section = math.floor(len(tickers) / num_portions)
    beginning_index = section * portion_id
    if portion_id + 1 < num_portions:
        end_index = beginning_index + section - 1
    else:
        end_index = len(tickers) - 1
    log.debug(
        f"Thread-{portion_id} handling {end_index - beginning_index + 1} tickers ({beginning_index}-{end_index})")
    return tickers[beginning_index:(end_index + 1)]
