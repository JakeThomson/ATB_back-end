from src.strategy.technical_analysis import BaseTechnicalAnalysisComponent


class MovingAverages(BaseTechnicalAnalysisComponent):
    """ Uses moving day average indicator. """

    def __init__(self, wrapped, config):
        self._wrapped = wrapped
        self.config = config

    def analyse_data(self, historical_df):
        historical_df = self._wrapped.analyse_data(historical_df)
        return historical_df


class RelativeStrengthIndex(BaseTechnicalAnalysisComponent):
    """ Uses RSI indicator. """

    def __init__(self, wrapped, config):
        self._wrapped = wrapped
        self.config = config

    def analyse_data(self, historical_df):
        historical_df = self._wrapped.analyse_data(historical_df)
        return historical_df
