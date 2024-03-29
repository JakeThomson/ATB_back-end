from src.data_handlers.historical_data_handler import HistoricalDataHandler
from src.data_validators import date_validator
from src.trades import graph_composer
from src.exceptions.custom_exceptions import TradeCreationError, TradeAnalysisError, InvalidHistoricalDataIndexError
from src.data_handlers import request_handler
from src.trades.trade import Trade
from src.strategy import strategy

import datetime as dt
import math
import logging
import random
import time
import threading
import plotly.graph_objects as go
import numpy as np

logger = logging.getLogger("trade_handler")


class TradeHandler:
    max_strategy_threads = 6

    def __init__(self, backtest, tickers):
        self.backtest = backtest
        self.hist_data_handler = HistoricalDataHandler(start_date=backtest.start_date)
        self.tickers = tickers
        self.open_trades = []
        # The dynamically created strategy that will be used within the backtest.
        self.strategy = strategy.create_strategy(backtest)

    def analyse_historical_data(self):
        """ Goes through the list of tickers and performs technical analysis on each one, as defined in the trading
            strategy.

        :return: A dataframe containing all information on the stock that has the most confidence from the analysis.
        """

        potential_trades = []
        download_threads = []
        start_time = time.time()
        logger.debug(f"Executing strategy on {len(self.tickers)} tickers")

        # Create a number of threads to download data concurrently, to speed up the process.
        for thread_id in range(0, self.max_strategy_threads):
            download_thread = threading.Thread(target=self.strategy.execute,
                                               args=(self.tickers, potential_trades,
                                                     self.max_strategy_threads, thread_id))
            download_threads.append(download_thread)
            download_thread.start()

        # Wait for all threads to finish downloading data before continuing.
        for download_thread in download_threads:
            download_thread.join()

        total_time = dt.timedelta(seconds=(time.time() - start_time))
        logger.debug(f"Strategy executed in {total_time}")

        if not potential_trades:
            # No interesting stocks could be found for this date.
            raise TradeAnalysisError(self.backtest.backtest_date)

        choice = random.choice(potential_trades)
        return choice

    def calculate_num_shares_to_buy(self, interesting_df):
        """ Calculate the total number of shares the bot should buy in one order.

        :param interesting_df: A dataframe holding all data on the stock to be invested in.
        :return buy_price: The price of the stock at the time the order was opened.
        :return qty: The number of shares the bot should buy.
        :return investment_total: The total cost of the shares to be bought.
        """
        buy_price = interesting_df["close"].iloc[-1]

        # Work out the maximum amount of money the bot should spent on the order (a percentage of the total capital).
        max_investment = self.backtest.total_balance * self.backtest.max_cap_pct_per_trade
        # If the max investment is more than is available, then the max that can be invested is reduced to
        # what can be afforded.
        if max_investment > self.backtest.available_balance:
            max_investment = self.backtest.available_balance

        if buy_price <= max_investment:
            # The bot can afford at least one stock, calculate how many it can buy within the max investment limit.
            qty = math.floor(max_investment / buy_price)
            investment_total = qty * buy_price
        else:
            # Share price is higher than available_balance
            raise TradeCreationError(f"Available balance ({'£{:,.2f}'.format(self.backtest.available_balance)}) "
                                     f"can not cover a single share ({'£{:,.2f}'.format(buy_price)})")
        return buy_price, qty, investment_total

    def calculate_tp_sl(self, qty, investment_total):
        """ Calculates the take profit and stop loss thresholds based on the tp/sl limits set in the backtest.
            When the stock price reaches one of these values, the bot will automatically sell them.

        :param qty: The number of shares in the order.
        :param investment_total: The total amount of money invested in the shares.
        :return tp: The take profit stock price threshold.
        :return sl: The stop loss stock price threshold.
        """
        tp = (investment_total * self.backtest.tp_limit) / qty
        sl = (investment_total * self.backtest.sl_limit) / qty
        return tp, sl

    def create_trade(self, interesting_df, analysis_fig):
        """ Creates a trade object using all information gathered.

        :param analysis_fig: A figure object holding the details of the triggered indicators.
        :param interesting_df: A dataframe holding all data on the stock to be invested in.
        :return trade: A trade object holding all information on the opened trade.
        """
        buy_price, qty, investment_total = self.calculate_num_shares_to_buy(interesting_df)
        tp, sl = self.calculate_tp_sl(qty, investment_total)

        # Update yaxis range if tp/sl limits are higher or lower than the current.
        yaxis_range = analysis_fig.layout.yaxis['range']
        if tp >= yaxis_range[1]:
            analysis_fig.layout.yaxis['range'] = (yaxis_range[0], tp + (yaxis_range[1] - yaxis_range[0]) * 0.04)
        if sl <= yaxis_range[0]:
            analysis_fig.layout.yaxis['range'] = (sl - (yaxis_range[1] - yaxis_range[0]) * 0.04, yaxis_range[1])

        # Add the stop loss/take profit lines and the buy marker to the figure.
        analysis_fig.add_traces([go.Scatter(x=[interesting_df.index[-1]], y=[buy_price], showlegend=False,
                                            hoverinfo="skip", mode="markers", name="buysell",
                                            marker=dict(color=["lawngreen", "orangered"],
                                                        symbol=["triangle-up", "triangle-down"], size=10,
                                                        line=dict(color=["darkgreen", "darkred"], width=1.5))),
                                 go.Scatter(
                                     x=[interesting_df.index[-2],
                                        date_validator.validate_date(interesting_df.index[-2] + np.timedelta64(7, 'D'),
                                                                     -1)],
                                     y=[tp, tp], showlegend=True,
                                     hoverinfo="skip", mode="lines", name="TP/SL", legendgroup="tp/sl",
                                     line=dict(color="rgba(0, 100, 0, 0.5)", dash="dot", width=1.3)),
                                 go.Scatter(
                                     x=[interesting_df.index[-2],
                                        date_validator.validate_date(interesting_df.index[-2] + np.timedelta64(7, 'D'),
                                                                     -1)],
                                     y=[sl, sl], showlegend=False,
                                     hoverinfo="skip", mode="lines", name="TP/SL", legendgroup="tp/sl",
                                     line=dict(color="rgba(1000, 0, 0, 0.5)", dash="dot", width=1.3)),
                                 ])

        trade = Trade(backtest_id=self.backtest.backtest_id,
                      ticker=interesting_df.attrs['ticker'],
                      historical_data=interesting_df,
                      buy_date=self.backtest.backtest_date,
                      buy_price=buy_price,
                      share_qty=qty,
                      investment_total=investment_total,
                      take_profit=tp,
                      stop_loss=sl,
                      triggered_indicators=interesting_df.attrs['triggered_indicators'],
                      figure=analysis_fig)
        # Draws the open trade graph using the new trade object.
        trade.simpleFigure, trade.figure_pct = graph_composer.draw_open_trade_graph(trade)
        return trade

    def make_trade(self, trade):
        """ Finalises the trade, subtracting it's investment total from the available balance and sending the new
            information to the database.

        :param trade: A trade object holding all information on the opened trade.
        :return: none
        """
        logger.info(f"Buying {trade.share_qty} shares of {trade.ticker} for "
                    f"{'£{:,.2f}'.format(trade.investment_total)} based off {', '.join(trade.triggered_indicators)}")
        self.backtest.available_balance -= trade.investment_total
        # Convert the object to allow it to be serialized correctly for storage within the MySQL database.
        json_trade = trade.to_JSON_serializable()
        # POST requests to /trades return the unique trade_id generated by the database assign it to the trade
        # object for easy future reference.
        response = request_handler.post(f"/trades/{self.backtest.backtest_id}", json_trade)
        trade.trade_id = response.json().get("trade_id")
        request_handler.put(f"/backtests/{self.backtest.backtest_id}", self.backtest.to_JSON_serializable())
        self.open_trades.append(trade)

    def close_trade(self, trade):
        """ Performs all calculations that will affect the backtest properties when the trade has sold.

        :param trade: The trade to be closed.
        :return: none
        """
        logger.info(f"Closing trade {trade.ticker} with {'profit' if trade.profit_loss > 0 else 'loss'} "
                    f"of {round(trade.profit_loss, 2)}, which was triggered by {', '.join(trade.triggered_indicators)}")
        trade.sell_price = trade.current_price
        trade.sell_date = self.backtest.backtest_date
        self.backtest.available_balance += trade.sell_price * trade.share_qty
        trade.profit_loss = (trade.current_price * trade.share_qty) - trade.investment_total
        trade.profit_loss_pct = (trade.profit_loss / trade.investment_total) * 100
        self.backtest.total_balance += trade.profit_loss
        self.backtest.total_profit_loss = self.backtest.total_balance - self.backtest.start_balance
        self.backtest.total_profit_loss_pct = self.backtest.total_profit_loss / self.backtest.start_balance * 100
        trade.simpleFigure = graph_composer.draw_closed_trade_graph(trade)
        # Add the close trade marker to the figure.
        for i, trace in enumerate(trade.figure.data):
            if trace['name'] == "buysell":
                trace['x'] = np.append(trace['x'], trade.sell_date)
                trace['y'] = np.append(trace['y'], trade.sell_price)

    def analyse_open_trades(self):
        """ Iterates through all trades in the open_trades array stored in the trade_handler's properties. Sells trades
            who's prices have exceeded their take profit/stop loss limits and updates the price for trades that have
            not yet hit them.

        :return: none
        """

        # All open and closed trades will be sent to the api for processing at once, so store their JSON serializable
        # objects in separate arrays.
        json_open_trades_array = []
        json_closed_trades_array = []
        for i, trade in reversed(list(enumerate(self.open_trades))):
            # Get the respective day's data for the targeted trade from the SQLite tables and append to historical
            # data, trimming off the first column to keep the dataframe short.
            new_data = self.hist_data_handler.get_hist_dataframe(trade.ticker, self.backtest.backtest_date, num_weeks=0,
                                                                 num_days=1)
            trade.historical_data = trade.historical_data[1:].append(new_data)
            trade.current_price = trade.historical_data['close'].iloc[-1]
            trade.profit_loss = (trade.current_price * trade.share_qty) - trade.investment_total
            trade.profit_loss_pct = (trade.profit_loss / trade.investment_total) * 100
            trade.simpleFigure, trade.figure_pct = graph_composer.draw_open_trade_graph(trade)

            # Get all analysis modules that triggered this trade to update their traces in the figure.
            trade.figure = self.strategy.update_figure(trade)

            if trade.current_price > trade.take_profit or trade.current_price < trade.stop_loss:
                # Close the trade
                self.close_trade(trade)
                del self.open_trades[i]
                # Add json object to closed trades array.
                json_trade = trade.to_JSON_serializable()
                json_closed_trades_array.append(json_trade)
            else:
                # Add updated json object to open trades array.
                json_trade = trade.to_JSON_serializable()
                json_open_trades_array.append(json_trade)

        # Generate profit/loss graph.
        self.backtest.total_profit_loss_graph = graph_composer.update_profit_loss_graph(self.backtest)
        # Send open and closed trades to the database to be updated/removed in the database accordingly.
        request_handler.put(f"/trades/{self.backtest.backtest_id}",
                            {"open_trades": json_open_trades_array, "closed_trades": json_closed_trades_array})
        # Update backtest properties.
        request_handler.put(f"/backtests/{self.backtest.backtest_id}", self.backtest.to_JSON_serializable())
