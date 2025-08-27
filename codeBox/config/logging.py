import logging
import time

RESET = "\x1b[0m"
COLORS = {
    "DEBUG": "\x1b[38;5;245m",
    "INFO": "\x1b[38;5;39m",
    "WARNING": "\x1b[33m",
    "ERROR": "\x1b[31m",
    "CRITICAL": "\x1b[41;97m",
}


class ColorFormatter(logging.Formatter):
    default_time_format = "%Y-%m-%d %H:%M:%S"
    default_msec_format = "%s.%03d"
    converter = time.localtime

    def format(self, record: logging.LogRecord) -> str:
        base = self.format_time(record, self.default_time_format)
        record.asctime = f"{base}.{int(record.msecs):03d}"

        level_name = record.levelname
        color = COLORS.get(level_name, "")

        formatted = (
            f"{record.asctime} | {level_name:<8} | "
            f"{record.module}:{record.lineno:<4} | {record.getMessage()}"
        )

        if color:
            formatted = f"{color}{formatted}{RESET}"

        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        if record.stack_info:
            formatted += "\n" + self.formatStack(record.stack_info)

        return formatted

    def format_time(self, record, datefmt=None):
        ct = self.converter(record.created)
        return time.strftime(datefmt or self.default_time_format, ct)
