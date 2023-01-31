import ctypes
import functools
import io
import time

import six

try:
    from typing import Any, MutableSequence, Optional, Tuple, Type, Union  # noqa
except ImportError:
    pass


class WinError(Exception):
    def __init__(self, winerror, funcname, strerror):
        # type: (int, str, str) -> None
        self.winerror = winerror
        self.funcname = funcname
        self.strerror = strerror


BOOL = ctypes.c_long

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
GENERIC_EXECUTE = 0x20000000
GENERIC_ALL = 0x10000000

CREATE_NEW = 1
CREATE_ALWAYS = 2
OPEN_EXISTING = 3
OPEN_ALWAYS = 4
TRUNCATE_EXISTING = 5

FILE_ATTRIBUTE_NORMAL = 0x00000080

INVALID_HANDLE_VALUE = -1

NULL = 0
FALSE = BOOL(0)
TRUE = BOOL(1)

LPVOID = ctypes.c_void_p

LPCOLESTR = LPOLESTR = OLESTR = ctypes.c_wchar_p
LPCWSTR = LPWSTR = ctypes.c_wchar_p
LPCSTR = LPSTR = ctypes.c_char_p
LPCVOID = LPVOID = ctypes.c_void_p

ULONG = ctypes.c_ulong
LONG = ctypes.c_long
DWORD = ctypes.c_ulong

LPDWORD = ctypes.POINTER(DWORD)
HANDLE = ctypes.c_void_p  # in the header files: void *
Handle = HANDLE

try:
    import ctypes.wintypes
except (ImportError, ValueError):
    setattr(ctypes, 'wintypes', None)


class _US(ctypes.Structure):
    _fields_ = [
        ("Offset", DWORD),
        ("OffsetHigh", DWORD),
    ]


class _U(ctypes.Union):
    _fields_ = [
        ("s", _US),
        ("Pointer", ctypes.c_void_p),
    ]

    _anonymous_ = ("s",)


class OVERLAPPED(ctypes.Structure):
    _fields_ = [
        ("Internal", ctypes.POINTER(ULONG)),
        ("InternalHigh", ctypes.POINTER(ULONG)),
        ("u", _U),
        ("hEvent", HANDLE),
        # Custom fields.
        ("channel", ctypes.py_object),
    ]
    _anonymous_ = ("u",)


try:
    ReadFile = ctypes.windll.kernel32.ReadFile  # type: ignore[attr-defined]
    ReadFile.argtypes = (HANDLE, ctypes.c_void_p, DWORD, ctypes.POINTER(DWORD), ctypes.POINTER(OVERLAPPED))
    ReadFile.restype = BOOL

    WriteFile = ctypes.windll.kernel32.WriteFile  # type: ignore[attr-defined]
    WriteFile.argtypes = (HANDLE, ctypes.c_void_p, DWORD, ctypes.POINTER(DWORD), ctypes.POINTER(OVERLAPPED))
    WriteFile.restype = BOOL

    CreateFileA = ctypes.windll.kernel32.CreateFileA  # type: ignore[attr-defined]
    CreateFileA.argtypes = (LPCSTR, DWORD, DWORD, ctypes.c_void_p, DWORD, DWORD, HANDLE)
    CreateFileA.restype = HANDLE

    CreateFileW = ctypes.windll.kernel32.CreateFileW  # type: ignore[attr-defined]
    CreateFileW.argtypes = (LPCWSTR, DWORD, DWORD, ctypes.c_void_p, DWORD, DWORD, HANDLE)
    CreateFileW.restype = HANDLE

    CloseHandle = ctypes.windll.kernel32.CloseHandle  # type: ignore[attr-defined]
    CloseHandle.argtypes = (HANDLE,)
    CloseHandle.restype = BOOL
except AttributeError:
    ReadFile = None
    WriteFile = None
    CreateFileA = None
    CreateFileW = None
    CloseHandle = None


def _CloseHandle(handle):
    # type: (Handle) -> None
    if CloseHandle is not None:
        return CloseHandle(handle)
    return None


def _ReadFile(
        handle,         # type: Handle
        read_size,      # type: int
):  # type: (...) -> Tuple[int, bytes]
    """See: CreateFile function
    http://msdn.microsoft.com/en-us/library/windows/desktop/aa363858(v=vs.85).aspx
    """
    buffer = ctypes.create_string_buffer(b"", read_size)
    number_of_bytes_read = DWORD(0)
    result = BOOL(ReadFile(handle, ctypes.byref(buffer), read_size, ctypes.byref(number_of_bytes_read), None))
    if result.value == 0:
        raise WinError(result.value, "ReadFile", "Failed to read file.")
    return number_of_bytes_read.value, ctypes.string_at(buffer)


def _WriteFile(
        handle,     # type: Handle
        buffer      # type: bytes
):  # type: (...) -> Tuple[int, int]
    """See: CreateFile function
    http://msdn.microsoft.com/en-us/library/windows/desktop/aa363858(v=vs.85).aspx
    """
    number_of_bytes_written = DWORD(0)
    if WriteFile is not None:
        result = BOOL(WriteFile(
            handle,
            buffer, len(buffer),
            ctypes.byref(number_of_bytes_written), None))
        if result.value == 0:
            raise WinError(result.value, "WriteFile", "Failed to write file.")
        return result.value, number_of_bytes_written.value
    return 0, 0


