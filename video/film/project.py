"""Which film is being built. Set FILM=china (or pass --film china to build.py); default is still_rolling."""
import importlib
import os

NAME = os.environ.get("FILM", "still_rolling")
_MODULES = {"still_rolling": ("film.story", "film.edit"), "china": ("film.china_story", "film.china_edit"),
            "victory": ("film.victory_story", "film.victory_edit")}
story = importlib.import_module(_MODULES[NAME][0])
edit = importlib.import_module(_MODULES[NAME][1])
SUBDIR = "" if NAME == "still_rolling" else NAME
