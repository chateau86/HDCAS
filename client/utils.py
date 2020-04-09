from tkinter import Frame, Listbox, Scrollbar

SMART_PARAM_ENABLED = [1, 4, 5, 7, 9, 12, 190, 192, 193, 194, 197, 198, 199, 240, 241, 242]  # noqa: E501
SMART_PARAM_CYCLES = [241, 242]


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
        return str(self.to_json_dict())

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


def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]
