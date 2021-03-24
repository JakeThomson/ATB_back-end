class BaseTechnicalAnalysisComponent:
    """ Represents a technical analysis module. """

    def analyse_data(self):
        pass


class TechnicalAnalysis(BaseTechnicalAnalysisComponent):
    """ Concrete component with the default analysis functionality (nothing). """

    def __init__(self, historical_df):
        self.historical_df = historical_df

    def analyse_data(self):
        return self.historical_df, []
