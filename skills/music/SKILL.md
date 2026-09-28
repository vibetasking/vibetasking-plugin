---
name: music
description: Music generation, full songs with vocals and lyrics or short instrumental
  clips and loops
---

# Music (LyriaToolkit + ffmpeg)

Generate music with Google Lyria 3.5. Every track is a 44.1 kHz stereo MP3 and carries a SynthID audio watermark plus the platform's AI-provenance tag.

**There is no `music` CLI in the sandbox.** Generation goes through the `lyria` CLI below. Trimming, looping, mixing and muxing use `ffmpeg` directly.

## Commands

### Generate music

```bash
lyria generate_music --json '{"prompt": "An upbeat indie pop song about a road trip at sunrise, bright guitars, driving drums, warm female vocals, about 90 seconds", "path": "roadtrip.mp3"}'
```

Parameters:
- `prompt` (str, required): what the track should sound like, plus any lyrics or timed structure
- `path` (str): output path, default "music.mp3". The extension is always .mp3.
- `model` (str): "lyria-3.5" (default, full-length song of a couple of minutes) or "lyria-3-clip-preview" (fixed 30-second clip or loop, half the price)
- `images` (list[str], optional): up to 10 images whose mood and colors inspire the track

The result is the path to the track, followed by the lyrics when the model sang any. They arrive with Lyria's own section markers (`[[A0]]`, `[[B1]]`, `[[C2]]`) and a `[:]` prefix per line. Strip those before showing lyrics to the user.

## Prompting

- **Describe the music, not the use.** Genre, mood, instruments, tempo, vocal style and structure: "a slow, melancholic piano ballad with soft strings and a male vocal that builds to a big final chorus".
- **Instrumental**: end the prompt with "Instrumental only, no vocals." Lyria sings by default.
- **Length**: say it in the prompt ("a 45-second jingle", "a two-minute track"). It is a hint, not a cut: Lyria 3.5 lands around a couple of minutes on its own and rounds a short request up to a full verse and chorus, so trim with ffmpeg when the length must be exact. Lyria 3 Clip is always 30 seconds.
- **Language**: write the prompt in the language the vocals should sing in. A Spanish prompt gets Spanish vocals.
- **Custom lyrics**: put them in the prompt under section tags, one section per block:

```text
Create a dreamy indie pop song with the following lyrics:

[Verse 1]
Walking through the neon glow, city lights reflect below

[Chorus]
We are the echoes in the night, burning brighter than the light
```

- **Timed structure**: pin sections to time ranges so the arrangement follows a script or a video cut:

```text
[0:00 - 0:10] Intro: soft lo-fi beat and vinyl crackle.
[0:10 - 0:30] Verse: warm Rhodes piano and gentle vocals about a rainy morning.
[0:30 - 0:50] Chorus: full band, upbeat drums, soaring synth lead.
[0:50 - 1:00] Outro: fade out on the piano alone.
```

- **From an image**: pass the image in `images` and ask for "a track inspired by the mood and colors of this image".

## Editing with ffmpeg

```bash
# Trim to the first 30 seconds with a two-second fade out
ffmpeg -hide_banner -loglevel error -y -i music.mp3 -t 30 -af "afade=t=out:st=28:d=2" short.mp3

# Loop a clip three times
ffmpeg -hide_banner -loglevel error -y -stream_loop 2 -i clip.mp3 -c copy looped.mp3

# Put the track under a video, cut to the shorter of the two
ffmpeg -hide_banner -loglevel error -y -i video.mp4 -i music.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest scored.mp4

# Mix music under a narration, music at a quarter of its volume
ffmpeg -hide_banner -loglevel error -y -i narration.mp3 -i music.mp3 -filter_complex "[1:a]volume=0.25[bg];[0:a][bg]amix=inputs=2:duration=first" mixed.mp3

# Inspect duration
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 music.mp3
```

## Workflows

- **Soundtrack a video**: generate the video with the video skill, probe its duration, ask Lyria for a track of that length with a timed structure matching the cuts, then mux with `-shortest`.
- **Narration with a bed**: `speech text_to_speech` for the voice (speech skill), an instrumental from Lyria, then `amix` with the music turned down.
- **Jingle or sting**: use `lyria-3-clip-preview` for a 30-second loop, then trim with `-t` and a fade.
- **A song for someone**: draft the lyrics with the user's details, tag the sections, and pass them in the prompt. Return the lyrics that came back so the user can read what is sung.

## Notes

- Generation is one shot. There is no editing of an existing track by prompt. Change the prompt and regenerate.
- Two identical prompts give two different tracks.
- The model refuses prompts that name a real artist's voice or quote copyrighted lyrics. Describe the style instead ("a 70s funk groove with a falsetto lead").
- The output is always MP3. When a downstream step needs WAV, convert it: `ffmpeg -i music.mp3 music.wav`.
- All paths are relative to the sandbox root.
- A full-length song takes a few minutes to generate. This is normal.
