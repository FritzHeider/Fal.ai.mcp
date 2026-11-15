"""
Automated Viral Episode Production Pipeline CLI.

Takes a narrative concept, prompts fal.ai for video (Kling) and voiceover (Kokoro),
generates high-CTR thumbnails (FLUX), and compiles final 16:9 and 9:16 Shorts with ffmpeg.
"""

import argparse
import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

import httpx
import db
import fal_api_client
from settings import settings

OUTPUT_DIR = Path(__file__).resolve().parent / "episodes"


async def produce_episode(
    episode_num: int,
    title: str,
    video_prompt: str,
    script_narration: str,
    thumbnail_prompt: str,
    output_dir: Path = OUTPUT_DIR
) -> Dict[str, Any]:
    """Execute complete end-to-end automated production for an episode."""
    ep_slug = f"episode_{episode_num:02d}_{title.lower().replace(' ', '_')[:30]}"
    target_folder = output_dir / ep_slug
    target_folder.mkdir(parents=True, exist_ok=True)

    print(f"\n=======================================================")
    print(f"🎬 PRODUCING EPISODE {episode_num}: '{title}'")
    print(f"📁 Output Directory: {target_folder}")
    print(f"=======================================================\n")

    async with httpx.AsyncClient(timeout=180.0) as client:
        # Step 1: Submit Voiceover (Kokoro TTS)
        print("🎙️ [1/4] Generating AI Voiceover with fal.ai Kokoro...")
        tts_sub = await fal_api_client.submit_job("fal-ai/kokoro", {
            "prompt": script_narration,
            "voice": "am_adam"
        })
        tts_status_url = tts_sub.get("status_url")
        tts_resp_url = tts_sub.get("response_url")

        # Step 2: Submit Video Render (Kling Video)
        print("🎥 [2/4] Generating 3D Animated Video with fal.ai Kling...")
        vid_sub = await fal_api_client.submit_job("fal-ai/kling-video/v1/standard/text-to-video", {
            "prompt": video_prompt,
            "duration": 5,
            "aspect_ratio": "16:9"
        })
        vid_status_url = vid_sub.get("status_url")
        vid_resp_url = vid_sub.get("response_url")

        # Step 3: Submit 4K Thumbnail (FLUX Schnell)
        print("🖼️ [3/4] Generating 4K Viral Thumbnail with fal.ai FLUX...")
        thumb_sub = await fal_api_client.submit_job("fal-ai/flux/schnell", {
            "prompt": thumbnail_prompt,
            "image_size": "landscape_16_9",
            "num_images": 1
        })
        thumb_status_url = thumb_sub.get("status_url")
        thumb_resp_url = thumb_sub.get("response_url")

        # Poll all jobs concurrently
        print("⏳ Polling render jobs until completion...")

        async def poll_until_done(status_url, resp_url, job_name):
            while True:
                data = await fal_api_client.poll_job_status(status_url)
                st = data.get("status")
                if st == "COMPLETED":
                    res = await fal_api_client.get_job_result(resp_url)
                    print(f"✅ {job_name} finished!")
                    return res
                elif st in ("FAILED", "CANCELLED"):
                    raise RuntimeError(f"{job_name} failed: {data}")
                await asyncio.sleep(2.0)

        tts_res, vid_res, thumb_res = await asyncio.gather(
            poll_until_done(tts_status_url, tts_resp_url, "Voiceover (Kokoro)"),
            poll_until_done(vid_status_url, vid_resp_url, "Video (Kling)"),
            poll_until_done(thumb_status_url, thumb_resp_url, "Thumbnail (FLUX)")
        )

        # Download raw assets
        print("\n📥 Downloading raw rendered assets...")
        audio_url = tts_res["audio"]["url"]
        audio_file = target_folder / "voiceover.wav"
        a_resp = await client.get(audio_url)
        audio_file.write_bytes(a_resp.content)

        raw_vid_url = (vid_res.get("video", {}).get("url") or vid_res.get("output", {}).get("url") or vid_res.get("url"))
        raw_vid_file = target_folder / "raw_render.mp4"
        v_resp = await client.get(raw_vid_url)
        raw_vid_file.write_bytes(v_resp.content)

        thumb_url = thumb_res["images"][0]["url"]
        thumb_file = target_folder / "thumbnail_4k.jpg"
        t_resp = await client.get(thumb_url)
        thumb_file.write_bytes(t_resp.content)

        # Step 4: Compile Final Masters with ffmpeg
        print("🎞️ [4/4] Mastering 16:9 & 9:16 Shorts with ffmpeg...")
        master_16x9 = target_folder / "final_master_16x9.mp4"
        shorts_9x16 = target_folder / "final_shorts_9x16.mp4"

        # 16:9 master
        subprocess.run([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(raw_vid_file),
            "-i", str(audio_file),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(master_16x9)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 9:16 shorts master
        subprocess.run([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(raw_vid_file),
            "-i", str(audio_file),
            "-filter_complex", "[0:v]crop=ih*9/16:ih,scale=1080:1920[v]",
            "-map", "[v]", "-map", "1:a:0",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(shorts_9x16)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Manifest
        manifest = {
            "episode_number": episode_num,
            "title": title,
            "script": script_narration,
            "video_prompt": video_prompt,
            "files": {
                "master_16x9": str(master_16x9),
                "shorts_9x16": str(shorts_9x16),
                "thumbnail": str(thumb_file),
                "voiceover_wav": str(audio_file),
                "raw_video": str(raw_vid_file)
            },
            "cloud_urls": {
                "audio": audio_url,
                "video": raw_vid_url,
                "thumbnail": thumb_url
            }
        }
        manifest_file = target_folder / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2))

        # Copy to artifact folder for Antigravity viewer
        artifact_dir = Path("/Users/drop/.gemini/antigravity/brain/cdfbb993-99a9-4475-800f-13fb4b5fcbe6")
        if artifact_dir.exists():
            import shutil
            shutil.copy(master_16x9, artifact_dir / f"ep{episode_num}_master_16x9.mp4")
            shutil.copy(shorts_9x16, artifact_dir / f"ep{episode_num}_shorts_9x16.mp4")
            shutil.copy(thumb_file, artifact_dir / f"ep{episode_num}_thumbnail.jpg")

        print(f"\n🎉 Episode {episode_num} Master Complete!")
        print(f"16:9 Master: {master_16x9}")
        print(f"9:16 Shorts: {shorts_9x16}")
        return manifest


def main():
    parser = argparse.ArgumentParser(description="Auto Produce Viral YouTube Episode")
    parser.add_argument("--ep", type=int, default=2, help="Episode number")
    parser.add_argument("--title", default="The Red Button Catastrophe", help="Episode title")
    args = parser.parse_args()

    # Default Episode 2 script
    script = (
        "Episode two! Pip is floating in zero-G panic while footsteps echo down the arcade hall! "
        "Desperate to disable gravity, Pip spots the giant flashing RED BUTTON on the ceiling! "
        "With one heroic leap, he slams his paws right onto the switch! "
        "Uh oh... that wasn't the gravity reset. THAT WAS MEGA DISCO LASER MODE! "
        "Can Pip escape the laser dance floor?! Vote in the comments for his next move!"
    )
    
    vid_prompt = (
        "3D Pixar animated cartoon shot, cute chubby character named Pip in bright yellow bunny hoodie "
        "floating upside down in zero gravity, desperately slamming a glowing red arcade emergency button, "
        "instant neon laser disco lights explosion, chaotic funny cartoon expression, 8k render, octane render"
    )

    thumb_prompt = (
        "High energy 3D Pixar YouTube thumbnail, cute chubby character Pip in yellow bunny hoodie with terrified "
        "jaw-dropped funny expression pressing a giant glowing neon red button, massive rainbow laser explosion "
        "in background, high click-through rate composition, 8k octane render"
    )

    asyncio.run(produce_episode(
        episode_num=args.ep,
        title=args.title,
        video_prompt=vid_prompt,
        script_narration=script,
        thumbnail_prompt=thumb_prompt
    ))


if __name__ == "__main__":
    main()
