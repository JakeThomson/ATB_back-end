from src.data_validators import date_validator
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

        x_val = trade.historical_data.index[-1]
        open_val = trade.historical_data['open'][-1]
        high_val = trade.historical_data['high'][-1]
        low_val = trade.historical_data['low'][-1]
        close_val = trade.historical_data['close'][-1]
        tp_sl_end_val = next((trace for trace in trade.figure.data if trace['legendgroup'] == "tp/sl"))['x'][1]
        tp_sl_end_val_new = date_validator.validate_date(tp_sl_end_val + dt.timedelta(days=1), -1)

        fig.data[0]['x'] = np.append(fig.data[0]['x'], x_val)
        fig.data[0]['open'] = np.append(fig.data[0]['open'], open_val)
        fig.data[0]['high'] = np.append(fig.data[0]['high'], high_val)
        fig.data[0]['low'] = np.append(fig.data[0]['low'], low_val)
        fig.data[0]['close'] = np.append(fig.data[0]['close'], close_val)
        for trace in fig.data:
            if trace['legendgroup'] == "tp/sl":
                trace['x'] = (trace['x'][0], tp_sl_end_val_new)

        return fig
