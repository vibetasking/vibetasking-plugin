---
name: video
description: Video generation, editing, frame extraction, and OCR of frames and photos
---

# Video (OmniToolkit + ffmpeg)

Generate, edit and extend video with Google Gemini Omni Flash. Audio is always generated with the video.

**There is no `video` CLI in the sandbox.** For generation and editing use the `omni` CLI below; for reading an existing video file (inspecting a customer attachment, sampling frames, checking dimensions/duration) use `ffmpeg`/`ffprobe` directly (see "Extract frame" and "Sample frames for inspection" below).

## Commands

### Generate video

```bash
omni generate_video --json '{"prompt": "A cat dancing in the rain, cinematic lighting. Single continuous shot.", "path": "cat.mp4", "duration": 8}'
```

Parameters:
- `prompt` (str, required): what the video shows and sounds like, or the motion to apply to the given frame(s)
- `path` (str): output path, default "video.mp4"
- `duration` (int): 3 to 10 seconds, default 8
- `aspect_ratio` (str): "16:9" (default) or "9:16"
- `resolution` (str): "360p" (cheapest, good for drafts), "720p" (default), "1080p" or "4k" (both upscaled, and cost more)
- `first_frame` (str, optional): image to open the video with (image-to-video)
- `last_frame` (str, optional): image to close the video with. Requires `first_frame`, and generates the motion between the two
- `reference_images` (list[str], optional): images of a person, character, product or style to keep. Name them in the prompt as `<IMAGE_REF_0>`, `<IMAGE_REF_1>` in the order given: `"the woman <IMAGE_REF_0> holds the bottle <IMAGE_REF_1> and smiles"`

### Edit video

```bash
omni edit_video --json '{"prompt": "Make the umbrella bright yellow", "source_video": "cat.mp4", "path": "cat_yellow.mp4"}'
```

Parameters:
- `prompt` (str, required): only the change. Everything not mentioned is kept
- `source_video` (str, required): the video to edit
- `path` (str): output path, default "video_edited.mp4"
- `resolution` (str): as for `generate_video`

A video made by `omni` can be edited again and again, each edit building on the last. A video from anywhere else must be 10 seconds or shorter, and editing one is not available in the EEA, Switzerland or the UK, where the call fails.

### Extend video

```bash
omni extend_video --json '{"prompt": "The camera pulls back to reveal a city skyline. The music swells.", "source_video": "cat.mp4", "duration": 6}'
```

Parameters:
- `prompt` (str, required): how the scene continues. Timings count from the start of the new part
- `source_video` (str, required): the video to extend
- `path` (str): output path, default "video_extended.mp4". The file holds the whole video with the new part appended
- `duration` (int): seconds to add, 3 to 10, default 8
- `resolution` (str): as for `generate_video`

A video made by `omni` can be extended repeatedly up to 40 seconds in total. A video from anywhere else must be 10 seconds or shorter, cannot gain new spoken dialogue, and extending one is not available in the EEA, Switzerland or the UK.

### Extract frame

```bash
# At a specific timestamp
ffmpeg -hide_banner -loglevel error -y -ss 00:00:04 -i video.mp4 -frames:v 1 frame.jpg

# First frame
ffmpeg -hide_banner -loglevel error -y -i video.mp4 -vf "select=eq(n\,0)" -vframes 1 frame.jpg

# Using the helper script
bash system/skills/video/scripts/frame.sh video.mp4 --time 00:00:04 --out frame.jpg
bash system/skills/video/scripts/frame.sh video.mp4 --index 0 --out frame.png
```

Options:
- `--time HH:MM:SS` -- extract frame at timestamp
- `--index N` -- extract Nth frame (0-based)
- `--out /path/to/output` -- output path (required). Use `.jpg` for quick share, `.png` for crisp frames.

### Sample frames for inspection

To review a video you didn't generate (e.g. a customer attachment) for a defect or issue, extract several evenly-spaced frames rather than guessing a single timestamp:

```bash
# One frame every 5 seconds, into a directory
bash system/skills/video/scripts/frame.sh video.mp4 --interval 5 --out frames/frame.jpg
```

This writes `frames/frame-00000.jpg`, `frames/frame-00005.jpg`, ... (suffixed by the timestamp in seconds) and prints each path it wrote, one per line. Every interval before the video's full duration is sampled, so a 5.5s clip at a 5s interval yields two frames. Start with a 5s interval; for a short clip (under ~30s) or a fast-moving defect, drop to 1-2s. There's no need to re-derive the ffmpeg flags per run -- the script handles both `-ss`-seeking and clamping the interval to the video's duration (via `ffprobe`).

### Inspect metadata

```bash
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,avg_frame_rate -of json video.mp4
```

### Contact sheet (one-glance overview)

Tile evenly-sampled frames into a single image to review a whole clip at once instead of opening frames one by one:

```bash
ffmpeg -hide_banner -loglevel error -y -i video.mp4 -vf "fps=1/5,scale=320:-1,tile=6x5" sheet.jpg
```

Pick `fps` and `tile` from the duration (frames = duration x fps, and they must fit the grid). One sheet is usually enough to decide which timestamps deserve a full-size frame.

