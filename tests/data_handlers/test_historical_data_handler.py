import pytest
import requests
import datetime as dt
import os
from data_handlers.historical_data_handler import HistoricalDataManager

hist_data_mgr = HistoricalDataManager(market_index="S&P500")


@pytest.mark.historical_data_handler
def test_get_tickers_extracts_values_from_html_table(requests_mock):
    # Mock the endpoint for the Wikipedia page, and return the test html results to be used by get_tickers.
    with open('data_handlers/test_data/test_wikipedia_html.txt') as f:
        text = f.read()
    requests_mock.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", text=text)
    hist_data_mgr.market_index_file_path = "data_handlers/historical_data/market_index_lists/"
    tickers = hist_data_mgr.grab_tickers()

    assert tickers == ['TEST1', 'TEST2', 'TEST3']


@pytest.mark.historical_data_handler
def test_get_tickers_creates_ticker_list_cache_file():
    # Check to see if cache file was created.
    today_date = dt.date.today()
    file_exists = os.path.isfile(f"data_handlers/historical_data/market_index_lists/S&P500_{today_date}.pickle")

    assert file_exists


@pytest.mark.historical_data_handler
def test_get_tickers_updates_ticker_list_cache_file(requests_mock):
    # Test setup: Mock wikipedia endpoint, and change the previously created cache file to yesterday's date.
    with open('data_handlers/test_data/test_wikipedia_html.txt') as f:
        text = f.read()
    requests_mock.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", text=text)
    today_date = dt.date.today()
    yesterday_date = dt.date.today() - dt.timedelta(days=1)
    os.rename(fr'data_handlers/historical_data/market_index_lists/S&P500_{today_date}.pickle',
              fr'data_handlers/historical_data/market_index_lists/S&P500_{yesterday_date}.pickle')

    # Test to see if grab_tickers updates the file.
    hist_data_mgr.grab_tickers()

    file_exists = os.path.isfile(f"data_handlers/historical_data/market_index_lists/S&P500_{today_date}.pickle")

    assert file_exists
