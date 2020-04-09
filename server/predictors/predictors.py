from predictors.loopback import LoopbackPredictor
from predictors.dtree import DTreePredictor
from datetime import datetime
from data_model import dump_datetime


class WarningItem:
    def __init__(
                self,
                name="",
                desc="",
                value="",
                level='green'
            ):
        self.name = name
        self.desc = desc
        self.value = value
        self.level = level

    def to_json_dict(self):
        return {
            'name': self.name,
            'desc': self.desc,
            'value': self.value,
            'level': self.level,
        }

    def __repr__(self):
        return str(self.to_json_dict())


class AlgoResult:
    def __init__(
                self,
                algo="",
                version="UNKNOWN",
                data_date=datetime.utcfromtimestamp(0),
                init_date=datetime.now(),
                level='green',
                warn_list=[]
            ):
        self.algo = algo
        self.version = version
        self.init_date = init_date
        self.data_date = data_date
        self.warn_list = warn_list
        self.level = level

    def to_json_dict(self):
        warn_json_list = []
        for w in self.warn_list:
            warn_json_list.append(w.to_json_dict())
        return {
            'algo': self.algo,
            'version': self.version,
            'init_date': dump_datetime(self.init_date),
            'data_date': dump_datetime(self.data_date),
            'level': self.level,
            'warn_list': warn_json_list,
        }

    def __repr__(self):
        return str(self.to_json_dict())


class MasterPredictor:
    def __init__(self):
        self.predictor_dict = {}
        self.predictor_dict['loopback'] = LoopbackPredictor.LoopbackPredictor()
        self.predictor_dict['dtree'] = DTreePredictor.DTreePredictor()

    def predict(self, datum):
        out_dict = {}
        for pred in self.predictor_dict:
            out_dict[pred] = self.predictor_dict[pred]\
                .predict(datum).to_json_dict()
        return out_dict

    def train(self, DB_URL):
        for pred in self.predictor_dict:
            self.predictor_dict[pred].train(DB_URL)
