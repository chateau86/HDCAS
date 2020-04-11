from datetime import datetime, timedelta
import pickle
from sqlalchemy import text
import numpy as np
import sklearn.impute as impute
import sklearn.ensemble as ensemble
from concurrent.futures import ThreadPoolExecutor

from predictors import predictors
from data_model import HistoricalDatum
from data_model import db, SMART_PARAM_ENABLED, SMART_PARAM_CYCLES
VERSION = '1.0.0'
DATA_PATH = './model_data/DTreePredictor_model.pickle'
# DRIVE_COUNT_LIMIT = 100
DRIVE_COUNT_LIMIT = None
SAFE_DAYS = 60
YELLOW_DAYS = 30
RED_DAYS = 15
LOOKAHEAD_DAYS = 90


def pickle_model(model_data):
    model = {
        'data': model_data,
        'version': VERSION,
    }
    pickle.dump(model, open(DATA_PATH, 'wb'))


def load_model():
    try:
        model_obj_in = pickle.load(open(DATA_PATH, 'rb'))
        # print("Loaded data: {:}".format(model_obj_in))
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
    # Note:
    #   self.imputer will be *replaced* on each training run
    #   DTree will be incrementally grown though.

    def __init__(self):
        print("DTreePredictor: Init started")
        self.init_at = datetime.now()
        self.data_date = datetime.utcfromtimestamp(0)
        self.imputer = None
        self.predictor = None
        # TODO: Try to load data
        model = load_model()
        if model is not None:
            if 'imputer' in model:
                self.imputer = model['imputer']
                print("imputer loaded")
            if 'predictor' in model:
                self.predictor = model['predictor']
                print("predictor loaded")
            if 'data_date' in model:
                self.data_date = model['data_date']
        print("DTreePredictor: Init done")

    def _build_drive(self, res_itm):
        drive_arr = []
        ind, len_res, res_itm = res_itm
        if (ind + 1) % 50 == 0 or (ind + 1) == len_res:
            print("At drive {:}/{:}".format(ind + 1, len_res))
        serial_number, failure_day = res_itm
        # print((serial_number, failure_day))
        history_records = HistoricalDatum.query\
            .filter_by(serial_number=serial_number)\
            .filter((failure_day - HistoricalDatum.created_at) < timedelta(days=LOOKAHEAD_DAYS)).all()  # noqa: E501
        for record in history_records:
            days_to_failure = (failure_day - record.created_at) / timedelta(days=1)  # noqa: E501
            if days_to_failure < 0:
                continue
            days_to_failure = min(days_to_failure, SAFE_DAYS)
            data_row = self._vectorize_obj(record, days_to_failure)
            drive_arr.append(data_row)
        if len(drive_arr) == 0:
            return np.zeros((0, len(SMART_PARAM_ENABLED) + 1))
        drive_arr = np.asarray(drive_arr)
        # print("Drive {:} ok".format(ind+1))
        return drive_arr

    def train(self, db_url):
        print("DTreePredictor: Training started")
        '''select distinct status_date, count(*) from drive_details where drive_status='failed' group by status_date order by status_date;'''  # noqa: E501
        limit = ""
        if DRIVE_COUNT_LIMIT is not None:
            limit = " limit {:}".format(DRIVE_COUNT_LIMIT)
        failed_drives_query = text(
            "select serial_number, status_date from drive_details where drive_status='failed' order by status_date{:};".format(limit)  # noqa: E501
        )
        res = db.engine.execute(failed_drives_query)
        res = [itm for itm in res]
        res = [(ind, len(res), res[ind]) for ind in range(len(res))]
        data_arr = []
        print("Checking {:} drives".format(len(res)))
        time_start = datetime.now()
        executor = ThreadPoolExecutor(max_workers=8)
        data_arr = list(executor.map(self._build_drive, res))
        print("threads done")
        data_arr = np.concatenate(data_arr, axis=0)
        self.imputer = impute.SimpleImputer(
            missing_values=np.nan,
            strategy='median'
        )
        input_arr = data_arr[:, 0:-1]
        self.imputer.fit(input_arr)
        input_arr = self.imputer.transform(input_arr)
        output_arr = data_arr[:, -1]

        print("Checking {:} data points".format(len(output_arr)))
        elapsed = (datetime.now() - time_start).total_seconds()
        print("Data loaded in {:} s rate {:} point/s".format(elapsed, len(output_arr)/elapsed))  # noqa: E501
        print("rate {:} drives/s".format(len(res)/elapsed))  # noqa: E501
        time_start = datetime.now()
        self.predictor = ensemble.RandomForestRegressor(
            n_estimators=200,
            n_jobs=-1,
        )
        self.predictor.fit(input_arr, output_arr)
        current_r2 = self.predictor.score(input_arr, output_arr)
        print("Training result: 1-R2={:}".format(1 - current_r2))  # noqa: E501
        elapsed = (datetime.now() - time_start).total_seconds()
        print("Trained in {:} s".format(elapsed))
        model = {
            'imputer': self.imputer,
            'predictor': self.predictor,
            'data_date': datetime.now(),
        }
        pickle_model(model)
        print("DTreePredictor: Training completed")

    def _vectorize_obj(self, record, days_to_failure):
        out_arr = np.zeros(len(SMART_PARAM_ENABLED) + 1)
        for ind in range(len(SMART_PARAM_ENABLED)):
            var = SMART_PARAM_ENABLED[ind]
            name = 'smart_{:}_raw'.format(var)
            if var in SMART_PARAM_CYCLES:
                name = 'smart_{:}_cycles'.format(var)
            out_arr[ind] = getattr(record, name, np.nan)
        out_arr[-1] = days_to_failure
        return out_arr

    def _vectorize_json(self, record):
        # Fill missing with NaN, then impute
        # https://scikit-learn.org/stable/modules/impute.html
        out_arr = np.zeros(len(SMART_PARAM_ENABLED))
        for ind in range(len(SMART_PARAM_ENABLED)):
            var = SMART_PARAM_ENABLED[ind]
            name = 'smart_{:}_raw'.format(var)
            if var in SMART_PARAM_CYCLES:
                name = 'smart_{:}_cycles'.format(var)
            if name in record:
                out_arr[ind] = record[name]
            else:
                out_arr[ind] = np.nan
        out_arr = self.imputer.transform([out_arr])
        return out_arr[0]

    def predict(self, datum):
        # Datum is HistoricalDatum-compatible object
        # print("DTree predictor called")
        vct = self._vectorize_json(datum)
        days_to_failure = self.predictor.predict([vct])[0]
        # print(vct)
        # print(days_to_failure)
        level = 'green'
        if days_to_failure <= YELLOW_DAYS:
            level = 'yellow'
        if days_to_failure <= RED_DAYS:
            level = 'red'
        ret = predictors.AlgoResult(
            algo="DTree",
            version=VERSION,
            data_date=self.data_date,
            init_date=self.init_at,
            level=level,
            warn_list=[
                predictors.WarningItem(
                    name="DTreePredictor days to failure",
                    desc="Days until failure predicted by DTreePredictor",
                    value=days_to_failure,
                    level=level
                )
            ],
        )
        return ret
