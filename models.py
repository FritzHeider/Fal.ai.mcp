"""
Pydantic models for fal.ai MCP server.

Defines input validation models for all tools and output data structures
for API responses.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


# ============================================================================
# Input Models for Tools
# ============================================================================


class ListApplicationsInput(BaseModel):
    """Parameters for listing available applications."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    limit: Optional[int] = Field(
        default=20,
        description="Maximum number of applications to return (1-100)",
        ge=1,
        le=100
    )
    offset: Optional[int] = Field(
        default=0,
        description="Number of applications to skip for pagination",
        ge=0
    )
    search: Optional[str] = Field(
        default=None,
        description="Search term to filter applications by name or description (e.g., 'image', 'video')",
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class GetApplicationInput(BaseModel):
    """Parameters for getting a specific application."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    application_id: str = Field(
        ...,
        description="The unique identifier of the application (e.g., '110602490541725184')",
        min_length=1,
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class SubmitJobInput(BaseModel):
    """Parameters for submitting a job to an application queue."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    application_id: str = Field(
        ...,
        description="The unique identifier of the application to run",
        min_length=1,
        max_length=100
    )
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters for the application as a JSON object"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Optional custom request ID for idempotent submissions",
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'markdown' or 'json'"
    )


class PollJobStatusInput(BaseModel):
    """Parameters for polling job status."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    status_url: str = Field(
        ...,
        description="The status_url returned by submit_job (e.g. 'https://queue.fal.run/fal-ai/flux/requests/{id}/status')",
        min_length=1,
        max_length=500
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for structured data"
    )


class GetJobResultInput(BaseModel):
    """Parameters for retrieving job results."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    response_url: str = Field(
        ...,
        description="The response_url returned by submit_job (e.g. 'https://queue.fal.run/fal-ai/flux/requests/{id}')",
        min_length=1,
        max_length=500
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'markdown' or 'json'"
    )


