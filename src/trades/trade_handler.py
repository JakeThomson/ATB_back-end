from src.data_handlers.historical_data_handler import HistoricalDataHandler
import random
import math
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

    def calculate_num_shares_to_buy(self, interesting_df):
        current_share_price = interesting_df["close"].iloc[-1]
        max_investment = self.backtest.total_balance * self.backtest.max_capital_pct_per_trade
        if max_investment > self.backtest.available_balance:
            max_investment = self.backtest.available_balance
        if current_share_price <= max_investment:
            qty = math.floor(max_investment / current_share_price)
            investment_total = qty * current_share_price
        else:
            # Share price is higher than available_balance
            raise
        return qty, investment_total

    def calculate_tp_sl(self, qty, investment_total):
        # Calculate TP/SL
        tp = (investment_total * self.backtest.tp_limit) / qty
        sl = (investment_total * self.backtest.sl_limit) / qty
        return tp, sl