def _CreateFile(
        filename,   # type: str
        access,     # type: int
        mode,       # type: int
        creation,   # type: int
        flags,      # type: int
):  # type: (...) -> Handle
    """See: CreateFile function
    http://msdn.microsoft.com/en-us/library/windows/desktop/aa363858(v=vs.85).aspx
    """
    if CreateFileW is not None:
        return HANDLE(CreateFileW(filename, access, mode, None, creation, flags, None))
    return HANDLE(0)


def _GetNamedPipeInfo(handle):
    # type: (Handle) -> Tuple[int, int, int, int]
    """See: CreateFile function
    http://msdn.microsoft.com/en-us/library/windows/desktop/aa363858(v=vs.85).aspx
    """
    GetNamedPipeInfo_Fn = ctypes.windll.kernel32.GetNamedPipeInfo  # type: ignore[attr-defined]
    GetNamedPipeInfo_Fn.argtypes = [
        HANDLE,     # [in]            HANDLE  hNamedPipe,
        LPDWORD,    # [out, optional] LPDWORD lpFlags,
        LPDWORD,    # [out, optional] LPDWORD lpOutBufferSize,
        LPDWORD,    # [out, optional] LPDWORD lpInBufferSize,
        LPDWORD,    # [out, optional] LPDWORD lpMaxInstances
    ]
    GetNamedPipeInfo_Fn.restype = BOOL

    lpFlags = DWORD()
    lpOutBufferSize = DWORD()
    lpInBufferSize = DWORD()
    lpMaxInstances = DWORD()
    result = BOOL(GetNamedPipeInfo_Fn(
        handle, ctypes.byref(lpFlags), ctypes.byref(lpOutBufferSize), ctypes.byref(lpInBufferSize), ctypes.byref(lpMaxInstances)))
    if result.value == 0:
        raise WinError(result.value, "GetNamedPipeInfo_Fn", "Failed to write file.")

    return (int(lpFlags.value), int(lpOutBufferSize.value), int(lpInBufferSize.value), int(lpMaxInstances.value))


class Win32(object):
    """
    Wrapper around `win32file` and `win32pipe` in case 'pywin32' is not installed.
    """

    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3

    NMPWAIT_WAIT_FOREVER = 0xffffffff
    NMPWAIT_USE_DEFAULT_WAIT = 0
    NMPWAIT_NO_WAIT = 1  # todo:jve:Not sure what this is supposed to be

    def __init__(self):
        try:
            self._kernel32 = ctypes.windll.LoadLibrary('kernel32.dll')
        except AttributeError:
            self._kernel32 = None

        try:
            import ctypes.wintypes as wintypes

            self._wintypes = wintypes
        except (AttributeError, ValueError):
            self._wintypes = None

        try:
            import win32file  # type: ignore[import]
            import win32pipe  # type: ignore[import]

            self._file = win32file
            self._pipe = win32pipe
        except ImportError:
            self._file = None
            self._pipe = None

    def ReadFile(self, handle, size):
        # type: (Handle, int)-> Tuple[int, bytes]
        return _ReadFile(handle, size)

    def ReadFileBuffer(self, handle, buffer):
        # type: (Handle, memoryview)-> Tuple[int, bytes]
        size, data = self.ReadFile(handle, len(buffer))
        return _ReadFile(handle, len(buffer))

    def WriteFile(self, handle, data):
        # type: (Handle, Union[str, bytes])-> Tuple[int, int]
        return _WriteFile(handle, six.ensure_binary(data))

    def CreateFile(
            self,
            filename,                   # type: str
            desired_access=0,           # type: int
            share_mode=0,               # type: int
            security_attributes=None,   # type: Optional[Any]
            creation_disposition=0,     # type: int
            flags_and_attributes=0,     # type: int
            __hTemplateFile=None,       # type: Optional[int]
    ):  # type: (...) -> Handle
        return _CreateFile(
            filename, access=desired_access, mode=share_mode, creation=creation_disposition, flags=flags_and_attributes)

    def GetNamedPipeInfo(self, handle):
        # type: (Handle) -> Tuple[int, int, int, int]
        return _GetNamedPipeInfo(handle)

    @property
    def error(self):
        # type: () -> Type[Exception]
        if self._pipe:
            exception = self._pipe.error
        else:
            exception = WinError
        return exception


cERROR_PIPE_BUSY = 0xe7
cSECURITY_SQOS_PRESENT = 0x100000
cSECURITY_ANONYMOUS = 0

MAXIMUM_RETRY_COUNT = 10
WIN32_WRAPPER = Win32()


