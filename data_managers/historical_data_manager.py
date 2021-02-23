import math
import threading

import requests
import bs4
from exceptions.custom_exceptions import InvalidMarketIndexError
import logging as log
import os


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


class HistoricalDataManager:

    def __init__(self, index="S&P500", max_threads=4):
        """ Constructor class that instantiates the historical data manager.

        :param index: Label for the market index to be used in the backtest.
            Currently supported index labels: 'S&P500'.
        """
        self.index = index
        self.max_threads = max_threads

    # Split the number of s&p500 companies into equal index ranges for each thread to work with.
    # The thread id is passed through to calculate what index range that thread should work on.

    def grab_tickers(self):
        """ Returns a list of tickers that are a part of the index stated in self.index.

        :return tickers: A list of company tickers.
        """

        tickers = []

        log.debug(f"Looking for tickers in the market index '{self.index}'")

        # Determining the source of the list of tickers.
        if self.index == "S&P500":
            # Wikipedia holds a list of companies in the S&P500 that gets updated regularly.
            resp = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
            soup = bs4.BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"id": "constituents"})

            # Extract tickers from Wikipedia table.
            for row in table.findAll("tr")[1:]:
                ticker = row.findAll("td")[0].text.replace('\n', '')
                if "." in ticker:
                    ticker = ticker.replace('.', '-')
                tickers.append(ticker)

            log.info(f"Successfully found list of {len(tickers)} tickers in market index '{self.index}'")
        else:
            # Raise an error if the provided index is not recognised.
            raise InvalidMarketIndexError(self.index)

        return tickers

    def download_historical_data_to_CSV(self, tickers):
        """ Downloads historical data for all values in the provided list of tickers .

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



        # for ticker in tickers[beginning_index:end_index + 1]:
        #     try_count = 0
        #     while True:
        #         if not os.path.exists(f"stock_dfs/{ticker}.csv"):
        #             df = web.DataReader(ticker, "yahoo", start, end)
        #             df = df.reindex(columns=["Open", "High", "Low", "Close", "Volume", "Adj Close"])
        #             df.columns = ["open", "high", "low", "close", "volume", "adj close"]
        #             df.to_csv(f"stock_dfs/{ticker}.csv")
        #             percentage = round(len(os.listdir('./stock_dfs')) / len(tickers) * 100, 2)
        #             print(f"Grabbed {ticker} data \t\t({len(os.listdir('./stock_dfs'))}"
        #                   f"/{len(tickers)} - {percentage}%)")
        #             break
        #         else:
        #             is_up_to_date, new_start = up_to_date(ticker)
        #             if is_up_to_date:
        #                 # print(f"Already have up to date {ticker} data.")
        #                 break
        #             else:
        #                 df = web.DataReader(ticker, "yahoo", new_start, end)
        #                 df = df.reindex(columns=["Open", "High", "Low", "Close", "Volume", "Adj Close"])
        #                 df.columns = ["open", "high", "low", "close", "volume", "adj close"]
        #                 df.to_csv(f"stock_dfs/{ticker}.csv", mode="a", header=False)
        #                 if try_count > 0:
        #                     print(f"{ticker} data succeeded after retry {try_count}")
        #                 break
        #         # except Exception as e:
        #         #     if try_count <= 7:
        #         #         time.sleep(1.5)
        #         #         try_count += 1
        #         #     else:
        #         #         print(f"FATAL: Failed to download {ticker} data, aborting...")
        #         #         exit()
