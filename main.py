from data_managers import historical_data_manager


# Main code
if __name__ == '__main__':
    hist_data_mgr = historical_data_manager.HistoricalDataManager("S&P500")

    print(hist_data_mgr.grab_tickers())