def check_closed(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        if self._closed:
            raise RuntimeError(
                'Can not reuse socket after connection was closed.'
            )
        return f(self, *args, **kwargs)
    return wrapped


class NpipeSocket(object):
    """ Partial implementation of the socket API over windows named pipes.
        This implementation is only designed to be used as a client socket,
        and server-specific methods (bind, listen, accept...) are not
        implemented.
    """

    def __init__(self, handle=None):
        # type: (Optional[Any]) -> None
        self._timeout = WIN32_WRAPPER.NMPWAIT_USE_DEFAULT_WAIT
        self._handle = HANDLE(handle) if handle else None
        self._closed = False

    @property
    def handle(self):
        # type: () -> Handle
        assert self._handle is not None
        return self._handle

    def accept(self):
        raise NotImplementedError()

    def bind(self, address):
        raise NotImplementedError()

    def close(self):
        _CloseHandle(self.handle)
        self._closed = True

    @check_closed
    def connect(self, address, retry_count=0):
        # type: (str, int) -> None
        try:
            handle = WIN32_WRAPPER.CreateFile(
                address,
                desired_access=WIN32_WRAPPER.GENERIC_READ | WIN32_WRAPPER.GENERIC_WRITE,
                creation_disposition=WIN32_WRAPPER.OPEN_EXISTING,
                flags_and_attributes=cSECURITY_ANONYMOUS | cSECURITY_SQOS_PRESENT
            )
        except Exception as e:
            # See Remarks:
            # https://msdn.microsoft.com/en-us/library/aa365800.aspx
            if getattr(e, 'winerror', None) == cERROR_PIPE_BUSY:
                # Another program or thread has grabbed our pipe instance
                # before we got to it. Wait for availability and attempt to
                # connect again.
                retry_count = retry_count + 1
                if (retry_count < MAXIMUM_RETRY_COUNT):
                    time.sleep(1)
                    return self.connect(address, retry_count)
            raise e

        self._handle = handle

        self.flags = WIN32_WRAPPER.GetNamedPipeInfo(self.handle)[0]
        self._address = address

    @check_closed
    def connect_ex(self, address):
        return self.connect(address)

    @check_closed
    def detach(self):
        self._closed = True
        return self._handle

    @check_closed
    def dup(self):
        return NpipeSocket(self._handle)

    def getpeername(self):
        return self._address

    def getsockname(self):
        return self._address

    def getsockopt(self, level, optname, buflen=None):
        raise NotImplementedError()

    def ioctl(self, control, option):
        raise NotImplementedError()

    def listen(self, backlog):
        raise NotImplementedError()

    def makefile(self, mode=None, bufsize=None):
        assert mode is not None
        if mode.strip('b') != 'r':
            raise NotImplementedError()
        rawio = NpipeFileIOBase(self)
        if bufsize is None or bufsize <= 0:
            bufsize = io.DEFAULT_BUFFER_SIZE
        return io.BufferedReader(rawio, buffer_size=bufsize)

    @check_closed
    def recv(self, bufsize, flags=0):
        # type: (int, int) -> bytes
        _err, data = WIN32_WRAPPER.ReadFile(self.handle, bufsize)
        return data

    @check_closed
    def recvfrom(self, bufsize, flags=0):
        data = self.recv(bufsize, flags)
        return (data, self._address)

    @check_closed
    def recvfrom_into(self, buf, nbytes=0, flags=0):
        return self.recv_into(buf, nbytes, flags), self._address

    @check_closed
    def recv_into(self, buf, nbytes=0, flags=0):
        # type: (Optional[MutableSequence[int]], int, int) -> int
        if buf:
            _err, data = WIN32_WRAPPER.ReadFile(self.handle, nbytes or len(buf))
            n = len(data)
            buf[:n] = data  # type: ignore
        else:
            n = 0
        return n

    @check_closed
    def send(self, string, flags=0):
        _err, nbytes = WIN32_WRAPPER.WriteFile(self.handle, string)
        return nbytes

    @check_closed
    def sendall(self, string, flags=0):
        return self.send(string, flags)

    @check_closed
    def sendto(self, string, address):
        self.connect(address)
        return self.send(string)

    def setblocking(self, flag):
        if flag:
            return self.settimeout(None)
        return self.settimeout(0)

    def settimeout(self, value):
        if value is None:
            # Blocking mode
            self._timeout = WIN32_WRAPPER.NMPWAIT_WAIT_FOREVER
        elif not isinstance(value, (float, int)) or value < 0:
            raise ValueError('Timeout value out of range')
        elif value == 0:
            # Non-blocking mode
            self._timeout = WIN32_WRAPPER.NMPWAIT_NO_WAIT
        else:
            # Timeout mode - Value converted to milliseconds
            self._timeout = value * 1000

    def gettimeout(self):
        return self._timeout

    def setsockopt(self, level, optname, value):
        raise NotImplementedError()

    @check_closed
    def shutdown(self, how):
        return self.close()


class NpipeFileIOBase(io.RawIOBase):
    def __init__(self, npipe_socket):
        self.sock = npipe_socket

    def close(self):
        super(NpipeFileIOBase, self).close()
        self.sock = None

    def fileno(self):
        assert self.sock is not None
        return self.sock.fileno()

    def isatty(self):
        return False

    def readable(self):
        return True

    def readinto(self, buf):
        assert self.sock is not None
        return self.sock.recv_into(buf)

    def seekable(self):
        return False

    def writable(self):
        return False
