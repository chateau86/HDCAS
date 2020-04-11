from datetime import datetime
from predictors import predictors

DANGER_VAR = [5, 197, 198, 199]


class BasicCheckPredictor:
    def __init__(self):
        self.init_at = datetime.now()

    def train(self, db_url):
        print("LoopbackPredictor: Training completed")

    def predict(self, datum):
        # Datum is JSON dict
        # print("Loopback predictor called")
        # print(datum)
        warn_list = []
        for var in DANGER_VAR:
            level = 'green'
            param_name = 'SMART {:}'.format(var)
            raw_name = 'smart_{:}_raw'.format(var)
            if raw_name not in datum:
                continue
            desc_str = 'Value should be zero for good drive'
            value_str = str(datum[raw_name])
            if datum[raw_name] > 0:
                level = 'yellow'
            warn_list.append(predictors.WarningItem(
                name=param_name,
                desc=desc_str,
                value=value_str,
                level=level
            ))
        ret = predictors.AlgoResult(
            algo="Basic check",
            version="0.0.0",
            data_date=datetime.utcfromtimestamp(0),
            init_date=self.init_at,
            warn_list=warn_list,
        )
        return ret
