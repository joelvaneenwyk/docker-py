import errno
import os
import select
import struct
import sys

import six

try:
    from typing import Optional, Union  # noqa
except ImportError:
    pass

try:
    from socket import socket as Socket  # noqa
    from socket import SocketIO
except ImportError:
    pass

try:
    from ..transport import NpipeSocket  # type: ignore
except ImportError:
    class NpipeSocket(object):  # type: ignore[no-redef]
        pass


STDOUT = 1
STDERR = 2


class SocketError(Exception):
    """Socket specific exception."""
    pass


NPIPE_ENDED = 109
"""
NpipeSockets have their own error types
pywintypes.error: (109, 'ReadFile', 'The pipe has been ended.')
"""


def read(socket, n=4096):
    # type: (Union[NpipeSocket, Socket, SocketIO], int) -> Optional[bytes]
    """
    Reads at most n bytes from socket
    """

    recoverable_errors = (errno.EINTR, errno.EDEADLK, errno.EWOULDBLOCK)

    if sys.version_info[0] >= 3 and not isinstance(socket, NpipeSocket):
        try:
            select.select([socket], [], [])
        except ValueError:
            return six.binary_type(0)

    try:
        if hasattr(socket, 'recv'):
            return socket.recv(n)
        if sys.version_info[0] >= 3 and isinstance(socket, SocketIO):
            return socket.read(n)
        return os.read(socket.fileno(), n)
    except OSError as os_error:
        if os_error.errno not in recoverable_errors:
            raise
    except Exception as exception:
        is_pipe_ended = (
            isinstance(socket, NpipeSocket)
            and len(exception.args) > 0
            and exception.args[0] == NPIPE_ENDED)
        if is_pipe_ended:
            # npipes don't support duplex sockets, so we interpret
            # a PIPE_ENDED error as a close operation (0-length read).
            return six.binary_type(0)
        raise

    return six.binary_type(0)


def read_exactly(socket, n):
    """
    Reads exactly n bytes from socket
    Raises SocketError if there isn't enough data
    """
    data = six.binary_type()
    while len(data) < n:
        next_data = read(socket, n - len(data))
        if not next_data:
            raise SocketError("Unexpected EOF")
        data += next_data
    return data


def next_frame_header(socket):
    """
    Returns the stream and size of the next frame of data waiting to be read
    from socket, according to the protocol defined here:

    https://docs.docker.com/engine/api/v1.24/#attach-to-a-container
    """
    try:
        data = read_exactly(socket, 8)
    except SocketError:
        return (-1, -1)

    stream, actual = struct.unpack('>BxxxL', data)
    return (stream, actual)


def frames_iter(socket, tty):
    """
    Return a generator of frames read from socket. A frame is a tuple where
    the first item is the stream number and the second item is a chunk of data.

    If the tty setting is enabled, the streams are multiplexed into the stdout
    stream.
    """
    if tty:
        return ((STDOUT, frame) for frame in frames_iter_tty(socket))
    return frames_iter_no_tty(socket)


def frames_iter_no_tty(socket):
    """
    Returns a generator of data read from the socket when the tty setting is
    not enabled.
    """
    while True:
        (stream, n) = next_frame_header(socket)
        if n < 0:
            break
        while n > 0:
            result = read(socket, n)
            if result is None:
                continue
            data_length = len(result)
            if data_length == 0:
                # We have reached EOF
                return
            n -= data_length
            yield (stream, result)


def frames_iter_tty(socket):
    """
    Return a generator of data read from the socket when the tty setting is
    enabled.
    """
    while True:
        result = read(socket)
        if len(result) == 0:
            # We have reached EOF
            return
        yield result


def consume_socket_output(frames, demux=False):
    """
    Iterate through frames read from the socket and return the result.

    Args:

        demux (bool):
            If False, stdout and stderr are multiplexed, and the result is the
            concatenation of all the frames. If True, the streams are
            demultiplexed, and the result is a 2-tuple where each item is the
            concatenation of frames belonging to the same stream.
    """
    if demux is False:
        # If the streams are multiplexed, the generator returns strings, that
        # we just need to concatenate.
        return six.binary_type().join(frames)

    # If the streams are demultiplexed, the generator yields tuples
    # (stdout, stderr)
    out = [None, None]
    for frame in frames:
        # It is guaranteed that for each frame, one and only one stream
        # is not None.
        assert frame != (None, None)
        if frame[0] is not None:
            if out[0] is None:
                out[0] = frame[0]
            else:
                out[0] += frame[0]
        else:
            if out[1] is None:
                out[1] = frame[1]
            else:
                out[1] += frame[1]
    return tuple(out)


def demux_adaptor(stream_id, data):
    """
    Utility to demultiplex stdout and stderr when reading frames from the
    socket.
    """
    if stream_id == STDOUT:
        return (data, None)
    elif stream_id == STDERR:
        return (None, data)
    else:
        raise ValueError('{0} is not a valid stream'.format(stream_id))
