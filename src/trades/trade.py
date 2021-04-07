import copy

class Trade:
    def __init__(self, ticker, historical_data, buy_date, buy_price, share_qty, investment_total, take_profit, stop_loss, triggered_indicators):
        self.trade_id = None
        self.ticker = ticker
        self.historical_data = historical_data
        self.buy_date = buy_date
        self.buy_price = buy_price
        self.sell_date = None
        self.sell_price = None
        self.profit_loss = 0
        self.profit_loss_pct = 0
        self.current_price = buy_price
        self.share_qty = share_qty
        self.investment_total = investment_total
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.triggered_indicators = triggered_indicators
        self.figure = {"graph": "placeholder"}
        self.figure_pct = 0

    def to_JSON_serializable(self):
        trade_dict = copy.deepcopy(self.__dict__)
        trade_dict['buy_date'] = str(trade_dict["buy_date"])
        trade_dict['sell_date'] = str(trade_dict["sell_date"])
        trade_dict['historical_data'].index = trade_dict['historical_data'].index.strftime('%Y-%m-%d %H:%M:%S').copy()
        trade_dict['historical_data'].reset_index(level="date", inplace=True)
        trade_dict['historical_data'] = trade_dict['historical_data'].to_dict(orient="list")
        return trade_dict
