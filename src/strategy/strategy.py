import time

from src.data_handlers.historical_data_handler import HistoricalDataHandler, split_list
from src.strategy.technical_analysis import TechnicalAnalysis
from src.exceptions.custom_exceptions import InvalidHistoricalDataIndexError
import logging
import sqlite3
import pandas as pd
import datetime as dt

logger = logging.getLogger("strategy")


def create_strategy(backtest):
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

    return Strategy(input_config, backtest)


class Strategy:
    def __init__(self, strategy_config, backtest):
        self.backtest = backtest
        self.hist_data_handler = HistoricalDataHandler(start_date=backtest.start_date)
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

    def execute(self, tickers, interesting_stock_dfs, max_strategy_threads, thread_id):
        # Get a portion of tickers for this thread to work with.
        slice_of_tickers = split_list(tickers, max_strategy_threads, thread_id)

        for ticker in slice_of_tickers:
            try:
                stock_df = self.hist_data_handler.get_hist_dataframe(ticker, self.backtest.backtest_date,
                                                                     self.max_lookback_range_weeks, validate_date=False)
            except InvalidHistoricalDataIndexError as e:
                continue
            # Execute strategy on the ticker's past data.
            technical_analysis_results = self.technical_analysis.analyse_data(stock_df)

            if not technical_analysis_results.empty:
                # If the ticker is flagged as interesting, append to interesting tickers array for further evaluation.
                interesting_stock_dfs.append(technical_analysis_results)
        return
