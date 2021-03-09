from src.data_handlers.historical_data_handler import HistoricalDataHandler
from src.exceptions.custom_exceptions import TradeCreationError, InvalidHistoricalDataIndexError, TradeAnalysisError
from src.data_handlers import request_handler
from src.trades.trade import Trade
import random
import math
import logging

logger = logging.getLogger("trade_handler")


class TradeHandler:
    def __init__(self, backtest, tickers):
        self.backtest = backtest
        self.hist_data_handler = HistoricalDataHandler(start_date=backtest.start_date)
        self.tickers = tickers
        self.open_trades = []

    def analyse_historical_data(self):
        if random.random() < 0.6:
            while True:
                try:
                    interesting_tickers = [random.choice(self.tickers)]
                    interesting_stock = interesting_tickers[0]

                    interesting_stock_df = self.hist_data_handler.get_hist_dataframe(interesting_stock, num_weeks=16,
                                                                                     backtest_date=self.backtest.backtest_date)
                    return interesting_stock_df
                except FileNotFoundError:
                    logger.debug(f"CSV file for '{interesting_stock}' could not be found, possibly has been recognised as "
                                 f"invalid. Choosing new ticker as 'interesting'")
                except InvalidHistoricalDataIndexError as e:
                    logger.debug(e)
        else:
            raise TradeAnalysisError(self.backtest.backtest_date)

    def calculate_num_shares_to_buy(self, interesting_df):
        buy_price = interesting_df["close"].iloc[-1]
        max_investment = self.backtest.total_balance * self.backtest.max_capital_pct_per_trade
        if max_investment > self.backtest.available_balance:
            max_investment = self.backtest.available_balance
        if buy_price <= max_investment:
            qty = math.floor(max_investment / buy_price)
            investment_total = qty * buy_price
        else:
            # Share price is higher than available_balance
            raise TradeCreationError(f"Available balance ({self.backtest.available_balance}) can not cover a single "
                                     f"share ({buy_price}).")
        return buy_price, qty, investment_total

    def calculate_tp_sl(self, qty, investment_total):
        tp = (investment_total * self.backtest.tp_limit) / qty
        sl = (investment_total * self.backtest.sl_limit) / qty
        return tp, sl

    def create_trade(self, interesting_df):
        buy_price, qty, investment_total = self.calculate_num_shares_to_buy(interesting_df)
        tp, sl = self.calculate_tp_sl(qty, investment_total)
        trade = Trade(ticker=interesting_df.ticker,
                      buy_date=self.backtest.backtest_date,
                      buy_price=buy_price,
                      share_qty=qty,
                      investment_total=investment_total,
                      take_profit=tp,
                      stop_loss=sl)
        return trade

    def make_trade(self, trade):
        self.backtest.available_balance -= trade.investment_total
        json_trade = trade.to_JSON_serializable()
        response = request_handler.post("/trades", json_trade)
        body = {"available_balance": self.backtest.available_balance}
        request_handler.patch("/backtest_properties/available_balance", body)
        trade.trade_id = response.json().get("trade_id")
        self.open_trades.append(trade)

