import re
from typing import Tuple, List
from aworld.logs.util import logger
from aworld.trace.base import Propagator, Carrier, TraceContext


class W3CTraceContextPropagator(Propagator):
    """
    OtelPropagator is a Propagator that extracts and injects using w3c TraceContext's headers.
        carrier = {
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-00f067aa0ba902b7-01",
            "tracestate": "congo=t61rcWkgMzE",
            "baggage": "key1=value1,key2=value2"
        }
    """
    _STATE_KEY_FORMAT = (
        r"[a-z][_0-9a-z\-\*\/]{0,255}|"
        r"[a-z0-9][_0-9a-z\-\*\/]{0,240}@[a-z][_0-9a-z\-\*\/]{0,13}"
    )
    _STATE_VALUE_FORMAT = (
        r"[\x20-\x2b\x2d-\x3c\x3e-\x7e]{0,255}[\x21-\x2b\x2d-\x3c\x3e-\x7e]"
    )
    _state_delimiter_pattern = re.compile(r"[ \t]*,[ \t]*")
    _state_member_pattern = re.compile(
        f"({_STATE_KEY_FORMAT})(=)({_STATE_VALUE_FORMAT})[ \t]*")

    _TRACEPARENT_HEADER_NAME = "traceparent"
    _TRACESTATE_HEADER_NAME = "tracestate"
    _TRACEPARENT_HEADER_FORMAT = (
        "^[ \t]*([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})"
        + "(-.*)?[ \t]*$"
    )
    _TRACEPARENT_HEADER_FORMAT_RE = re.compile(_TRACEPARENT_HEADER_FORMAT)

    def extract(self, carrier: Carrier) -> TraceContext:
        """
        Extract trace context from carrier.
        Args:
            carrier: The carrier to extract trace context from.
        Returns:
            A dict of trace context.
        """
        header = carrier.get(self._TRACEPARENT_HEADER_NAME) or carrier.get(
            'HTTP_' + self._TRACEPARENT_HEADER_NAME.upper())

        if header is None:
            return None

        match = re.search(self._TRACEPARENT_HEADER_FORMAT_RE, header)
        if not match:
            return None

        version: str = match.group(1)
        trace_id: str = match.group(2)
        span_id: str = match.group(3)
        trace_flags: str = match.group(4)

        logger.debug(
            f"extract trace_id: {trace_id}, span_id: {span_id}, trace_flags: {trace_flags}, version: {version}")

        if trace_id == "0" * 32 or span_id == "0" * 16:
            return None
        if version == "00":
            if match.group(5):  # type: ignore
                return None
        if version == "ff":
            return None

        state_header = carrier.get(self._TRACESTATE_HEADER_NAME) or carrier.get(
            'HTTP_' + self._TRACESTATE_HEADER_NAME.upper())
        return TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            trace_flags=trace_flags,
            version=version,
            attributes=(self._extract_state_from_header(state_header))
        )

    def inject(self, trace_context: TraceContext, carrier: Carrier) -> None:
        """
        Inject trace context into carrier.
        Args:
            context: The trace context to inject.
            carrier: The carrier to inject trace context into.
        """
        attribute_copy = trace_context.attributes.copy()
        version: str = trace_context.version
        trace_flags: str = trace_context.trace_flags
        trace_id = trace_context.trace_id
        span_id = trace_context.span_id
        logger.debug(
            f"inject trace_id: {trace_id}, span_id: {span_id}, trace_flags: {trace_flags}, version: {version}")
        if (not trace_id or trace_id == "0" * 32
                or not span_id or span_id == "0" * 16):
            return

        if isinstance(trace_id, int):
            trace_id = format(trace_id, "032x")
        if isinstance(span_id, int):
            span_id = format(span_id, "016x")
        traceparent_string = f"{version}-{trace_id}-{span_id}-{trace_flags}"
        carrier.set(self._TRACEPARENT_HEADER_NAME, traceparent_string)
        tracestate_string = ",".join(
            f"{key}={value}" for key, value in attribute_copy.items())
        if tracestate_string:
            carrier.set(self._TRACESTATE_HEADER_NAME, tracestate_string)

    def _extract_state_from_header(self, header: str) -> dict:
        """
        Extract state from header.
        Args:
            header: The header to extract state from.
        Returns:
            A dict of state.
        """
        if header is None:
            return {}
        state = {}
        members: List[str] = re.split(self._state_delimiter_pattern, header)
        for member in members:
            # empty members are valid, but no need to process further.
            if not member:
                continue
            match = self._state_member_pattern.fullmatch(member)
            if not match:
                logger.warning(
                    "Member doesn't match the w3c identifiers format {member}")
                return state
            groups: Tuple[str, ...] = match.groups()
            key, _eq, value = groups
            # duplicate keys are not legal in header
            if key in state:
                return state
            state[key] = value
        return state
