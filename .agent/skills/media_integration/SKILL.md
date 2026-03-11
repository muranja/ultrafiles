---
name: media_rails
description: Standards for implementing reliable media playback and metadata handling.
---

# Media Integration Rails

## 1. Architecture Rails

- **Separation**:
  - **MUST** separate Media Logic (services) from UI Widgets.
  - `MediaPlayerService`: Handles GStreamer/Gtk.MediaStream.
  - `VideoWidget`: Handles display and input.

## 2. Playback Rails

- **State Management**:
  - **MUST** handle error states (missing codec, corrupt file) gracefully with `Adw.StatusPage`.
  - **MUST** pause playback when window loses focus or minimizes.
- **Preview**:
  - **MUST** be muted by default.
  - **MUST NOT** steal focus from file list.

## 3. Metadata Rails

- **Library**:
  - **MUST** use `mutagen` for MP3/FLAC/OGG/MP4 tagging.
  - **AVOID** parsing binary headers manually.
- **Safety**:
  - **MUST** operate on a temporary file or backup before saving tags to avoid corruption.
  - **MUST** reload file stats after metadata write.
