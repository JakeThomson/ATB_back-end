import datetime as dt
from data_handlers import request_handler


class TradeSimulator:
    def __init__(self, start_date=dt.datetime(2015, 1, 1), start_balance=15000):
        """ Constructor class that instantiates the simulator object and simultaneously calls upon the simulation
            initialisation endpoint in the data access api.

        :param start_date: a datetime object that the simulation will start on.
        :param start_balance: an integer value that represents the money the simulation will start on.
        """
        self.simulation_date = start_date
        self.start_balance = start_balance
        self.total_balance = start_balance
        self.available_balance = start_balance
        self.total_profit_loss_value = 0
        self.total_profit_loss_percentage = 0
        self.is_paused = False
        # TODO: Replace this placeholder with an actual empty graph JSON object.
        self.total_profit_loss_graph = {"graph": "placeholder"}

        body = {
            "simulation_date": self.simulation_date,
            "start_balance": self.start_balance
        }

        request_handler.put("/simulation_properties/initialise", body)


class SimulatorController:
    def __init__(self, simulator):
        self.simulator = simulator
