from sqlalchemy import Column, ForeignKey  # noqa: E501
from sqlalchemy import BigInteger, DateTime, Enum, Integer, Text, text, Float, Boolean  # noqa: E501
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import flask
from flask_sqlalchemy import SQLAlchemy
'''sqlacodegen $DB_URL'''

app = flask.Flask(__name__)
db = SQLAlchemy(app)

SMART_PARAM_ENABLED = [1, 4, 5, 7, 9, 12, 190, 192, 193, 194, 197, 198, 199, 240, 241, 242]  # noqa: E501
SMART_PARAM_CYCLES = [241, 242]


# https://stackoverflow.com/questions/7102754/jsonify-a-sqlalchemy-result-set-in-flask
# Python can't even serialize DateTime by itself. WTF??
def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")


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
    is_ssd = Column(Boolean)

    def to_json_dict(self):
        return {
            'serial_number': self.serial_number,
            'drive_model': self.drive_model,
            'drive_status': str(self.drive_status),
            'drive_nickname': self.drive_nickname,
            'drive_total_size_byte': self.drive_size_bytes,
            'drive_lba_size_byte': self.drive_lba_size_bytes,
            'status_date': dump_datetime(self.status_date),
            'is_ssd': self.is_ssd,
        }


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
    username = Column(ForeignKey('users.username'), nullable=False)
    smart_1_raw = Column(BigInteger)
    smart_1_normalized = Column(BigInteger)
    smart_4_raw = Column(BigInteger)
    smart_4_normalized = Column(BigInteger)
    smart_5_raw = Column(BigInteger)
    smart_5_normalized = Column(BigInteger)
    smart_7_raw = Column(BigInteger)
    smart_7_normalized = Column(BigInteger)
    smart_9_raw = Column(BigInteger)
    smart_9_normalized = Column(BigInteger)
    smart_12_raw = Column(BigInteger)
    smart_12_normalized = Column(BigInteger)
    smart_190_raw = Column(BigInteger)
    smart_190_normalized = Column(BigInteger)
    smart_192_raw = Column(BigInteger)
    smart_192_normalized = Column(BigInteger)
    smart_193_raw = Column(BigInteger)
    smart_193_normalized = Column(BigInteger)
    smart_197_raw = Column(BigInteger)
    smart_197_normalized = Column(BigInteger)
    smart_198_raw = Column(BigInteger)
    smart_198_normalized = Column(BigInteger)
    smart_199_raw = Column(BigInteger)
    smart_199_normalized = Column(BigInteger)
    smart_240_raw = Column(BigInteger)
    smart_240_normalized = Column(BigInteger)
    smart_241_raw = Column(BigInteger)
    smart_241_normalized = Column(BigInteger)
    smart_241_cycles = Column(Float)
    smart_242_raw = Column(BigInteger)
    smart_242_normalized = Column(BigInteger)
    smart_242_cycles = Column(Float)
    created_at = Column(DateTime, server_default=text("now()"))

    drive_detail = relationship('DriveDetail')
    user = relationship('User')
