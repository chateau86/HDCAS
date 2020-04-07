from pySMART import DeviceList
import threading


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
    def __init__(self, out_queue):
        self.out_queue = out_queue

    def run(self):
        # TODO
        pass


class DriveStatusRecieverThread(threading.Thread):
    def __init__(self, out_queue):
        self.out_queue = out_queue

    def run(self):
        # TODO
        pass
