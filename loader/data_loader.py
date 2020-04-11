from os import listdir
from os.path import isfile, join
from datetime import datetime, timedelta
import csv
import copy
import hashlib
import requests
import json
from concurrent.futures import ThreadPoolExecutor

path = "./csv_data"
BACKEND_URL = "http://10.0.0.115:5000"
API_TOKEN = 'd72aea55-1c05-41c5-a9dd-3c3c0c0e8e2d'  # backblaze

SMART_PARAM_ENABLED = [1, 4, 5, 7, 9, 12, 190, 192, 193, 194, 197, 198, 199, 240, 241, 242]  # noqa: E501
SAMPLE_RATE_ACTIVE = 0.001
SAMPLE_RATE_RETIRED = 1.000
SAMPLE_RATE_FAIL = 1.000
FORCE_PRED_MODE = True
DEMO_MODE = True
if DEMO_MODE:
    API_TOKEN = 'd065ad28-fe88-4edf-95bb-8663605659d2'  # backblaze_demo

def hash_10e8(str_in):
    return int(hashlib.sha256(str_in.encode('utf-8')).hexdigest(), 16) % 10**8
    
def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")


def register_drive(row, status='active', date=datetime.now()):
    req_body = {
        'token': API_TOKEN,
        'serial_number': row['serial_number'],
        'status': status,
        'model': row['model'],
        'total_size_byte': row['capacity_bytes'],
        'date_override': dump_datetime(date),
        'is_ssd': 'False',
    }
    try:
        resp = requests.post(BACKEND_URL+'/update_drive_info', data=req_body)  # noqa: E501
        if resp.status_code != 200:
            print("Error {:}: {:}".format(resp.status_code, resp.reason))  # noqa: E501
        else:
            #print("Request OK")
            body = resp.json()
            if 'error' in body:
                print("Error: {:}".format(body['error']))
    except Exception as e:
        print(e)
    # print("Registered {:}".format(row['serial_number']))


def maybe_register_drive(row, status='active', date=datetime.now()):
    req_body = {
        'token': API_TOKEN,
        'serial_number': row['serial_number'],
    }
    try:
        resp = requests.post(BACKEND_URL+'/get_drive_info', data=req_body)  # noqa: E501
        if resp.status_code == 404:
            #print("{:} registering".format(row['serial_number']))
            register_drive(row, status, date)
        else:
            pass
            # print("{:} already registered".format(row['serial_number']))
    except Exception as e:
        print(e)
    send_smart_info(row, date)


def send_smart_info(row, date=datetime.now()):
    #print(row)
    # build smart_json dict
    smart_json_dict = {}
    for var in SMART_PARAM_ENABLED:
        raw_name = 'smart_{:}_raw'.format(var)
        norm_name = 'smart_{:}_normalized'.format(var)
        if raw_name in row and row[raw_name] != '':
            smart_json_dict[raw_name] = row[raw_name]
        if norm_name in row and row[norm_name] != '':
            smart_json_dict[norm_name] = row[norm_name]
    #print(smart_json_dict)
    req_body = {
        'token': API_TOKEN,
        'serial_number': row['serial_number'],
        'date_override': dump_datetime(date),
        'smart_json': json.dumps(smart_json_dict),
    }
    if FORCE_PRED_MODE:
        req_body['force_predict'] = 'true'
    try:
        resp = requests.post(BACKEND_URL+'/push_data', data=req_body)  # noqa: E501
        if resp.status_code != 200:
            print("Error {:}: {:}".format(resp.status_code, resp.reason))  # noqa: E501
        else:
            #print("Request OK")
            body = resp.json()
            if 'error' in body:
                print("Error: {:}".format(body['error']))
    except Exception as e:
        print(e)
    # print("Updated {:}".format(row['serial_number']))


drive_fate = {}
f_list = listdir(path)
f_list.reverse()
file_index = 0
first_day = True
for f in f_list:
    file_index += 1
    day_start = datetime.now()
    executor = ThreadPoolExecutor(128)
    print("File {:}/{:}: {:}".format(file_index, len(f_list), dump_datetime(day_start)))
    if not isfile(join(path, f)):
        continue
    date_str = f.split('.')[0]
    date_obj = datetime.strptime(date_str,"%Y-%m-%d") + timedelta(hours=1)
    print(date_obj)
    drives_failed = 0
    drives_retired = 0
    drives_count = 0
    with open(join(path, f), 'r') as f_in:
        reader = csv.DictReader(f_in)
        for row in reader:
            sn = row['serial_number']
            if DEMO_MODE:
                sn = sn + '-DEMO'
                row['serial_number'] = sn
            model = row['model']
            fail = row['failure'] == '1'
            #print(sn, model)
            if sn not in drive_fate:
                status = 'active'
                if row['failure'] == '1':
                    if hash_10e8(sn) > (SAMPLE_RATE_FAIL * 10**8):
                        drive_fate[sn] = 'skipped'
                        continue
                    status = 'failed'
                    drive_fate[sn] = status
                    drives_failed += 1
                else:
                    if first_day:
                        status = 'active'
                        if hash_10e8(sn) > (SAMPLE_RATE_ACTIVE * 10**8):
                            drive_fate[sn] = 'skipped'
                            continue
                    else:
                        status = 'retired'
                        if hash_10e8(sn) > (SAMPLE_RATE_RETIRED * 10**8):
                            drive_fate[sn] = 'skipped'
                            continue
                        drives_retired += 1
                    drive_fate[sn] = status
                future = executor.submit(maybe_register_drive, row, status, date_obj)
                #maybe_register_drive(row, status, date_obj)
                drives_count += 1
            else:
                if drive_fate[sn] == 'skipped':
                    continue
                if not FORCE_PRED_MODE and not DEMO_MODE:
                    future = executor.submit(send_smart_info, row, date_obj)
                drives_count += 1
                # send_smart_info(row, date_obj)
    executor.shutdown(wait=True)
    first_day = False
    print("\tCount: {:}".format(drives_count))
    print("\tRetired: {:}".format(drives_retired))
    print("\tFailed: {:}".format(drives_failed))
    elapsed = (datetime.now() - day_start).total_seconds()
    print("\tLoaded in: {:} s Rate: {:} row/s".format(elapsed, drives_count/elapsed))
