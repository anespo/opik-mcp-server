"""
AWS AgentCore observability integration
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.boto3sqs import Boto3SQSInstrumentor
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .config import settings
from .models import EvaluationResult

# Setup logging
logger = logging.getLogger(__name__)

# Global tracer
tracer = None
cloudwatch_client = None


def setup_observability():
    """Setup OpenTelemetry and AWS observability for AgentCore"""
    global tracer, cloudwatch_client
    
    if not settings.agentcore_enabled:
        return
    
    try:
        # Setup OpenTelemetry resource
        resource = Resource.create({
            "service.name": settings.otel_service_name,
            "service.version": "1.0.0",
            "aws.log.group.names": settings.cloudwatch_log_group,
        })
        
        # Setup tracer provider
        trace.set_tracer_provider(TracerProvider(resource=resource))
        tracer = trace.get_tracer(__name__)
        
        # Setup OTLP exporter for X-Ray
        if settings.xray_enabled:
            try:
                # For AgentCore, we need to use the proper X-Ray endpoint with IAM authentication
                if settings.agentcore_enabled:
                    # Use AWS X-Ray SDK instead of direct OTLP for better IAM integration
                    from aws_xray_sdk.core import xray_recorder
                    from aws_xray_sdk.core import patch_all
                    
                    # Configure X-Ray recorder for AgentCore
                    xray_recorder.configure(
                        context_missing='LOG_ERROR',
                        plugins=('ECSPlugin', 'EC2Plugin'),
                        daemon_address='127.0.0.1:2000',  # X-Ray daemon in AgentCore
                        use_ssl=False
                    )
                    
                    # Patch AWS SDK calls for automatic tracing
                    patch_all()
                    logger.info("X-Ray tracing configured for AgentCore")
                else:
                    # Local development - use OTLP exporter
                    otlp_exporter = OTLPSpanExporter(
                        endpoint=f"https://xray.{settings.aws_region}.amazonaws.com/v1/traces",
                        headers={
                            "Content-Type": "application/x-protobuf"
                        }
                    )
                    
                    span_processor = BatchSpanProcessor(otlp_exporter)
                    trace.get_tracer_provider().add_span_processor(span_processor)
                    logger.info("X-Ray OTLP exporter configured for local development")
                    
            except Exception as xray_error:
                logger.warning(f"Failed to setup X-Ray tracing (continuing without X-Ray): {xray_error}")
                # Continue without X-Ray tracing
        
        # Setup AWS instrumentation
        BotocoreInstrumentor().instrument()
        Boto3SQSInstrumentor().instrument()
        LoggingInstrumentor().instrument(set_logging_format=True)
        
        # Setup CloudWatch client - use IAM role in AgentCore, profile locally
        try:
            if settings.agentcore_enabled:
                # In AgentCore, use IAM role - disable profile usage entirely
                import os
                # Temporarily remove AWS profile environment variables
                old_profile = os.environ.get('AWS_PROFILE')
                old_default_profile = os.environ.get('AWS_DEFAULT_PROFILE')
                if 'AWS_PROFILE' in os.environ:
                    del os.environ['AWS_PROFILE']
                if 'AWS_DEFAULT_PROFILE' in os.environ:
                    del os.environ['AWS_DEFAULT_PROFILE']
                
                try:
                    cloudwatch_client = boto3.client('logs', region_name=settings.aws_region)
                finally:
                    # Restore environment variables
                    if old_profile:
                        os.environ['AWS_PROFILE'] = old_profile
                    if old_default_profile:
                        os.environ['AWS_DEFAULT_PROFILE'] = old_default_profile
            else:
                # Local development, use profile
                session = boto3.Session(
                    profile_name=settings.aws_profile,
                    region_name=settings.aws_region
                )
                cloudwatch_client = session.client('logs')
        except Exception as aws_error:
            logger.warning(f"Failed to setup CloudWatch client: {aws_error}")
            # Continue without CloudWatch logging
            cloudwatch_client = None
        
        # Ensure log group exists (only if we have a client)
        if cloudwatch_client:
            try:
                # Try creating log group without tags first
                cloudwatch_client.create_log_group(
                    logGroupName=settings.cloudwatch_log_group
                )
                logger.info(f"Created CloudWatch log group: {settings.cloudwatch_log_group}")
                
                # Try to add tags separately if log group creation succeeded
                try:
                    cloudwatch_client.tag_log_group(
                        logGroupName=settings.cloudwatch_log_group,
                        tags={
                            'Service': 'opik-mcp-server',
                            'Environment': 'production' if not settings.debug else 'development'
                        }
                    )
                    logger.info("Successfully tagged CloudWatch log group")
                except Exception as tag_error:
                    logger.warning(f"Failed to tag log group (continuing without tags): {tag_error}")
                    
            except cloudwatch_client.exceptions.ResourceAlreadyExistsException:
                logger.info(f"CloudWatch log group already exists: {settings.cloudwatch_log_group}")
            except Exception as log_group_error:
                logger.warning(f"Failed to create log group (continuing without CloudWatch logging): {log_group_error}")
                cloudwatch_client = None
        
        logger.info("AgentCore observability setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup observability: {e}")
        # Continue without observability rather than failing


async def log_evaluation_result(result: EvaluationResult):
    """Log evaluation result to CloudWatch in EMF format"""
    global cloudwatch_client, tracer
    
    if not settings.agentcore_enabled or not cloudwatch_client:
        return
    
    try:
        # Create span for tracing
        with tracer.start_as_current_span("evaluation_result") as span:
            span.set_attribute("evaluation.id", result.evaluation_id)
            span.set_attribute("evaluation.agent_id", result.agent_id or "")
            span.set_attribute("evaluation.workflow_id", result.workflow_id or "")
            span.set_attribute("evaluation.overall_score", result.overall_score)
            span.set_attribute("evaluation.passed", result.passed)
            
            # Prepare EMF log entry
            emf_log = {
                "_aws": {
                    "Timestamp": int(result.timestamp.timestamp() * 1000),
                    "CloudWatchMetrics": [
                        {
                            "Namespace": "OpikMCP/Evaluations",
                            "Dimensions": [
                                ["ServiceName"],
                                ["ServiceName", "AgentId"],
                                ["ServiceName", "WorkflowId"],
                                ["ServiceName", "EvaluationStatus"]
                            ],
                            "Metrics": [
                                {
                                    "Name": "EvaluationScore",
                                    "Unit": "None"
                                },
                                {
                                    "Name": "EvaluationCount", 
                                    "Unit": "Count"
                                },
                                {
                                    "Name": "ExecutionTime",
                                    "Unit": "Milliseconds"
                                }
                            ]
                        }
                    ]
                },
                "ServiceName": settings.otel_service_name,
                "AgentId": result.agent_id or "unknown",
                "WorkflowId": result.workflow_id or "unknown", 
                "EvaluationStatus": "passed" if result.passed else "failed",
                "EvaluationScore": result.overall_score,
                "EvaluationCount": 1,
                "ExecutionTime": result.execution_time_ms,
                "EvaluationId": result.evaluation_id,
                "TestCaseId": result.test_case_id,
                "SessionId": result.session_id,
                "OpikTraceId": result.opik_trace_id,
                "Timestamp": result.timestamp.isoformat(),
                "Scores": [
                    {
                        "metric": score.metric.value,
                        "score": score.score,
                        "passed": score.passed,
                        "explanation": score.explanation
                    }
                    for score in result.scores
                ],
                "Metadata": result.metadata
            }
            
            # Send to CloudWatch Logs
            log_stream_name = f"evaluations-{datetime.utcnow().strftime('%Y/%m/%d')}"
            
            try:
                # Create log stream if it doesn't exist
                cloudwatch_client.create_log_stream(
                    logGroupName=settings.cloudwatch_log_group,
                    logStreamName=log_stream_name
                )
            except cloudwatch_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Put log event
            cloudwatch_client.put_log_events(
                logGroupName=settings.cloudwatch_log_group,
                logStreamName=log_stream_name,
                logEvents=[
                    {
                        'timestamp': int(result.timestamp.timestamp() * 1000),
                        'message': json.dumps(emf_log)
                    }
                ]
            )
            
            span.set_attribute("log.sent", True)
            logger.info(f"Evaluation result logged to CloudWatch: {result.evaluation_id}")
            
    except Exception as e:
        logger.error(f"Failed to log evaluation result: {e}")
        # Don't fail the evaluation if logging fails


async def log_batch_evaluation_summary(
    batch_id: str,
    total_evaluations: int,
    successful_evaluations: int,
    failed_evaluations: int,
    overall_average_score: float,
    execution_time_ms: float
):
    """Log batch evaluation summary to CloudWatch"""
    global cloudwatch_client, tracer
    
    if not settings.agentcore_enabled or not cloudwatch_client:
        return
    
    try:
        with tracer.start_as_current_span("batch_evaluation_summary") as span:
            span.set_attribute("batch.id", batch_id)
            span.set_attribute("batch.total_evaluations", total_evaluations)
            span.set_attribute("batch.successful_evaluations", successful_evaluations)
            span.set_attribute("batch.failed_evaluations", failed_evaluations)
            span.set_attribute("batch.overall_average_score", overall_average_score)
            
            # Prepare EMF log entry for batch summary
            emf_log = {
                "_aws": {
                    "Timestamp": int(datetime.utcnow().timestamp() * 1000),
                    "CloudWatchMetrics": [
                        {
                            "Namespace": "OpikMCP/BatchEvaluations",
                            "Dimensions": [
                                ["ServiceName"],
                                ["ServiceName", "BatchId"]
                            ],
                            "Metrics": [
                                {
                                    "Name": "BatchEvaluationCount",
                                    "Unit": "Count"
                                },
                                {
                                    "Name": "BatchSuccessRate",
                                    "Unit": "Percent"
                                },
                                {
                                    "Name": "BatchAverageScore",
                                    "Unit": "None"
                                },
                                {
                                    "Name": "BatchExecutionTime",
                                    "Unit": "Milliseconds"
                                }
                            ]
                        }
                    ]
                },
                "ServiceName": settings.otel_service_name,
                "BatchId": batch_id,
                "BatchEvaluationCount": total_evaluations,
                "BatchSuccessRate": (successful_evaluations / total_evaluations * 100) if total_evaluations > 0 else 0,
                "BatchAverageScore": overall_average_score,
                "BatchExecutionTime": execution_time_ms,
                "SuccessfulEvaluations": successful_evaluations,
                "FailedEvaluations": failed_evaluations,
                "Timestamp": datetime.utcnow().isoformat()
            }
            
            # Send to CloudWatch Logs
            log_stream_name = f"batch-evaluations-{datetime.utcnow().strftime('%Y/%m/%d')}"
            
            try:
                cloudwatch_client.create_log_stream(
                    logGroupName=settings.cloudwatch_log_group,
                    logStreamName=log_stream_name
                )
            except cloudwatch_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            cloudwatch_client.put_log_events(
                logGroupName=settings.cloudwatch_log_group,
                logStreamName=log_stream_name,
                logEvents=[
                    {
                        'timestamp': int(datetime.utcnow().timestamp() * 1000),
                        'message': json.dumps(emf_log)
                    }
                ]
            )
            
            span.set_attribute("batch_log.sent", True)
            logger.info(f"Batch evaluation summary logged: {batch_id}")
            
    except Exception as e:
        logger.error(f"Failed to log batch evaluation summary: {e}")


def create_custom_metric(
    metric_name: str,
    value: float,
    unit: str = "None",
    dimensions: Optional[Dict[str, str]] = None
):
    """Create custom CloudWatch metric"""
    global cloudwatch_client
    
    if not settings.agentcore_enabled or not cloudwatch_client:
        return
    
    try:
        try:
            if settings.agentcore_enabled:
                # In AgentCore, use IAM role - disable profile usage entirely
                import os
                # Temporarily remove AWS profile environment variables
                old_profile = os.environ.get('AWS_PROFILE')
                old_default_profile = os.environ.get('AWS_DEFAULT_PROFILE')
                if 'AWS_PROFILE' in os.environ:
                    del os.environ['AWS_PROFILE']
                if 'AWS_DEFAULT_PROFILE' in os.environ:
                    del os.environ['AWS_DEFAULT_PROFILE']
                
                try:
                    cloudwatch_metrics = boto3.client('cloudwatch', region_name=settings.aws_region)
                finally:
                    # Restore environment variables
                    if old_profile:
                        os.environ['AWS_PROFILE'] = old_profile
                    if old_default_profile:
                        os.environ['AWS_DEFAULT_PROFILE'] = old_default_profile
            else:
                session = boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)
                cloudwatch_metrics = session.client('cloudwatch')
        except Exception as aws_error:
            logger.warning(f"Failed to setup CloudWatch metrics client: {aws_error}")
            return
        
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        
        cloudwatch_metrics.put_metric_data(
            Namespace='OpikMCP/Custom',
            MetricData=[metric_data]
        )
        
        logger.debug(f"Custom metric sent: {metric_name} = {value}")
        
    except Exception as e:
        logger.error(f"Failed to send custom metric: {e}")


def get_trace_context() -> Optional[Dict[str, str]]:
    """Get current trace context for correlation"""
    global tracer
    
    if not tracer:
        return None
    
    try:
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            span_context = current_span.get_span_context()
            return {
                "trace_id": format(span_context.trace_id, '032x'),
                "span_id": format(span_context.span_id, '016x'),
                "trace_flags": span_context.trace_flags
            }
    except Exception as e:
        logger.error(f"Failed to get trace context: {e}")
    
    return None