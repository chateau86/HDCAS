from tkinter import Frame, Listbox, Scrollbar, Label, Entry, Checkbutton, IntVar  # noqa: E501
from tkinter.ttk import Combobox

SMART_PARAM_ENABLED = [1, 4, 5, 7, 9, 12, 190, 192, 193, 194, 197, 198, 199, 240, 241, 242]  # noqa: E501
SMART_PARAM_CYCLES = [241, 242]

SURROGATE_PAIRS = {
    'green': '\u2714',
    'yellow': '\u26a0',
    'red': '\u274c',
    'unknown': '?',
    'failed': '\u2620',
    'retired': '\u26b1',
}


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
    def __init__(self, title, desc, color='unknown'):
        self.title = title
        self.desc = desc
        self.color = color

    def __repr__(self):
        return self.title + ": " + self.desc

    def get_display_name(self):
        return SURROGATE_PAIRS[self.color] + self.title


class DriveItem:
    def __init__(
        self,
        smart_data,
        warnings,
        serial,
        model,
        is_registered=False,
        is_ssd=False,
        status='unknown',
        nickname='',
    ):
        self.serial = serial
        self.model = model
        self.smart_data = smart_data
        self.warnings = warnings
        self.status = status
        self.is_registered = is_registered
        self.is_ssd = is_ssd
        self.nickname = nickname

    def __repr__(self):
        out = self.serial + ": " + self.get_name() + '\n' + \
              '\tSMART: ' + self.smart_data
        for warn in self.warnings:
            out += '\t\t' + str(warn)
        return out

    def get_name(self):
        name = self.model + ': ' + self.serial
        if self.nickname:
            name = self.nickname
        return name

    def _get_danger_level(self):
        if len(self.warnings) == 0:
            return -1
        warn_level = 0
        for w in self.warnings:
            # if w.title == 'Decision tree':
            #     continue
            if w.color == 'yellow':
                warn_level = max(warn_level, 1)
            elif w.color == 'red':
                warn_level = 2
        return warn_level

    def get_display_name(self):
        name = self.model + ': ' + self.serial
        if self.nickname:
            name = self.nickname
        if not self.is_registered:
            name = SURROGATE_PAIRS['red'] + name
        elif len(self.warnings) == 0:
            name = SURROGATE_PAIRS['unknown'] + name
        else:
            if self.status == 'failed':
                name = SURROGATE_PAIRS['failed'] + name
            elif self.status == 'retired':
                name = SURROGATE_PAIRS['retired'] + name
            else:
                # scan self for active warnings
                warn_level = self._get_danger_level()
                if warn_level >= 1:
                    name = SURROGATE_PAIRS['yellow'] + name
                if warn_level >= 2:
                    name = SURROGATE_PAIRS['yellow'] + name
        return name

    def ui_sort_key(self):
        # row = (is_registered, color, nickname/(model: sn))
        color_order = ['unknown', 'active', 'retired', 'failed']
        color_ind = color_order.index(self.status)
        name = ' ' + self.model + ': ' + self.serial
        if self.nickname:
            name = self.nickname
        return (self.is_registered, color_ind, -self._get_danger_level(), name)


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


class CheckWithLabel:
    def __init__(self, parent, row, label_text):
        self._label = Label(parent, text=label_text, justify='left')
        self._label.grid(row=row, column=0)

        self._var = IntVar()
        self._entry = Checkbutton(parent, variable=self._var)
        self._entry.grid(row=row, column=1)

    def set_val(self, do_select=False):
        if do_select:
            self._entry.select()
        else:
            self._entry.deselect()

    def get_val(self):
        return self._var.get() > 0

    def get_entry(self):
        return self._entry


class SelectWithLabel:
    def __init__(self, parent, row, label_text, options_list):
        self._label = Label(parent, text=label_text, justify='left')
        self._label.grid(row=row, column=0)

        self._entry = Combobox(parent)
        self._entry['values'] = options_list
        self._entry.current(0)
        self._entry['state'] = 'readonly'
        self._entry.grid(row=row, column=1)

    def set_val(self, index):
        self._entry.current(index)

    def get_val(self):
        return self._entry.get()

    def get_entry(self):
        return self._entry


class EntryWithLabel:
    def __init__(self, parent, row, label_text, default_text, validator_cmd=None):  # noqa: E501
        self._label = Label(parent, text=label_text, justify='left')
        self._label.grid(row=row, column=0)

        self._entry = Entry(parent, width=30)
        self._entry.delete(0, 'end')
        self._entry.insert(0, default_text)
        self._entry.grid(row=row, column=1)
        self.validator_cmd = validator_cmd

    def set_val(self, text):
        self._entry.delete(0, 'end')
        self._entry.insert(0, text)

    def get_val(self):
        return self._entry.get()

    def get_entry(self):
        return self._entry

    def _validate(self, action, index, value_if_allowed,
                  prior_value, text, validation_type, trigger_type, widget_name):  # noqa: E501
        if self.validator_cmd is None:
            return True
        else:
            return self.validator_cmd(value_if_allowed)


class PasswordWithLabel:
    def __init__(self, parent, row, label_text, default_text, validator_cmd=None):  # noqa: E501
        self._label = Label(parent, text=label_text, justify='left')
        self._label.grid(row=row, column=0)

        self._entry = Entry(parent, width=30, show='*')
        self._entry.delete(0, 'end')
        self._entry.insert(0, default_text)
        self._entry.grid(row=row, column=1)
        self.validator_cmd = validator_cmd

    def set_val(self, text):
        self._entry.delete(0, 'end')
        self._entry.insert(0, text)

    def get_val(self):
        return self._entry.get()

    def get_entry(self):
        return self._entry

    def _validate(self, action, index, value_if_allowed,
                  prior_value, text, validation_type, trigger_type, widget_name):  # noqa: E501
        if self.validator_cmd is None:
            return True
        else:
            return self.validator_cmd(value_if_allowed)


def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]
