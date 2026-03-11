# SPDX-License-Identifier: GPL-3.0-or-later
"""
Meme Editor Service - Handles video/audio cropping, mixing, and exporting.
"""
import os
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

logger = logging.getLogger(__name__)


class MemeEditorService:
    def __init__(self):
        # Default export directory for remixed memes
        self.export_dir = os.path.expanduser("~/MemeExports")
        os.makedirs(self.export_dir, exist_ok=True)

    def crop_to_vertical(self, video_path: str, output_filename: str) -> str:
        """
        Takes a standard landscape video and crops it from the center
        to a 9:16 ratio (TikTok/Reel/Shorts format).
        """
        try:
            clip = VideoFileClip(video_path)
            w, h = clip.size

            # Calculate target width for 9:16 aspect ratio based on original height
            target_w = int(h * (9 / 16))
            x_center = w / 2

            # Crop the center
            cropped = clip.crop(
                x1=x_center - target_w / 2,
                y1=0,
                x2=x_center + target_w / 2,
                y2=h,
            )

            output_path = os.path.join(self.export_dir, output_filename)
            logger.info(f"Exporting cropped video to: {output_path}")

            # Write file (using standard fast web-ready codecs)
            cropped.write_videofile(output_path, codec="libx264", audio_codec="aac")
            clip.close()

            return output_path
        except Exception as e:
            logger.error(f"Failed to crop video: {e}")
            raise

    def add_sound_effect(
        self,
        video_path: str,
        audio_path: str,
        output_filename: str,
        mute_original: bool = False,
    ) -> str:
        """
        Overlays an audio file (like a sound effect) onto a video clip.
        """
        try:
            video = VideoFileClip(video_path)
            sfx = AudioFileClip(audio_path)

            if mute_original or not video.audio:
                final_audio = sfx
            else:
                # Mix original audio with the sound effect
                final_audio = CompositeAudioClip([video.audio, sfx])

            final_clip = video.set_audio(final_audio)

            output_path = os.path.join(self.export_dir, output_filename)
            logger.info(f"Exporting audio-mixed video to: {output_path}")

            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

            video.close()
            sfx.close()

            return output_path
        except Exception as e:
            logger.error(f"Failed to add sound effect: {e}")
            raise
