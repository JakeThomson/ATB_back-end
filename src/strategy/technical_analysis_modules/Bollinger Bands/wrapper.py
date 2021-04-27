from src.strategy.technical_analysis import TechnicalAnalysisDecorator
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def simple_moving_avg(df, period):
    """ Converts the close column in a historical dataframe into a simple moving average of the specified day period.

    :param df: A DataFrame object holding a ticker's historical data.
    :param period: The day period for the simple moving average.
    :return: A Series object with the simple moving average.
    """
    res = df['close'].rolling(window=period).mean()
    return res


class BollingerBands(TechnicalAnalysisDecorator):
    """ Uses Bollinger Bands indicator to detect a potential mean reversion opportunity.
        Currently only uses the Overbought and Oversold approach.
     """

    def analyse_data(self, historical_df):
        """ Analyse the historical data for an opportunity to trade using Bollinger Bands indicator.
            If the closing trade of the most recent day has fallen below a lower boundary, make a prediction that it
            is going to bounce back to the mean price.

        :param historical_df: A DataFrame holding the historical data to be analysed.
        :return: The same historical dataframe, and a plotly figure object if indicator has been triggered, or None if
            not.
        """
        # Perform the inner layers of the strategy first (In order defined in the config).
        historical_df, fig = self._wrapped.analyse_data(historical_df)

        # Calculate SMA and standard deviation.
        sma = simple_moving_avg(historical_df, self.config['dayPeriod'])
        stdev = historical_df['close'].rolling(window=self.config['dayPeriod']).std()

        # Calculate upper and lower bands using the SMA and stdev.
        upper_band = sma + (stdev * 2)
        lower_band = sma - (stdev * 2)

        opportunity = self._check_for_opportunity(historical_df, sma, upper_band, lower_band)
        if opportunity:
            # If the price has just fallen beneath the lower band, then mark as triggered by BB and draw graph.
            historical_df.attrs['triggered_indicators'].append("Bollinger Bands")
            fig = self._draw_figure(historical_df, fig, sma, upper_band, lower_band)

        # Return dataframe and figure (if it has been drawn).
        return historical_df, fig

    def _check_for_opportunity(self, historical_df, sma, upper_band, lower_band):
        """ Check for a break out of the lower bound, which indicates a potential trade opportunity.
            Does not check for breakouts from the upper bound, as short-selling is not a feature in the backtester yet.

        :param historical_df: A DataFrame holding the historical data to be analysed.
        :param sma: A Series holding the simple moving average of the stock.
        :param upper_band: A Series holding the upper Bollinger Band.
        :param lower_band: A Series holding the lower Bollinger Band.
        :return: True if price has broken out, False if not.
        """
        lb_last_val = lower_band[-1]
        lb_second_last_val = lower_band[-2]
        close_last_val = historical_df['close'][-1]
        close_second_last_val = historical_df['close'][-2]
        sma_last_val = sma[-1]
        sma_second_last_val = sma[-2]

        if close_second_last_val >= lb_second_last_val and close_last_val <= lb_last_val \
                and sma_last_val > sma_second_last_val:
            # Indicates a BUY signal.
            return True
        else:
            return False

    def _draw_figure(self, historical_df, fig, sma, upper_band, lower_band):
        """ Draw the plotly figure to illustrate the analysis that influenced the trade.

        :param historical_df: A DataFrame object holding a ticker's historical data.
        :param fig: The current figure object, is None if analysis hasn't yet been triggered.
        :param sma: A Series holding the simple moving average of the stock.
        :param upper_band: A Series holding the upper Bollinger Band.
        :param lower_band: A Series holding the lower Bollinger Band.
        :return: A plotly figure object.
        """

        range_days = 10
        start_index_offset = len(historical_df.index) - 20
        y_min = min(np.concatenate((historical_df['low'][-range_days:].values, lower_band[-range_days:].values)))
        y_max = max(np.concatenate((historical_df['high'][-range_days:].values, upper_band[-range_days:].values)))
        y_range_offset = (y_max - y_min) * 0.15

        # If the figure has not yet been drawn, then draw the foundation candlestick chart.
        if fig is None:
            fig = self._draw_initial_figure(historical_df)

        fig.update_layout(yaxis=dict(range=[y_min - y_range_offset, y_max + y_range_offset]))

        # Add the upper/lower Bollinger Bands to the figure with the area between filled in.
        fig.add_trace(go.Scatter(
            x=historical_df.index.append(historical_df.index[::-1])[-start_index_offset:],
            y=pd.concat([upper_band[-start_index_offset:], lower_band[::-1][-start_index_offset:]]),
            fill='toself',
            fillcolor='rgba(126, 163, 204, 0.15)',
            line=dict(color="rgb(126, 163, 204)"),
            hoverinfo='skip',
            name=f"{self.config['dayPeriod']}-day Bollinger Bands"
        ))

        # Add the SMA line to the figure.
        fig.add_trace(go.Scatter(
            x=historical_df.index[-start_index_offset:], y=sma, name=f"{self.config['dayPeriod']}-day SMA",
            line=dict(shape="spline", smoothing=1.3)
        ))

        # Update the figure with relevant information.
        fig.update_layout(
            xaxis_rangeslider_visible=False
        )
        return fig
