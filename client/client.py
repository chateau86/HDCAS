#!/usr/bin/env python3

from tkinter import Tk, Frame, Label, Button, scrolledtext, Toplevel, messagebox  # noqa: E501

import queue
import ctypes
import os
import sys
import requests
# import pprint

from worker import SMARTReaderThread, DriveStatusTransmitterThread, DriveStatusRecieverThread  # noqa: E501
from utils import DriveInfoRequestPayload, WarningItem, DriveItem, AttrItem  # noqa: E501
from utils import ListWithScroll, EntryWithLabel, SelectWithLabel, CheckWithLabel, PasswordWithLabel  # noqa: E501
from utils import SURROGATE_PAIRS


BACKEND_URL = "http://10.0.0.115:5000"
# API_TOKEN = "c91a3ec3-0ad2-471e-8899-3211da76074f"  # test
# API_TOKEN = "a72fbda1-4cbc-4e0f-b457-d26cab89e125"  # chateau86
# API_TOKEN = "d72aea55-1c05-41c5-a9dd-3c3c0c0e8e2d"  # backblaze
API_TOKEN = "d065ad28-fe88-4edf-95bb-8663605659d2"  # backblaze_demo
API_TOKEN = None
# TODO: Ask user for token


class MainWindow(Frame):
    def __init__(self, master=None):
        self.drive_list = []
        self.drive_dict = {}
        self.current_drive = None

        self.master = master
        self.master.title("HDCAS")
        self.master.minsize(height=200, width=600)

        self.smart_device_queue = queue.Queue()
        self.network_pull_queue = queue.Queue()
        self.network_send_response_queue = queue.Queue()
        self.child_window = None

        top_controls_frame = Frame(master)
        drive_list_frame = Frame(master)
        drive_detail_frame = Frame(master)
        top_controls_frame.grid(sticky='nsew', row=0, column=0)
        drive_list_frame.grid(sticky="nsew", row=1, column=0)
        drive_detail_frame.grid(sticky="nsew", row=2, column=0)
        master.grid_rowconfigure(0, weight=0)
        master.grid_rowconfigure(1, weight=0)
        master.grid_rowconfigure(2, weight=1)
        master.grid_columnconfigure(0, weight=1)

        # init top controls
        btn = Button(top_controls_frame,
                     text="Login",
                     command=self._login)
        btn.pack(side='left')
        btn = Button(top_controls_frame,
                     text="Load SMART data",
                     command=self.do_SMART_read)
        btn.pack(side='left')
        btn = Button(top_controls_frame,
                     text="Download data",
                     command=self.do_network_pull)
        btn.pack(side='left')
        btn = Button(top_controls_frame,
                     text="Register/update selected drive",
                     command=self.do_drive_register)
        btn.pack(side='left')

        # init drive list frame
        drive_list = ListWithScroll(drive_list_frame,
                                    self._drive_click_callback)
        drive_list.get_frame().pack(fill='both')

        self._drive_list = drive_list.get_list_box()

        # init drive details frame
        drive_msg = Label(drive_detail_frame,
                          text="Drive name here",
                          anchor='w',
                          )
        drive_msg.grid(row=0, column=0, sticky='nsew')
        drive_detail_frame.grid_columnconfigure(0, weight=1)
        self._drive_msg = drive_msg

        warning_list = ListWithScroll(drive_detail_frame,
                                      self._warning_click_callback)
        warning_list.get_frame().grid(row=1, column=0, sticky="nsew")

        warning_detail_frame = Frame(drive_detail_frame)
        warning_detail_frame.grid(sticky="nsew", row=2, column=0)
        drive_detail_frame.grid_rowconfigure(2, weight=1)
        warning_msg_label = Label(warning_detail_frame,
                                  text="Warning details",
                                  anchor='w',)
        warning_msg_label.grid(row=0, column=0, sticky='nsew')
        warning_msg = scrolledtext.ScrolledText(
            warning_detail_frame,
            state='disabled',
            width=40, height=10,
            wrap='word',
        )
        warning_msg.grid(row=1, column=0, sticky='nsew')
        warning_detail_frame.grid_rowconfigure(1, weight=1)
        warning_detail_frame.grid_columnconfigure(0, weight=1)

        self.master.after(100, self._load_user_token)

        self._warning_list = warning_list.get_list_box()
        self._warning_msg = warning_msg
        self._watch_smart_data_queue()
        self._watch_net_send_resp_queue()
        self._watch_net_recv_resp_queue()

    def _load_user_token(self):
        global API_TOKEN
        try:
            with open('token.txt', 'r') as f_in:
                API_TOKEN = f_in.read().strip()
            self.do_network_pull()
        except:  # noqa: E722
            # TODO Ask user for token
            # API_TOKEN = "d065ad28-fe88-4edf-95bb-8663605659d2"
            self.child_window = LoginWindow()

    def _login(self):
        self.drive_list = []
        self.drive_dict = {}
        self.current_drive = None
        self._update_drive_list()
        self.child_window = LoginWindow()

    def _update_drive_list(self):
        # now sort the dict
        drive_list = []
        for sn in self.drive_dict:
            drive_list.append(self.drive_dict[sn])
        drive_list.sort(key=lambda x: x.ui_sort_key())
        # print(drive_list)
        self._drive_list.delete(0, 'end')
        self.drive_list = drive_list
        self.current_drive = None
        for i in range(len(self.drive_list)):
            self._drive_list.insert(i, self.drive_list[i].get_display_name())
        self._update_warn_box()

    def _drive_click_callback(self, event):
        w = event.widget
        if len(w.curselection()) == 0:
            self.current_drive = None
            self._drive_msg.configure(text="No drive selected")
        else:
            index = int(w.curselection()[0])
            self.current_drive = self.drive_list[index]
            self._drive_msg.configure(text=str(self.current_drive.get_display_name()))  # noqa: E501
        self._update_warn_box()

    def _update_warn_box(self):
        self._warning_list.delete(0, 'end')
        if self.current_drive is not None:
            for i in range(len(self.current_drive.warnings)):
                self._warning_list \
                    .insert(i, self.current_drive.warnings[i].get_display_name())  # noqa: E501
        self._set_warning_msg("No warning selected")

    def _warning_click_callback(self, event):
        w = event.widget
        if len(w.curselection()) == 0:
            # self.current_drive = None
            self._set_warning_msg("No warning selected")
            return
        index = int(w.curselection()[0])
        self._set_warning_msg(str(self.current_drive.warnings[index].desc))
        return

    def _set_warning_msg(self, msg):
        self._warning_msg['state'] = 'normal'
        self._warning_msg.delete('1.0', 'end')
        self._warning_msg.insert('1.0', msg)
        self._warning_msg['state'] = 'disabled'

    def _watch_smart_data_queue(self):
        # print("Watching SMART queue")
        self.master.after(200, self._watch_smart_data_queue)
        drive_list = {}
        try:
            drive_list = self.smart_device_queue.get_nowait()
        except queue.Empty:
            return
        drive_item_dict = self.drive_dict
        drive_request_dict = {}
        for serial in drive_list:
            drive = drive_list[serial]
            attr_list = {}
            for attr in drive.attributes:
                if attr is None:
                    continue
                attr_list[attr.num] = AttrItem(
                    attr.num,
                    attr.name,
                    attr.raw,
                    attr.value
                )
            disp_string = ""
            for attr in attr_list:
                disp_string += str(attr_list[attr]) + '\n'
            # implicitly also discard all past warnings
            # as they would no longer be valid
            warning_list = [
                WarningItem("Raw SMART readings", disp_string),
            ]
            if drive.serial not in drive_item_dict:
                drive_item_dict[drive.serial] = DriveItem(
                    str(drive),
                    warning_list,
                    drive.serial,
                    drive.model,
                    is_ssd=drive.is_ssd,
                )
            else:
                drive_item_dict[drive.serial].warnings = warning_list
            drive_request_dict[serial] = DriveInfoRequestPayload(
                model=drive.model,
                serial=drive.serial,
                is_ssd=drive.is_ssd,
                attr_list=attr_list,
                timestamp_override=None,
            )
        self.drive_dict = drive_item_dict
        self._update_drive_list()
        self.do_network_push(drive_request_dict)

    def _watch_net_send_resp_queue(self):
        # print("Watching SMART queue")
        self.master.after(200, self._watch_net_send_resp_queue)
        try:
            _ = self.network_send_response_queue.get_nowait()
        except queue.Empty:
            return
        # TODO

    def _watch_net_recv_resp_queue(self):
        # print("Watching SMART queue")
        self.master.after(200, self._watch_net_recv_resp_queue)
        try:
            info_dict, warning_dict = self.network_pull_queue.get_nowait()
        except queue.Empty:
            return
        # pprint.pprint(info_dict)
        # pprint.pprint(warning_dict)
        for sn in info_dict:
            if sn not in self.drive_dict:
                self.drive_dict[sn] = DriveItem(
                    "",
                    [],
                    sn,
                    info_dict[sn]['drive_model'],
                    is_registered=True,
                    nickname=info_dict[sn]['drive_nickname'],
                    status=info_dict[sn]['drive_status'],
                )
            else:
                self.drive_dict[sn].is_registered = True
                self.drive_dict[sn].model = info_dict[sn]['drive_model']
                self.drive_dict[sn].nickname = info_dict[sn]['drive_nickname']
                self.drive_dict[sn].status = info_dict[sn]['drive_status']
        # Read warning
        for sn in warning_dict:
            warning_list = []
            warnings_dict = warning_dict[sn]['response_json']
            for algo in warnings_dict:
                res = warning_dict[sn]['response_json'][algo]
                # pprint.pprint(res)
                warning_msg = "Algorithm: {:}\n".format(algo)
                warning_msg += "\tAlgorithm version: {:}\n".format(res['version'])  # noqa: E501
                warning_msg += "\tTraining data date: {:}\n".format(res['data_date'])  # noqa: E501
                for item in res['warn_list']:
                    warning_msg += "{:}{:}\n".format(SURROGATE_PAIRS[item['level']], item['name'])  # noqa: E501
                    warning_msg += "\tDescription: {:}\n".format(item['desc'])
                    warning_msg += "\tValue: {:}\n".format(item['value'])
                warning_list.append(
                    WarningItem(
                        algo,
                        warning_msg,
                        color=res['level'],
                    ),
                )
            self.drive_dict[sn].warnings = warning_list
        # print("net recv ok")
        self._update_drive_list()

    def do_SMART_read(self):
        worker = SMARTReaderThread(self.smart_device_queue)
        worker.run()

    def do_network_push(self, drive_request_dict):
        worker = DriveStatusTransmitterThread(self.network_send_response_queue, BACKEND_URL, API_TOKEN)  # noqa: E501
        worker.run(drive_request_dict)

    def do_drive_register(self):
        # TODO:
        if self.child_window:
            self.child_window.destroy()
            self.child_window = None
        else:
            if self.current_drive is not None:
                self.child_window = DriveRegisterWindow(
                    cancel_callback=self._clear_child_window,
                    serial=self.current_drive.serial,
                    drive_item=self.drive_dict[self.current_drive.serial],
                )
            else:
                self.child_window = DriveRegisterWindow(
                    cancel_callback=self._clear_child_window,
                )

    def _clear_child_window(self):
        self.child_window = None
        self.do_network_pull()

    def do_network_pull(self):
        worker = DriveStatusRecieverThread(self.network_pull_queue, BACKEND_URL, API_TOKEN)  # noqa: E501
        worker.run()


