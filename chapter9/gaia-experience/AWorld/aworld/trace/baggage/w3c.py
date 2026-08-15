import re
from typing import List
from aworld.trace.base import Propagator, Carrier, TraceContext
from aworld.trace.baggage import BaggageContext
from aworld.logs.util import logger
from urllib.parse import quote_plus, unquote_plus


class W3CBaggagePropagator(Propagator):
    """
    W3C baggage propagator.
    """

    _MAX_HEADER_LENGTH = 8192
    _MAX_PAIR_LENGTH = 4096
    _MAX_PAIRS = 180
    _BAGGAGE_HEADER_NAME = "baggage"
    _DELIMITER_PATTERN = re.compile(r"[ \t]*,[ \t]*")

    def extract(self, carrier: Carrier):
        """
        Extract the trace context from the carrier.
        Args:
            carrier: The carrier to extract the trace context from.
        """
        baggage_header = self._get_value(carrier, self._BAGGAGE_HEADER_NAME)
        if not baggage_header:
            return None

        if len(baggage_header) > self._MAX_HEADER_LENGTH:
            logger.warning(
                f"baggage header length exceeds {self._MAX_HEADER_LENGTH}")
            return None

        baggage_entries: List[str] = re.split(
            self._DELIMITER_PATTERN, baggage_header)
        if len(baggage_entries) > self._MAX_PAIRS:
            logger.warning(f"baggage entries exceeds {self._MAX_PAIRS}")

        for entry in baggage_entries:
            if len(entry) > self._MAX_PAIR_LENGTH:
                logger.warning(
                    f"baggage entry length exceeds {self._MAX_PAIR_LENGTH}")
                continue
            try:
                key, value = entry.split("=", 1)
                key = unquote_plus(key).strip()
                value = unquote_plus(value).strip()
            except ValueError:
                logger.warning(f"baggage entry format error: {entry}")
                continue
            BaggageContext.set_baggage(key, value)

    def inject(self, carrier: Carrier, context: TraceContext):
        """
        Inject the trace context into the carrier.
        Args:
            carrier: The carrier to inject the trace context into.
            context: The trace context to inject.
        """
        baggage = BaggageContext.get_baggage()
        if baggage:
            baggage_header = ",".join(
                f"{quote_plus(key)}={quote_plus(value)}" for key, value in baggage.items())
            carrier.set(self._BAGGAGE_HEADER_NAME, baggage_header)
