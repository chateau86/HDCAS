from datetime import datetime
from predictors import predictors
import pickle

VERSION = '0.0.0'
DATA_PATH = './model_data/DTreePredictor_model.pickle'


def pickle_model(model_data):
    model = {
        'data': model_data,
        'version': VERSION,
    }
    pickle.dump(model, open(DATA_PATH, 'wb'))


def load_model():
    try:
        model_obj_in = pickle.load(open(DATA_PATH, 'rb'))
        print("Loaded data: {:}".format(model_obj_in))
        if model_obj_in['version'] != VERSION:
            print("Data version mismatch: Wanted {:} but got {:}".format(VERSION, model_obj_in['version']))  # noqa: E501
            return None
        if 'data' not in model_obj_in:
            print("Data missing from pickled file")
            return None
        return model_obj_in['data']
    except Exception as e:
        print("Model load failed: {:}".format(e))
        return None


class DTreePredictor:
    def __init__(self):
        print("DTreePredictor: Init started")
        self.init_at = datetime.now()
        # TODO: Try to load data
        self.model = load_model()
        print(self.model)

    def train(self, db_url):
        print("DTreePredictor: Training started")


        
        model = {'test': 'ok'}
        pickle_model(model)
        print("DTreePredictor: Training completed")

    def predict(self, datum):
        # Datum is HistoricalDatum-compatible object
        print("DTree predictor called")
        ret = predictors.AlgoResult(
            algo="DTree",
            version=VERSION,
            data_date=datetime.utcfromtimestamp(0),
            init_date=self.init_at,
            warn_list=[],
        )
        return ret
