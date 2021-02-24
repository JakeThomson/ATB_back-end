import math
import threading
import datetime as dt
import requests
import bs4
from exceptions.custom_exceptions import InvalidMarketIndexError
import logging as log
import os
import re
import pickle


class HistoricalDataManager:

    def __init__(self, index="S&P500", max_threads=4):
        """ Constructor class that instantiates the historical data manager.

        :param index: Label for the market index to be used in the backtest.
            Currently supported index labels: 'S&P500'.
        """
        self.index = index
        self.max_threads = max_threads

    def grab_tickers(self):
        """ Returns a list of tickers that are a part of the index stated in self.index.

        :return tickers: A list of company tickers.
        """

        tickers = []
        log.debug(f"Looking for tickers in the market index '{self.index}'")

        # Determining the source of the list of tickers.
        if self.index == "S&P500":

            # Look for ticker list in cache.
            pattern = re.compile(f"^S&P500_(.*)\.pickle")
            dir = "historical_data/market_index_lists/"
            for filename in os.listdir(dir):
                match = pattern.match(filename)
                if match:
                    # Use cache if it is up to date.
                    if dt.datetime.strptime(match.group(1), "%Y-%m-%d").date() == dt.datetime.today().date():
                        with open(dir + filename, "rb") as f:
                            tickers = pickle.load(f)

                        log.info(f"Successfully obtained list of {len(tickers)} tickers in "
                                 f"market index '{self.index}' from cache")
                        return tickers
                    # Remove cache file if it is not up to date, and proceed to re-download from Wikipedia.
                    else:
                        log.debug(f"Updating cache file for market index '{self.index}'")
                        os.remove(dir + filename)

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

            filename = self.index+"_"+str(dt.datetime.today().date())
            with open(dir+filename, "wb") as f:
                pickle.dump(tickers, f)

            log.info(f"Successfully obtained list of {len(tickers)} tickers in market index '{self.index}' "
                     f"from Wikipedia")
        else:
            # Raise an error if the provided index is not recognised.
            raise InvalidMarketIndexError(self.index)

        return tickers

    def threaded_data_download(self, tickers):
        """ Downloads historical data using multiple threads, max threads are set in the class attributes.

        :param tickers: A list of company tickers.
        :return: none
        """

        if not os.path.exists(f"historical_data/{self.index}"):
            os.makedirs(f"historical_data/{self.index}")

        download_threads = []

        for thread_id in range(0, self.max_threads):
            download_thread = threading.Thread()
            download_threads.append(download_thread)
            download_thread.start()
            download_thread.list_section = split_list(tickers, self.max_threads, thread_id)

        for download_thread in download_threads:
            download_thread.join()


def split_list(tickers, num_portions, portion_id):
    """ Splits a list into equal sections, returns the portion of the list needed by that thread.

    :param tickers: A list of company tickers.
    :param num_portions: The total number of portions to split the list between.
    :param portion_id: The portion of the split to be returned.
    :return: The required section of a list.
    """

    # TODO: Try and make this more accurate
    section = math.floor(len(tickers) / num_portions)
    beginning_index = section * portion_id
    if portion_id + 1 < num_portions:
        end_index = beginning_index + section - 1
    else:
        end_index = len(tickers) - 1
    log.debug(f"Thread-{portion_id} downloading {end_index-beginning_index+1} tickers ({beginning_index}-{end_index})")
    return tickers[beginning_index:(end_index+1)]
