#!/usr/bin/env python3
"""
Example usage patterns for fal.ai MCP server.

This script demonstrates common workflows and how to interact with
the fal.ai MCP server programmatically.
"""

import asyncio
import json
import os
from typing import Dict, Any

import fal_api_client
from models import (
    ResponseFormat,
    ListApplicationsInput,
    GetApplicationInput,
    SubmitJobInput,
    PollJobStatusInput,
)


async def example_1_list_applications():
    """Example 1: List available applications."""
    print("\n" + "="*60)
    print("EXAMPLE 1: List Available Applications")
    print("="*60)
    
    try:
        result = await fal_api_client.list_applications(
            limit=5,
            search="image"
        )
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(f"Error: {e}")


async def example_2_get_application_details():
    """Example 2: Get details about a specific application."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Get Application Details")
    print("="*60)
    
    # First, list apps to find an ID
    try:
        apps = await fal_api_client.list_applications(limit=1)
        if apps.get("items"):
            app_id = apps["items"][0].get("id")
            print(f"Getting details for app: {app_id}")
            
            result = await fal_api_client.get_application(app_id)
            print(json.dumps(result, indent=2, default=str))
        else:
            print("No applications found")
    except Exception as e:
        print(f"Error: {e}")


async def example_3_submit_job():
    """Example 3: Submit a job to an application."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Submit a Job")
    print("="*60)
    
    # Example app ID for image generation (you'll need a real one)
    APP_ID = "110602490541725184"  # FLUX.1 [pro] - example
    
    input_data = {
        "prompt": "a peaceful mountain landscape at sunset",
        "num_images": 1,
        "num_inference_steps": 20,
        "guidance_scale": 7.5,
    }
    
    try:
        print(f"Submitting job to app {APP_ID}")
        print(f"Input: {json.dumps(input_data, indent=2)}")
        
        result = await fal_api_client.submit_job(
            application_id=APP_ID,
            input_data=input_data,
        )
        
        print(f"\nJob submitted successfully!")
        print(f"Request ID: {result.get('request_id')}")
        print(json.dumps(result, indent=2, default=str))
        
        return result.get("request_id")
    except Exception as e:
        print(f"Error: {e}")
        return None


async def example_4_poll_and_get_result(request_id: str):
    """Example 4: Poll job status and get result."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Poll Job Status and Get Result")
    print("="*60)
    
    if not request_id:
        print("No request ID provided")
        return
    
    try:
        # Poll status
        print(f"Checking status of job: {request_id}")
        status = await fal_api_client.poll_job_status(request_id)
        print(f"Current status: {status.get('status')}")
        print(json.dumps(status, indent=2, default=str))
        
        # If not complete, show how to check later
        if status.get("status") != "COMPLETED":
            print("\nJob is still processing. Come back later to get results.")
            print(f"Use poll_job_status('{request_id}') to check progress.")
            return
        
        # Get result if complete
        print("\nJob is complete! Getting results...")
        result = await fal_api_client.get_job_result(request_id)
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"Error: {e}")


async def example_5_batch_operations():
    """Example 5: Submit multiple jobs as batch."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Batch Operations")
    print("="*60)
    
    APP_ID = "110602490541725184"  # Example
    
    # List of items to process
    batch_items = [
        {"prompt": "a red apple"},
        {"prompt": "a blue ocean"},
        {"prompt": "a green forest"},
    ]
    
    try:
        request_ids = []
        print(f"Submitting {len(batch_items)} jobs as batch...")
        
        for i, item in enumerate(batch_items):
            print(f"  [{i+1}/{len(batch_items)}] Submitting: {item}")
            
            result = await fal_api_client.submit_job(
                application_id=APP_ID,
                input_data=item,
            )
            
            request_ids.append(result.get("request_id"))
        
        print(f"\nBatch submission complete!")
        print(f"Request IDs: {request_ids}")
        print("\nYou can now track each job individually:")
        for i, req_id in enumerate(request_ids):
            print(f"  Job {i+1}: {req_id}")
            
    except Exception as e:
        print(f"Error: {e}")


