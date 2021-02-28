from data_validators.historical_data_validator import HistoricalDataValidator
from data_validators import date_validator
from exceptions.custom_exceptions import InvalidMarketIndexError

import math
import threading
import datetime as dt
import pandas as pd
import pandas_datareader as web
import requests
import bs4
import logging as log
import os
import re
import pickle
import time

# Set log level for get requests to yahoo finance.
log.getLogger("urllib3").setLevel(log.WARNING)


class HistoricalDataManager:

    num_tickers = 0

    def __init__(self, market_index="S&P500", max_threads=4, start_date=dt.datetime(2000, 1, 1),
                 end_date=(dt.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
                           - dt.timedelta(days=1))):
        """ Constructor class that instantiates the historical data manager.

        :param market_index: Label for the market index to be used in the backtest.
            Currently supported index labels: 'S&P500'.
        :param max_threads: The max number of threads to be used to download data.
        :param start_date: The date to download data from.
        :param end_date: The date to download data up to (Default is yesterday).
        """
        self.market_index = market_index
        self.max_threads = max_threads
        self.start_date = date_validator.validate_date(start_date, 1)
        self.end_date = date_validator.validate_date(end_date, -1)
        self.file_path = f"historical_data/{self.market_index}/"
        self.invalid_file_path = f"historical_data/{self.market_index}/INVALID/"

    def grab_tickers(self):
        """ Returns a list of tickers that are a part of the index stated in self.index.

        :return tickers: A list of company tickers.
        """

        tickers = []
        log.info(f"Looking for tickers in the market index '{self.market_index}'")

        # Determining the source of the list of tickers.
        if self.market_index == "S&P500":

            # Look for ticker list in cache.
            pattern = re.compile(f"^S&P500_(.*)\\.pickle")
            file_path = "historical_data/market_index_lists/"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            for filename in os.listdir(file_path):
                match = pattern.match(filename)
                if match:
                    # Use cache if it is up to date.
                    if dt.datetime.strptime(match.group(1), "%Y-%m-%d").date() == dt.datetime.today().date():
                        with open(file_path + filename, "rb") as f:
                            tickers = pickle.load(f)
                        self.num_tickers = len(tickers)
                        log.info(f"Successfully obtained list of {self.num_tickers} tickers in "
                                 f"market index '{self.market_index}' from cache")
                        return tickers
                    # Remove cache file if it is not up to date, and proceed to re-download from Wikipedia.
                    else:
                        log.debug(f"Updating cache file for market index '{self.market_index}'")
                        os.remove(file_path + filename)

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
            with open(file_path + filename, "wb") as f:
                pickle.dump(tickers, f)

            log.info(f"Successfully obtained list of {len(tickers)} tickers in market index '{self.market_index}' "
                     f"from Wikipedia")
        else:
            # Raise an error if the provided index is not recognised.
            raise InvalidMarketIndexError(self.market_index)

        self.num_tickers = len(tickers)
        return tickers

    def __csv_up_to_date(self, ticker):
        """ Opens the ticker's CSV file and checks to see if the data runs up to the date set in self.start_date,
            which is yesterday by default due to that being guaranteed to be the last full day of data.

        :param ticker: A string containing a company ticker
        :return: True if CSV covers the dates, False if not.
        """
        # Load the ticker data, look at the last index and compare the date to self.end_date.
        historical_df = pd.read_csv(f"historical_data/{self.market_index}/{ticker}.csv")
        last_date = historical_df.iloc[historical_df.last_valid_index(), 0]
        last_date = dt.datetime.strptime(last_date, "%Y-%m-%d")

        if last_date.date() < self.end_date.date():
            return False, last_date
        else:
            return True, None

    def __download_historical_data_to_csv(self, tickers, thread_id):
        """ Gets historical data from Yahoo using a slice of the tickers provided in the tickers list.

        :param tickers: A list of company tickers.
        :param thread_id: The ID of the thread that called this function.
        :return: none
        """

        # Get a portion of tickers for this thread to work with.
        slice_of_tickers = split_list(tickers, self.max_threads, thread_id)

        # Iterate through ticker list and download historical data into a CSV if it does not already exist.
        for ticker in slice_of_tickers:
            file_name = f"{ticker}.csv"

            if not os.path.exists(self.file_path+file_name):
                # Check to see if CSV has been placed in the invalid folder previously.
                if os.path.exists(self.invalid_file_path+file_name):
                    log.warning(f"{ticker} has previously been identified as invalid, skipping")
                    continue

                percentage = \
                    round(len(os.listdir(f'./historical_data/{self.market_index}')) / self.num_tickers * 100, 2)
                progress = f"{len(os.listdir(f'historical_data/{self.market_index}'))}" \
                           f"/{self.num_tickers} - {percentage}%"

                # Download data from Yahoo finance using pandas_datareader.
                log.debug(f"Saving {(ticker + ' data').ljust(13)} ({progress})")
                historical_df = web.DataReader(ticker, "yahoo", self.start_date, self.end_date)
                historical_df = historical_df.reindex(columns=["Open", "High", "Low", "Close", "Volume", "Adj Close"])
                historical_df.columns = ["open", "high", "low", "close", "volume", "adj close"]
                historical_df.ticker = ticker

                # Validate data, and save as CSV to the appropriate locations.
                valid = HistoricalDataValidator(historical_df).validate_data()
                if valid:
                    historical_df.to_csv(self.file_path+file_name, mode="a")
                else:
                    historical_df.to_csv(self.invalid_file_path+file_name, mode="a")
            # If CSV already exists, check to see if it has data up until self.end_date.
            else:
                up_to_date, last_date_in_csv = self.__csv_up_to_date(ticker)
                if not up_to_date:
                    # If not up to date, then download the missing data.
                    download_from_date = last_date_in_csv + dt.timedelta(days=1)
                    log.debug(f"Updating {ticker} data")
                    historical_df = web.DataReader(ticker, "yahoo", download_from_date, self.end_date)
                    if historical_df.index[0] == historical_df.index[1]:
                        historical_df = historical_df.iloc[1:]
                    historical_df = historical_df.reindex(
                        columns=["Open", "High", "Low", "Close", "Volume", "Adj Close"])
                    historical_df.columns = ["open", "high", "low", "close", "volume", "adj close"]
                    historical_df.ticker = ticker

                    # Validate data, and append new data onto existing CSVs.
                    valid = HistoricalDataValidator(historical_df).validate_data()
                    if valid:
                        historical_df.to_csv(self.file_path+file_name, mode="a", header=False)
                    else:
                        # If invalid, move the original 'valid' file before appending onto it.
                        os.rename(self.file_path+file_name, self.invalid_file_path+file_name)
                        historical_df.to_csv(self.invalid_file_path+file_name, mode="a", header=False)

    def threaded_data_download(self, tickers):
        """ Downloads historical data using multiple threads, max threads are set in the class attributes.

        :param tickers: A list of company tickers.
        :return: none
        """

        log.info("Saving/updating ticker historical data to CSVs")
        download_threads = []
        start_time = time.time()

        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)
        if not os.path.exists(self.invalid_file_path):
            os.makedirs(self.invalid_file_path)

        # Create a number of threads to download data concurrently, to speed up the process.
        for thread_id in range(0, self.max_threads):
            download_thread = threading.Thread(target=self.__download_historical_data_to_csv,
                                               args=(tickers, thread_id))
            download_threads.append(download_thread)
            download_thread.start()

        # Wait for all threads to finish downloading data before continuing.
        for download_thread in download_threads:
            download_thread.join()
        total_time = dt.timedelta(seconds=(time.time() - start_time))
        log.info(f"Historical data checks completed in: {total_time}")


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
