# VERTEX WORKS — VERTEX CONTEXT MENU FOUNDATION 000097

Windows / Chromium-style native right-click menus are not part of the Vertex visual language.

000097 establishes the Works-side foundation for the global Vertex mouse contract:

- Left Click = ACT
- Right Click = CONTEXT
- Middle Click = RELAY

Right-click behavior:

- Empty / non-semantic area:
  - Product Properties
  - Help / Input Guide
  - Vertex Product Site
- Incoming Cargo card:
  - Inspect
  - Clip In Path
  - Copy Path
  - Properties
- Selected text:
  - Clip In
  - Copy

The native WebView context menu is globally suppressed with `contextmenu.preventDefault()`.

This is the Works implementation of a policy intended to become common across Vertex products. More semantic actions (delete card, per-component settings, X-Ray, Send to Vera, etc.) can be added incrementally without bringing the native context menu back.
