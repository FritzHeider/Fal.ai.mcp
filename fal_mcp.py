"""
fal.ai MCP Server

Enables LLMs to interact with fal.ai API for running AI models,
managing applications, and handling media generation workflows.

Usage:
    python fal_mcp.py                 # stdio transport (default)
    python fal_mcp.py --transport http --port 8000  # HTTP transport
"""

import json
import asyncio
from typing import Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict

import fal_api_client
import db
import pipeline
from settings import settings
from models import (
    ResponseFormat,
    ListApplicationsInput,
    GetApplicationInput,
    SubmitJobInput,
    PollJobStatusInput,
    GetJobResultInput,
    ListQueueItemsInput,
    CancelJobInput,
    GetAccountInfoInput,
    GetUsageStatsInput,
    SubmitBatchJobInput,
    GetJobLogsInput,
    GenerateVideoProjectInput,
    ListVideoJobsInput,
    GetVideoJobInput,
    RetryVideoJobInput,
)

# Initialize database schema dynamically
db.init_db_sync()


# ============================================================================
# Server Initialization
# ============================================================================

mcp = FastMCP("fal_mcp")


# ============================================================================
# Utility Functions
# ============================================================================


def _format_markdown(data: Dict[str, Any], title: str = "") -> str:
    """Format data as readable markdown."""
    if not data:
        return "No data available"
    
    lines = []
    if title:
        lines.append(f"# {title}\n")
    
    def format_value(val: Any, indent: int = 0) -> str:
        prefix = "  " * indent
        if isinstance(val, dict):
            return "\n" + "\n".join(
                f"{prefix}- **{k}**: {format_value(v, indent + 1)}"
                for k, v in val.items() if v is not None
            )
        elif isinstance(val, (list, tuple)):
            if not val:
                return "[]"
            if all(isinstance(x, str) for x in val):
                return ", ".join(str(x) for x in val)
            return "\n" + "\n".join(f"{prefix}- {format_value(x, indent + 1)}" for x in val)
        return str(val)
    
    for key, value in data.items():
        if value is not None:
            lines.append(f"## {key}\n{format_value(value, 0)}\n")
    
    return "\n".join(lines)


def _format_response(data: Any, format_type: ResponseFormat) -> str:
    """Format response data based on requested format."""
    if format_type == ResponseFormat.JSON:
        return json.dumps(data, indent=2, default=str)
    else:
        if isinstance(data, dict):
            return _format_markdown(data)
        return str(data)


# ============================================================================
# Application Discovery Tools
# ============================================================================


