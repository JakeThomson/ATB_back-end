import datetime as dt
from src.exceptions.custom_exceptions import TradeCreationError, TradeAnalysisError
from src.trades.graph_composer import create_initial_profit_loss_figure
from src.data_handlers import request_handler
from src.data_validators import date_validator
from src.trades.trade_handler import TradeHandler
from threading import Thread
import logging
import time
import copy

logger = logging.getLogger("backtest")


class Backtest:

    def __init__(self, settings):
        """ Constructor that instantiates the backtest object and simultaneously calls upon the backtest
            initialisation endpoint in the data access api.

        :param properties: a dict object holding all properties of the backtest.
        """
        self.start_date = settings['startDate']
        self._end_date = settings['endDate']
        self.backtest_date = self.start_date
        self.start_balance = settings['startBalance']
        self.total_balance = self.start_balance
        self.available_balance = self.start_balance
        self.total_profit_loss = 0
        self.total_profit_loss_pct = 0
        self.max_cap_pct_per_trade = settings['capPct']
        self.tp_limit = settings['takeProfit']
        self.sl_limit = settings['stopLoss']
        self.market_index = settings['marketIndex']
        self.strategy_id = settings['strategyId']
        self._is_paused = request_handler.get("/backtest_settings/is_paused").json().get("isPaused")
        self.total_profit_loss_graph = create_initial_profit_loss_figure(self.start_date,
                                                                         self.start_balance)
        self.state = "active"

        body = {
            "start_date": str(self.start_date),
            "start_balance": self.start_balance,
            "total_profit_loss_graph": self.total_profit_loss_graph,
            "strategy_id": self.strategy_id
        }

        self.backtest_id = request_handler.post("/backtests", body).json()['backtestId']

    def to_JSON_serializable(self):
        backtest_dict = copy.deepcopy(self.__dict__)
        backtest_dict['backtest_date'] = str(backtest_dict["backtest_date"])
        backtest_dict['start_date'] = str(backtest_dict["start_date"])
        backtest_dict['_end_date'] = str(backtest_dict["_end_date"])
        return backtest_dict

    def increment_date(self):
        """ Increases the backtest date to the next valid date, and updates the date in the database.

        :return: none
        """
        next_date = self.backtest_date + dt.timedelta(days=1)
        self.backtest_date = date_validator.validate_date(next_date, 1)

        logger.info(f"---- BACKTEST DATE: {dt.datetime.strftime(self.backtest_date, '%Y-%m-%d')} ----")

        body = {
            "backtest_date": self.backtest_date
        }

        request_handler.patch(f"/backtests/{self.backtest_id}/date", body)

    def start_backtest(self, tickers):
        """ Holds the logic for the backtest loop:
        1. Increment Date.
        2. Analyse stocks.
        3. Make trade(s) with the stock that has the most confidence.

        :return: none
        """
        logger.info("*---------------------- Starting backtest ----------------------*")
        if self.strategy_id is None:
            logger.warning("No strategy selected to run.")
            self.state = "stopping"
        else:
            trade_handler = TradeHandler(self, tickers)

        backtest_start_time = time.time()

        last_state = "executing"
        while self.backtest_date < self._end_date and self.state == "active":
            if self._is_paused:
                # Print the state of the application if it has changed since the last loop.
                if last_state != "paused":
                    logger.info("Backtest has been paused")
                    last_state = "paused"
                # Do not do anything if paused.
                time.sleep(0.3)
            else:
                # Print the state of the application if it has changed since the last loop.
                if last_state != "executing":
                    logger.info("Backtest has been resumed")
                    last_state = "executing"

                loop_start_time = time.time()
                self.increment_date()

                if len(trade_handler.open_trades) > 0:
                    trade_handler.analyse_open_trades()

                # Try to invest in new stocks, move to the next day if nothing good is found or if balance is too low.
                try:
                    # Select the stock that has the most confidence from the analysis.
                    interesting_df, analysis_fig = trade_handler.analyse_historical_data()
                    # Go to automatically open an order for that stock using the rules set.
                    trade = trade_handler.create_trade(interesting_df, analysis_fig)
                    trade_handler.make_trade(trade)

                except (TradeCreationError, TradeAnalysisError) as e:
                    logger.debug(e)

                # Ensure loop is not executing too fast.
                loop_time_taken = dt.timedelta(seconds=(time.time() - loop_start_time)).total_seconds()
                while loop_time_taken < 1.5:
                    loop_time_taken = dt.timedelta(seconds=(time.time() - loop_start_time)).total_seconds()
                    time.sleep(0.3)
        backtest_time_taken = dt.timedelta(seconds=(time.time() - backtest_start_time)).total_seconds()
        if self.state == "active":
            logger.info(f"Backtest completed in {str(dt.timedelta(seconds=backtest_time_taken))}")
            request_handler.put(f"/backtests/{self.backtest_id}/finalise", {})
        else:
            logger.info(f"Backtest stopped after {str(dt.timedelta(seconds=backtest_time_taken))}")
        # Delete self in main thread by setting state flag
        self.state = "inactive"


class BacktestController:
    def __init__(self, sio, tickers):
        """ Constructor for the backtest controller, automatically starts a new backtest on instantiation and also sets
            up socket listeners for stop/restart events.

        :param sio: The socket connection established for the application.
        :param tickers: Array of tickers
        """
        self.socket = sio
        self.tickers = tickers
        self.backtest = None
        self.settings = None

        @self.socket.on('playpause')
        def toggle_pause(data):
            """ Toggle the pause state of the backtest. """
            self.backtest._is_paused = data['isPaused']

        @self.socket.on('restartBacktest')
        def restart_backtest():
            """ Stops the current backtest, removes it from self.backtest, and then starts a new backtest. """
            self._get_settings()
            self.stop_backtest()
            self._start_backtest()

        @self.socket.on('stopBacktest')
        def manual_stop_backtest(strategy_id, msg):
            """ Stops the current backtest if the strategy in use matches the provided. """
            if self.backtest.strategy_id == strategy_id:
                self.stop_backtest()
                logger.info(msg)

        self._get_settings()
        thread = Thread(target=self._start_backtest)
        thread.start()

    def _start_backtest(self):
        """ Instantiates a new backtest object using the most recently updated properties, and then runs it. """
        self.backtest = Backtest(self.settings)
        self.backtest.start_backtest(self.tickers)

    def stop_backtest(self):
        """ Sets the stopping flag in the backtest so that the thread can safely exit the loop early, then deletes the
            backtest object from the controller. """
        self.backtest.state = "stopping" if self.backtest.state == "active" else "inactive"
        while self.backtest.state != "inactive":
            time.sleep(0.3)
        self.backtest = None

    def _get_settings(self):
        """ Gets the most up to date settings from the database and saves them to self. """
        settings = request_handler.get("/backtest_settings").json()
        settings['startDate'] = dt.datetime.strptime(settings['startDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
        settings['endDate'] = dt.datetime.strptime(settings['endDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
        self.settings = settings
