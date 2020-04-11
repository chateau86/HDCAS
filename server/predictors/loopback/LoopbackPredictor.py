from datetime import datetime
from predictors import predictors
from data_model import SMART_PARAM_CYCLES, SMART_PARAM_ENABLED


class LoopbackPredictor:
    def __init__(self):
        self.init_at = datetime.now()

    def train(self, db_url):
        print("LoopbackPredictor: Training completed")

    def predict(self, datum):
        # Datum is JSON dict
        # print("Loopback predictor called")
        # print(datum)
        warn_list = []
        for var in SMART_PARAM_ENABLED:
            param_name = 'SMART {:}'.format(var)
            raw_name = 'smart_{:}_raw'.format(var)
            norm_name = 'smart_{:}_normalized'.format(var)
            desc_str = ''
            value_str = ''
            if raw_name in datum:
                desc_str += 'Raw, '
                value_str += str(datum[raw_name]) + ', '
            if norm_name in datum:
                desc_str += 'Normalized, '
                value_str += str(datum[norm_name]) + ', '
            if var in SMART_PARAM_CYCLES:
                cycle_name = 'smart_{:}_cycles'.format(var)
                if cycle_name in datum:
                    desc_str += 'Cycles, '
                    value_str += str(datum[cycle_name]) + ', '
            if desc_str == '':
                continue
            warn_list.append(predictors.WarningItem(
                name=param_name,
                desc=desc_str,
                value=value_str,
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
