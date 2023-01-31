"""Compatibility imports"""

import sys

try:
    from packaging.version import Version as StrictVersion  # type: ignore
except ImportError:
    from distutils.version import StrictVersion  # pylint: disable=deprecated-module  # noqa

from requests.adapters import HTTPAdapter  # type: ignore[import]  # noqa

try:
    from ssl import CertificateError, match_hostname
except ImportError:
    from backports.ssl_match_hostname import CertificateError, match_hostname  # noqa

if sys.version_info[0] >= 3:
    import http.client as httplib  # noqa
else:
    import httplib  # noqa

try:
    import urllib3
except ImportError:
    from requests.packages import urllib3  # type: ignore[import]  # noqa  # pylint: disable=ungrouped-imports


# Monkey-patching match_hostname with a version that supports
# IP-address checking. Not necessary for Python 3.5 and above
if sys.version_info[:2] < (3, 5):
    urllib3.connection.match_hostname = match_hostname  # type: ignore  # noqa

RecentlyUsedContainer = urllib3._collections.RecentlyUsedContainer  # type: ignore
PoolManager = urllib3.poolmanager.PoolManager

import six  # noqa
from six import binary_type, ensure_binary, integer_types, iteritems, moves, PY2, PY3, string_types, text_type, u  # noqa

# six\.([a-zA-Z._\d]+)
# binary_type
# ensure_binary
# integer_types
# iteritems
# moves
# moves.BaseHTTPServer.BaseHTTPRequestHandler
# moves.queue.Empty
# moves.socketserver.ThreadingTCPServer
# moves.urllib_parse.urlparse
# moves.urllib.parse.quote
# PY2
# PY3
# string_types
# text_type
# u

__all__ = [
    'RecentlyUsedContainer', 'match_hostname', 'httplib', 'CertificateError',
    'HTTPAdapter', 'StrictVersion', 'PoolManager', 'six'
]
