#!/usr/bin/env python3

# run `flask run --host=0.0.0.0`

import os

import flask
from flask import request
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import BigInteger, Column, DateTime, Enum, Integer, Text, text, Float, ForeignKey  # noqa: E501
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from uuid import UUID as UUID_class

from predictors import MasterPredictor

app = flask.Flask(__name__)
app.config["DEBUG"] = True
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Base = declarative_base()
metadata = Base.metadata

master_predictor = MasterPredictor.MasterPredictor()

print("Server init ok")
print("DB URL: "+os.environ['DB_URL'])


# https://stackoverflow.com/questions/7102754/jsonify-a-sqlalchemy-result-set-in-flask
# Python can't even serialize DateTime by itself. WTF??
def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]


'''sqlacodegen $DB_URL'''


class DriveDetail(db.Model):
    __tablename__ = 'drive_details'

    id = Column(Integer, primary_key=True, server_default=text("nextval('drive_details_id_seq'::regclass)"))  # noqa: E501
    serial_number = Column(Text, nullable=False)
    username = Column(Text, nullable=False)
    drive_model = Column(Text, nullable=False, server_default=text("'unknown'::text"))  # noqa: E501
    drive_status = Column(Enum('active', 'retired', 'failed', name='drive_status_enum'), server_default=text("'active'::drive_status_enum"))  # noqa: E501
    drive_nickname = Column(Text)
    drive_size_bytes = Column(BigInteger, server_default=text("0"))
    drive_lba_size_bytes = Column(Integer, server_default=text("512"))
    status_date = Column(DateTime, server_default=text("now()"))


class Response(db.Model):
    __tablename__ = 'responses'

    id = Column(Integer, primary_key=True, server_default=text("nextval('responses_id_seq'::regclass)"))  # noqa: E501
    serial_number = Column(ForeignKey('drive_details.serial_number'), nullable=False)  # noqa: E501
    username = Column(ForeignKey('users.username'), ForeignKey('users.username'), ForeignKey('users.username'), ForeignKey('users.username'), nullable=False)  # noqa: E501
    raw_smart_json = Column(Text)
    response_json = Column(Text)
    created_at = Column(DateTime, server_default=text("now()"))

    drive_detail = relationship('DriveDetail')
    user = relationship('User', primaryjoin='Response.username == User.username')  # noqa: E501
    user1 = relationship('User', primaryjoin='Response.username == User.username')  # noqa: E501
    user2 = relationship('User', primaryjoin='Response.username == User.username')  # noqa: E501
    user3 = relationship('User', primaryjoin='Response.username == User.username')  # noqa: E501


class User(db.Model):
    __tablename__ = 'users'

    username = Column(Text, primary_key=True)
    email = Column(Text)
    password_hash = Column(Text, nullable=False, server_default='invalid')
    current_token = Column(UUID, server_default='gen_random_uuid()')


class HistoricalDatum(db.Model):
    __tablename__ = 'historical_data'

    id = Column(Integer, primary_key=True, server_default=text("nextval('historical_data_id_seq'::regclass)"))  # noqa: E501
    serial_number = Column(ForeignKey('drive_details.serial_number'), nullable=False)  # noqa: E501
    drive_model = Column(Text, nullable=False, server_default=text("'unknown'::text"))  # noqa: E501
    drive_status = Column(Enum('active', 'retired', 'failed', name='drive_status_enum'), server_default=text("'active'::drive_status_enum"))  # noqa: E501
    smart_1_raw = Column(Integer)
    smart_1_normalized = Column(Integer)
    smart_4_raw = Column(Integer)
    smart_4_normalized = Column(Integer)
    smart_5_raw = Column(Integer)
    smart_5_normalized = Column(Integer)
    smart_7_raw = Column(Integer)
    smart_7_normalized = Column(Integer)
    smart_9_raw = Column(Integer)
    smart_9_normalized = Column(Integer)
    smart_12_raw = Column(Integer)
    smart_12_normalized = Column(Integer)
    smart_190_raw = Column(Integer)
    smart_190_normalized = Column(Integer)
    smart_192_raw = Column(Integer)
    smart_192_normalized = Column(Integer)
    smart_193_raw = Column(Integer)
    smart_193_normalized = Column(Integer)
    smart_197_raw = Column(Integer)
    smart_197_normalized = Column(Integer)
    smart_198_raw = Column(Integer)
    smart_198_normalized = Column(Integer)
    smart_199_raw = Column(Integer)
    smart_199_normalized = Column(Integer)
    smart_240_raw = Column(Integer)
    smart_240_normalized = Column(Integer)
    smart_241_raw = Column(Integer)
    smart_241_normalized = Column(Integer)
    smart_241_cycles = Column(Float)
    smart_242_raw = Column(Integer)
    smart_242_normalized = Column(Integer)
    smart_242_cycles = Column(Float)

    drive_detail = relationship('DriveDetail')


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
    print(f"Get token: ({username}:{password})")
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
    print(f"Get token: ({username}:{password})")
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

    print(f"Get token: ({username}:{password})")
    user_obj = _get_user_object(username, password)
    if user_obj is None:
        return flask.jsonify({
            'error': 'bad_credential',
        })

    new_email = None
    if "new_password" in request.form:
        new_password = request.form["new_password"]
        print(f"New password: {new_password}")
        db.session.execute(
            "UPDATE users SET password_hash = crypt(:password, gen_salt('bf')) WHERE username=:user;",  # noqa: E501
            {
                'user': username,
                'password': new_password,
            }
        ).close()

    if "new_email" in request.form:
        new_email = request.form["new_email"]
        print(f"New email: {new_email}")
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
        })
    username = user_obj.username
    responses = Response.query\
        .join(DriveDetail)\
        .filter_by(username=username)\
        .filter_by(serial_number=serial).all()
    return flask.jsonify(_serialize_responses(responses))


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
    print("smart_json: "+smart_json)
    # TODO: Decode smart_json to HistoricalDatum and save to DB
    # TODO: Put request into response update queue
    res = master_predictor.predict(None)
    return flask.jsonify(res)


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
        return_dict[resp[0].serial_number] = {
            'drive_status': resp[1].drive_status,
            'drive_nickname': resp[1].drive_nickname,
            'smart_json': resp[0].raw_smart_json,
            'response_json': resp[0].response_json,
            'created_at': dump_datetime(resp[0].created_at),
        }
    return return_dict


def _validate_uuid(uuid_str):
    try:
        uuid_obj = UUID_class(uuid_str, version=4)
    except ValueError:
        return False
    return str(uuid_obj).replace('-', '') == uuid_str.replace('-', '')
