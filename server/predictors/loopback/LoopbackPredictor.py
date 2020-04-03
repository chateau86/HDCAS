from datetime import datetime
from predictors import MasterPredictor


class LoopbackPredictor:
    def __init__(self):
        self.init_at = datetime.now()

    def predict(self, datum):
        # Datum is HistoricalDatum-compatible object
        print("Loopback predictor called")
        return {
            'algo': 'LoopbackPredictor',
            'version': '0.0.0',
            'init_date': MasterPredictor.dump_datetime(self.init_at),
            'warn_level': 'green',
            'warnings': [],
        }
