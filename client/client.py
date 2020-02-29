#!/usr/bin/env python3

from tkinter import Tk, Frame, Listbox, Scrollbar, Label, Button
from pySMART import DeviceList
import ctypes
import os
import sys


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
        self.master.minsize(height=200, width=200)

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
        warning_msg = Label(warning_detail_frame,
                            text="Drive warning here",
                            anchor='w',
                            )
        warning_msg.grid(row=0, column=0, sticky='nsew')
        warning_detail_frame.grid_columnconfigure(0, weight=1)

        self._warning_list = warning_list.get_list_box()
        self._warning_msg = warning_msg

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
        self._warning_msg.configure(text="No warning selected")

    def _warning_click_callback(self, event):
        w = event.widget
        if len(w.curselection()) == 0:
            # self.current_drive = None
            self._warning_msg.configure(text="No warning selected")
            return
        index = int(w.curselection()[0])
        self._warning_msg \
            .configure(text=str(self.current_drive.warnings[index].desc))
        return

    def do_SMART_read(self):
        # TODO: Actual SMART data read and stuff
        # TODO: Async this
        raw_drive_list = DeviceList()
        print(raw_drive_list)
        drive_list = []
        for dev in raw_drive_list.devices:
            param_list = []
            for attr in dev.attributes:
                if attr is None:
                    continue
                param_list.append(
                    WarningItem(attr.name, attr.name + ": " + attr.raw)
                )
            drive_list.append(
                DriveItem(dev.model + ": " + dev.serial, str(dev), param_list)
            )
        self._update_drive_list(drive_list)

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
