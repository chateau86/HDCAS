#!/usr/bin/env python3

from tkinter import Tk, Frame, Listbox, Scrollbar, Label, Button, scrolledtext

import queue
import ctypes
import os
import sys
import pprint

from worker import SMARTReaderThread

SMART_PARAM_ENABLED = [1, 4, 5, 7, 9, 12, 190, 192, 193, 194, 197, 198, 199, 240, 241, 242]  # noqa: E501
SMART_PARAM_CYCLES = [241, 242]

BACKEND_URL = "10.0.0.115:5000"
API_TOKEN = "c91a3ec3-0ad2-471e-8899-3211da76074f"
# TODO: Ask user for token


def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]


class DriveInfoRequestPayload:
    def __init__(self,
                 model="",
                 serial="",
                 is_ssd=False,
                 attr_list={},
                 timestamp_override=None,
                 ):
        self.model = model
        self.serial = serial
        self.is_ssd = is_ssd
        self.attr_list = attr_list
        self.timestamp_override = timestamp_override

    def __repr__(self):
        return self.to_json_dict()

    def to_json_dict(self):
        out_dict = {}
        for p in SMART_PARAM_ENABLED:
            p = str(p)
            if p in self.attr_list:
                out_dict['smart_{:}_raw'.format(p)] = self.attr_list[p].raw
                out_dict['smart_{:}_normalized'.format(p)] = self.attr_list[p].norm  # noqa: E501
        if '190' not in self.attr_list and '194' in self.attr_list:
            out_dict['smart_190_raw'.format(p)] = self.attr_list['194'].raw
            out_dict['smart_190_normalized'.format(p)] = self.attr_list['194'].norm  # noqa: E501
        out_dict['model'] = self.model
        out_dict['serial'] = self.serial
        out_dict['is_ssd'] = str(self.is_ssd)
        if self.timestamp_override is not None:
            out_dict['timestamp_override'] = dump_datetime(self.timestamp_override)  # noqa: E501
        return out_dict


class WarningItem:
    def __init__(self, title, desc):
        self.title = title
        self.desc = desc

    def __repr__(self):
        return self.title + ": " + self.desc


class DriveItem:
    def __init__(self, title, smart_data, warnings):
        self.title = title
        self.smart_data = smart_data
        self.warnings = warnings

    def __repr__(self):
        out = self.title + '\n' + \
              '\tSMART: ' + self.smart_data
        for warn in self.warnings:
            out += '\t\t' + str(warn)
        return out


class AttrItem:
    def __init__(self, num, name, raw, norm):
        self.num = num
        self.name = name
        self.raw = raw
        self.norm = norm

    def __repr__(self):
        return str(self.num) + ": " + self.name + ": " + self.raw


class ListWithScroll:
    def __init__(self, parent, callback):
        self._frame = Frame(parent)
        self._scrollbar = Scrollbar(self._frame)
        self._list_box = Listbox(self._frame, selectmode="browse",
                                 exportselection=False,
                                 yscrollcommand=self._scrollbar.set)
        self._scrollbar.config(command=self._list_box.yview)
        self._list_box.pack(side='left', fill='both', expand=1)
        self._scrollbar.pack(side='right', fill='both')
        self._list_box.bind('<<ListboxSelect>>', callback)

    def get_list_box(self):
        return self._list_box

    def get_frame(self):
        return self._frame


class Main_window(Frame):
    def __init__(self, master=None):
        self.drive_list = []
        self.current_drive = None

        self.master = master
        self.master.title("HDCAS")
        self.master.minsize(height=200, width=400)

        self.smart_device_queue = queue.Queue()
        self.network_response_queue = queue.Queue()

        top_controls_frame = Frame(master)
        drive_list_frame = Frame(master)
        drive_detail_frame = Frame(master)
        top_controls_frame.grid(sticky='nsew', row=0, column=0)
        drive_list_frame.grid(sticky="nsew", row=1, column=0)
        drive_detail_frame.grid(sticky="nsew", row=2, column=0)
        master.grid_rowconfigure(1, weight=1)
        master.grid_rowconfigure(2, weight=1)
        master.grid_columnconfigure(0, weight=1)

        # init top controls
        btn = Button(top_controls_frame,
                     text="Clear data",
                     command=self.clear_data)
        btn.pack(side='left')
        btn = Button(top_controls_frame,
                     text="Load SMART data",
                     command=self.do_SMART_read)
        btn.pack(side='left')
        btn = Button(top_controls_frame,
                     text="Upload data",
                     command=self.do_network_push)
        btn.pack(side='left')
        btn = Button(top_controls_frame,
                     text="Download data",
                     command=self.do_network_pull)
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
        warning_msg_label = Label(warning_detail_frame,
                                  text="Warning details",
                                  anchor='w',)
        warning_msg_label.grid(row=0, column=0, sticky='nsew')
        warning_msg = scrolledtext.ScrolledText(
            warning_detail_frame,
            state='disabled', width=40, height=10, wrap='none'
        )
        warning_msg.grid(row=1, column=0, sticky='nsew')
        warning_detail_frame.grid_rowconfigure(0, weight=1)
        warning_detail_frame.grid_columnconfigure(0, weight=1)

        self._warning_list = warning_list.get_list_box()
        self._warning_msg = warning_msg
        self._watch_smart_data_queue()

    def _update_drive_list(self, drive_list):
        self._drive_list.delete(0, 'end')
        self.drive_list = drive_list
        self.current_drive = None
        for i in range(len(self.drive_list)):
            self._drive_list.insert(i, self.drive_list[i].title)
        self._update_warn_box()

    def _drive_click_callback(self, event):
        w = event.widget
        if len(w.curselection()) == 0:
            self.current_drive = None
            self._drive_msg.configure(text="No drive selected")
        else:
            index = int(w.curselection()[0])
            self.current_drive = self.drive_list[index]
            self._drive_msg.configure(text=str(self.current_drive.title))
        self._update_warn_box()

    def _update_warn_box(self):
        self._warning_list.delete(0, 'end')
        if self.current_drive is not None:
            for i in range(len(self.current_drive.warnings)):
                self._warning_list \
                    .insert(i, self.current_drive.warnings[i].title)
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
        drive_item_list = []
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
            drive_item_list.append(
                DriveItem(
                    drive.model + ": " + drive.serial,
                    str(drive),
                    warning_list,
                )
            )
            drive_request_dict[serial] = DriveInfoRequestPayload(
                model=drive.model,
                serial=drive.serial,
                is_ssd=drive.is_ssd,
                attr_list=attr_list,
                timestamp_override=None,
            )
        self._update_drive_list(drive_item_list)
        # TODO: Push drive_Attr_dict to the network
        self.do_network_push(drive_request_dict)

    def do_SMART_read(self):
        worker = SMARTReaderThread(self.smart_device_queue)
        worker.run()

    def do_network_push(self, drive_request_dict):
        # TODO: Actual SMART data read and stuff
        # TODO: Async this
        print("---")
        for serial in drive_request_dict:
            pprint.pprint(drive_request_dict[serial].to_json_dict())
            print("-")
        print("---")

    def do_network_pull(self):
        # TODO: Actual SMART data read and stuff
        # TODO: Async this
        pass

    def clear_data(self):
        # TODO: Actual SMART data read and stuff
        drive_list = []
        self._update_drive_list(drive_list)


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
    app = Main_window(root)
    root.mainloop()
