from aworld.metrics.context_manager import MetricContext
from aworld.metrics.template import MetricTemplate
from aworld.metrics.metric import MetricType

tokens_usage_histogram = MetricTemplate(
    type=MetricType.HISTOGRAM,
    name="llm_token_usage",
    unit="token",
    description="Measures number of input and output tokens used"
)

chat_choice_counter = MetricTemplate(
    type=MetricType.COUNTER,
    name="llm_generation_choice_counter",
    unit="choice",
    description="Number of choices returned by chat completions call"
)

duration_histogram = MetricTemplate(
    type=MetricType.HISTOGRAM,
    name="llm_chat_duration",
    unit="s",
    description="AI chat duration",
)

chat_exception_counter = MetricTemplate(
    type=MetricType.COUNTER,
    name="llm_chat_exception_counter",
    unit="time",
    description="Number of exceptions occurred during chat completions",
)

streaming_time_to_first_token_histogram = MetricTemplate(
    type=MetricType.HISTOGRAM,
    name="llm_streaming_time_to_first_token",
    unit="s",
    description="Time to first token in streaming chat completions",
)
streaming_time_to_generate_histogram = MetricTemplate(
    type=MetricType.HISTOGRAM,
    name="streaming_time_to_generate",
    unit="s",
    description="Time between first token and completion in streaming chat completions",
)


def record_exception_metric(exception, duration):
    '''
    record chat exception to metrics
    '''
    if MetricContext.metric_initialized():
        labels = {
            "error.type": exception.__class__.__name__,
        }
        if duration_histogram:
            MetricContext.histogram_record(
                duration_histogram, duration, labels=labels)
        if chat_exception_counter:
            MetricContext.count(
                chat_exception_counter, 1, labels=labels)


def record_streaming_time_to_first_token(duration, labels):
    '''
    Record duration of start time to first token in stream. 
    '''
    if MetricContext.metric_initialized():
        MetricContext.histogram_record(
            streaming_time_to_first_token_histogram, duration, labels=labels)


def record_streaming_time_to_generate(first_token_to_generate_duration, labels):
    '''
    Record duration the first token to response to generation
    '''
    if MetricContext.metric_initialized():
        MetricContext.histogram_record(
            streaming_time_to_generate_histogram, first_token_to_generate_duration, labels=labels)


def record_chat_response_metric(attributes,
                                prompt_tokens,
                                completion_tokens,
                                duration,
                                choices=None
                                ):
    '''
    Record chat response to metrics
    '''
    if MetricContext.metric_initialized():
        if prompt_tokens and tokens_usage_histogram:
            labels = {
                **attributes,
                "llm.prompt_usage_type": "prompt_tokens"
            }
            MetricContext.histogram_record(
                tokens_usage_histogram, prompt_tokens, labels=labels)
        if completion_tokens and tokens_usage_histogram:
            labels = {
                **attributes,
                "llm.prompt_usage_type": "completion_tokens"
            }
            MetricContext.histogram_record(
                tokens_usage_histogram, completion_tokens, labels=labels)
        if duration and duration_histogram:
            MetricContext.histogram_record(
                duration_histogram, duration, labels=attributes)
        if choices and chat_choice_counter:
            MetricContext.count(chat_choice_counter,
                                len(choices), labels=attributes)
            for choice in choices:
                if choice.get("finish_reason"):
                    finish_reason_attr = {
                        **attributes,
                        "llm.finish_reason": choice.get("finish_reason")
                    }
                    MetricContext.count(
                        chat_choice_counter, 1, labels=finish_reason_attr)
