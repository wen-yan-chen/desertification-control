"""Reusable paper figures plus a lazy index of historical training scripts."""

from builtins import __dict__ as _builtins
from collections.abc import Mapping
from importlib import import_module, util
from pathlib import Path
import sys
from threading import RLock

_ROOT = Path(__file__).resolve().parents[2]
_TRAINING = _ROOT / "FigureTraining/toolkit"
_STYLE = _ROOT / "Practice2/FigureAndFlowworkStyle"
_DEMOS = _STYLE / "FigureStyleDemos/Scripts"
_STRUCTURES = _STYLE / "MCM_B新结构样张"
_LATEX = Path(__file__).resolve().parent / "latex"
SOURCE_DIRS = [_TRAINING, _DEMOS, _STRUCTURES]
GROUPS = {
    "toolkit": [
        "templates", "workflow01", "concept03", "gis02", "seasonal04",
        "tradeoff05", "radar06", "three_d07", "three_d07_style", "heatmap08",
        "feasible09", "sensitivity10", "bars11", "render_training",
    ],
    "scripts": ["mcm_figures", "demo_figures", "demo_figures2", "figure_paths"],
    "structures": ["generate_structures"],
}
_SOURCES = {name: folder / f"{name}.py" for group, folder in zip(GROUPS.values(), SOURCE_DIRS)
            for name in group}
_API = ("charts", "bars", "diagrams", "maps")
BATCH_SCRIPTS = {"generate_gallery": _STYLE / "MCM_B图表样张/generate_gallery.py"}
LATEX_WORKFLOW = {"sty": _LATEX / "mcmworkflow.sty", "style_guide": _LATEX / "STYLE_GUIDE.md",
                  "examples": _LATEX / "examples"}
_LOCK = RLock()


def available():
    """List historical module names without importing or probing their dependencies."""
    return sorted(_SOURCES)


def _legacy_import(name, globals=None, locals=None, fromlist=(), level=0):
    # Resolve the archived scripts' sibling imports without hijacking short
    # names like "templates" in the caller or changing sys.path.
    if level == 0 and name in _SOURCES:
        return get(name)
    return _builtins["__import__"](name, globals, locals, fromlist, level)


def get(name):
    """Load a legacy training script explicitly; see CATALOG before calling."""
    if name in _API:
        return import_module(f".{name}", __name__)
    path = _SOURCES[name]
    if not path.is_file():
        raise FileNotFoundError(
            f"Legacy reference {name!r} needs the workspace source: {path}\n"
            "This historical module is not part of the portable package. "
            "Either copy the original training folders next to _shared "
            "(FigureTraining/toolkit, Practice2/FigureAndFlowworkStyle), "
            "or use the formal API in mcm_library.charts / bars / diagrams / maps "
            "(see mcm_library/CATALOG.md).")
    key = f"{__name__}._archive_{name}"
    with _LOCK:
        if key in sys.modules:
            return sys.modules[key]
        spec = util.spec_from_file_location(key, path)
        module = util.module_from_spec(spec)
        module.__builtins__ = {**_builtins, "__import__": _legacy_import}
        sys.modules[key] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(key, None)
            raise
        return module


class _ArchiveIndex(Mapping):
    def __getitem__(self, name):
        return get(name)

    def __iter__(self):
        return iter(_SOURCES)

    def __len__(self):
        return len(_SOURCES)

    def __contains__(self, name):
        return name in _SOURCES


MODULES = _ArchiveIndex()


def __getattr__(name):
    if name in _API or name in _SOURCES:
        return get(name)
    raise AttributeError(name)


__all__ = [*_API, "MODULES", "GROUPS", "BATCH_SCRIPTS", "LATEX_WORKFLOW",
           "SOURCE_DIRS", "available", "get"]
