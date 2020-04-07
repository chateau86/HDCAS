from datetime import datetime
from predictors import predictors


class LoopbackPredictor:
    def __init__(self):
        self.init_at = datetime.now()

    def predict(self, datum):
        # Datum is HistoricalDatum-compatible object
        print("Loopback predictor called")
        ret = predictors.AlgoResult(
            algo="Loopback",
            version="0.0.0",
            data_date=datetime.utcfromtimestamp(0),
            init_date=self.init_at,
            warn_list=[],
        )
        return ret