class ListQueueItemsInput(BaseModel):
    """Parameters for listing items in an application queue."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    application_id: str = Field(
        ...,
        description="The application ID whose queue to list",
        min_length=1,
        max_length=100
    )
    limit: Optional[int] = Field(
        default=20,
        description="Maximum items to return (1-100)",
        ge=1,
        le=100
    )
    offset: Optional[int] = Field(
        default=0,
        description="Offset for pagination",
        ge=0
    )
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: 'QUEUED', 'IN_PROGRESS', 'COMPLETED', 'FAILED'",
        max_length=50
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class CancelJobInput(BaseModel):
    """Parameters for canceling a job."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    cancel_url: str = Field(
        ...,
        description="The cancel_url returned by submit_job (e.g. 'https://queue.fal.run/fal-ai/flux/requests/{id}/cancel')",
        min_length=1,
        max_length=500
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class GetAccountInfoInput(BaseModel):
    """Parameters for getting account information."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class GetUsageStatsInput(BaseModel):
    """Parameters for getting usage statistics."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    days: Optional[int] = Field(
        default=7,
        description="Number of days to retrieve stats for (1-90)",
        ge=1,
        le=90
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class SubmitBatchJobInput(BaseModel):
    """Parameters for submitting batch jobs."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    application_id: str = Field(
        ...,
        description="Application ID to run for each batch item",
        min_length=1,
        max_length=100
    )
    batch_data: List[Dict[str, Any]] = Field(
        ...,
        description="List of input objects, one per batch item",
        min_length=1,
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format"
    )


class GetJobLogsInput(BaseModel):
    """Parameters for getting job logs."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    response_url: str = Field(
        ...,
        description="The response_url returned by submit_job (e.g. 'https://queue.fal.run/fal-ai/flux/requests/{id}')",
        min_length=1,
        max_length=500
    )
    limit: Optional[int] = Field(
        default=100,
        description="Maximum log lines to return (1-1000)",
        ge=1,
        le=1000
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


# ============================================================================
# Output Models (Response Data Structures)
# ============================================================================


class ApplicationCapability(BaseModel):
    """Represents a capability of an application."""
    name: str
    description: Optional[str] = None
    input_type: Optional[str] = None
    output_type: Optional[str] = None


class ApplicationInfo(BaseModel):
    """Detailed information about an application."""
    application_id: str
    name: str
    description: Optional[str] = None
    owner: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: Optional[str] = None
    capabilities: Optional[List[ApplicationCapability]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    pricing_per_request: Optional[float] = None
    icon_url: Optional[str] = None
    homepage_url: Optional[str] = None


class JobStatus(BaseModel):
    """Job status information."""
    request_id: str
    status: str
    queue_position: Optional[int] = None
    eta_seconds: Optional[float] = None
    error: Optional[str] = None
    result_url: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class JobResult(BaseModel):
    """Job result with output data."""
    request_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    logs: Optional[str] = None
    execution_time_ms: Optional[int] = None


class QueueItem(BaseModel):
    """Item in an application queue."""
    request_id: str
    status: str
    created_at: str
    position_in_queue: Optional[int] = None
    eta_seconds: Optional[float] = None


class AccountInfo(BaseModel):
    """Account information."""
    user_id: str
    email: Optional[str] = None
    subscription_tier: str
    credits_available: float
    credits_used_this_month: float
    created_at: str
    last_active: Optional[str] = None


class UsageStats(BaseModel):
    """Usage statistics."""
    period_start: str
    period_end: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_credits_used: float
    average_execution_time_ms: float


# ============================================================================
# Video Pipeline Input Models
# ============================================================================


class GenerateVideoProjectInput(BaseModel):
    """Input parameters for submitting a complete video generation project."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='ignore'
    )

    title: str = Field(
        default="Untitled Video Project",
        description="The title of the video or episode",
        max_length=200
    )
    niche: Optional[str] = Field(
        default="Cinematic Sci-Fi",
        description="The genre or niche (e.g., 'Sci-Fi Lore', 'Tech Breakdown', 'True Crime', 'Dark Fantasy')"
    )
    focus_keyword: Optional[str] = Field(
        default=None,
        description="Core topic, focal keyword, or character name",
        max_length=150
    )
    visual_style: str = Field(
        default="Cinematic Photorealism",
        description="Visual aesthetic (e.g. 'Cinematic Photorealism', 'Anime / Cyberpunk', 'Retro 80s VHS', '3D Pixar / Unreal 5', 'Dark Noir')"
    )
    target_duration_sec: int = Field(
        default=60,
        description="Desired target video duration in seconds (15 - 300)",
        ge=15,
        le=300
    )
    full_script: Optional[str] = Field(
        default=None,
        description="Full script or narrative text. If omitted, script is automatically composed."
    )
    recap_intro: Optional[str] = Field(
        default=None,
        description="Optional intro or recap hook (e.g. 'Previously on...')"
    )
    custom_cliffhanger: Optional[str] = Field(
        default=None,
        description="Optional cliffhanger ending hook to tease the next episode"
    )
    target_demographic: Optional[str] = Field(
        default="General Audience",
        description="Audience persona (e.g. 'Gen Z', 'Tech Enthusiasts', 'Kids', 'Finance Bros')"
    )
    voice_tone: Optional[str] = Field(
        default="Cinematic Narrator",
        description="Voice narration tone"
    )
    model_id: Optional[str] = Field(
        default=None,
        description="fal.ai model ID to use for generation (defaults to Kling or configured model)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class ListVideoJobsInput(BaseModel):
    """Input parameters for listing video pipeline jobs."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='ignore')

    status: Optional[str] = Field(
        default=None,
        description="Filter jobs by status ('QUEUED', 'IN_PROGRESS', 'COMPLETED', 'FAILED')"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search term to filter jobs by title, keyword, or prompt"
    )
    limit: int = Field(
        default=20,
        description="Maximum number of jobs to return",
        ge=1,
        le=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class GetVideoJobInput(BaseModel):
    """Input parameters for retrieving a specific video pipeline job."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='ignore')

    job_id: str = Field(
        ...,
        description="The unique identifier of the video job (e.g. 'job_123456789abc')"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class RetryVideoJobInput(BaseModel):
    """Input parameters for retrying a failed or incomplete video pipeline job."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='ignore')

    job_id: str = Field(
        ...,
        description="The unique identifier of the video job to retry"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )

