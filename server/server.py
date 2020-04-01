#!/usr/bin/env python3

# run `flask run --host=0.0.0.0`

import os

import flask
from flask import request
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import BigInteger, Column, DateTime, Enum, Integer, Text, text, Float  # noqa: E501
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

app = flask.Flask(__name__)
app.config["DEBUG"] = True
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Base = declarative_base()
metadata = Base.metadata


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


class DriveDetail(Base):
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


class Response(Base):
    __tablename__ = 'responses'

    id = Column(Integer, primary_key=True, server_default=text("nextval('responses_id_seq'::regclass)"))  # noqa: E501
    serial_number = Column(Text, nullable=False)
    username = Column(Text, nullable=False)
    raw_smart_json = Column(Text)
    response_json = Column(Text)
    created_at = Column(DateTime, server_default=text("now()"))


class User(db.Model):
    __tablename__ = 'users'

    username = Column(Text, primary_key=True)
    email = Column(Text)
    password_hash = Column(Text, nullable=False, server_default='invalid')
    current_token = Column(UUID, server_default='gen_random_uuid()')


class HistoricalDatum(Base):
    __tablename__ = 'historical_data'

    id = Column(Integer, primary_key=True, server_default=text("nextval('historical_data_id_seq'::regclass)"))  # noqa: E501
    serial_number = Column(Text, nullable=False)
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


@app.route('/', methods=['GET'])
def home():
    return "<h1>It's alive!!!</h1>"


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
