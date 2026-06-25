"""
Comprehensive test suite for fal.ai Video Pipeline and Command Center.
"""

import asyncio
import json
import os
import unittest
from pathlib import Path

# Ensure testing uses local temporary DB
os.environ["DATABASE_PATH"] = "/tmp/test_pipeline.db"

import db
import pipeline
from settings import settings
import models
import fal_mcp


class TestVideoPipeline(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        """Set up test database."""
        db.init_db_sync()

    async def asyncTearDown(self):
        """Clean up test database."""
        if Path("/tmp/test_pipeline.db").exists():
            try:
                os.remove("/tmp/test_pipeline.db")
            except Exception:
                pass

    def test_settings_loaded(self):
        """Test settings configuration and validation."""
        self.assertIsNotNone(settings.APP_NAME)
        self.assertEqual(settings.VERSION, "2.0.0")

    def test_json_recovery_heuristic(self):
        """Test sanitization of glitchy/repetitive LLM text."""
        # Clean JSON with markdown wrapper
        sample_md = '```json\n{"title": "Neo-Tokyo", "shots": 4}\n```'
        parsed = pipeline.sanitize_llm_json_response(sample_md)
        self.assertEqual(parsed.get("title"), "Neo-Tokyo")
        self.assertEqual(parsed.get("shots"), 4)

        # JSON with repetitive trailing glitch phrases
        sample_glitch = '{"scene": "Cyberpunk City"} and then and then and then and then'
        parsed_glitch = pipeline.sanitize_llm_json_response(sample_glitch)
        self.assertEqual(parsed_glitch.get("scene"), "Cyberpunk City")

        # JSON with trailing comma
        sample_comma = '{"status": "ready", "count": 10, }'
        parsed_comma = pipeline.sanitize_llm_json_response(sample_comma)
        self.assertEqual(parsed_comma.get("count"), 10)

    def test_visual_cue_timeline_generator(self):
        """Test visual cue timeline breakdown."""
        script = "In Neo-Kyoto, neon lights pierce the rainy darkness. A cybernetic detective enters an abandoned data vault. He discovers a secret that alters everything."
        timeline = pipeline.generate_visual_cue_timeline(
            script=script,
            visual_style="Anime / Cyberpunk",
            target_duration_sec=30,
            focus_keyword="Cybernetic Underworld"
        )
        self.assertGreaterEqual(len(timeline), 3)
        self.assertEqual(timeline[0]["shot_number"], 1)
        self.assertIn("visual_prompt", timeline[0])
        self.assertIn("timestamp_start", timeline[0])

    async def test_database_crud_and_migration(self):
        """Test SQLite job persistence and dynamic columns."""
        job_data = {
            "title": "Test Production",
            "niche": "Sci-Fi Lore",
            "visual_style": "Dark Noir",
            "focus_keyword": "Quantum Core",
            "target_duration_sec": 45,
            "status": "QUEUED"
        }
        created = await db.create_job(job_data)
        self.assertIsNotNone(created.get("id"))
        self.assertEqual(created["title"], "Test Production")
        self.assertEqual(created["status"], "QUEUED")

        # Fetch job
        fetched = await db.get_job(created["id"])
        self.assertEqual(fetched["id"], created["id"])

        # Update job
        updated = await db.update_job(created["id"], {
            "status": "IN_PROGRESS",
            "video_path": "https://example.com/test.mp4"
        })
        self.assertEqual(updated["status"], "IN_PROGRESS")
        self.assertEqual(updated["video_path"], "https://example.com/test.mp4")

        # List jobs
        jobs = await db.list_jobs()
        self.assertGreaterEqual(len(jobs), 1)

    async def test_fallback_generation_pipeline(self):
        """Test high-quality fallback engine."""
        job_data = {
            "title": "Fallback Test Episode",
            "niche": "Dark Fantasy",
            "visual_style": "Cinematic Photorealism",
            "focus_keyword": "Forgotten Bloodline",
            "target_duration_sec": 60
        }
        created = await db.create_job(job_data)
        final_job = await pipeline.run_video_pipeline(created["id"])

        self.assertEqual(final_job["status"], "COMPLETED")
        self.assertIsNotNone(final_job["video_path"])
        self.assertIsNotNone(final_job["full_script"])
        self.assertIn("timeline", final_job["metadata"])

    async def test_mcp_tools_registered(self):
        """Verify new video tools are registered on the FastMCP instance."""
        tools = fal_mcp.mcp._tool_manager._tools
        self.assertIn("generate_video_project", tools)
        self.assertIn("list_video_jobs", tools)
        self.assertIn("get_video_job", tools)
        self.assertIn("retry_video_job", tools)


if __name__ == "__main__":
    unittest.main()
