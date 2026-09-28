---
name: speech
description: Text-to-speech, two-voice dialogue and speech-to-text using Gemini audio
  models
---

# Speech (SpeechToolkit)

## Commands

### Text to speech

```bash
speech text_to_speech --json '{"text": "Bienvenidos a la revisión trimestral. <short pause> Empecemos.", "path": "intro.mp3", "voice": "es-es-advisor-2", "style": "calm and confident"}'
```

The text is read verbatim, in the language it is written in. Direction goes elsewhere:
- `style`: how the whole text is delivered, in a few words ("warm and enthusiastic", "speaking slowly", "whispered urgently"). Leave it out for a natural read, which is right most of the time.
- Inline vocal tags in angle brackets, placed where they happen: `<laugh>`, `<chuckle>`, `<sigh>`, `<breath>`, `<gasp>`, `<cough>`, `<whispers>`, `<short pause>`, `<long pause>`. Keep the tags in English whatever the language of the text.
- Capitalize a word to stress it. Commas and ellipses shape the pacing.

Voice selection:
- Prebuilt voices work in every language: `Kore` (firm, the default), `Puck` (upbeat), `Charon` (informative), `Aoede` (breezy), `Zephyr` (bright), `Sulafat` (warm), `Achird` (friendly), `Gacrux` (mature), `Schedar` (even), and more.
- For a native accent, list the voice library by language and pick an id: `speech list_voices --json '{"language": "es-ES"}'`. Filter by `gender` or `search` ("narrator", "warm", "news") to narrow it. Use the voice's id as `voice`.
- Keep one voice per character across a piece. Change the voice, not the `style`, to change age, gender or accent.

Formats:
- `mp3` by default (universally playable, small).
- `wav` when feeding the output into downstream audio processing.
- `opus` (Ogg Opus) for voice notes on WhatsApp and other messaging channels.

Long text is synthesized in pieces and joined into one file, so there is no need to split it yourself.

### Dialogue

```bash
speech speak_dialogue --json '{"turns": [{"speaker": "Ana", "text": "¿Ya está listo el informe?"}, {"speaker": "Luis", "text": "Casi |ah, vale| me falta una tabla.", "style": "relaxed"}], "voices": {"Ana": "Kore", "Luis": "Puck"}, "path": "dialogue.mp3"}'
```

Two speakers at most, each on a prebuilt voice. Each turn may carry its own `style`. Wrap a listener's short reaction in pipes inside the other speaker's turn (`|oh really?|`) to overlap it naturally. Use this for podcasts, role plays, and sample calls.

### Speech to text

```bash
speech speech_to_text --json '{"source_audio": "uploads/meeting.mp3"}'
```

The transcript comes back diarized: one line per speaker turn, each prefixed with the speaker label and its
start and end time in seconds (`[12.3-15.6] A: ...`). Speakers are labeled A, B, C in order of appearance.

Splitting large audio:
- Files over 25 MB must be split before transcription. Use ffmpeg:

```bash
ffmpeg -hide_banner -loglevel error -i long.mp3 -f segment -segment_time 600 -c copy part_%03d.mp3
```

Then call `speech speech_to_text` on each part and concatenate the transcripts.

## Workflows

- **Voice reply**: compose a reply with the agent, call `speech text_to_speech` to produce an audio file, then deliver it in your reply or attached to a message to the user.
- **Meeting transcript**: user uploads a recording → `speech speech_to_text` → summarize/structure the transcript → write to a document with the documents skill.
- **Dubbing / localization**: `speech speech_to_text` (with `language`) → translate the transcript → `speech list_voices` for the target language → `speech text_to_speech` with that voice.
- **Video narration**: draft the script, `speech text_to_speech` → combine with visuals using the video skill (`ffmpeg -i video.mp4 -i narration.mp3 -c:v copy -c:a aac -shortest out.mp4`).
- **Voice memo intake**: user sends a voice note → transcribe → act on the content (create todos, draft email, fill a form).
