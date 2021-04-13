from src.data_handlers.historical_data_handler import HistoricalDataHandler, split_list
from src.strategy.technical_analysis import TechnicalAnalysis
from src.exceptions.custom_exceptions import InvalidHistoricalDataIndexError, InvalidStrategyConfigException
import logging

logger = logging.getLogger("strategy")


def create_strategy(backtest):
    """ Creates a strategy object to be used throughout the backtest, using the configuration saved in the database.

    :param backtest: A backtest object.
    :return: A strategy object.
    """

    # Manual configuration for now, will eventually be set by the UI.
    input_config = {
        "lookbackRangeWeeks": 24,
        "technicalAnalysis": [
            {
                "name": "Moving Averages",
                "config": {
                    "shortTermType": "SMA",
                    "shortTermDayPeriod": 20,
                    "longTermType": "SMA",
                    "longTermDayPeriod": 50,
                }
            },
            {
                "name": "Bollinger Bands",
                "config": {
                    "dayPeriod": 20
                }
            }
        ]
    }

    for i, x in enumerate(input_config['technicalAnalysis']):
        input_config['technicalAnalysis'][i]['name'] = input_config['technicalAnalysis'][i]['name'].replace(" ", "")

    # Create the strategy using the configuration.
    strategy = Strategy(input_config, backtest)
    return strategy


class Strategy:
    """ A strategy object that dynamically changes its logic based on the provided configuration. """

    def __init__(self, strategy_config, backtest):
        """ Constructor function.

        :param strategy_config: A JSON object holding the strategy configuration defined by the user, which is used to
            dynamically set the logic of the analysis.
        :param backtest: The object that holds all information on the backtest that the strategy will be used on.
        """
        self.backtest = backtest
        self.hist_data_handler = HistoricalDataHandler(start_date=backtest.start_date)
        self.max_lookback_range_weeks = strategy_config['lookbackRangeWeeks']
        self.technical_analysis = self.init_technical_analysis(strategy_config)

    def init_technical_analysis(self, config):
        """ Dynamically creates an order of execution for the analysis segment of the strategy defined in the provided
            config JSON by using the decorator pattern.

        :param config: A JSON object holding the strategy configuration defined by the user, which is used to
            dynamically set the logic of the analysis.
        :return: A TechnicalAnalysis object which may have been dynamically wrapped depending on the config provided.
        """

        # Create a module object that has all references to the wrapper classes within it.
        wrappers = __import__('src.strategy.technical_analysis_wrappers',
                              fromlist=[d['name'] for d in config['technicalAnalysis']])

        # Create a plain technical analysis that has no logic.
        technical_analysis = TechnicalAnalysis()

        # Iterate through all methods specified in the config.
        for method in config['technicalAnalysis']:
            # Get a reference to the wrapper class that matches the method name provided in the config.
            analysis_wrapper = getattr(wrappers, method['name'])
            # Wrap the technical analysis object with the wrapper that the reference object points to, also passing the
            # config settings provided for that method.
            technical_analysis = analysis_wrapper(technical_analysis, method['config'])

        # Return the dynamically wrapped technical analysis module.
        return technical_analysis

    def execute(self, tickers, potential_trades, max_strategy_threads, thread_id):
        # Get a portion of tickers for this thread to work with.
        slice_of_tickers = split_list(tickers, max_strategy_threads, thread_id)

        # Iterate through the slice of the ticker list set for this thread.
        for ticker in slice_of_tickers:
            try:
                # Get the required historical data for this ticker.
                stock_df = self.hist_data_handler.get_hist_dataframe(ticker, self.backtest.backtest_date,
                                                                     self.max_lookback_range_weeks)
                stock_df.attrs['triggered_indicators'] = []
            except InvalidHistoricalDataIndexError:
                # If there isn't enough data recorded for this ticker, skip it.
                continue

            try:
                # Execute the dynamically defined technical analysis on the historical data.
                stock_df, fig = self.technical_analysis.analyse_data(stock_df)
            except InvalidStrategyConfigException as e:
                # If the strategy config includes unrecognised values, then stop the analysis.
                # TODO: handle this in the initialisation of the strategy so that the backtest doesn't bother starting.
                logger.error(e)
                break

            # If there were any opportunities identified in the analysis, append the dataframe and analysis figure to
            # the list shared between all the other threads.
            if stock_df.attrs['triggered_indicators']:
                potential_trades.append((stock_df, fig))
        return