class DriveRegisterWindow(Toplevel):
    def __init__(self, cancel_callback, serial="", drive_item=None):
        self._cancel_callback = cancel_callback
        super().__init__(root)
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        box_frames = Frame(self)
        box_frames.pack()

        self.model_entry = EntryWithLabel(box_frames, 0, "Model", "")
        self.serial_entry = EntryWithLabel(box_frames, 1, "Serial Number", serial)  # noqa: E501
        self.nickname_entry = EntryWithLabel(box_frames, 2, "Nickname", "")
        self.status_entry = SelectWithLabel(box_frames, 3, "Drive status", ["Active", "Retired", "Failed"])  # noqa: E501
        self.total_size_entry = EntryWithLabel(box_frames, 4, "Total size (bytes)", 0, self._is_int)  # noqa: E501
        self.lba_size_entry = EntryWithLabel(box_frames, 5, "LBA size (bytes)", 512, self._is_int)  # noqa: E501
        self.is_ssd_box = CheckWithLabel(box_frames, 6, "Drive is SSD")

        btn_frame = Frame(self)
        btn = Button(btn_frame,
                     text="Submit",
                     command=self._submit)
        btn.pack(side='left')
        btn = Button(btn_frame,
                     text="Cancel",
                     command=self._cancel)
        btn.pack(side='left')
        btn_frame.pack()
        # TODO: Load drive info from server after form is loaded
        if drive_item is not None:
            self.model_entry.set_val(drive_item.model)
            self.is_ssd_box.set_val(drive_item.is_ssd)
        self._fetch_drive()

    def _fetch_drive(self):
        try:
            req_body = {
                'token': API_TOKEN,
                'serial_number': self.serial_entry.get_val(),
            }
            resp = requests.post(BACKEND_URL+'/get_drive_info', data=req_body)  # noqa: E501
            if resp.status_code == 404:
                return
            if resp.status_code != 200:
                print("Error {:}: {:}".format(resp.status_code, resp.reason))  # noqa: E501
            else:
                print("Drive info Request OK")
                body = resp.json()
                if 'error' in body:
                    print("Error: {:}".format(body['error']))
                    return
                # pprint.pprint(body)
        except Exception as e:
            print(e)
            return
        self.model_entry.set_val(body['drive_model'])
        if body['drive_nickname'] is not None:
            self.nickname_entry.set_val(body['drive_nickname'])
        self.status_entry.set_val(['active', 'retired', 'failed'].index(body['drive_status']))  # noqa: E501
        self.total_size_entry.set_val(body['drive_total_size_byte'])
        self.lba_size_entry.set_val(body['drive_lba_size_byte'])
        self.is_ssd_box.set_val(body['is_ssd'])

    def _submit(self):
        try:
            req_body = {
                'token': API_TOKEN,
                'serial_number': self.serial_entry.get_val(),
            }
            req_body['status'] = self.status_entry.get_val().lower()
            if self.model_entry.get_val() != '':
                req_body['model'] = self.model_entry.get_val()
            if self.nickname_entry.get_val() != '':
                req_body['nickname'] = self.nickname_entry.get_val()
            size_str = self.total_size_entry.get_val()
            try:
                size = int(size_str)
                if size > 0:
                    req_body['total_size_byte'] = size
            except:  # noqa: E722
                pass
            size_str = self.lba_size_entry.get_val()
            try:
                size = int(size_str)
                if size > 0:
                    req_body['lba_size_byte'] = size
            except:  # noqa: E722
                pass
            print(req_body)
            resp = requests.post(BACKEND_URL+'/update_drive_info', data=req_body)  # noqa: E501
            if resp.status_code == 404:
                return
            if resp.status_code != 200:
                print("Error {:}: {:}".format(resp.status_code, resp.reason))  # noqa: E501
            else:
                print("Drive info Request OK")
                body = resp.json()
                if 'error' in body:
                    print("Error: {:}".format(body['error']))
                # pprint.pprint(body)
        except Exception as e:
            print(e)
        self._cancel()

    def _cancel(self):
        print("Cancel called")
        self._cancel_callback()
        self.destroy()

    def _is_int(self, val):
        if val == '':
            return True
        try:
            int(val)
            return True
        except Exception:
            return False


