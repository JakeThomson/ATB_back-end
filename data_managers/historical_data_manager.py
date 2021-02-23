import requests
import bs4
from exceptions.custom_exceptions import InvalidMarketIndexError
import logging as log


class HistoricalDataManager:

    def __init__(self, index="S&P500"):
        """ Constructor class that instantiates the historical data manager.

        :param index: Label for the market index to be used in the backtest.
            Currently supported index labels: 'S&P500'.
        """
        self.index = index

    def grab_tickers(self):
        """ Returns a list of tickers that are a part of the index stated in self.index.

        :return tickers: A list of company tickers.
        """

        tickers = []

        # Determining the source of the list of tickers.
        if self.index == "S&P500":
            # Wikipedia holds a list of companies in the S&P500 that gets updated regularly.
            resp = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
            soup = bs4.BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"id": "constituents"})

            # Extract tickers from table.
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
