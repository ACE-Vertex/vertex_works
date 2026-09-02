# VERTEX WORKS — UI SOURCE CAPTURE CP932 HOTFIX 000075

000074 brand/application identity work succeeded.
Only the read-only UI source capture failed because the Vertex Works evidence
transport is CP932 and encountered Unicode U+00B7.

000075 changes no product source. It emits all captured source lines as
ASCII-safe escaped text, so Japanese/localization/theme/header anchors can be
returned through the existing evidence channel without encoding failure.

Use the resulting Evidence as the exact basis for:
000076 — ORANGE WORKSPACE + ENGLISH-ONLY UI CORE.
