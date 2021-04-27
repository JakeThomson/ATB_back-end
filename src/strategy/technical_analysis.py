from src.data_validators import date_validator
import plotly.graph_objects as go
import datetime as dt
import numpy as np



class TechnicalAnalysisInterface:
    """ The base component for the decorator pattern used in the dynamic technical analysis creation. """

    def analyse_data(self, historical_df):
        pass


class TechnicalAnalysisDecorator(TechnicalAnalysisInterface):
    """ Concrete component with the default analysis functionality (nothing). This is what gets wrapped by the
        'real' technical analysis modules.
    """

    def __init__(self, wrapped, config):
        """ Constructor method for the MovingAverages wrapper class.

        :param wrapped: The technical analysis method that is wrapped by this one.
        :param config: The configuration set for this analysis method.
        """
        self._wrapped = wrapped
        self.config = config

    def analyse_data(self, historical_df):
        """ Blank analysis module, holds no analysis logic.

        :param historical_df: A DataFrame holding the historical data to be analysed.
        :return: The same historical dataframe, and a NoneType in place for a figure to be applied if further analysis
            identifies the stock as a potential trade opportunity.
        """
        # Perform the inner layers of the strategy first (In order defined in the config).
        historical_df, fig = self._wrapped.analyse_data(historical_df)

        return historical_df, fig

    def update_figure(self, trade):
        """ Blank analysis module, holds no analysis logic.

        :param historical_df: A DataFrame holding the historical data to be analysed.
        :return: The same historical dataframe, and a NoneType in place for a figure to be applied if further analysis
            identifies the stock as a potential trade opportunity.
        """
        # Perform the inner layers of the strategy first (In order defined in the config).
        fig = self._wrapped.update_figure(trade)

        return fig

    def _draw_figure(self):
        """ Draw the plotly figure to illustrate the analysis that influenced the trade.
        :return: A plotly figure object (Or none).
        """
        return None

    def _draw_initial_figure(self, historical_df):
        range_days = 30
        start_index_offset = len(historical_df.index) - 50
        start_date_range = historical_df.index[-range_days]
        end_date_range = historical_df.index[-1] + np.timedelta64(7, 'D')
        y_min = min(historical_df['low'][-range_days:].values)
        y_max = max(historical_df['high'][-range_days:].values)

        y_range_offset = (y_max - y_min) * 0.15
        # Draw the foundation candlestick chart.
        fig = go.Figure(data=[go.Candlestick(x=historical_df.index[-start_index_offset:],
                                             open=historical_df['open'][-start_index_offset:],
                                             high=historical_df['high'][-start_index_offset:],
                                             low=historical_df['low'][-start_index_offset:],
                                             close=historical_df['close'][-start_index_offset:],
                                             line=dict(width=1.2),
                                             name="Stock Price")])
        fig.update_layout(height=250, width=460, template="simple_white",
                          legend=dict(orientation="h", yanchor="top", y=1.17, xanchor="center", x=0.5,
                                      font_size=10),
                          margin=dict(t=10, l=0, r=0, b=0), plot_bgcolor='rgba(0,0,0,0)',
                          xaxis=dict(rangebreaks=[dict(bounds=['sat', 'mon'])], showline=True,
                                     linewidth=1, range=[start_date_range, end_date_range],
                                     tickcolor="rgba(0,0,0,0.3)", linecolor="rgba(0,0,0,0.3)", showgrid=False),
                          yaxis=dict(showline=True, linecolor="rgba(0,0,0,0.3)", linewidth=1, showgrid=True,
                                     gridcolor="rgba(0,0,0,0.08)", tickcolor="rgba(0,0,0,0.3)",
                                     layer="below traces", range=[y_min - y_range_offset, y_max + y_range_offset]))

        return fig


class BaseTechnicalAnalysisModule(TechnicalAnalysisInterface):
    """ Concrete component with the default analysis functionality (nothing). This is what gets wrapped by the
        'real' technical analysis modules.
    """

    def analyse_data(self, historical_df):
        """ Blank analysis method, holds no analysis logic.

        :param historical_df: A DataFrame holding the historical data to be analysed.
        :return: The same historical dataframe, and a NoneType in place for a figure to be applied if further analysis
            identifies the stock as a potential trade opportunity.
        """
        fig = None
        return historical_df, fig

    def update_figure(self, trade):
        """ Blank analysis module, holds no analysis logic.

        :param historical_df: A DataFrame holding the historical data to be analysed.
        :return: The same historical dataframe, and a NoneType in place for a figure to be applied if further analysis
            identifies the stock as a potential trade opportunity.
        """
        fig = trade.figure
        range_days = 30

        x_val = trade.historical_data.index[-1]
        open_val = trade.historical_data['open'][-1]
        high_val = trade.historical_data['high'][-1]
        low_val = trade.historical_data['low'][-1]
        close_val = trade.historical_data['close'][-1]
        tp_sl_end_val = trade.historical_data.index[-1] + np.timedelta64(5, 'D')
        tp_sl_end_val = date_validator.validate_date(tp_sl_end_val, -1)

        fig.data[0]['x'] = np.append(fig.data[0]['x'], x_val)
        fig.data[0]['open'] = np.append(fig.data[0]['open'], open_val)
        fig.data[0]['high'] = np.append(fig.data[0]['high'], high_val)
        fig.data[0]['low'] = np.append(fig.data[0]['low'], low_val)
        fig.data[0]['close'] = np.append(fig.data[0]['close'], close_val)
        for i, trace in enumerate(fig.data):
            if trace['legendgroup'] == "tp/sl":
                trace['x'] = (trace['x'][0], tp_sl_end_val)

        start_date_range = trade.historical_data.index[-range_days]
        end_date_range = trade.historical_data.index[-1] + np.timedelta64(7, 'D')
        y_min = min(np.append(trade.historical_data['low'][-range_days:].values, trade.take_profit))
        y_max = max(np.append(trade.historical_data['high'][-range_days:].values, trade.stop_loss))
        y_range_offset = (y_max - y_min) * 0.15

        fig.update_layout(xaxis=dict(range=[start_date_range, end_date_range]),
                          yaxis=dict(range=[y_min - y_range_offset, y_max + y_range_offset]))

        return fig