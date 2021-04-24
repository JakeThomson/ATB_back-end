from src.data_validators.historical_data_validator import HistoricalDataValidator
from src.data_validators import date_validator
from src.exceptions.custom_exceptions import InvalidMarketIndexError, InvalidHistoricalDataIndexError

import math
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
import threading
import sqlite3


class HistoricalDataHandler:
    num_tickers = 0

    def __init__(self, market_index="S&P500", max_processes=4, start_date=dt.datetime(2000, 1, 1),
                 end_date=(dt.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
                           - dt.timedelta(days=1))):
        """ Constructor class that instantiates the historical data manager.

        :param market_index: Label for the market index to be used in the backtest.
            Currently supported index labels: 'S&P500'.
        :param max_processes: The max number of processes to be used to download data.
        :param start_date: The date to download data from.
        :param end_date: The date to download data up to (Default is yesterday).
        """
        self.market_index = market_index
        self.max_processes = max_processes
        self.start_date = date_validator.validate_date(start_date, 1)
        self.end_date = date_validator.validate_date(end_date, -1)
        self.market_index_file_path = "historical_data/market_index_lists/"

    def get_tickers(self):
        """ Returns a list of tickers that are a part of the index stated in self.index.

        :return tickers: A list of company tickers.
        """

        tickers = []
        log.info(f"Looking for tickers in the market index '{self.market_index}'")

        # Determining the source of the list of tickers.
        if self.market_index == "S&P500":

            # Look for ticker list in cache.
            pattern = re.compile(f"^S&P500_(.*)\\.pickle")

            if not os.path.exists(self.market_index_file_path):
                os.makedirs(self.market_index_file_path)

            for filename in os.listdir(self.market_index_file_path):
                match = pattern.match(filename)
                if match:
                    # Use cache if it is up to date.
                    if dt.datetime.strptime(match.group(1), "%Y-%m-%d").date() == dt.datetime.today().date():
                        with open(self.market_index_file_path + filename, "rb") as f:
                            tickers = pickle.load(f)
                        self.num_tickers = len(tickers)
                        log.info(f"Successfully obtained list of {self.num_tickers} tickers in "
                                 f"market index '{self.market_index}' from cache")
                        return tickers
                    # Remove cache file if it is not up to date, and proceed to re-download from Wikipedia.
                    else:
                        log.info(f"Updating cache file for market index '{self.market_index}'")
                        os.remove(self.market_index_file_path + filename)

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
            with open(self.market_index_file_path + filename, "wb") as f:
                pickle.dump(tickers, f)

            log.info(f"Successfully obtained list of {len(tickers)} tickers in market index '{self.market_index}' "
                     f"from Wikipedia")
        else:
            # Raise an error if the provided index is not recognised.
            raise InvalidMarketIndexError(self.market_index)

        self.num_tickers = len(tickers)
        return tickers

    def get_hist_dataframe(self, ticker, backtest_date, num_weeks=12, num_days=0):
        """ Retrieves the historical dataframe for the specified ticker from the SQLite database, for a number of
            days or weeks before the given date.

        :param ticker: String of the company ticker to retrieve.
        :param backtest_date: A datetime object holding the 'end' date to retrieve.
        :param num_weeks: Number of weeks worth of data to retrieve before 'end' date.
        :param num_days: Number of days worth of data to retrieve before 'end' date.
        :return: A DataFrame holding the historical data for the given period.
        """

        # Connect to SQLite database.
        conn = sqlite3.connect('historical_data/historical_data.db')
        c = conn.cursor()
        # Calculate the 'start' date for the date range.
        buffer_date = backtest_date - dt.timedelta(weeks=num_weeks, days=num_days)

        # Get the first date of historical data that is recorded in the SQLite database of the ticker.
        first_date = c.execute(f"""SELECT first_date FROM available_tickers WHERE ticker=? """, [ticker]).fetchone()[0]
        first_date = dt.datetime.strptime(first_date, '%Y-%m-%d %H:%M:%S')
        if buffer_date <= first_date:
            # If trying to access a data that doesn't exist, throw exception.
            raise InvalidHistoricalDataIndexError(ticker, buffer_date, first_date)

        # Grab historical dataframe from the relevant SQLite table for the correct date range.
        historical_df = pd.read_sql_query(
            f"""SELECT * FROM '{ticker}' WHERE `date` >= ? AND `date` <= ?""", conn, params=[buffer_date, backtest_date],
            index_col='date', parse_dates=['date'])

        # Add the ticker to the dataframe's custom attributes for later identification.
        historical_df.attrs['ticker'] = ticker

        conn.close()
        return historical_df

    def sqlite_table_up_to_date(self, ticker):
        """ Opens the ticker's SQLite table  and checks to see if the data runs up to the date set in self.start_date,
            which is yesterday by default due to that being guaranteed to be the last full day of data.

        :param ticker: A string containing a company ticker
        :return: True if table data covers the dates, False if not.
        """
        conn = sqlite3.connect('historical_data/historical_data.db')
        c = conn.cursor()

        # Retrieve the most recent recorded date in the relevant SQLite table.
        last_date = c.execute(f"""SELECT last_date FROM available_tickers WHERE ticker=? """, [ticker]).fetchone()[0]
        last_date = dt.datetime.strptime(last_date, '%Y-%m-%d %H:%M:%S')

        conn.close()

        if last_date.date() < self.end_date.date():
            # If the date is before the end date set in the handler, then it is not up to date.
            return False, last_date
        else:
            # Else, it is up to date.
            return True, None

    def download_historical_data_to_sqlite(self, tickers, process_id):
        """ Gets historical data from Yahoo using a slice of the tickers provided in the tickers list.

        :param tickers: A list of company tickers.
        :param process_id: The ID of the process that called this function.
        :return: none
        """

        # Get a portion of tickers for this process to work with.
        slice_of_tickers = split_list(tickers, self.max_processes, process_id)

        # Iterate through ticker list and download historical data into a sqlite table if it does not already exist.
        for ticker in slice_of_tickers:

            conn = sqlite3.connect('historical_data/historical_data.db', timeout=10)
            c = conn.cursor()

            # Get the count of tables with the name == ticker.
            c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name=? ''', [ticker])

            # If the count is 0, then table does not exist.
            if c.fetchone()[0] == 0:

                tables_count = c.execute("""SELECT count(*) FROM available_tickers""").fetchone()[0]
                percentage = \
                    round(tables_count / self.num_tickers * 100, 2)
                progress = f"{tables_count}/{self.num_tickers} - {percentage}%"

                # Download data from Yahoo finance using pandas_datareader.
                log.debug(f"Saving {(ticker + ' data').ljust(13)} ({progress})")
                historical_df = web.DataReader(ticker, "yahoo", self.start_date, self.end_date)
                historical_df = historical_df.reset_index().reindex(
                    columns=["Date", "Open", "High", "Low", "Close", "Volume", "Adj Close"])
                historical_df.columns = ["date", "open", "high", "low", "close", "volume", "adj_close"]

                # Validate data, and save into a SQLite table.
                valid = HistoricalDataValidator(historical_df).validate_data()
                last_date = dt.datetime.strftime(historical_df.iloc[-1]['date'], "%Y-%m-%d %H:%M:%S")
                first_date = dt.datetime.strftime(historical_df.iloc[0]['date'], "%Y-%m-%d %H:%M:%S")
                historical_df.to_sql(ticker, conn, if_exists='replace', index=False)
                c.execute(f'''INSERT INTO available_tickers (ticker, valid, market_index, first_date, last_date) 
                                    VALUES (?, ?, ?, ?, ?)''', [ticker, valid, self.market_index, first_date, last_date])
                conn.commit()
            # If table already exists in SQLite DB, check to see if it has data up until self.end_date.
            else:
                # Check to see if the dataset has been marked as invalid.
                valid = c.execute('''SELECT valid FROM available_tickers WHERE ticker=?''', [ticker]).fetchone()[0]
                if not valid:
                    log.warning(f"{ticker} has previously been identified as invalid, skipping")
                    continue
                up_to_date, last_date_in_table = self.sqlite_table_up_to_date(ticker)
                if not up_to_date:
                    # If not up to date, then download the missing data.
                    download_from_date = last_date_in_table + dt.timedelta(days=1)
                    download_from_date = date_validator.validate_date(download_from_date)
                    log.debug(f"Updating {ticker} data")
                    try:
                        historical_df = web.DataReader(ticker, "yahoo", download_from_date, self.end_date)
                        if historical_df.index[0] == historical_df.index[1]:
                            historical_df = historical_df.iloc[1:]
                    except IndexError:
                        # There is only one line.
                        pass
                    except KeyError:
                        # No data was returned from DataReader.
                        conn.close()
                        log.error(f"No data avaiblable for {ticker} between {download_from_date.date()} & {self.end_date.date()}")
                        continue
                    historical_df = historical_df.reset_index().reindex(
                        columns=["Date", "Open", "High", "Low", "Close", "Volume", "Adj Close"])
                    historical_df.columns = ["date", "open", "high", "low", "close", "volume", "adj_close"]

                    # Validate data, and append to an existing SQLite table.
                    valid = HistoricalDataValidator(historical_df).validate_data()
                    historical_df.to_sql(ticker, conn, if_exists='append', index=False)
                    c.execute("""UPDATE available_tickers
                                                    SET valid=?, last_date=?
                                                        WHERE ticker=? """, [valid, self.end_date, ticker])
                    conn.commit()
            conn.close()

    def multiprocess_data_download(self, tickers):
        """ Downloads historical data using multiple processes, max processes are set in the class attributes.

        :param tickers: A list of company tickers.
        :return: none
        """
        conn = sqlite3.connect('historical_data/historical_data.db', timeout=10)
        c = conn.cursor()
        # Get the count of tables with the name == ticker
        exists = \
            c.execute(
                '''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='available_tickers' ''') \
                .fetchone()[0]
        # If the table does not exist in SQLite, then create it.
        if not exists:
            c.execute('''CREATE TABLE available_tickers
                             ([ticker] text, [valid] boolean, [market_index] text, [first_date] datetime, 
                              [last_date] datetime)''')
        conn.commit()
        conn.close()

        log.info("Saving/updating ticker historical data to local database.")
        download_processes = []
        start_time = time.time()

        # Create a number of processes to download data concurrently, to speed up the process.
        for process_id in range(0, self.max_processes):
            download_process = threading.Thread(target=self.download_historical_data_to_sqlite,
                                                      args=(tickers, process_id))
            download_processes.append(download_process)
            download_process.start()

        # Wait for all processes to finish downloading data before continuing.
        for download_process in download_processes:
            download_process.join()
        total_time = dt.timedelta(seconds=(time.time() - start_time))
        log.info(f"Historical data checks completed in: {total_time}")


def split_list(tickers, num_portions, portion_id):
    """ Splits a list into equal sections, returns the portion of the list needed by that process/thread.

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
    return tickers[beginning_index:(end_index + 1)]
