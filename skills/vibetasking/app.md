# The app and the Chrome extension

Some of what a person does on the platform happens in the app or in the VibeTasking Browser extension for Chrome, with no operation behind it. When an ask lands on one, point the person to it by the name the app gives it, in their language, and say how it works.

## Recording a task

A person shows the platform how they do a task by recording their screen while they narrate it, and the recording reaches a run as the files of a message. They record from either place:

- **From the chat.** **Record screen** in the composer, on a computer, since a phone cannot record its screen from the browser. Chrome asks what to share (the entire screen, a window or a tab), and the microphone records their voice. A blocked microphone records on without their voice, and the app says how to allow it for the next one. A Mac that does not let the browser record the screen gets a button to the setting that allows it, and the browser must be reopened after. The sound the computer plays is recorded too when they tick the picker's option to share audio, which Chrome on a Mac does not offer for the entire screen. With the extension installed, the recording also carries every click, typed value and page they went through, and a screenshot of each step. Without it the recording is the video alone, and the app suggests installing the extension. Stopping attaches the files to the message they are writing, sent with whatever they type to the conversation that composer belongs to, so a recording made in a conversation with their Coordinator reaches the Coordinator.
- **From the extension.** **Record** in the extension's side panel, with the app open or closed. A recorder tab asks for the microphone, then what to share. A blocked microphone stops there with **Allow microphone** or **Record without narration**, and a start that fails says why with **Try again**, pointing a Mac to the setting that lets Chrome record the screen. Then they do the task in their own tabs and stop from the recorder tab, the side panel or Chrome's own bar to stop sharing. The recording stays in the extension until they send it with **Send to VibeTasking**, which starts a new run with no agent, named after the site it began on, whose first message is the recording.

A run that receives a recording is told which file is which, and to work out the task and carry it out by the best route, an integration's action wherever one covers a step. So a recording is how a person hands over a task they find easier to show than to describe, and the trace of clicks is what makes its steps exact. The trace never holds what was typed into a password, card, one time code or other sensitive field: it marks the field and names the secret its value should be stored as.

A recording made with any other tool is a video like any other file: attached to a message, or added to a disk, whose search reads what it says and shows (see **Finding what they hold** in `disks.md`).

## The Chrome extension

The VibeTasking Browser extension, installed from the Chrome Web Store, does three things in the person's own Chrome:

- **Runs work in their browser.** **Use my Chrome** in the composer, or ``browser_local`` in a run's configuration, has the run's browser work in their Chrome with the accounts they are signed in to (see **Local browser mode** in `runtime.md`). The tab it works in is framed and carries the agent's name and a Stop button, and the tabs a run opens are grouped apart from the person's own.
- **Its side panel follows those runs.** It lists the runs working in that browser, opens each one in the app, and raises a notification when one waits on the person. **Connect this browser** signs the browser in to a workspace, so the runs the person starts in their Chrome reach it with the app closed, while they are at that computer.
- **It records a task**, as **Recording a task** above describes.

## Talking instead of typing

- **Dictate** in the composer types what the person says into the message as they speak, in any conversation, while the workspace's dictation runs on a provider it has switched on.
- **Talk with the Coordinator**, where Send sits in an empty composer of a conversation with their Coordinator, starts a voice conversation: what they say reaches the Coordinator, and what it tells them is spoken back. The voice it speaks with is set in the app's settings, under Coordinator.

## Taking over a conversation

A channel conversation's composer carries an **Agent** and **You** switch. **You** takes the conversation over: the agent pauses, and what the person sends goes to the contact through the channel. **Agent** hands it back. The channel's ``operator_timeout`` hands it back on its own after a stretch with no reply from the team, and the ``OPERATOR`` notification setting tells the person when a contact writes in a conversation they hold (see **Notifications** in `operations.md`). The switch is the app's side of ``dispatch_human`` (see **Talking to people** in `runtime.md`). Over the API the same move is `update_run`'s ``hold``: ``OPERATOR`` takes the conversation over and ``null`` hands it back, neither sending a message, from a person's key and never from a run's own. On a channel with ``silent_handoff`` on the switch is unavailable, since its people reply from the account itself.

## The workspace's AI providers

The app's settings hold, under **AI providers**, what the workspace's AI runs on: its providers (its Claude Code or ChatGPT subscription, its own API accounts such as an OpenAI or Anthropic key, an Azure, Bedrock or Vertex tenancy or a server of its own, each checked with its provider before it is saved, and the platform's, each with a switch only an owner turns), and what each purpose runs on, Automatic being the platform's own configuration. Connecting an account offers to use it for every purpose it serves. An owner or admin who manages credentials sets them up there. `get_purposes` and `list_accounts` read the same (see **Where the workspace's AI runs** in `configuration.md`).

## Learning the platform

**Academy**, in the app's sidebar, holds the platform's videos and guides and a catalog of what agents can do, each ability with requests to try with the Coordinator.
