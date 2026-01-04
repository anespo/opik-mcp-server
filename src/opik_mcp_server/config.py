"""
Configuration management for Opik MCP Server
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpikConfig(BaseModel):
    """Opik platform configuration"""
    api_key: str = Field(..., description="Opik API key")
    workspace: str = Field("default", description="Opik workspace")
    base_url: str = Field("https://www.comet.com/opik/api", description="Opik API base URL")
    timeout: int = Field(30, description="Request timeout in seconds")


class AWSConfig(BaseModel):
    """AWS configuration"""
    region: str = Field("eu-west-1", description="AWS region")
    profile: str = Field("default", description="AWS profile")
    agentcore_enabled: bool = Field(True, description="Enable AgentCore integration")
    cloudwatch_log_group: str = Field("/aws/bedrock-agentcore/opik-evaluations", description="CloudWatch log group")
    xray_enabled: bool = Field(True, description="Enable X-Ray tracing")


class ServerConfig(BaseModel):
    """Server configuration"""
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    log_level: str = Field("INFO", description="Log level")
    max_concurrent_evaluations: int = Field(10, description="Max concurrent evaluations")
    evaluation_timeout: int = Field(300, description="Evaluation timeout in seconds")


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Allow extra environment variables from AgentCore
    )
    
    # Opik configuration
    opik_api_key: str = Field(..., json_schema_extra={"env": "OPIK_API_KEY"})
    opik_workspace: str = Field("default", json_schema_extra={"env": "OPIK_WORKSPACE"})
    opik_base_url: str = Field("https://www.comet.com/opik/api", json_schema_extra={"env": "OPIK_BASE_URL"})
    opik_timeout: int = Field(30, json_schema_extra={"env": "OPIK_TIMEOUT"})
    
    # AWS configuration
    aws_region: str = Field("eu-west-1", json_schema_extra={"env": "AWS_REGION"})
    aws_profile: str = Field("default", json_schema_extra={"env": "AWS_PROFILE"})
    agentcore_enabled: bool = Field(True, json_schema_extra={"env": "AGENTCORE_ENABLED"})
    cloudwatch_log_group: str = Field(
        "/aws/bedrock-agentcore/opik-evaluations", 
        json_schema_extra={"env": "CLOUDWATCH_LOG_GROUP"}
    )
    xray_enabled: bool = Field(True, json_schema_extra={"env": "XRAY_ENABLED"})
    
    # Server configuration
    server_host: str = Field("0.0.0.0", json_schema_extra={"env": "SERVER_HOST"})
    server_port: int = Field(8000, json_schema_extra={"env": "SERVER_PORT"})
    log_level: str = Field("INFO", json_schema_extra={"env": "LOG_LEVEL"})
    max_concurrent_evaluations: int = Field(10, json_schema_extra={"env": "MAX_CONCURRENT_EVALUATIONS"})
    evaluation_timeout: int = Field(300, json_schema_extra={"env": "EVALUATION_TIMEOUT"})
    
    # OpenTelemetry configuration for AgentCore
    otel_service_name: str = Field("opik-mcp-server", json_schema_extra={"env": "OTEL_SERVICE_NAME"})
    otel_resource_attributes: str = Field(
        "service.name=opik-mcp-server,aws.log.group.names=/aws/bedrock-agentcore/opik-evaluations",
        json_schema_extra={"env": "OTEL_RESOURCE_ATTRIBUTES"}
    )
    
    # Development settings
    debug: bool = Field(False, json_schema_extra={"env": "DEBUG"})
    testing: bool = Field(False, json_schema_extra={"env": "TESTING"})
    
    @property
    def opik_config(self) -> OpikConfig:
        """Get Opik configuration"""
        return OpikConfig(
            api_key=self.opik_api_key,
            workspace=self.opik_workspace,
            base_url=self.opik_base_url,
            timeout=self.opik_timeout
        )
    
    @property
    def aws_config(self) -> AWSConfig:
        """Get AWS configuration"""
        return AWSConfig(
            region=self.aws_region,
            profile=self.aws_profile,
            agentcore_enabled=self.agentcore_enabled,
            cloudwatch_log_group=self.cloudwatch_log_group,
            xray_enabled=self.xray_enabled
        )
    
    @property
    def server_config(self) -> ServerConfig:
        """Get server configuration"""
        return ServerConfig(
            host=self.server_host,
            port=self.server_port,
            log_level=self.log_level,
            max_concurrent_evaluations=self.max_concurrent_evaluations,
            evaluation_timeout=self.evaluation_timeout
        )


# Global settings instance
settings = Settings()