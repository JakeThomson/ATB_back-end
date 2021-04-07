class BaseTechnicalAnalysisComponent:
    """ The base component for the decorator pattern used in the dynamic technical analysis creation. """

    def analyse_data(self, historical_df):
        pass


class TechnicalAnalysis(BaseTechnicalAnalysisComponent):
    """ Concrete component with the default analysis functionality (nothing). This is what gets wrapped by the
        'real' technical analysis modules.
    """

    def analyse_data(self, historical_df):
        """ Blank analysis module, holds no analysis logic.

        :param historical_df: A DataFrame holding the historical data to be analysed.
        :return: The same historical dataframe, and a NoneType in place for a figure to be applied if further analysis
            identifies the stock as a potential trade opportunity.
        """
        fig = None
        return historical_df, fig
