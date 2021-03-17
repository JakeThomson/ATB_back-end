import datetime as dt
from src.exceptions.custom_exceptions import TradeCreationError, TradeAnalysisError
from src.trades.graph_composer import create_initial_profit_loss_figure
from src.data_handlers import request_handler
from src.data_validators import date_validator
from src.trades.trade_handler import TradeHandler
import logging
import time
import copy

logger = logging.getLogger("backtest")


class Backtest:

    def __init__(self, properties):
        """ Constructor class that instantiates the backtest object and simultaneously calls upon the backtest
            initialisation endpoint in the data access api.

        :param properties: a dict object holding all properties of the backtest.
        """
        self.start_date = properties['start_date']
        self.backtest_date = self.start_date
        self.start_balance = properties['start_balance']
        self.total_balance = self.start_balance
        self.available_balance = self.start_balance
        self.total_profit_loss = 0
        self.total_profit_loss_pct = 0
        self.max_cap_pct_per_trade = properties['max_cap_pct_per_trade']
        self.tp_limit = properties['tp_limit']
        self.sl_limit = properties['sl_limit']
        self.is_paused = request_handler.get("/backtest_properties/is_paused").json().get("isPaused")
        self.total_profit_loss_graph = create_initial_profit_loss_figure(self.start_date,
                                                                         self.start_balance)
        self.state = "active"

        body = {
            "backtest_date": str(self.backtest_date),
            "start_balance": self.start_balance,
            "total_profit_loss_graph": self.total_profit_loss_graph
        }

        request_handler.put("/backtest_properties/initialise", body)

    def to_JSON_serializable(self):
        backtest_dict = copy.deepcopy(self.__dict__)
        backtest_dict['backtest_date'] = str(backtest_dict["backtest_date"])
        backtest_dict['start_date'] = str(backtest_dict["start_date"])
        return backtest_dict

    def increment_date(self):
        """ Increases the backtest date to the next valid date, and updates the date in the database.

        :return: none
        """
        next_date = self.backtest_date + dt.timedelta(days=1)
        self.backtest_date = date_validator.validate_date(next_date, 1)

        logger.info(f"BACKTEST DATE: {dt.datetime.strftime(self.backtest_date, '%Y-%m-%d')}")

        body = {
            "backtest_date": self.backtest_date
        }

        request_handler.patch("/backtest_properties/date", body)

    def start_backtest(self, tickers):
        """ Holds the logic for the backtest loop:
        1. Increment Date.
        2. Analyse stocks.
        3. Make trade(s) with the stock that has the most confidence.

        :return: none
        """
        logger.info("*---------------------- Starting backtest ----------------------*")
        trade_handler = TradeHandler(self, tickers)

        time.sleep(2)

        last_state = "executing"
        while self.backtest_date < (dt.datetime.today() - dt.timedelta(days=1)) and self.state == "active":
            if self.is_paused:
                if last_state != "paused":
                    logger.info("Backtest has been paused")
                    last_state = "paused"
                time.sleep(0.3)
            else:
                if last_state != "executing":
                    logger.info("Backtest has been resumed")
                    last_state = "executing"

                start_time = time.time()
                self.increment_date()

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
        if self.state == "active":
            logger.info("Backtest completed")

        self.state = "inactive"


class BacktestController:
    def __init__(self, sio, tickers, properties):
        self.socket = sio
        self.tickers = tickers
        self.backtest = None
        self.properties = properties

        @self.socket.on('playpause')
        def toggle_pause(data):
            self.backtest.is_paused = data['isPaused']

        @self.socket.on('restartBacktest')
        def restart_backtest():
            self.backtest.state = "stopping"
            while self.backtest.state is "stopping":
                time.sleep(0.3)
            self.backtest = None
            logger.info("Backtest stopped")
            self.start_backtest()

        self.start_backtest()

    def start_backtest(self):
        self.backtest = Backtest(self.properties)
        self.backtest.start_backtest(self.tickers)
