from .bit_flag import BitFlag
from .color_print import ColorPrint
from .credentials import del_credentials, get_credentials
from .datestr_flags import DateFlag, DateFormat
from .dictionary import join_dictionary_items, join_dictionary_values, map_list_to_dict
from .file import export_csv, export_json, export_txt, import_csv, import_json, import_txt
from .init_option_handle import str_file_option_handle
from .stdouthook import StdOutHook
from .time_convertions import days_diff, seconds_to_str, unixtime_to_str

__all__ = [
    "BitFlag",
    "ColorPrint",
    "get_credentials",
    "del_credentials",
    "DateFormat",
    "DateFlag",
    "date_format_from_flag",
    "join_dictionary_items",
    "join_dictionary_values",
    "map_list_to_dict",
    "import_txt",
    "export_txt",
    "import_csv",
    "export_csv",
    "import_json",
    "export_json",
    "str_file_option_handle",
    "StdOutHook",
    "days_diff",
    "unixtime_to_str",
    "seconds_to_str",
]

# TODO: Rework utils modules to use OOP when possible
