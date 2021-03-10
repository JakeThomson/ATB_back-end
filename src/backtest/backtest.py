import datetime as dt
from src.exceptions.custom_exceptions import TradeCreationError, TradeAnalysisError
from src.data_handlers import request_handler
from src.data_validators import date_validator
from src.trades.trade_handler import TradeHandler
import logging
import time

logger = logging.getLogger("backtest")


class Backtest:

    # Global variables that will eventually be set in the UI.
    max_capital_pct_per_trade = 0.25
    tp_limit = 1.02
    sl_limit = 0.99

    def __init__(self, start_date=dt.datetime(2015, 1, 1), start_balance=15000):
        """ Constructor class that instantiates the backtest object and simultaneously calls upon the backtest
            initialisation endpoint in the data access api.

        :param start_date: a datetime object that the backtest will start on.
        :param start_balance: an integer value that represents the money the backtest will start on.
        """
        self.start_date = start_date
        self.backtest_date = start_date
        self.start_balance = start_balance
        self.total_balance = start_balance
        self.available_balance = start_balance
        self.total_profit_loss_value = 0
        self.total_profit_loss_percentage = 0
        self.is_paused = False
        # TODO: Replace this placeholder with an actual empty graph JSON object.
        self.total_profit_loss_graph = {"graph": "placeholder"}

        body = {"backtest_date": str(self.backtest_date), "start_balance": self.start_balance}

        request_handler.put("/backtest_properties/initialise", body)

    def increment_date(self):
        """ Increases the backtest date to the next valid date, and updates the date in the database.

        :return: none
        """
        next_date = self.backtest_date + dt.timedelta(days=1)
        self.backtest_date = date_validator.validate_date(next_date, 1)

        body = {
            "backtest_date": self.backtest_date
        }

        request_handler.patch("/backtest_properties/date", body)


class BacktestController:
    def __init__(self, backtest, tickers):
        self.backtest = backtest
        self.tickers = tickers

    def start_backtest(self):
        """ Holds the logic for the backtest loop:
        1. Increment Date.
        2. Analyse stocks.
        3. Make trade(s) with the stock that has the most confidence.

        :return: none
        """

        trade_handler = TradeHandler(self.backtest, self.tickers)

        while self.backtest.backtest_date < (dt.datetime.today() - dt.timedelta(days=1)):
            start_time = time.time()
            self.backtest.increment_date()

            if len(trade_handler.open_trades) > 0:
                trade_handler.analyse_open_trades()

            # Try to invest in new stocks, move to the next day if nothing good is found or if balance is too low.
            try:
                # Select the stock that has the most confidence from the analysis.
                interesting_df = trade_handler.analyse_historical_data()
                # Go to automatically open an order for that stock using the rules set.
                trade = trade_handler.create_trade(interesting_df)
                trade_handler.make_trade(trade)

            except (TradeCreationError, TradeAnalysisError) as e:
                logger.debug(e)

            # Ensure loop is not executing too fast.
            time_taken = dt.timedelta(seconds=(time.time() - start_time)).total_seconds()
            while time_taken < 3:
                time_taken = dt.timedelta(seconds=(time.time() - start_time)).total_seconds()
                time.sleep(0.3)

        logger.info("Backtest completed.")
