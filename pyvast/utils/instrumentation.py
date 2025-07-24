
from contextlib import asynccontextmanager
from opentelemetry import trace

tracer = trace.get_tracer('vast')

@asynccontextmanager
async def traced(name:str, **attrs):
    with tracer.start_as_current_span(name, attributes=attrs):
        yield
