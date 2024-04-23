import math
import time
import bittensor as bt


class logging(bt.logging):
    __last_time__: int = 0

    def __new__(
        cls,
        config: "bt.config" = None,
        debug: bool = None,
        trace: bool = None,
        record_log: bool = None,
        logging_dir: str = None,
    ):
        cls.__last_time__ = 0

        super.__new__(
            config=config,
            debug=debug,
            trace=trace,
            record_log=record_log,
            logging_dir=logging_dir,
        )

        return cls

    @classmethod
    def can_log(cls, silence_period=None):
        if not silence_period:
            return True

        current_time = time.time()
        delta = math.floor(current_time - cls.__last_time__)
        if delta <= silence_period:
            return False

        cls.__last_time__ = current_time
        return True

    @classmethod
    def info(cls, message: str, silence_period=None):
        if not cls.__has_been_inited__:
            cls()

        if not cls.can_log(silence_period):
            return

        bt.logging.info(message)

    @classmethod
    def warn(cls, message: str, silence_period=None):
        if not cls.__has_been_inited__:
            cls()

        if not cls.can_log(silence_period):
            return

        bt.logging.warning(message)

    @classmethod
    def success(cls, message: str, silence_period=None):
        if not cls.__has_been_inited__:
            cls()

        if not cls.can_log(silence_period):
            return

        bt.logging.success(message)

    @classmethod
    def error(cls, message: str, silence_period=None):
        if not cls.__has_been_inited__:
            cls()

        if not cls.can_log(silence_period):
            return

        bt.logging.error(message)