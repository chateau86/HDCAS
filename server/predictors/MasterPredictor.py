from predictors.loopback import LoopbackPredictor


class MasterPredictor:
    def __init__(self):
        self.predictor_dict = {}
        self.predictor_dict['loopback'] = LoopbackPredictor.LoopbackPredictor()

    def predict(self, datum):
        out_dict = {}
        for pred in self.predictor_dict:
            out_dict[pred] = self.predictor_dict[pred].predict(datum)
        return out_dict


def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]
