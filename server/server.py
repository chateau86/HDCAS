#!/usr/bin/env python3

# run `flask run --host=0.0.0.0`

import os
import queue
import threading
from datetime import datetime
from distutils.util import strtobool

import flask
from flask import request
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.ext.declarative import declarative_base

from uuid import UUID as UUID_class
import json

from predictors.predictors import MasterPredictor
from data_model import SMART_PARAM_ENABLED
from data_model import DriveDetail, Response, User, HistoricalDatum, dump_datetime  # noqa: E501

app = flask.Flask(__name__)
# app.config["DEBUG"] = True
# app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Base = declarative_base()
metadata = Base.metadata

prediction_queue = queue.Queue()

print("Server init ok")
print("DB URL: "+os.environ['DB_URL'])


def decode_datetime(str_in):
    return datetime.strptime(str_in, "%Y-%m-%d %H:%M:%S")


@app.route('/', methods=['GET'])
def home():
    return "<h1>It's alive!!!</h1>"


@app.route('/_test_get_user', methods=['POST'])
def _test_get_user():
    token = request.form["token"]
    user_obj = _get_user_object_from_token(token)
    if user_obj is None:
        return flask.jsonify({
            'error': 'not found',
        })
    else:
        return flask.jsonify({
            'username': user_obj.username,
            'token': user_obj.current_token,
        })


@app.route('/get_token', methods=['POST'])
def get_token():
    username = request.form["username"]
    password = request.form["password"]
    # print(f"Get token: ({username}:{password})")
    user_obj = _get_user_object(username, password)
    if user_obj is None:
        return flask.jsonify({
            'error': 'bad_credential',
        })
    else:
        return flask.jsonify({
            'username': user_obj.username,
            'token': user_obj.current_token,
        })


@app.route('/regen_token', methods=['POST'])
def regen_token():
    username = request.form["username"]
    password = request.form["password"]
    # print(f"Get token: ({username}:{password})")
    user_obj = _get_user_object(username, password)
    if user_obj is None:
        return flask.jsonify({
            'error': 'bad_credential',
        })
    # now do update
    db.session.execute(
        'UPDATE users SET current_token = gen_random_uuid() WHERE username=:user;',  # noqa: E501
        {'user': username}
    )
    db.session.commit()
    return flask.jsonify({
            'result': 'success',
        })


@app.route('/update_user', methods=['POST'])
def update_user():
    username = request.form["username"]
    password = request.form["password"]

    # print(f"Get token: ({username}:{password})")
    user_obj = _get_user_object(username, password)
    if user_obj is None:
        return flask.jsonify({
            'error': 'bad_credential',
        })

    new_email = None
    if "new_password" in request.form:
        new_password = request.form["new_password"]
        # print(f"New password: {new_password}")
        db.session.execute(
            "UPDATE users SET password_hash = crypt(:password, gen_salt('bf')) WHERE username=:user;",  # noqa: E501
            {
                'user': username,
                'password': new_password,
            }
        ).close()

    if "new_email" in request.form:
        new_email = request.form["new_email"]
        # print(f"New email: {new_email}")
        # TODO: Email validation
        user_obj.email = new_email

    # now do update
    db.session.commit()
    return flask.jsonify({
            'result': 'success',
        })


@app.route('/create_user', methods=['POST'])
def create_user():
    username = request.form["username"]
    password = request.form["password"]
    email = request.form["email"]
    if _get_user_object(username, password=None) is not None:
        return flask.jsonify({
            'error': 'user_exists',
        })
    db.session.add(
        User(
            username=username,
            email=email,
        )
    )
    db.session.commit()
    db.session.execute(
        "UPDATE users SET password_hash = crypt(:password, gen_salt('bf')) WHERE username=:user;",  # noqa: E501
        {
            'user': username,
            'password': password,
        }
    ).close()
    # now do update
    db.session.commit()
    user_obj = _get_user_object(username, password=None)
    return flask.jsonify({
            'result': 'success',
            'username': user_obj.username,
            'email': user_obj.email,
            'token': user_obj.current_token,
        })


@app.route('/get_all', methods=['POST'])
def get_all():
    token = request.form["token"]
    user_obj = _get_user_object_from_token(token)
    if user_obj is None:
        return flask.jsonify({
            'error': 'not found',
        })
    username = user_obj.username
    responses = db.session.query(Response, DriveDetail)\
        .join(DriveDetail)\
        .filter_by(username=username).all()
    return flask.jsonify(_serialize_responses(responses))


@app.route('/get_all_active', methods=['POST'])
def get_all_active():
    token = request.form["token"]
    user_obj = _get_user_object_from_token(token)
    if user_obj is None:
        return flask.jsonify({
            'error': 'not found',
        })
    username = user_obj.username
    responses = db.session.query(Response, DriveDetail)\
        .join(DriveDetail)\
        .filter_by(username=username)\
        .filter(DriveDetail.drive_status == 'active').all()
    return flask.jsonify(_serialize_responses(responses))


