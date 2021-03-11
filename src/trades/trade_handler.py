from src.data_handlers.historical_data_handler import HistoricalDataHandler
from src.trades import graph_composer
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
        """ Goes through the list of tickers and performs technical analysis on each one, as defined in the trading
            strategy.

        :return: A dataframe containing all information on the stock that has the most confidence from the analysis.
        """
        # Currently there is no analysis, just a 60% chance of the bot choosing a random ticker from the list.
        if random.random() < 0.6:
            while True:
                try:
                    interesting_tickers = [random.choice(self.tickers)]
                    interesting_stock = interesting_tickers[0]

                    interesting_stock_df = self.hist_data_handler.get_hist_dataframe(interesting_stock, num_weeks=16,
                                                                                     backtest_date=self.backtest.backtest_date)
                    return interesting_stock_df
                except FileNotFoundError:
                    logger.debug(f"CSV file for '{interesting_stock}' could not be found, possibly has been "
                                 f"recognised as invalid. Choosing new ticker as 'interesting'")
                except InvalidHistoricalDataIndexError as e:
                    # The chosen stock does not have enough data covering the set period ahead of the current date.
                    logger.debug(e)
        else:
            # No interesting stocks could be found for this date.
            raise TradeAnalysisError(self.backtest.backtest_date)

    def calculate_num_shares_to_buy(self, interesting_df):
        """ Calculate the total number of shares the bot should buy in one order.

        :param interesting_df: A dataframe holding all data on the stock to be invested in.
        :return buy_price: The price of the stock at the time the order was opened.
        :return qty: The number of shares the bot should buy.
        :return investment_total: The total cost of the shares to be bought.
        """
        buy_price = interesting_df["close"].iloc[-1]

        # Work out the maximum amount of money the bot should spent on the order (a percentage of the total capital).
        max_investment = self.backtest.total_balance * self.backtest.max_capital_pct_per_trade
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

    def create_trade(self, interesting_df):
        """ Creates a trade object using all information gathered.

        :param interesting_df: A dataframe holding all data on the stock to be invested in.
        :return trade: A trade object holding all information on the opened trade.
        """
        buy_price, qty, investment_total = self.calculate_num_shares_to_buy(interesting_df)
        tp, sl = self.calculate_tp_sl(qty, investment_total)
        trade = Trade(ticker=interesting_df.ticker,
                      historical_data=interesting_df,
                      buy_date=self.backtest.backtest_date,
                      buy_price=buy_price,
                      share_qty=qty,
                      investment_total=investment_total,
                      take_profit=tp,
                      stop_loss=sl)
        # Draws the open trade graph using the new trade object.
        trade.figure, trade.figure_pct = graph_composer.draw_open_trade_figure(trade)
        return trade

    def make_trade(self, trade):
        """ Finalises the trade, subtracting it's investment total from the available balance and sending the new
            information to the database.

        :param trade: A trade object holding all information on the opened trade.
        :return: none
        """
        logger.debug(f"Buying {trade.share_qty} shares of {trade.ticker}.")
        self.backtest.available_balance -= trade.investment_total
        # Convert the object to allow it to be serialized correctly for storage within the MySQL database.
        json_trade = trade.to_JSON_serializable()
        # POST requests to /trades return the unique trade_id generated by the database assign it to the trade
        # object for easy future reference.
        response = request_handler.post("/trades", json_trade)
        trade.trade_id = response.json().get("trade_id")
        request_handler.put("/backtest_properties", self.backtest.to_JSON_serializable())
        logger.debug(f"Bought {trade.share_qty} shares in {trade.ticker} for "
                     f"{'£{:,.2f}'.format(trade.investment_total)}")
        self.open_trades.append(trade)

    def close_trade(self, trade):
        logger.debug(f"Closing trade {trade.ticker} with {'profit' if trade.profit_loss > 0 else 'loss'} "
                     f"of {trade.profit_loss}.")
        trade.sell_price = trade.current_price
        trade.sell_date = self.backtest.backtest_date
        self.backtest.available_balance += trade.sell_price * trade.share_qty
        trade.profit_loss = (trade.current_price * trade.share_qty) - trade.investment_total
        trade.profit_loss_pct = (trade.profit_loss / trade.investment_total) * 100
        self.backtest.total_balance += trade.profit_loss
        self.backtest.total_profit_loss = self.backtest.total_balance - self.backtest.start_balance
        self.backtest.total_profit_loss_pct = self.backtest.total_profit_loss / self.backtest.start_balance * 100
        trade.figure = graph_composer.draw_closed_trade_figure(trade)

    def analyse_open_trades(self):
        json_open_trades_array = []
        json_closed_trades_array = []
        for i, trade in enumerate(self.open_trades):
            new_data = self.hist_data_handler.get_hist_dataframe(trade.ticker, self.backtest.backtest_date, num_weeks=0)
            trade.historical_data = trade.historical_data[1:].append(new_data)
            trade.current_price = trade.historical_data['close'][-1]
            trade.profit_loss = (trade.current_price * trade.share_qty) - trade.investment_total
            trade.profit_loss_pct = (trade.profit_loss / trade.investment_total) * 100
            trade.figure, trade.figure_pct = graph_composer.draw_open_trade_figure(trade)

            if trade.current_price > trade.take_profit or trade.current_price < trade.stop_loss:
                # Close the trade
                self.close_trade(trade)
                del self.open_trades[i]
                json_trade = trade.to_JSON_serializable()
                json_closed_trades_array.append(json_trade)
                pass
            else:
                # Convert the object to allow it to be serialized correctly for storage within the MySQL database.
                json_trade = trade.to_JSON_serializable()
                json_open_trades_array.append(json_trade)
                pass

        self.backtest.total_profit_loss_graph = graph_composer.update_profit_loss_graph(self.backtest)
        # POST requests to /trades return the unique trade_id generated by the database assign it to the trade
        # object for easy future reference.
        request_handler.put(f"/trades",
                            {"open_trades": json_open_trades_array, "closed_trades": json_closed_trades_array})
        request_handler.put("/backtest_properties", self.backtest.to_JSON_serializable())
