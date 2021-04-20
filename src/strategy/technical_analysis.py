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
