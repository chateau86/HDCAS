from pySMART import DeviceList
import threading
import pprint
import requests
import json


class SMARTReaderThread(threading.Thread):
    def __init__(self, out_queue):
        self.out_queue = out_queue

    def run(self):
        raw_drive_list = DeviceList()
        print(raw_drive_list)
        drive_list = {}
        for dev in raw_drive_list.devices:
            drive_list[dev.serial] = dev
        self.out_queue.put_nowait(drive_list)


class DriveStatusTransmitterThread(threading.Thread):
    def __init__(self, out_queue, backend_url, token):
        self.out_queue = out_queue
        self.backend_url = backend_url
        self.token = token

    def run(self, request_dict):
        for sn in request_dict:
            print("---")
            pprint.pprint(request_dict[sn])
            req_body = {
                'token': self.token,
                'serial_number': sn,
                'smart_json': json.dumps(request_dict[sn].to_json_dict())
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
        print("---")


class DriveStatusRecieverThread(threading.Thread):
    # do get_all_drive_info and get_all
    # Then return the two dicts
    def __init__(self, out_queue, backend_url, token):
        self.out_queue = out_queue
        self.backend_url = backend_url
        self.token = token

    def run(self):
        req_body = {
            'token': self.token,
        }
        info_dict = {}
        try:
            resp = requests.post(self.backend_url+'/get_all_drive_info', data=req_body)  # noqa: E501
            if resp.status_code != 200:
                print("Error {:}: {:}".format(resp.status_code, resp.reason))  # noqa: E501
            else:
                print("Drive info Request OK")
                body = resp.json()
                if 'error' in body:
                    print("Error: {:}".format(body['error']))
                # pprint.pprint(body)
                info_dict = body
        except Exception as e:
            print(e)
        warning_dict = {}
        try:
            resp = requests.post(self.backend_url+'/get_all', data=req_body)  # noqa: E501
            if resp.status_code != 200:
                print("Error {:}: {:}".format(resp.status_code, resp.reason))  # noqa: E501
            else:
                print("Get All Request OK")
                body = resp.json()
                if 'error' in body:
                    print("Error: {:}".format(body['error']))
                # pprint.pprint(body)
                warning_dict = body
        except Exception as e:
            print(e)
        self.out_queue.put_nowait((info_dict, warning_dict))
