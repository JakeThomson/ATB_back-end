class BaseTechnicalAnalysisComponent:
    """ Represents a technical analysis module. """

    def analyse_data(self, historical_df):
        pass


class TechnicalAnalysis(BaseTechnicalAnalysisComponent):
    """ Concrete component with the default analysis functionality (nothing). """

    def analyse_data(self, historical_df):
        return historical_df, []
