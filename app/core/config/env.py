import os
from typing import Literal

from dotenv import load_dotenv

_ = load_dotenv()

EnvKey = Literal["DB_STRING"]


def get_env(name: EnvKey | str, default: str = ""):
    return os.getenv(name) or default
