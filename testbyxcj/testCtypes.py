import ctypes
from mininet.cli import CLI

anothernet = ctypes.cast(0x7fe5087a7a10, ctypes.py_object).value
CLI(anothernet)