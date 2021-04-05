class BaseTechnicalAnalysisComponent:
    """ Represents a technical analysis module. """

    def analyse_data(self, historical_df, interesting_stock_dfs):
        pass


class TechnicalAnalysis(BaseTechnicalAnalysisComponent):
    """ Concrete component with the default analysis functionality (nothing). """

    def analyse_data(self, historical_df, interesting_stock_dfs):
        return historical_df, interesting_stock_dfs
