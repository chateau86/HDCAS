#!/usr/bin/env python3

# run `flask run --host=0.0.0.0`

import os
from datetime import datetime

import flask
from flask import request
from flask_sqlalchemy import SQLAlchemy

app = flask.Flask(__name__)
app.config["DEBUG"] = True,
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URL']

db = SQLAlchemy(app)


print("Server init ok")
print("DB URL: "+os.environ['DB_URL'])


# https://stackoverflow.com/questions/7102754/jsonify-a-sqlalchemy-result-set-in-flask
# Python can't even serialize DateTime by itself. WTF??
def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]


class test_message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.String())
    timestamp = db.Column(db.DateTime(timezone=False), default=datetime.utcnow)

    def __repr__(self):
        return str(self.id) + " " + str(self.timestamp) + ": " + self.msg

    @property
    def serialize(self):
        return {
            'id': self.id,
            'timestamp': dump_datetime(self.timestamp),
            'message': self.msg,
        }


@app.route('/', methods=['GET'])
def home():
    return "<h1>It's alive!!!</h1>"


@app.route('/msg', methods=['GET'])
def read_msg():
    messages = db.session \
        .query(test_message) \
        .order_by(test_message.timestamp) \
        .all()
    print(messages)
    return flask.jsonify(json_list=[i.serialize for i in messages])


@app.route('/send', methods=['POST'])
def put_test_msg():
    msg = request.form["msg"]
    print("Got msg: " + msg)
    db.session.add(test_message(msg=msg))
    db.session.commit()
    return "<h1>Msg recieved</h1>"


# update the schema
# Will not overwrite existing table per
# https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.MetaData.create_all
db.create_all()
