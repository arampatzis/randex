"""Create randomized multiple choice exams using latex."""

from importlib.metadata import version

try:
    __version__ = version("randex")
except ImportError:
    __version__ = "0.0.0"
