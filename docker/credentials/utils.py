import os
import sys


def find_executable(executable, path=None):
    """
    As distutils.spawn.find_executable, but on Windows, look up
    every extension declared in PATHEXT instead of just `.exe`
    """
    if sys.platform != 'win32':
        import warnings

        warnings.filterwarnings("ignore", message="The distutils package is deprecated")

        import distutils.spawn
        return distutils.spawn.find_executable(executable, path)

    if path is None:
        path = os.environ['PATH']

    paths = path.split(os.pathsep)
    paths.append("C:\\Program Files\\Docker\\Docker\\resources\\bin")
    paths.append("C:\\Program Files\\Docker\\Docker")
    extensions = os.environ.get('PATHEXT', '.exe').split(os.pathsep)
    base, ext = os.path.splitext(executable)

    if not os.path.isfile(executable):
        for p in paths:
            for ext in extensions:
                f = os.path.join(p, base + ext)
                if os.path.isfile(f):
                    return f
        return None
    else:
        return executable


def create_environment_dict(overrides):
    """
    Create and return a copy of os.environ with the specified overrides
    """
    result = os.environ.copy()
    result.update(overrides or {})
    return result