async def example_6_account_info():
    """Example 6: Check account information."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Account Information")
    print("="*60)
    
    try:
        # Get account info
        account = await fal_api_client.get_account_info()
        print("Account Information:")
        print(json.dumps(account, indent=2, default=str))
        
        # Get usage stats
        usage = await fal_api_client.get_usage_stats(days=7)
        print("\nUsage Statistics (Last 7 Days):")
        print(json.dumps(usage, indent=2, default=str))
        
    except Exception as e:
        print(f"Error: {e}")


async def example_7_list_queue():
    """Example 7: List queue items for an application."""
    print("\n" + "="*60)
    print("EXAMPLE 7: List Queue Items")
    print("="*60)
    
    APP_ID = "110602490541725184"  # Example
    
    try:
        # List all items in queue
        print(f"Listing queue for app: {APP_ID}")
        queue = await fal_api_client.list_queue_items(
            application_id=APP_ID,
            limit=10,
            status="IN_PROGRESS"
        )
        print(json.dumps(queue, indent=2, default=str))
        
    except Exception as e:
        print(f"Error: {e}")


async def example_8_cancel_job():
    """Example 8: Cancel a job."""
    print("\n" + "="*60)
    print("EXAMPLE 8: Cancel a Job")
    print("="*60)
    
    request_id = "req_example123"  # Would be actual request ID
    
    print(f"To cancel a job, use request ID: {request_id}")
    print("Uncomment the code below to actually cancel:")
    print(f"""
    # result = await fal_api_client.cancel_job('{request_id}')
    # print(json.dumps(result, indent=2, default=str))
    """)


async def example_9_workflow_image_generation():
    """Example 9: Complete image generation workflow."""
    print("\n" + "="*60)
    print("EXAMPLE 9: Complete Image Generation Workflow")
    print("="*60)
    
    APP_ID = "110602490541725184"  # FLUX.1 [pro]
    
    try:
        # Step 1: Check account
        print("Step 1: Checking account...")
        account = await fal_api_client.get_account_info()
        credits = account.get("credits_available", 0)
        print(f"  ✓ Available credits: {credits}")
        
        if credits < 1:
            print("  ✗ Insufficient credits!")
            return
        
        # Step 2: Submit job
        print("\nStep 2: Submitting job...")
        job_input = {
            "prompt": "a futuristic robot in a neon city",
            "num_images": 1,
        }
        
        job = await fal_api_client.submit_job(
            application_id=APP_ID,
            input_data=job_input,
        )
        request_id = job.get("request_id")
        print(f"  ✓ Job submitted: {request_id}")
        
        # Step 3: Poll until complete
        print("\nStep 3: Waiting for job to complete...")
        max_attempts = 60
        for attempt in range(max_attempts):
            status = await fal_api_client.poll_job_status(request_id)
            current_status = status.get("status")
            position = status.get("queue_position")
            eta = status.get("eta_seconds", 0)
            
            if current_status == "COMPLETED":
                print(f"  ✓ Job completed!")
                break
            elif current_status == "FAILED":
                print(f"  ✗ Job failed!")
                break
            else:
                print(f"  → Status: {current_status}, Position: {position}, ETA: {eta}s")
            
            # Wait before next poll
            await asyncio.sleep(2)
        else:
            print("  ⚠ Max polling attempts reached")
        
        # Step 4: Get result
        if current_status == "COMPLETED":
            print("\nStep 4: Retrieving results...")
            result = await fal_api_client.get_job_result(request_id)
            output = result.get("result", {})
            
            if output.get("image_url"):
                print(f"  ✓ Image URL: {output['image_url']}")
            
            print("\nWorkflow complete!")
        
    except Exception as e:
        print(f"Error: {e}")


async def example_10_error_handling():
    """Example 10: Error handling patterns."""
    print("\n" + "="*60)
    print("EXAMPLE 10: Error Handling Patterns")
    print("="*60)
    
    print("""
Common errors and how to handle them:

1. Authentication Error:
   - Check FAL_API_KEY environment variable is set
   - Verify key is valid at https://www.fal.ai/dashboard/keys
   - Regenerate if necessary

2. Not Found Error:
   - Verify application_id is correct
   - Use list_applications to find valid IDs
   - Check request_id is from recent submission

3. Rate Limit Error:
   - Wait before making more requests
   - Check your subscription tier at https://www.fal.ai/pricing
   - Upgrade if needed for higher limits

4. Timeout Error:
   - Job may still be processing
   - Use poll_job_status to check progress
   - Don't immediately retry, wait a moment

5. Insufficient Credits:
   - Check account_info for credit balance
   - See pricing for each application
   - Upgrade subscription or purchase credits
    """)


async def main():
    """Run all examples."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║         fal.ai MCP Server - Usage Examples                    ║
╚════════════════════════════════════════════════════════════════╝
    
These examples demonstrate common patterns for using the
fal.ai MCP server with Claude and LLMs.
    """)
    
    # Check API key
    if not os.environ.get("FAL_API_KEY"):
        print("⚠  WARNING: FAL_API_KEY not set!")
        print("  Please set your API key:")
        print("  export FAL_API_KEY='your-key-here'")
        print("\nExamples will show patterns but may not execute fully.")
    
    # Run examples
    await example_1_list_applications()
    await example_6_account_info()
    await example_5_batch_operations()
    await example_7_list_queue()
    await example_8_cancel_job()
    await example_9_workflow_image_generation()
    await example_10_error_handling()
    
    # Note about interactive examples
    print("\n" + "="*60)
    print("NOTES")
    print("="*60)
    print("""
- Examples 2, 3, 4 require valid application IDs
- Example 3 submits a real job and may use credits
- Example 4 polls a specific job (provide request_id)
- Uncomment code examples to test with real data
- Check fal.ai dashboard for available applications
    """)


if __name__ == "__main__":
    asyncio.run(main())
