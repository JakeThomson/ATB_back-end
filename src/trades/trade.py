class Trade:
    def __init__(self, ticker, buy_date, buy_price, share_qty, investment_total, take_profit, stop_loss):
        self.trade_id = None
        self.ticker = ticker
        self.buy_date = buy_date
        self.buy_price = buy_price
        self.current_price = buy_price
        self.share_qty = share_qty
        self.investment_total = investment_total
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.figure = {"graph": "placeholder"}
        self.figure_pct = 0

    def to_JSON_serializable(self):
        trade_dict = self.__dict__
        trade_dict['buy_date'] = str(trade_dict["buy_date"])
        return trade_dict
