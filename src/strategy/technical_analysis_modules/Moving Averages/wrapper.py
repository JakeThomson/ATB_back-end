from src.exceptions.custom_exceptions import InvalidStrategyConfigException
from src.strategy.technical_analysis import BaseTechnicalAnalysisComponent
import plotly.graph_objects as go


def simple_moving_avg(df, period):
    """ Converts the close column in a historical dataframe into a simple moving average of the specified day period.

    :param df: A DataFrame object holding a ticker's historical data.
    :param period: The day period for the simple moving average.
    :return: A Series object with the simple moving average.
    """
    res = df['close'].rolling(window=period).mean()
    return res


def exponential_moving_avg(df, period):
    """ Converts the close column in a historical dataframe into a exponential moving average of the specified day
        period.

    :param df: A DataFrame object holding a ticker's historical data.
    :param period: The day period for the exponential moving average.
    :return: A Series object with the exponential moving average
    """
    res = df['close'].ewm(span=period, adjust=False).mean()
    return res


class MovingAverages(BaseTechnicalAnalysisComponent):
    """ Uses moving day average indicator to detect trends. Can use SMA of EMA for any day period. """

    def __init__(self, wrapped, config):
        """ Constructor method for the MovingAverages wrapper class.

        :param wrapped: The technical analysis method that is wrapped by this one.
        :param config: The configuration set for this analysis method.
        """
        self._wrapped = wrapped
        self.config = config

    def analyse_data(self, historical_df):
        """ Analyse the historical data for an opportunity to trade using moving averages.
            If the short-term MA has just become more than the long-term, then that indicates an uptrend is occurring.

        :param historical_df: A DataFrame holding the historical data to be analysed.
        :return: The same historical dataframe, and a plotly figure object if indicator has been triggered, or None if
            not.
        """
        # Perform the inner layers of the strategy first (In order defined in the config).
        historical_df, fig = self._wrapped.analyse_data(historical_df)

        # Define long-term and short-term lines based on config.
        if self.config['longTermType'] == "SMA":
            long_term = simple_moving_avg(historical_df, self.config['longTermDayPeriod'])
        elif self.config['longTermType'] == "EMA":
            long_term = exponential_moving_avg(historical_df, self.config['longTermDayPeriod'])
        else:
            raise InvalidStrategyConfigException(f"MovingAverage indicator type '{self.config['longTermType']}' is "
                                                 f"unrecognised.")

        if self.config['shortTermType'] == "SMA":
            short_term = simple_moving_avg(historical_df, self.config['shortTermDayPeriod'])
        elif self.config['shortTermType'] == "EMA":
            short_term = exponential_moving_avg(historical_df, self.config['shortTermDayPeriod'])
        else:
            raise InvalidStrategyConfigException(f"MovingAverage indicator type '{self.config['shortTermType']}' is "
                                                 f"unrecognised.")

        opportunity = self.check_for_intersect(long_term, short_term)
        if opportunity:
            # If the short-term and long-term have just intersected then mark as triggered by MA and draw graph.
            historical_df.attrs['triggered_indicators'].append("MovingAverages")
            fig = self.draw_moving_avg_graph(historical_df, fig, long_term, short_term)

        # Return dataframe and figure (if it has been drawn).
        return historical_df, fig

    def check_for_intersect(self, long_term, short_term):
        """ Check the short-term and long-term lines to see if they have just intersected.

        :param long_term: A Series holding the long term moving average.
        :param short_term: A Series holding the short term moving average.
        :return: True if they have just intersected, False if not.
        """
        lt_last_val = long_term[-1]
        lt_second_last_val = long_term[-2]
        st_last_val = short_term[-1]
        st_second_last_val = short_term[-2]

        if st_second_last_val <= lt_second_last_val and st_last_val >= lt_last_val:
            # Indicates a BUY signal.
            return True
        elif st_second_last_val >= lt_second_last_val and st_last_val <= lt_last_val:
            # Indicates a SELL signal, not yet worried about these.
            return False
        else:
            return False

    def draw_moving_avg_graph(self, historical_df, fig, long_term, short_term):
        """ Draw the plotly figure to illustrate the analysis that influenced the trade.

        :param historical_df: A DataFrame object holding a ticker's historical data.
        :param fig: The current figure object, is None if analysis hasn't yet been triggered.
        :param long_term: A Series holding the long term moving average.
        :param short_term: A Series holding the short term moving average.
        :return: A plotly figure object.
        """

        # If the figure has not yet been drawn, then draw the foundation candlestick chart.
        if fig is None:
            fig = go.Figure(data=[go.Candlestick(x=historical_df.index, open=historical_df['open'],
                                                 high=historical_df['high'], low=historical_df['low'],
                                                 close=historical_df['close'],
                                                 name=f"{historical_df.attrs['ticker']} Stock")])

        # Add the short-term/long-term MA lines to the figure.
        fig.add_traces([
            go.Scatter(x=historical_df.index, y=long_term,
                       name=f"{self.config['longTermDayPeriod']}-day {self.config['longTermType']}",
                       line=dict(shape="spline", smoothing=1.3)),
            go.Scatter(x=historical_df.index, y=short_term,
                       name=f"{self.config['shortTermDayPeriod']}-day {self.config['shortTermType']}",
                       line=dict(shape="spline", smoothing=1.3))
        ])
        # Update the figure with relevant information.
        fig.update_layout(
            title=", ".join(historical_df.attrs['triggered_indicators']),
            yaxis_title=f"{historical_df.attrs['ticker']} Stock",
            xaxis_title='Date',
            xaxis_rangeslider_visible=False
        )
        return fig