from aworld.trace.base import Propagator, Carrier, TraceContext
from aworld.trace.baggage import BaggageContext
from aworld.logs.util import logger
from aworld.trace.base import AttributeValueType


class SofaTracerBaggagePropagator(Propagator):
    """
    Sofa tracer baggage propagator.
    """

    _TRACE_ID_HEDER_NAMES = ["SOFA-TraceId", "sofaTraceId"]
    _SPAN_ID_HEDER_NAMES = ["SOFA-RpcId", "sofaRpcId"]
    _PEN_ATTRS_HEDER_NAME = "sofaPenAttrs"
    _SYS_PEN_ATTRS_HEDER_NAME = "sysPenAttrs"

    _TRACE_ID_BAGGAGE_KEY = "attributes.sofa.traceid"
    _SPAN_ID_BAGGAGE_KEY = "attributes.sofa.rpcid"
    _PEN_ATTRS_BAGGAGE_KEY = "attributes.sofa.penattrs"
    _SYS_PEN_ATTRS_BAGGAGE_KEY = "attributes.sofa.syspenattrs"

    def extract(self, carrier: Carrier):
        """
        Extract trace context from carrier.
        Args:
            carrier: The carrier to extract trace context from.
        Returns:
            A dict of trace context.
        """
        trace_id = None
        span_id = None
        for name in self._TRACE_ID_HEDER_NAMES:
            trace_id = self._get_value(carrier, name)
            if trace_id:
                break
        for name in self._SPAN_ID_HEDER_NAMES:
            span_id = self._get_value(carrier, name)
            if span_id:
                break
        pen_attrs = self._get_value(carrier, self._PEN_ATTRS_HEDER_NAME)
        sys_pen_attrs = self._get_value(
            carrier, self._SYS_PEN_ATTRS_HEDER_NAME)

        logger.info(
            f"extract trace_id: {trace_id}, span_id: {span_id}, pen_attrs: {pen_attrs}, sys_pen_attrs: {sys_pen_attrs}")
        if trace_id and span_id:
            BaggageContext.set_baggage(self._TRACE_ID_BAGGAGE_KEY, trace_id)
            span_id = span_id + ".1"
            BaggageContext.set_baggage(self._SPAN_ID_BAGGAGE_KEY, span_id)
            if pen_attrs:
                BaggageContext.set_baggage(
                    self._PEN_ATTRS_BAGGAGE_KEY, pen_attrs)
            if sys_pen_attrs:
                BaggageContext.set_baggage(
                    self._SYS_PEN_ATTRS_BAGGAGE_KEY, sys_pen_attrs)

    def inject(self, trace_context: TraceContext, carrier: Carrier):
        """
        Inject trace context to carrier.
        Args:
            trace_context: The trace context to inject.
            carrier: The carrier to inject trace context to.
        """
        baggage = BaggageContext.get_baggage()

        if baggage:
            trace_id = baggage.get(self._TRACE_ID_BAGGAGE_KEY)
            span_id = baggage.get(self._SPAN_ID_BAGGAGE_KEY)
            if trace_id and span_id:
                carrier.set(self._TRACE_ID_HEDER_NAMES[0], trace_id)
                carrier.set(self._SPAN_ID_HEDER_NAMES[0], span_id)

            pen_attrs_dict = {}
            for key, value in baggage.items():
                if key == self._TRACE_ID_BAGGAGE_KEY or key == self._SPAN_ID_BAGGAGE_KEY:
                    continue
                if key == self._PEN_ATTRS_BAGGAGE_KEY and value:
                    pen_attrs_dict.update(dict(item.split("=")
                                          for item in value.split("&")))
                    continue
                if key == self._SYS_PEN_ATTRS_BAGGAGE_KEY and value:
                    carrier.set(self._SYS_PEN_ATTRS_HEDER_NAME, value)
                    continue

                # other baggage items will be injected to sofaPenAttrs
                pen_attrs_dict.update({key: value})

            if pen_attrs_dict:
                pen_attrs = "&".join(f"{key}={value}"
                                     for key, value in pen_attrs_dict.items())
                carrier.set(self._PEN_ATTRS_HEDER_NAME, pen_attrs)


class SofaSpanHelper:
    """
    Sofa span helper.
    """

    @staticmethod
    def set_sofa_context_to_attr(span_attributes: dict[str, AttributeValueType]):
        """
        Set sofa context to span attributes.
        Args:
            span_attributes: The span attributes to set sofa context to.
        """
        baggage = BaggageContext.get_baggage()
        if baggage:
            trace_id = baggage.get(
                SofaTracerBaggagePropagator._TRACE_ID_BAGGAGE_KEY)
            span_id = baggage.get(
                SofaTracerBaggagePropagator._SPAN_ID_BAGGAGE_KEY)
            if trace_id and span_id:
                span_attributes.update({
                    SofaTracerBaggagePropagator._TRACE_ID_BAGGAGE_KEY: trace_id,
                    SofaTracerBaggagePropagator._SPAN_ID_BAGGAGE_KEY: span_id
                })
            pen_attrs = baggage.get(
                SofaTracerBaggagePropagator._PEN_ATTRS_BAGGAGE_KEY)
            if pen_attrs:
                span_attributes.update({
                    SofaTracerBaggagePropagator._PEN_ATTRS_BAGGAGE_KEY: pen_attrs
                })
            sys_pen_attrs = baggage.get(
                SofaTracerBaggagePropagator._SYS_PEN_ATTRS_BAGGAGE_KEY)
            if sys_pen_attrs:
                span_attributes.update({
                    SofaTracerBaggagePropagator._SYS_PEN_ATTRS_BAGGAGE_KEY: sys_pen_attrs
                })
