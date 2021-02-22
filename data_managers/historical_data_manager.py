import requests
import bs4


class HistoricalDataManager:

    def __init__(self, index="S&P500"):
        """ Constructor class that instantiates the historical data manager.

        :param index: The market index to be used in the backtest.
        """
        self.index = index

    def grab_tickers(self):
        """ Returns a list of tickers that are a part of the index stated in self.index.

        :return tickers: A list of company tickers.
        """
        if self.index == "S&P500":
            resp = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
            soup = bs4.BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", {"id": "constituents"})

        tickers = []
        for row in table.findAll("tr")[1:]:
            ticker = row.findAll("td")[0].text.replace('\n', '')
            if "." in ticker:
                ticker = ticker.replace('.', '-')
            tickers.append(ticker)

        return tickers