class LoginWindow(Toplevel):
    def __init__(self):
        super().__init__(root)

        box_frames = Frame(self)
        box_frames.pack()

        self.user_entry = EntryWithLabel(box_frames, 0, "Username", "")
        self.password_entry = PasswordWithLabel(box_frames, 1, "Password", "")  # noqa: E501
        btn_frame = Frame(self)
        btn = Button(btn_frame,
                     text="Login",
                     command=self._submit)
        btn.pack(side='left')
        btn_frame.pack()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _submit(self):
        global API_TOKEN
        try:
            req_body = {
                'username': self.user_entry.get_val(),
                'password': self.password_entry.get_val(),
            }
            # print(req_body)
            resp = requests.post(BACKEND_URL+'/get_token', data=req_body)  # noqa: E501
            if resp.status_code == 404:
                return
            if resp.status_code != 200:
                print("Error {:}: {:}".format(resp.status_code, resp.reason))  # noqa: E501
            else:
                print("Token Request OK")
                body = resp.json()
                if 'error' in body:
                    print("Error: {:}".format(body['error']))
                    messagebox.showerror("Error", "Error: {:}".format(body['error']))  # noqa: E501
                elif 'token' in body:
                    API_TOKEN = body['token']
                    try:
                        with open('token.txt', 'w') as f_in:
                            f_in.write(API_TOKEN)
                    except:  # noqa: E722
                        pass
                    self._cancel()
                else:
                    print("Malformed response")
                # pprint.pprint(body)
        except Exception as e:
            print(e)

    def _cancel(self):
        if API_TOKEN is None:
            exit()
        self.destroy()


if __name__ == '__main__':
    is_windows = False
    # Check if is admin
    # https://stackoverflow.com/questions/1026431/cross-platform-way-to-check-admin-rights-in-a-python-script-under-windows
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        is_windows = True
    if not is_admin:
        # https://stackoverflow.com/questions/130763/request-uac-elevation-from-within-a-python-script
        if is_windows:
            # relaunch as admin
            ctypes.windll.shell32.ShellExecuteW(None,
                                                "runas",
                                                sys.executable,
                                                __file__,
                                                None, 1)
            print("Re-launched as admin")
            exit()
        print("Must run as admin for smartctl usage")
        exit()
    root = Tk()
    app = MainWindow(root)
    root.mainloop()
