# Vertex Receiver 0.2.2 — Silent Child Process

Observed during real Receiver use:
CLI verification processes such as cargo/python briefly created console windows,
causing DOS/Command Prompt flashes and taskbar flicker.

Windows child-process verification now uses CREATE_NO_WINDOW.

Important:
- stdout/stderr capture is preserved.
- exit codes are preserved.
- Receiver logs/Evidence/Return Lane remain unchanged.
- only the unwanted child console window is suppressed.
- the Receiver itself remains a normal Tauri GUI application.

The artifact that installs this fix is still executed by the OLD Receiver, so its
own verification may flash one final time. After launching 0.2.2, subsequent
verification jobs should stay visually silent.
