from backend.app.runners.file import FileRunner
from backend.app.runners.manual import ManualRunner
from backend.app.runners.mock import MockRunner


def get_runner(name: str):
    runners = {
        "manual": ManualRunner(),
        "file": FileRunner(),
        "mock": MockRunner(),
    }
    if name not in runners:
        raise ValueError(f"Unsupported runner: {name}")
    return runners[name]
