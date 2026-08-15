# Metrics Module

## Overview
The `aworld.core.metrics` module provides a unified interface for collecting and exporting metrics. It supports various types of metrics (e.g., counters, histograms) and allows exporting data to different monitoring systems (e.g., Prometheus).

## Key Features
- **Metric Types**:
  - `Counter`: A cumulative metric that represents a single numerical value that only ever increases.
  - `UpDownCounter`: A cumulative metric that can increase or decrease.
  - `Gauge`: A metric that represents a single numerical value that can arbitrarily go up and down.
  - `Histogram`: A metric that represents the distribution of a set of values.

- **Adapters**:
  - `PrometheusAdapter`: Exports metrics to Prometheus.
  - `ConsoleAdapter`: Prints metrics to the console (for debugging purposes).

## Usage Example

```python
import random
import time
from aworld.core.metrics.metric import set_metric_provider, MetricType
from aworld.core.metrics.prometheus.prometheus_adapter import PrometheusConsoleMetricExporter,

PrometheusMetricProvider
from aworld.core.metrics.context_manager import MetricContext, ApiMetricTracker
from aworld.core.metrics.template import MetricTemplate

# Set OpenTelemetry as the metric provider
# set_metric_provider(OpentelemetryMetricProvider())

# Set Prometheus as the metric provider
set_metric_provider(PrometheusMetricProvider(PrometheusConsoleMetricExporter(out_interval_secs=2)))

# Define metric templates
my_counter = MetricTemplate(
    type=MetricType.COUNTER,
    name="my_counter",
    description="My custom counter",
    unit="1"
)

my_gauge = MetricTemplate(
    type=MetricType.GAUGE,
    name="my_gauge"
)

my_histogram = MetricTemplate(
    type=MetricType.HISTOGRAM,
    name="my_histogram",
    buckets=[2, 4, 6, 8, 10]
)


# Track API metrics using decorator
@ApiMetricTracker()
def test_api():
    time.sleep(random.uniform(0, 1))


# Track custom code block using context manager
def test_custom_code():
    with ApiMetricTracker("test_custom_code"):
        time.sleep(random.uniform(0, 1))


# Main loop to generate and record metrics
while 1:
    MetricContext.count(my_counter, random.randint(1, 10))
    MetricContext.gauge_set(my_gauge, random.randint(1, 10))
    MetricContext.histogram_record(my_histogram, random.randint(1, 10))
    test_api()
    test_custom_code()
    time.sleep(random.random())
```

## Notes
- Before using metrics, you must set a metric provider ( set_metric_provider ).
- Different metric types serve different purposes; choose the appropriate type based on your needs.
- For production environments, it is recommended to use Prometheus as the exporter.