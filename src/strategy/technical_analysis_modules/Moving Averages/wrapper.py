from src.exceptions.custom_exceptions import InvalidStrategyConfigException
from src.strategy.technical_analysis import TechnicalAnalysisDecorator
from src.data_validators import date_validator
import plotly.graph_objects as go
import numpy as np
import datetime as dt


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


class MovingAverages(TechnicalAnalysisDecorator):
    """ Uses moving day average indicator to detect trends. Can use SMA of EMA for any day period. """

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

        opportunity = self._check_for_intersect(long_term, short_term)
        if opportunity:
            # If the short-term and long-term have just intersected then mark as triggered by MA and draw graph.
            historical_df.attrs['triggered_indicators'].append("Moving Averages")
            fig = self._draw_figure(historical_df, fig, long_term, short_term)

        # Return dataframe and figure (if it has been drawn).
        return historical_df, fig

    def update_figure(self, trade):
        """ Updates the bollinger band traces in the candlestick chart within the open trade object.

        :param trade: A Trade object holding all information on the open trade.
        :return: The updated figure.
        """
        # Perform the inner layers of the strategy first (In order defined in the config).
        fig = self._wrapped.update_figure(trade)

        if "Moving Averages" in trade.triggered_indicators:
            # Define long-term and short-term lines based on config.
            if self.config['longTermType'] == "SMA":
                long_term_val = simple_moving_avg(trade.historical_data, self.config['longTermDayPeriod'])[-1]
            elif self.config['longTermType'] == "EMA":
                long_term_val = exponential_moving_avg(trade.historical_data, self.config['longTermDayPeriod'])[-1]
            else:
                raise InvalidStrategyConfigException(f"MovingAverage indicator type '{self.config['longTermType']}' is "
                                                     f"unrecognised.")

            if self.config['shortTermType'] == "SMA":
                short_term_val = simple_moving_avg(trade.historical_data, self.config['shortTermDayPeriod'])[-1]
            elif self.config['shortTermType'] == "EMA":
                short_term_val = exponential_moving_avg(trade.historical_data, self.config['shortTermDayPeriod'])[-1]
            else:
                raise InvalidStrategyConfigException(
                    f"MovingAverage indicator type '{self.config['shortTermType']}' is "
                    f"unrecognised.")

            range_days = 30
            # Get the new y_max and y_min values to calculate the new yaxis range.
            y_min = min(np.append(trade.historical_data['low'][-range_days:].values, (long_term_val, short_term_val)))
            y_max = max(np.append(trade.historical_data['high'][-range_days:].values, (long_term_val, short_term_val)))
            y_range_offset = (y_max - y_min) * 0.15

            fig.update_layout(yaxis=dict(range=[y_min - y_range_offset, y_max + y_range_offset]))

            # Update the Moving Averages traces in the figure with the respective updated value.
            x_val = trade.historical_data.index[-1]
            for trace in fig.data:
                if trace['name'] == f"{self.config['longTermDayPeriod']}-day {self.config['longTermType']}":
                    trace['x'] = np.append(trace['x'], x_val)
                    trace['y'] = np.append(trace['y'], long_term_val)
                if trace['name'] == f"{self.config['shortTermDayPeriod']}-day {self.config['shortTermType']}":
                    trace['x'] = np.append(trace['x'], x_val)
                    trace['y'] = np.append(trace['y'], short_term_val)

        return fig

    def _check_for_intersect(self, long_term, short_term):
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

    def _draw_figure(self, historical_df, fig, long_term, short_term):
        """ Draw the plotly figure to illustrate the analysis that influenced the trade.

        :param historical_df: A DataFrame object holding a ticker's historical data.
        :param fig: The current figure object, is None if analysis hasn't yet been triggered.
        :param long_term: A Series holding the long term moving average.
        :param short_term: A Series holding the short term moving average.
        :return: A plotly figure object.
        """

        range_days = 30
        start_index_offset = len(historical_df.index) - 50
        y_min = min(np.concatenate((historical_df['low'][-range_days:].values, long_term[-range_days:].values, short_term[-range_days:].values)))
        y_max = max(np.concatenate((historical_df['high'][-range_days:].values, long_term[-range_days:].values, short_term[-range_days:].values)))
        y_range_offset = (y_max-y_min)*0.15
        # If the figure has not yet been drawn, then draw the foundation candlestick chart.
        if fig is None:
            fig = self._draw_initial_figure(historical_df)

        fig.update_layout(yaxis=dict(range=[y_min - y_range_offset, y_max + y_range_offset]))

        # Add the short-term/long-term MA lines to the figure.
        fig.add_traces([
            go.Scatter(x=historical_df.index[-start_index_offset:], y=long_term[-start_index_offset:], hoverinfo="skip",
                       name=f"{self.config['longTermDayPeriod']}-day {self.config['longTermType']}",
                       line=dict(shape="spline", smoothing=1.3, width=1.3, color="#59b6f0")),
            go.Scatter(x=historical_df.index[-start_index_offset:], y=short_term[-start_index_offset:], hoverinfo="skip",
                       name=f"{self.config['shortTermDayPeriod']}-day {self.config['shortTermType']}",
                       line=dict(shape="spline", smoothing=1.3, width=1.3, color="#3f6deb"))
        ])
        # Update the figure with relevant information.
        fig.update_layout(
            xaxis_rangeslider_visible=False
        )
        return fig
