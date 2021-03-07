import shutil

import pytest
import pandas as pd
import pickle
import datetime as dt
import os
from src.data_handlers.historical_data_handler import HistoricalDataHandler

hist_data_mgr = HistoricalDataHandler(market_index="S&P500", end_date=dt.datetime(year=2021, month=2, day=25))
hist_data_mgr.market_index_file_path = "data_handlers/test_data/historical_data/market_index_lists/"
hist_data_mgr.file_path = "data_handlers/test_data/historical_data/S&P500/"

if not os.path.exists(hist_data_mgr.file_path):
    os.makedirs(hist_data_mgr.file_path)


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
    file_exists = os.path.isfile(f"{hist_data_mgr.market_index_file_path}S&P500_{today_date}.pickle")

    assert file_exists


@pytest.mark.historical_data_handler
def test_get_tickers_extracts_values_from_ticker_list_cache_file():
    # Check to see if cache file can be read correctly.
    today_date = dt.date.today()
    file_name = f"{hist_data_mgr.market_index_file_path}S&P500_{today_date}.pickle"
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
    os.rename(fr'{hist_data_mgr.market_index_file_path}S&P500_{today_date}.pickle',
              fr'{hist_data_mgr.market_index_file_path}S&P500_{yesterday_date}.pickle')

    # Test to see if grab_tickers updates the file.
    hist_data_mgr.grab_tickers()

    file_exists = os.path.isfile(f"{hist_data_mgr.market_index_file_path}S&P500_{today_date}.pickle")

    assert file_exists


@pytest.mark.historical_data_handler
def test_historical_data_handler_download_to_csv(mocker):
    # Test set up: Create mocks for all function calls within download_historical_data_to_csv
    test_dataframe = pd.read_csv(f"data_handlers/test_data/historical_data/test_historical_data_1.csv")
    test_dataframe["Date"] = pd.to_datetime(test_dataframe["Date"])
    test_dataframe = test_dataframe.set_index("Date")
    mocker.patch("pandas_datareader.DataReader", return_value=test_dataframe)
    mocker.patch("src.data_handlers.historical_data_handler.HistoricalDataHandler.csv_up_to_date", return_value=True)
    mocker.patch("src.data_validators.historical_data_validator.HistoricalDataValidator.validate_data", return_value=True)
    mocker.patch("src.data_handlers.historical_data_handler.split_list", return_value=["TEST1"])
    test_tickers = ['TEST1', 'TEST2', 'TEST3']

    hist_data_mgr.download_historical_data_to_csv(test_tickers, 0)

    result_dataframe = pd.read_csv(f"{hist_data_mgr.file_path}TEST1.csv")
    result_dataframe["Date"] = pd.to_datetime(result_dataframe["Date"])
    result_dataframe = result_dataframe.set_index("Date")
    result_dataframe.columns = ["Open", "High", "Low", "Close", "Volume", "Adj Close"]

    assert result_dataframe.equals(test_dataframe)


@pytest.mark.historical_data_handler
def test_hist_data_detects_outdated_csv():
    result, last_date_in_csv = hist_data_mgr.csv_up_to_date("TEST1")

    assert result is False


@pytest.mark.historical_data_handler
def test_hist_data_handler_updates_existing_csv(mocker):
    # Test set up: Create mocks for all function calls within download_historical_data_to_csv.
    mocker.patch("src.data_handlers.historical_data_handler.split_list", return_value=["TEST1"])

    test_dataframe = pd.read_csv(f"data_handlers/test_data/historical_data/test_historical_data_2.csv")
    test_dataframe["Date"] = pd.to_datetime(test_dataframe["Date"])
    test_dataframe = test_dataframe.set_index("Date")
    mocker.patch("pandas_datareader.DataReader", return_value=test_dataframe)

    last_date_in_test_csv = dt.datetime(year=2021, month=2, day=24)
    mocker.patch("src.data_handlers.historical_data_handler.HistoricalDataHandler.csv_up_to_date",
                 return_value={False, last_date_in_test_csv})

    mocker.patch("src.data_validators.historical_data_validator.HistoricalDataValidator.validate_data", return_value=True)
    test_tickers = ['TEST1', 'TEST2', 'TEST3']

    hist_data_mgr.download_historical_data_to_csv(test_tickers, 0)

    # Assert that the updated CSV is the same as the expected.
    expected_dataframe = pd.read_csv(f"data_handlers/test_data/historical_data/test_historical_data_combined.csv")
    expected_dataframe["Date"] = pd.to_datetime(expected_dataframe["Date"])
    expected_dataframe = expected_dataframe.set_index("Date")

    result_dataframe = pd.read_csv(f"{hist_data_mgr.file_path}TEST1.csv")
    result_dataframe["Date"] = pd.to_datetime(result_dataframe["Date"])
    result_dataframe = result_dataframe.set_index("Date")
    result_dataframe.columns = ["Open", "High", "Low", "Close", "Volume", "Adj Close"]

    # Delete test file directory at end of tests.
    shutil.rmtree(hist_data_mgr.file_path)
    shutil.rmtree(hist_data_mgr.market_index_file_path)

    assert result_dataframe.equals(expected_dataframe)