@app.route('/get_one', methods=['POST'])
def get_one():
    token = request.form["token"]
    serial = request.form["serial_number"]
    user_obj = _get_user_object_from_token(token)
    if user_obj is None:
        return flask.jsonify({
                'error': 'not found',
            }),
    username = user_obj.username
    responses = db.session.query(Response, DriveDetail)\
        .join(DriveDetail)\
        .filter_by(username=username)\
        .filter_by(serial_number=serial).all()
    if len(responses) == 0:
        return flask.jsonify({
            'error': 'drive not found',
        }), 404
    return flask.jsonify(_serialize_responses(responses))


@app.route('/get_drive_info', methods=['POST'])
def get_drive_info():
    token = request.form["token"]
    serial = request.form["serial_number"]
    user_obj = _get_user_object_from_token(token)
    if user_obj is None:
        return flask.jsonify({
                'error': 'not found',
            }),
    username = user_obj.username
    drive = DriveDetail.query\
        .filter_by(username=username)\
        .filter_by(serial_number=serial).first()
    if drive is None:
        return flask.jsonify({
            'error': 'drive not found',
        }), 404
    return flask.jsonify(drive.to_json_dict())


@app.route('/push_data', methods=['POST'])
def push_data():
    token = request.form["token"]
    serial = request.form["serial_number"]
    smart_json = request.form["smart_json"]
    user_obj = _get_user_object_from_token(token)
    if user_obj is None:
        return flask.jsonify({
            'error': 'not found',
        })
    username = user_obj.username
    drive = DriveDetail.query\
        .filter_by(username=username)\
        .filter_by(serial_number=serial).first()
    if drive is None:
        return flask.jsonify({
            'error': 'Drive not registered',
        })
    # print("smart_json: "+smart_json)
    try:
        smart_json_dict = json.loads(smart_json)
    except json.JSONDecodeError:
        return flask.jsonify({
            'error': 'Malformed JSON payload',
        })
    smart_json_dict['drive_size_bytes'] = drive.drive_size_bytes
    smart_json_dict['drive_lba_size_bytes'] = drive.drive_lba_size_bytes
    smart_json_dict['drive_lba_count'] = (int)(drive.drive_size_bytes / (float)(drive.drive_lba_size_bytes))  # noqa: E501
    if 'smart_241_raw' in smart_json_dict:
        smart_json_dict['smart_241_cycles'] = int(smart_json_dict['smart_241_raw']) / (float)(smart_json_dict['drive_lba_count'])  # noqa: E501
    if 'smart_242_raw' in smart_json_dict:
        smart_json_dict['smart_242_cycles'] = int(smart_json_dict['smart_242_raw']) / (float)(smart_json_dict['drive_lba_count'])  # noqa: E501

    history_record = None
    new_record = False
    if 'date_override' in request.form:
        created_at = decode_datetime(request.form['date_override'])
        history_record = HistoricalDatum.query\
            .filter_by(created_at=created_at)\
            .filter_by(username=username)\
            .filter_by(serial_number=serial).first()
    if history_record is None:
        new_record = True
        history_record = HistoricalDatum(
            serial_number=serial,
            username=username,
            drive_model=drive.drive_model,
        )
        if 'date_override' in request.form:
            history_record.created_at = decode_datetime(request.form['date_override'])  # noqa: E501
    for var in SMART_PARAM_ENABLED:
        raw_name = 'smart_{:}_raw'.format(var)
        norm_name = 'smart_{:}_normalized'.format(var)
        if raw_name in smart_json_dict:
            smart_json_dict[raw_name] = int(smart_json_dict[raw_name])
            history_record.__setattr__(raw_name, int(smart_json_dict[raw_name]))  # noqa: E501
        if norm_name in smart_json_dict:
            smart_json_dict[norm_name] = int(smart_json_dict[norm_name])
            history_record.__setattr__(norm_name, int(smart_json_dict[norm_name]))  # noqa: E501
    if 'smart_241_cycles' in smart_json_dict:
        history_record.smart_241_cycles = smart_json_dict['smart_241_cycles']
    if 'smart_242_cycles' in smart_json_dict:
        history_record.smart_242_cycles = smart_json_dict['smart_242_cycles']

    if new_record:
        db.session.add(history_record)
    db.session.commit()
    # Put request into response update queue
    if 'date_override' not in request.form:
        prediction_queue.put_nowait((username, serial, smart_json_dict))
    return flask.jsonify({
            'status': 'ok',
        })


