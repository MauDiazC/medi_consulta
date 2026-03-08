import logging
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from app.core.config import settings

logger = logging.getLogger(__name__)

def setup_telemetry(app):
    """
    Configures OpenTelemetry Tracing for the application.
    """
    service_name = "mediconsulta-api"
    
    # 1. Define Resource
    resource = Resource.create({"service.name": service_name})
    
    # 2. Setup Tracer Provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # 3. Setup OTLP Exporter (Sending to Jaeger/Honeycomb/Grafana Tempo)
    # Default endpoint usually points to a local or cloud collector
    otlp_endpoint = settings.get("OTLP_ENDPOINT", "http://localhost:4318/v1/traces")
    
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        logger.info(f"OTLP Exporter configured to {otlp_endpoint}")
    except Exception as e:
        logger.warning(f"Could not initialize OTLP exporter: {e}. Traces will be local only.")

    # 4. Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # 5. Instrument SQLAlchemy (Async)
    from app.core.database import engine
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    
    logger.info("OpenTelemetry instrumentation completed.")

def get_tracer():
    return trace.get_tracer(__name__)
