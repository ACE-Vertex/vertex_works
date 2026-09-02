# VERTEX WORKS ENGINE — RECEIVING BAY EXACT CONTRACT MIGRATION 000070

000069 established the current source truth:

`G:\Vertex_Project\Development\vertex_works\src-tauri\src\main.rs`

Current runtime constant:

`const DEFAULT_INBOX: &str = r"G:\Vertex_Project\_incoming\vertex_works";`

000070 changes exactly that one runtime contract to:

`const DEFAULT_INBOX: &str = r"G:\Vertex_Project\Development\_incoming";`

The new directory is the single primary development receiving bay.

The legacy directory remains on disk during transition but is no longer the
runtime default after the new verified EXE is started.

Build/Test/Release are performed from the exact current Vertex Works source root.