### Find cuts and splices

```bash
ffmpeg -hide_banner -i video.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 | grep showinfo
```

Each `showinfo` line's `pts_time` is a scene change. Start at threshold 0.3 and drop toward 0.2 only if obvious cuts are missed. Useful for checking whether footage is continuous or edited.

### Read text in frames and photos (OCR)

```bash
tesseract frame.jpg out && cat out.txt
```

Extract the frame first (see above), then OCR it to read labels, reference numbers, or timestamps burned into the footage. The same pipeline reads customer photo attachments.

Tesseract's default settings assume a clean document scan and return noise on real-world photos. Preprocess first (grayscale, upscale, threshold) and pick a page-segmentation mode that matches the shot:

```bash
ffmpeg -i photo.jpg -vf "format=gray,scale=iw*2:ih*2" pre.png
tesseract pre.png out --psm 6 && cat out.txt
```

- `--psm 6` for a block of text, `--psm 7` for a single label or line, `--psm 11` for sparse text in a cluttered scene.
- Cropping to the label region before OCR beats running the whole photo.
- Empty or garbled output is a low-confidence signal, not an answer. Preprocess and retry once or twice. If it stays unreadable, report that (or ask for a clearer photo) rather than proceeding with noise.
- Scanning a video for a label: sample a handful of frames spread across the clip, OCR those, and stop at the first confident hit. Don't dump every frame and OCR them all.

## Workflows

- **Inspect before extending**: Extract a frame to see what's happening at a specific moment before deciding how to continue the scene. Use `--time` to sample different points in the video.
- **Inspect a customer/attachment video**: When you can dispatch a sub-agent, send the file to `dispatch_agent` with `specialist` set to "viewer" and your question, since the viewer watches and listens to the whole recording and answers with timestamps. Pull the frames you need to show, OCR or verify with `--interval` or `--time`, using the script rather than hand-rolled `ffmpeg -ss` loops.
- **Review video evidence (damage claims, disputes)**: probe metadata, build one contact sheet for the overview, extract full-size frames only at the timestamps that matter, scene-scan if you suspect edited footage, and OCR frames to read reference labels. This replaces re-deriving the pipeline from scratch each run.
- **Draft cheap, then finish**: Generate at 360p until the shot is right, then regenerate the chosen prompt at 720p or above.
- **Iterate on a clip**: Generate once, then refine with `edit_video` ("slower camera", "warmer light", "remove the logo on the wall") instead of regenerating from scratch. Each edit keeps what you did not mention.
- **Longer sequences**: Chain `extend_video` calls, up to 40 seconds in total. Each call returns the whole video so far, so extend the latest output.
- **Bridge two stills**: Pass `first_frame` and `last_frame` to `generate_video` to generate the motion between a starting and ending image, complete with audio. The same image as both gives a loop.
- **Keep a subject consistent**: Pass `reference_images` of a person, character, or product and name each one in the prompt as `<IMAGE_REF_N>`.
- **Image to video**: Generate an image with `banana generate_image`, then animate it with `omni generate_video` and `first_frame`.
- **Transcribe + plan**: Extract the audio (`ffmpeg -i video.mp4 -vn -c:a libmp3lame -q:a 4 audio.mp3`), transcribe it with `speech speech_to_text` (see the speech skill), then use the transcript to decide where to extract frames or how to extend the scene.
- **Presentation to video**: Create slides with the presentations skill, convert to images, then animate each slide into a video clip.
- **Add a soundtrack**: Generate a track with `lyria generate_music` (see the music skill for the timed-structure prompt and the ffmpeg mux), then mux it under the clip with `-shortest`.

## When to use this vs Tesseract and Remotion

- **Use this skill** when the footage itself has to be generated from a prompt or an image.
- **Use Tesseract** when the user supplies footage to cut, for ads and social edits, or for a project they can revise layer by layer.
- **Use Remotion** when the video is data driven, rendered in batches from parameters, or needs chart libraries, Lottie, maps or three.js.

Rule of thumb: if the user describes a **scene** ("a cat dancing in the rain"), use this. If they describe a **design** ("animated bar chart with our quarterly numbers"), use Remotion.

## Notes

- Content moderation may reject prompts. Rephrase and retry.
- Omni generates the video and its audio together. There is no separate audio step, and audio cannot be turned off. Describe the sound you want ("no dialogue", "calm background music").
- By default Omni cuts between a few shots to tell a story. Ask for "a single continuous shot, no scene cuts" when one unbroken scene is wanted.
- Put what to avoid in the prompt as plain instructions ("no text on screen"). There is no negative prompt parameter.
- Omni is only evaluated on English prompts. Write the prompt in English and quote any on-screen text or dialogue in the language it should appear in.
- All paths are relative to the sandbox root.
- A generation can take a few minutes. This is normal.

---

Companion files, each in this skill's folder beside this file:
- scripts/frame.sh

A ``system/skills/<skill>/<file>`` path cited above names ``<file>`` in the ``<skill>`` folder of this plugin's skills, next to this skill's own folder.
