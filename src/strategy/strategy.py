from src.strategy.technical_analysis import TechnicalAnalysis
import logging


logger = logging.getLogger("strategy")


def create_strategy():
    input_config = [
        {
            "name": "MovingAverages",
            "config": {
                "type": "SMA",
                "lookbackRangeWeeks": 12
            }
        },
        {
            "name": "RelativeStrengthIndex",
            "config": {
                "type": "SMA",
                "lookbackRangeWeeks": 16
            }
        }
    ]

    return Strategy(input_config)


class Strategy:
    def __init__(self, strategy_config):
        self.hist_data_handler = None
        self.max_lookback_range_weeks = 16
        self.technical_analysis = self.init_technical_analysis(strategy_config)

    def init_technical_analysis(self, config):
        wrappers = __import__('src.strategy.technical_analysis_wrappers', fromlist=[d['name'] for d in config])
        strategy = TechnicalAnalysis()

        for method in config:
            if method['config']['lookbackRangeWeeks'] > self.max_lookback_range_weeks:
                self.max_lookback_range_weeks = method['lookbackRangeWeeks']

            analysis_method = getattr(wrappers, method['name'])
            strategy = analysis_method(strategy, method['config'])

        return strategy

    def execute(self, stock_df):
        technical_analysis_results, array = self.technical_analysis.analyse_data(stock_df)
        return technical_analysis_results
