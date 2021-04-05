class BaseTechnicalAnalysisComponent:
    """ Represents a technical analysis module. """

    def analyse_data(self, historical_df, potential_trades):
        pass


class TechnicalAnalysis(BaseTechnicalAnalysisComponent):
    """ Concrete component with the default analysis functionality (nothing). """

    def analyse_data(self, historical_df, potential_trades):
        fig = None
        return historical_df, fig, potential_trades
