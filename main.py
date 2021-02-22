from data_managers.historical_data_manager import HistoricalDataManager


# Main code
if __name__ == '__main__':
    hist_data_mgr = HistoricalDataManager("S&P50")

    print(hist_data_mgr.grab_tickers())
