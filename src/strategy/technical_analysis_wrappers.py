from src.strategy.technical_analysis import BaseTechnicalAnalysisComponent
import plotly.graph_objects as go


class MovingAverages(BaseTechnicalAnalysisComponent):
    """ Uses moving day average indicator. """

    def __init__(self, wrapped, config):
        self._wrapped = wrapped
        self.config = config

    def analyse_data(self, historical_df, interesting_stock_dfs):
        historical_df, interesting_tickers = self._wrapped.analyse_data(historical_df, interesting_stock_dfs)

        long_term = historical_df['close'].rolling(window=self.config['longTermDayPeriod']).mean()
        short_term = historical_df['close'].rolling(window=self.config['shortTermDayPeriod']).mean()

        intersect = self.check_for_intersect(long_term, short_term)

        if intersect:
            self.draw_moving_avg_graph(historical_df, long_term, short_term)
            interesting_stock_dfs.append(historical_df)

        return historical_df, interesting_stock_dfs

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
        if not hasattr(historical_df, 'fig'):
            historical_df.fig = go.Figure(data=[go.Candlestick(x=historical_df.index, open=historical_df['open'],
                                                               high=historical_df['high'], low=historical_df['low'],
                                                               close=historical_df['close'],
                                                               name=f"{historical_df.ticker} Stock")])

        historical_df.fig.add_traces([
            go.Scatter(x=historical_df.index, y=long_term, name="50-day SMA", line=dict(shape="spline", smoothing=1.3)),
            go.Scatter(x=historical_df.index, y=short_term, name="20-day SMA", line=dict(shape="spline", smoothing=1.3))
        ])
        historical_df.fig.update_layout(
            title='Moving averages',
            yaxis_title=f'{historical_df.ticker} Stock',
            xaxis_title='Date',
            xaxis_rangeslider_visible=False
        )
        return


class RelativeStrengthIndex(BaseTechnicalAnalysisComponent):
    """ Uses RSI indicator. """

    def __init__(self, wrapped, config):
        self._wrapped = wrapped
        self.config = config

    def analyse_data(self, historical_df, interesting_stock_dfs):
        historical_df, interesting_tickers = self._wrapped.analyse_data(historical_df, interesting_stock_dfs)
        return historical_df, interesting_stock_dfs
