from enum import Enum
import logging
import os
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
import sys
from typing import List, Protocol, cast
from contextvars import ContextVar

from dotenv import load_dotenv

load_dotenv()

LOG_OUTPUT_FOLDER = os.environ["LOG_OUTPUT_FOLDER"]
LOG_ENABLE_COLORS = os.environ["LOG_ENABLE_COLORS"].lower() == "true"


class Color(Enum):
    YELLOW = "33"
    GREEN = "32"
    CYAN = "36"
    BLUE = "34"


PrefixListType = List[str]

LOG_SECTION_COLOR: ContextVar[Color | None] = ContextVar(
    "LOG_SECTION_COLOR",
    default=None,
)

LOG_PREFIX_LIST: ContextVar[list[str] | None] = ContextVar(
    "LOG_PREFIX_LIST",
    default=None,
)


def apply_color(text: str, color: Color | None) -> str:
    if not LOG_ENABLE_COLORS:
        return text
    if color is None:
        return text
    return f"\033[{color.value}m{text}\033[0m"


class PrefixLogRecord(Protocol):
    prefix__list: PrefixListType
    prefix__formatted: str


class PrefixFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        typed_record = cast(PrefixLogRecord, record)

        explicit_prefix_list = getattr(record, "prefix__list", None)
        context_prefix_list = LOG_PREFIX_LIST.get()

        if explicit_prefix_list is not None:
            if isinstance(explicit_prefix_list, list):
                typed_record.prefix__list = explicit_prefix_list
            else:
                typed_record.prefix__list = [str(explicit_prefix_list)]
        elif context_prefix_list is not None:
            typed_record.prefix__list = context_prefix_list
        else:
            typed_record.prefix__list = []

        typed_record.prefix__formatted = "".join(
            f"[{s}]" for s in typed_record.prefix__list
        )

        return True


class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        section_color = LOG_SECTION_COLOR.get()
        return apply_color(text, section_color)


def configure_logging(level: int = logging.DEBUG) -> None:
    os.makedirs(LOG_OUTPUT_FOLDER, exist_ok=True)

    log_format = (
        "[%(asctime)s]%(prefix__formatted)s[%(name)s][%(levelname)s] %(message)s"
    )

    file_handler = RotatingFileHandler(
        os.path.join(LOG_OUTPUT_FOLDER, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )

    stream_handler = logging.StreamHandler()

    file_formatter = logging.Formatter(log_format)
    stream_formatter = ColorFormatter(log_format)

    file_handler.setFormatter(file_formatter)
    stream_handler.setFormatter(stream_formatter)
    stream_handler.flush = sys.stdout.flush

    prefix_filter = PrefixFilter()
    file_handler.addFilter(prefix_filter)
    stream_handler.addFilter(prefix_filter)

    logging.basicConfig(
        level=level,
        handlers=[stream_handler, file_handler],
    )

    logging.getLogger("selenium.webdriver").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("selenium.webdriver.common.selenium_manager").setLevel(
        logging.ERROR,
    )
    logging.getLogger("pdfminer").setLevel(logging.WARNING)


@contextmanager
def suppress_logs(level: int = logging.CRITICAL):
    previous_level = logging.root.manager.disable
    logging.disable(level)
    try:
        yield
    finally:
        logging.disable(previous_level)


@contextmanager
def log_context(*, color: Color | None = None, prefix__list: list[str] | None = None):
    color_token = LOG_SECTION_COLOR.set(color)
    prefix_token = LOG_PREFIX_LIST.set(prefix__list)
    try:
        yield
    finally:
        LOG_SECTION_COLOR.reset(color_token)
        LOG_PREFIX_LIST.reset(prefix_token)
