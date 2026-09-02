# VERTEX WORKS — VERTEX CLIP RELAY 000093

While Vertex Works is running:

- selected browser text + middle button => CLIP IN;
- selected Explorer files + middle button => CLIP IN;
- next middle button elsewhere => RELEASE / PASTE;
- Evidence button => PRIORITY CLIP IN;
- next middle button in Vera / ChatGPT or another destination => RELEASE.

Priority Evidence always releases first.

Normal clips first attempt a fresh Ctrl+C selection capture on the next middle press. If no new selection changes the clipboard, the armed clip is released using Ctrl+V.

When nothing is selected and nothing is armed, native middle click passes through.

Explorer selections are captured as Windows CF_HDROP. On release the relay publishes both CF_HDROP and newline-separated Unicode paths, so targets can accept files or text-path fallback.

Windows only. Active only while Works is running. The listener reacts only to middle-button down/up.
