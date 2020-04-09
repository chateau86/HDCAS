from datetime import datetime
from predictors import predictors


class LoopbackPredictor:
    def __init__(self):
        self.init_at = datetime.now()

    def train(self, db_url):
        print("LoopbackPredictor: Training started")
        print(predictors.SMART_PARAM_ENABLED)
        print("LoopbackPredictor: Training completed")

    def predict(self, datum):
        # Datum is JSON dict
        print("Loopback predictor called")
        print(datum)
        warn_list = []
        for var in predictors.SMART_PARAM_ENABLED:
            raw_name = 'smart_{:}_raw'.format(var)
            norm_name = 'smart_{:}_normalized'.format(var)
            if raw_name in datum:
                warn_list.append(predictors.WarningItem(
                    name=raw_name,
                    desc="Raw value",
                    value=datum[raw_name],
                    level='green'
                ))
            if norm_name in datum:
                warn_list.append(predictors.WarningItem(
                    name=norm_name,
                    desc="Normalized value",
                    value=datum[norm_name],
                    level='green'
                ))
            if var in predictors.SMART_PARAM_CYCLES:
                cycle_name = 'smart_{:}_cycles'.format(var)
                if cycle_name in datum:
                    warn_list.append(predictors.WarningItem(
                        name=cycle_name,
                        desc="In cycles",
                        value=datum[cycle_name],
                        level='green'
                    ))
        ret = predictors.AlgoResult(
            algo="Loopback",
            version="0.0.0",
            data_date=datetime.utcfromtimestamp(0),
            init_date=self.init_at,
            warn_list=warn_list,
        )
        return ret