@app.route('/update_drive_info', methods=['POST'])
def update_drive_info():
    token = request.form["token"]
    serial = request.form["serial_number"]
    user_obj = _get_user_object_from_token(token)
    if user_obj is None:
        return flask.jsonify({
            'error': 'user not found',
        })
    username = user_obj.username
    drive = DriveDetail.query\
        .filter_by(username=username)\
        .filter_by(serial_number=serial).first()
    if drive is None:
        # TODO: Create the new record
        drive = DriveDetail(
            serial_number=serial,
            username=username,
            is_ssd=False,
        )
        try:
            if 'model' in request.form:
                drive.drive_model = request.form['model']
            if 'status' in request.form:
                if request.form['status'] not in ['active', 'retired', 'failed']:  # noqa: E501
                    return flask.jsonify({
                        'error': 'invalid status',
                    })
                drive.drive_status = request.form["status"]
            if 'nickname' in request.form:
                drive.drive_nickname = request.form['nickname']
            if 'total_size_byte' in request.form:
                drive.drive_size_bytes = int(request.form['total_size_byte'])
            if 'lba_size_byte' in request.form:
                drive.drive_lba_size_bytes = int(request.form['lba_size_byte'])
            if 'date_override' in request.form:
                drive.status_date = decode_datetime(request.form['date_override'])  # noqa: E501
            if 'is_ssd' in request.form:
                drive.is_ssd = strtobool(request.form['is_ssd'])
        except Exception as e:
            return flask.jsonify({
                'error': 'Malformed input: {:}'.format(e),
            })
        db.session.add(drive)
        db.session.commit()
        return flask.jsonify({
            'status': 'ok',
            'drive': drive.to_json_dict(),
        })
    try:
        if 'model' in request.form:
            drive.drive_model = request.form['model']
        if 'status' in request.form:
            if request.form['status'] not in ['active', 'retired', 'failed']:  # noqa: E501
                return flask.jsonify({
                    'error': 'invalid status',
                })
            drive.drive_status = request.form["status"]
        if 'nickname' in request.form:
            drive.drive_nickname = request.form['nickname']
        if 'total_size_byte' in request.form:
            drive.drive_size_bytes = int(request.form['total_size_byte'])
        if 'lba_size_byte' in request.form:
            drive.drive_lba_size_bytes = int(request.form['lba_size_byte'])
        if 'date_override' in request.form:
            drive.status_date = decode_datetime(request.form['date_override'])  # noqa: E501
        else:
            drive.status_date = datetime.now()
        if 'is_ssd' in request.form:
            drive.is_ssd = strtobool(request.form['is_ssd'])
    except Exception as e:
        return flask.jsonify({
            'error': 'Malformed input: {:}'.format(e),
        })
    db.session.commit()
    return flask.jsonify({
            'status': 'ok',
            'drive': drive.to_json_dict(),
        })


class PredictionWorkerThread(threading.Thread):
    def __init__(self, in_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.master_predictor = MasterPredictor()

    def run(self):
        with app.app_context():
            while True:
                try:
                    (username, serial, smart_json) = self.in_queue.get(block=True, timeout=0.1)  # noqa: E501
                except queue.Empty:
                    continue
                res = self.master_predictor.predict(smart_json)
                # get a new copy so its session will still be alive
                drive = DriveDetail.query\
                    .filter_by(username=username)\
                    .filter_by(serial_number=serial).first()
                # TODO: Get old response by serial number and delete
                # print("will now update response for {:}".format(drive.serial_number))  # noqa: E501
                Response.query.filter_by(serial_number=drive.serial_number).delete()  # noqa: E501
                old_response = Response.query\
                    .filter_by(serial_number=drive.serial_number).first()
                if old_response is None:
                    db.session.add(
                        Response(
                            serial_number=drive.serial_number,
                            username=drive.username,
                            raw_smart_json=json.dumps(smart_json),
                            response_json=json.dumps(res),
                            created_at=datetime.now(),
                        )
                    )
                else:
                    old_response.raw_smart_json = json.dumps(smart_json)
                    old_response.response_json = json.dumps(res)
                    old_response.created_at = datetime.now()
                db.session.commit()
                # print("Response for {:} updated".format(drive.serial_number))  # noqa: E501


def _get_user_object(username, password=''):
    user_obj = User.query.filter_by(username=username).first()
    if user_obj is None:
        return None
    if password is None:
        return user_obj
    is_correct = db.session.execute('SELECT :hash = crypt(:pass, :hash);',
                                    {'hash': user_obj.password_hash,
                                     'pass': password}).first()[0]
    if not is_correct:
        return None
    else:
        return user_obj


def _get_user_object_from_token(user_token):
    if not _validate_uuid(user_token):
        return None
    user_obj = User.query.filter_by(current_token=user_token).first()
    return user_obj


def _serialize_responses(responses):
    return_dict = {}
    for resp in responses:
        print("resp: {:}".format(resp))
        return_dict[resp[0].serial_number] = {
            'drive_status': resp[1].drive_status,
            'drive_nickname': resp[1].drive_nickname,
            'smart_json': json.loads(resp[0].raw_smart_json),
            'response_json': json.loads(resp[0].response_json),
            'created_at': dump_datetime(resp[0].created_at),
        }
    return return_dict


def _validate_uuid(uuid_str):
    try:
        uuid_obj = UUID_class(uuid_str, version=4)
    except ValueError:
        return False
    return str(uuid_obj).replace('-', '') == uuid_str.replace('-', '')


def _start_server():
    pred = PredictionWorkerThread(prediction_queue)
    pred.start()
    # app.run(host='0.0.0.0', threaded=False, processes=16)
    # app.run(host='0.0.0.0', threaded=False, processes=3)
    app.run(host='0.0.0.0', threaded=True)


if __name__ == '__main__':
    master_predictor = MasterPredictor()
    master_predictor.train(os.environ['DB_URL'])
    _start_server()
