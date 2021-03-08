from src.data_handlers.historical_data_handler import HistoricalDataHandler
import random
import pandas as pd


class TradeHandler:
    def __init__(self, backtest, tickers):
        self.backtest = backtest
        self.hist_data_handler = HistoricalDataHandler(start_date=backtest.start_date)
        self.tickers = tickers

    def analyse_historical_data(self):

        interesting_tickers = [random.choice(self.tickers)]
        interesting_stock = interesting_tickers[0]

        interesting_stock_df = self.hist_data_handler.get_hist_dataframe(interesting_stock, num_weeks=16,
                                                                         backtest_date=self.backtest.backtest_date)
        return interesting_stock_df

