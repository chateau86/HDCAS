from datetime import datetime
from predictors import predictors
import pickle

VERSION = '0.0.0'
DATA_PATH = './model_data/DTreePredictor_model.pickle'


class DTreePredictor:
    def __init__(self):
        print("DTreePredictor: Init started")
        self.init_at = datetime.now()
        # TODO: Try to load data
        try:
            model_obj_in = pickle.load(open(DATA_PATH, 'rb'))
            print("Loaded data: {:}".format(model_obj_in))
        except Exception as e:
            print("Model load failed: {:}".format(e))

    def train(self, db_url):
        print("DTreePredictor: Training started")
        f_out = open(DATA_PATH, 'wb')
        model = {'test': 'ok', 'version': '0.0.0'}
        pickle.dump(model, f_out)
        f_out.close()
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