@mcp.tool(
    name="list_applications",
    annotations={
        "title": "List Available Applications",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_applications(params: ListApplicationsInput) -> str:
    """
    List available AI applications and models on fal.ai.
    
    Retrieves a paginated list of all available applications. Each application
    represents a deployable AI model or pipeline. Use this to discover what
    applications are available before submitting jobs.
    
    Args:
        params (ListApplicationsInput): Request parameters containing:
            - limit (int): Max applications to return (1-100, default 20)
            - offset (int): Pagination offset (default 0)
            - search (str): Optional search term to filter by name/description
            - response_format (ResponseFormat): Output format (markdown or json)
    
    Returns:
        str: JSON or markdown formatted list of applications with details
    
    Examples:
        - List first 20 applications: {"limit": 20}
        - Search for image applications: {"search": "image", "limit": 10}
        - Get next page: {"limit": 20, "offset": 20}
    """
    try:
        data = await fal_api_client.list_applications(
            limit=params.limit,
            offset=params.offset,
            search=params.search,
        )
        return _format_response(data, params.response_format)
    except Exception as e:
        return f"Error listing applications: {str(e)}"


@mcp.tool(
    name="get_application",
    annotations={
        "title": "Get Application Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_application(params: GetApplicationInput) -> str:
    """
    Get detailed information about a specific application.
    
    Retrieves complete details including input/output schemas, capabilities,
    pricing, and documentation for a specific application.
    
    Args:
        params (GetApplicationInput): Request parameters containing:
            - application_id (str): The application ID to retrieve details for
            - response_format (ResponseFormat): Output format (markdown or json)
    
    Returns:
        str: Formatted application details with schema information
    
    Examples:
        - Get app details: {"application_id": "110602490541725184"}
    """
    try:
        data = await fal_api_client.get_application(params.application_id)
        return _format_response(data, params.response_format)
    except Exception as e:
        return f"Error getting application: {str(e)}"


# ============================================================================
# Job Submission and Status Tools
# ============================================================================


@mcp.tool(
    name="submit_job",
    annotations={
        "title": "Submit Job to Application",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def submit_job(params: SubmitJobInput) -> str:
    """
    Submit a job to an application queue for processing.
    
    Submits input data to an application and queues it for execution.
    Returns a request_id that can be used to poll status and retrieve results.
    Jobs are processed asynchronously; use poll_job_status to check progress.
    
    Args:
        params (SubmitJobInput): Request parameters containing:
            - application_id (str): The application ID to run
            - input_data (dict): Input parameters for the application as JSON
            - request_id (str, optional): Custom request ID for idempotent submissions
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Submission confirmation with request_id, status_url, and result_url
    
    Examples:
        - Submit image generation: {
            "application_id": "110602490541725184",
            "input_data": {"prompt": "a cat", "num_images": 1}
          }
        - Idempotent submission: {
            "application_id": "app123",
            "input_data": {"data": "value"},
            "request_id": "custom_req_123"
          }
    """
    try:
        data = await fal_api_client.submit_job(
            application_id=params.application_id,
            input_data=params.input_data,
            request_id=params.request_id,
        )
        return _format_response(data, params.response_format)
    except Exception as e:
        return f"Error submitting job: {str(e)}"


@mcp.tool(
    name="poll_job_status",
    annotations={
        "title": "Poll Job Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def poll_job_status(params: PollJobStatusInput) -> str:
    """
    Check the current status of a submitted job.
    
    Polls the queue to get the current status of a job without waiting.
    Returns immediate status information including position in queue and
    estimated time remaining.
    
    Args:
        params (PollJobStatusInput): Request parameters containing:
            - request_id (str): The request ID from job submission
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Current status (QUEUED, IN_PROGRESS, COMPLETED, FAILED) with ETA
    
    Examples:
        - Check status: {"request_id": "req_abc123"}
    """
    try:
        data = await fal_api_client.poll_job_status(params.status_url)
        return _format_response(data, params.response_format)
    except Exception as e:
        return f"Error polling job status: {str(e)}"


@mcp.tool(
    name="get_job_result",
    annotations={
        "title": "Get Job Result",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_job_result(params: GetJobResultInput) -> str:
    """
    Retrieve the result of a completed job.
    
    Gets the complete output/result from a job that has been processed.
    Only call this after confirming the job status is COMPLETED.
    
    Args:
        params (GetJobResultInput): Request parameters containing:
            - request_id (str): The request ID of the completed job
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Job result with output data, logs, and metadata
    
    Examples:
        - Get result: {"request_id": "req_abc123"}
    """
    try:
        data = await fal_api_client.get_job_result(params.response_url)
        return _format_response(data, params.response_format)
    except Exception as e:
        return f"Error getting job result: {str(e)}"


@mcp.tool(
    name="list_queue_items",
    annotations={
        "title": "List Queue Items",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_queue_items(params: ListQueueItemsInput) -> str:
    """
    List items currently in an application's queue.
    
    Shows all jobs in the queue for a specific application, with optional
    filtering by status (QUEUED, IN_PROGRESS, COMPLETED, FAILED).
    
    Args:
        params (ListQueueItemsInput): Request parameters containing:
            - application_id (str): The application whose queue to list
            - limit (int): Max items to return (default 20)
            - offset (int): Pagination offset (default 0)
            - status (str, optional): Filter by status
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Formatted list of queue items with status and position
    
    Examples:
        - List all in-progress jobs: {
            "application_id": "app123",
            "status": "IN_PROGRESS"
          }
    """
    try:
        data = await fal_api_client.list_queue_items(
            application_id=params.application_id,
            limit=params.limit,
            offset=params.offset,
            status=params.status,
        )
        return _format_response(data, params.response_format)
    except Exception as e:
        return f"Error listing queue items: {str(e)}"


@mcp.tool(
    name="cancel_job",
    annotations={
        "title": "Cancel Job",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def cancel_job(params: CancelJobInput) -> str:
    """
    Cancel a queued or in-progress job.
    
    Stops a job that is currently queued or being processed. Cannot cancel
    completed or already-failed jobs.
    
    Args:
        params (CancelJobInput): Request parameters containing:
            - request_id (str): The request ID to cancel
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Cancellation confirmation or error if already complete
    
    Examples:
        - Cancel job: {"request_id": "req_abc123"}
    """
    try:
        data = await fal_api_client.cancel_job(params.cancel_url)
        return _format_response(data, params.response_format)
    except Exception as e:
        return f"Error canceling job: {str(e)}"


# ============================================================================
# Account and Usage Tools
# ============================================================================


@mcp.tool(
    name="get_account_info",
    annotations={
        "title": "Get Account Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_account_info(params: GetAccountInfoInput) -> str:
    """
    Get current account information and subscription details.
    
    Retrieves account-level information including subscription tier,
    available credits, and usage metrics.
    
    Args:
        params (GetAccountInfoInput): Request parameters containing:
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Account details with subscription and credit information
    
    Examples:
        - Get account info: {"response_format": "markdown"}
    """
    try:
        data = await fal_api_client.get_account_info()
        return _format_response(data, params.response_format)
    except Exception as e:
        return f"Error getting account info: {str(e)}"


@mcp.tool(
    name="get_usage_stats",
    annotations={
        "title": "Get Usage Statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_usage_stats(params: GetUsageStatsInput) -> str:
    """
    Get usage statistics for the account.
    
    Retrieves usage metrics including request counts, success rates,
    execution times, and credits used over a time period.
    
    Args:
        params (GetUsageStatsInput): Request parameters containing:
            - days (int): Number of days to get stats for (1-90, default 7)
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Usage statistics showing requests, success rate, and credits used
    
    Examples:
        - Last 7 days: {"days": 7}
        - Last 30 days: {"days": 30}
    """
    try:
        data = await fal_api_client.get_usage_stats(days=params.days)
        return _format_response(data, params.response_format)
    except Exception as e:
        return f"Error getting usage stats: {str(e)}"


# ============================================================================
# Batch Operations Tools
# ============================================================================


@mcp.tool(
    name="submit_batch_job",
    annotations={
        "title": "Submit Batch Jobs",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def submit_batch_job(params: SubmitBatchJobInput) -> str:
    """
    Submit multiple jobs as a batch to an application.
    
    Submits multiple input sets to the same application for parallel processing.
    Useful for processing multiple items at once (e.g., multiple images).
    Returns a list of request IDs, one per batch item.
    
    Args:
        params (SubmitBatchJobInput): Request parameters containing:
            - application_id (str): The application to run
            - batch_data (list): List of input objects (1-100 items)
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Submission confirmation with list of request IDs
    
    Examples:
        - Process multiple images: {
            "application_id": "img_app",
            "batch_data": [
              {"image_url": "url1"},
              {"image_url": "url2"},
              {"image_url": "url3"}
            ]
          }
    """
    try:
        request_ids = []
        for item in params.batch_data:
            data = await fal_api_client.submit_job(
                application_id=params.application_id,
                input_data=item,
            )
            if "request_id" in data:
                request_ids.append(data["request_id"])
        
        result = {
            "batch_size": len(request_ids),
            "request_ids": request_ids,
            "status": "submitted"
        }
        return _format_response(result, params.response_format)
    except Exception as e:
        return f"Error submitting batch job: {str(e)}"


@mcp.tool(
    name="get_job_logs",
    annotations={
        "title": "Get Job Logs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_job_logs(params: GetJobLogsInput) -> str:
    """
    Get execution logs for a job.
    
    Retrieves detailed logs from job execution including debug information,
    errors, and execution timeline. Useful for troubleshooting failed jobs.
    
    Args:
        params (GetJobLogsInput): Request parameters containing:
            - request_id (str): The request ID to get logs for
            - limit (int): Max log lines to return (1-1000, default 100)
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Formatted execution logs with timestamps
    
    Examples:
        - Get all logs: {"request_id": "req_abc123"}
        - Last 50 lines: {"request_id": "req_abc123", "limit": 50}
    """
    try:
        # Get job result to access logs
        result = await fal_api_client.get_job_result(params.response_url)
        logs = result.get("logs", "No logs available")
        
        # Limit lines if needed
        if isinstance(logs, str) and params.limit:
            log_lines = logs.split("\n")
            logs = "\n".join(log_lines[-params.limit:])
        
        output = {
            "request_id": params.request_id,
            "logs": logs
        }
        return _format_response(output, params.response_format)
    except Exception as e:
        return f"Error getting job logs: {str(e)}"


# ============================================================================
# High-Level Video Pipeline Tools
# ============================================================================


@mcp.tool(
    name="generate_video_project",
    description="Submit a complete AI video generation project with script synthesis, visual cue timeline generation, and fal.ai rendering",
    annotations={
        "title": "Generate AI Video Project",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def generate_video_project(params: GenerateVideoProjectInput) -> str:
    """
    Generate an AI video project using fal.ai models with automated script & visual timeline.
    
    Creates a new job in the database and launches the video production pipeline.
    """
    try:
        job_data = {
            "title": params.title,
            "niche": params.niche,
            "focus_keyword": params.focus_keyword,
            "visual_style": params.visual_style,
            "target_duration_sec": params.target_duration_sec,
            "full_script": params.full_script,
            "recap_intro": params.recap_intro,
            "custom_cliffhanger": params.custom_cliffhanger,
            "target_demographic": params.target_demographic,
            "voice_tone": params.voice_tone,
            "model_id": params.model_id or settings.DEFAULT_MODEL_VIDEO,
            "status": "QUEUED"
        }
        created = await db.create_job(job_data)
        job_id = created["id"]

        # Run pipeline
        final_job = await pipeline.run_video_pipeline(job_id)
        return _format_response(final_job, params.response_format)
    except Exception as e:
        return f"Error generating video project: {str(e)}"


@mcp.tool(
    name="list_video_jobs",
    description="List all video pipeline projects, filtered by status or search keyword",
    annotations={
        "title": "List Video Pipeline Jobs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_video_jobs(params: ListVideoJobsInput) -> str:
    """
    List video projects recorded in the SQLite pipeline database.
    """
    try:
        jobs = await db.list_jobs(status=params.status, search=params.search, limit=params.limit)
        return _format_response({"jobs": jobs, "count": len(jobs)}, params.response_format)
    except Exception as e:
        return f"Error listing video jobs: {str(e)}"


@mcp.tool(
    name="get_video_job",
    description="Get detailed information for a specific video pipeline project including script, timeline, media URL, and logs",
    annotations={
        "title": "Get Video Project Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_video_job(params: GetVideoJobInput) -> str:
    """
    Get full metadata and execution state for a video project.
    """
    try:
        job = await db.get_job(params.job_id)
        if not job:
            return f"Job '{params.job_id}' not found."
        return _format_response(job, params.response_format)
    except Exception as e:
        return f"Error retrieving video job: {str(e)}"


@mcp.tool(
    name="retry_video_job",
    description="Retry a failed or incomplete video pipeline job",
    annotations={
        "title": "Retry Video Pipeline Job",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def retry_video_job(params: RetryVideoJobInput) -> str:
    """
    Restart video generation pipeline for an existing job.
    """
    try:
        job = await db.get_job(params.job_id)
        if not job:
            return f"Job '{params.job_id}' not found."
        final_job = await pipeline.run_video_pipeline(params.job_id)
        return _format_response(final_job, params.response_format)
    except Exception as e:
        return f"Error retrying video job: {str(e)}"


# ============================================================================
# Server Entry Point
# ============================================================================


def main() -> None:
    """Parse CLI arguments and start the MCP server on the chosen transport."""
    import argparse

    parser = argparse.ArgumentParser(description="fal.ai MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable_http", "sse"],
        default="stdio",
        help="MCP transport to use (default: stdio)",
    )
    parser.add_argument("--host", default=settings.HOST, help="Host for HTTP transports")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Port for HTTP transports")
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport=args.transport.replace("_", "-"))


if __name__ == "__main__":
    main()
