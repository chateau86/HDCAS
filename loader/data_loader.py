from os import listdir
from os.path import isfile, join
from datetime import datetime, timedelta
import csv
import copy
import hashlib

path = "./csv_data"
BACKEND_URL = "http://10.0.0.115:5000"
API_TOKEN = 'd72aea55-1c05-41c5-a9dd-3c3c0c0e8e2d'

def hash_10e8(str_in):
    return int(hashlib.sha256(str_in.encode('utf-8')).hexdigest(), 16) % 10**8

def register_drive(row):
    req_body = {
        # TODO
        'token': API_TOKEN,
        'serial_number': row['serial_number'],
        'smart_json': str(request_dict[sn].to_json_dict())
    }
    try:
        resp = requests.post(self.backend_url+'/push_data', data=req_body)  # noqa: E501
        if resp.status_code != 200:
            print("Error {:}: {:}".format(resp.status_code, resp.reason))  # noqa: E501
        else:
            print("Request OK")
            body = resp.json()
            if 'error' in body:
                print("Error: {:}".format(body['error']))
    except Exception as e:
        print(e)

SAMPLE_RATE_NORM = 0.01
SAMPLE_RATE_FAIL = 1.00

drive_fate = {}
f_list = listdir(path)
f_list.reverse()
for f in f_list:
    if isfile(join(path, f)):
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

                model = row['model']
                fail = row['failure'] == '1'
                #print(sn, model)
                
                if sn not in drive_fate:
                    if row['failure'] == '1':
                        if hash_10e8(sn) > (SAMPLE_RATE_FAIL * 10**8):
                            continue
                        drive_fate[sn] = 'failed'
                        drives_failed += 1
                    else:
                        if hash_10e8(sn) > (SAMPLE_RATE_NORM * 10**8):
                            continue
                        drive_fate[sn] = 'retired'
                        drives_retired += 1
                    drives_count += 1
                else:
                    drives_count += 1

        print("\tCount: {:}".format(drives_count))
        print("\tRetired: {:}".format(drives_retired))
        print("\tFailed: {:}".format(drives_failed))
