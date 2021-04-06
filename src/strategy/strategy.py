from src.data_handlers.historical_data_handler import HistoricalDataHandler, split_list
from src.strategy.technical_analysis import TechnicalAnalysis
from src.exceptions.custom_exceptions import InvalidHistoricalDataIndexError
import logging

logger = logging.getLogger("strategy")


def create_strategy(backtest):
    input_config = {
        "lookbackRangeWeeks": 24,
        "analysisTechniques": [
            {
                "name": "MovingAverages",
                "config": {
                    "shortTermType": "SMA",
                    "shortTermDayPeriod": 20,
                    "longTermType": "SMA",
                    "longTermDayPeriod": 50,
                }
            },
            {
                "name": "RelativeStrengthIndex",
                "config": {
                    "type": "SMA",
                }
            }
        ]
    }

    return Strategy(input_config, backtest)


class Strategy:
    def __init__(self, strategy_config, backtest):
        self.backtest = backtest
        self.hist_data_handler = HistoricalDataHandler(start_date=backtest.start_date)
        self.max_lookback_range_weeks = strategy_config['lookbackRangeWeeks']
        self.technical_analysis = self.init_technical_analysis(strategy_config)

    def init_technical_analysis(self, config):
        wrappers = __import__('src.strategy.technical_analysis_wrappers',
                              fromlist=[d['name'] for d in config['analysisTechniques']])
        strategy = TechnicalAnalysis()

        for method in config['analysisTechniques']:
            analysis_method = getattr(wrappers, method['name'])
            strategy = analysis_method(strategy, method['config'])

        return strategy

    def execute(self, tickers, potential_trades, max_strategy_threads, thread_id):
        # Get a portion of tickers for this thread to work with.
        slice_of_tickers = split_list(tickers, max_strategy_threads, thread_id)

        for ticker in slice_of_tickers:
            try:
                stock_df = self.hist_data_handler.get_hist_dataframe(ticker, self.backtest.backtest_date,
                                                                     self.max_lookback_range_weeks)
                stock_df.attrs['triggered_indicators'] = []
            except InvalidHistoricalDataIndexError as e:
                continue
            # Execute strategy on the ticker's past data.
            stock_df, fig = self.technical_analysis.analyse_data(stock_df)
            if stock_df.attrs['triggered_indicators']:
                potential_trades.append((stock_df, fig))
        return
