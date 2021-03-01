import pytest
import requests
import pandas as pd
import pickle
import datetime as dt
import os
from data_handlers.historical_data_handler import HistoricalDataHandler

hist_data_mgr = HistoricalDataHandler(market_index="S&P500", end_date=dt.datetime(year=2021, month=2, day=24))
hist_data_mgr.market_index_file_path = "data_handlers/test_data/historical_data/market_index_lists/"
hist_data_mgr.file_path = "data_handlers/test_data/historical_data/S&P500/"

if not os.path.exists(hist_data_mgr.file_path):
    os.makedirs(hist_data_mgr.file_path)

    # os.unlink(hist_data_mgr.file_path)


@pytest.mark.historical_data_handler
def test_get_tickers_extracts_values_from_html_table(requests_mock):
    # Mock the endpoint for the Wikipedia page, and return the test html results to be used by get_tickers.
    with open('data_handlers/test_data/historical_data/test_wikipedia_html.txt') as f:
        text = f.read()
    requests_mock.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", text=text)
    tickers = hist_data_mgr.grab_tickers()

    assert tickers == ['TEST1', 'TEST2', 'TEST3']


@pytest.mark.historical_data_handler
def test_get_tickers_creates_ticker_list_cache_file():
    # Check to see if cache file was created.
    today_date = dt.date.today()
    file_exists = os.path.isfile(f"data_handlers/test_data/historical_data/market_index_lists/S&P500_{today_date}.pickle")

    assert file_exists


@pytest.mark.historical_data_handler
def test_get_tickers_extracts_values_from_ticker_list_cache_file():
    # Check to see if cache file can be read correctly.
    today_date = dt.date.today()
    file_name = f"data_handlers/test_data/historical_data/market_index_lists/S&P500_{today_date}.pickle"
    with open(file_name, "rb") as f:
        tickers = pickle.load(f)

    assert tickers == ['TEST1', 'TEST2', 'TEST3']


@pytest.mark.historical_data_handler
def test_get_tickers_updates_ticker_list_cache_file(requests_mock):
    # Test setup: Mock wikipedia endpoint, and change the previously created cache file to yesterday's date.
    with open('data_handlers/test_data/historical_data/test_wikipedia_html.txt') as f:
        text = f.read()
    requests_mock.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", text=text)
    today_date = dt.date.today()
    yesterday_date = dt.date.today() - dt.timedelta(days=1)
    os.rename(fr'data_handlers/test_data/historical_data/market_index_lists/S&P500_{today_date}.pickle',
              fr'data_handlers/test_data/historical_data/market_index_lists/S&P500_{yesterday_date}.pickle')

    # Test to see if grab_tickers updates the file.
    hist_data_mgr.grab_tickers()

    file_exists = os.path.isfile(
        f"data_handlers/test_data/historical_data/market_index_lists/S&P500_{today_date}.pickle")

    assert file_exists


@pytest.mark.historical_data_handler
def test_download_historical_data_to_csv(mocker):
    # Test set up: Create mocks for all function calls within download_historical_data_to_csv
    test_dataframe = pd.read_csv(f"data_handlers/test_data/historical_data/test_historical_data_1.csv")
    test_dataframe["Date"] = pd.to_datetime(test_dataframe["Date"])
    test_dataframe = test_dataframe.set_index("Date")
    mocker.patch("pandas_datareader.DataReader", return_value=test_dataframe)
    mocker.patch("data_handlers.historical_data_handler.HistoricalDataHandler.csv_up_to_date", return_value=True)
    mocker.patch("data_validators.historical_data_validator.HistoricalDataValidator.validate_data", return_value=True)
    mocker.patch("data_handlers.historical_data_handler.split_list", return_value=["TEST1"])
    test_tickers = ['TEST1', 'TEST2', 'TEST3']

    hist_data_mgr.download_historical_data_to_csv(test_tickers, 0)

    result_dataframe = pd.read_csv(f"data_handlers/test_data/historical_data/S&P500/TEST1.csv")
    result_dataframe["Date"] = pd.to_datetime(result_dataframe["Date"])
    result_dataframe = result_dataframe.set_index("Date")
    result_dataframe.columns = ["Open", "High", "Low", "Close", "Volume", "Adj Close"]

    assert result_dataframe.equals(test_dataframe)