from src.strategy.technical_analysis import BaseTechnicalAnalysisComponent
import plotly.graph_objects as go


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
            raise Exception

        if self.config['shortTermType'] == "SMA":
            short_term = self.exponential_moving_avg(historical_df, self.config['shortTermDayPeriod'])
        elif self.config['shortTermType'] == "EMA":
            short_term = self.exponential_moving_avg(historical_df, self.config['longTermDayPeriod'])
        else:
            raise Exception

        intersect = self.check_for_intersect(long_term, short_term)

        if intersect:
            self.fig = self.draw_moving_avg_graph(historical_df, long_term, short_term)
            historical_df.attrs['triggered_indicators'].append("MovingAverages")

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
            # Indicates a BUY signal, not yet worried about these.
            return True
        elif st_second_last_val >= lt_second_last_val and st_last_val <= lt_last_val:
            # Indicates a SELL signal.
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
            title='Moving averages',
            yaxis_title=f"{historical_df.attrs['ticker']} Stock",
            xaxis_title='Date',
            xaxis_rangeslider_visible=False
        )
        return fig


class RelativeStrengthIndex(BaseTechnicalAnalysisComponent):
    """ Uses RSI indicator. """

    def __init__(self, wrapped, config):
        self._wrapped = wrapped
        self.config = config
        self.fig = None

    def analyse_data(self, historical_df):
        historical_df, self.fig = self._wrapped.analyse_data(historical_df)
        return historical_df, self.fig
