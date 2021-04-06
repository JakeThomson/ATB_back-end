from src.exceptions.custom_exceptions import InvalidStrategyConfigException
from src.strategy.technical_analysis import BaseTechnicalAnalysisComponent
import plotly.graph_objects as go
import pandas as pd
import numpy as np


class MovingAverages(BaseTechnicalAnalysisComponent):
    """ Uses moving day average indicator. """

    def __init__(self, wrapped, config):
        self._wrapped = wrapped
        self.config = config
        self.fig = None

    def analyse_data(self, historical_df):
        historical_df, self.fig = self._wrapped.analyse_data(historical_df)

        if self.config['longTermType'] == "SMA":
            long_term = self.simple_moving_avg(historical_df, self.config['longTermDayPeriod'])
        elif self.config['longTermType'] == "EMA":
            long_term = self.simple_moving_avg(historical_df, self.config['longTermDayPeriod'])
        else:
            raise InvalidStrategyConfigException(f"MovingAverage indicator type '{self.config['longTermType']}' is "
                                                 f"unrecognised.")

        if self.config['shortTermType'] == "SMA":
            short_term = self.exponential_moving_avg(historical_df, self.config['shortTermDayPeriod'])
        elif self.config['shortTermType'] == "EMA":
            short_term = self.exponential_moving_avg(historical_df, self.config['longTermDayPeriod'])
        else:
            raise InvalidStrategyConfigException(f"MovingAverage indicator type '{self.config['shortTermType']}' is "
                                                 f"unrecognised.")

        intersect = self.check_for_intersect(long_term, short_term)

        if intersect:
            historical_df.attrs['triggered_indicators'].append("MovingAverages")
            self.fig = self.draw_moving_avg_graph(historical_df, long_term, short_term)

        return historical_df, self.fig

    def simple_moving_avg(self, df, period):
        res = df['close'].rolling(window=period).mean()
        return res

    def exponential_moving_avg(self, df, period):
        res = df['close'].ewm(span=period, adjust=False).mean()
        return res

    def check_for_intersect(self, long_term, short_term):
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

    def draw_moving_avg_graph(self, historical_df, long_term, short_term):
        fig = self.fig

        if fig is None:
            fig = go.Figure(data=[go.Candlestick(x=historical_df.index, open=historical_df['open'],
                                                 high=historical_df['high'], low=historical_df['low'],
                                                 close=historical_df['close'],
                                                 name=f"{historical_df.attrs['ticker']} Stock")])

        fig.add_traces([
            go.Scatter(x=historical_df.index, y=long_term,
                       name=f"{self.config['longTermDayPeriod']}-day {self.config['longTermType']}",
                       line=dict(shape="spline", smoothing=1.3)),
            go.Scatter(x=historical_df.index, y=short_term,
                       name=f"{self.config['shortTermDayPeriod']}-day {self.config['shortTermType']}",
                       line=dict(shape="spline", smoothing=1.3))
        ])
        fig.update_layout(
            title=", ".join(historical_df.attrs['triggered_indicators']),
            yaxis_title=f"{historical_df.attrs['ticker']} Stock",
            xaxis_title='Date',
            xaxis_rangeslider_visible=False
        )
        return fig


class BollingerBands(BaseTechnicalAnalysisComponent):

    def __init__(self, wrapped, config):
        self._wrapped = wrapped
        self.config = config
        self.fig = None

    def analyse_data(self, historical_df):
        historical_df, self.fig = self._wrapped.analyse_data(historical_df)

        sma = historical_df['close'].rolling(window=self.config['dayPeriod']).mean()
        stdev = historical_df['close'].rolling(window=self.config['dayPeriod']).std()

        upper_band = sma + (stdev * 2)
        lower_band = sma - (stdev * 2)

        opportunity = self.check_for_opportunity(historical_df, upper_band, lower_band)

        if opportunity:
            historical_df.attrs['triggered_indicators'].append("BollingerBands")
            self.fig = self.draw_moving_avg_graph(historical_df, upper_band, lower_band)

        return historical_df, self.fig

    def check_for_opportunity(self, historical_df, upper_band, lower_band):
        ub_last_val = upper_band[-1]
        ub_second_last_val = upper_band[-2]
        close_last_val = historical_df['close'][-1]
        close_second_last_val = historical_df['close'][-2]
        if close_second_last_val <= ub_second_last_val and close_last_val >= ub_last_val:
            # Indicates a BUY signal, not yet worried about these.
            return True
        else:
            return False

    def draw_moving_avg_graph(self, historical_df, upper_band, lower_band):
        fig = self.fig

        if fig is None:
            fig = go.Figure(data=[go.Candlestick(x=historical_df.index, open=historical_df['open'],
                                                 high=historical_df['high'], low=historical_df['low'],
                                                 close=historical_df['close'],
                                                 name=f"{historical_df.attrs['ticker']} Stock")])
        x = historical_df.index.append(historical_df.index[::-1])
        y = pd.concat([upper_band, lower_band[::-1]])
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            fill='toself',
            fillcolor='rgba(126, 163, 204, 0.15)',
            line=dict(color="rgb(126, 163, 204)"),
            hoverinfo='skip',
            name=f"{self.config['dayPeriod']}-day Bollinger Bands"
        ))
        fig.update_layout(
            title=", ".join(historical_df.attrs['triggered_indicators']),
            yaxis_title=f"{historical_df.attrs['ticker']} Stock",
            xaxis_title='Date',
            xaxis_rangeslider_visible=False
        )
        return fig
