#![cfg_attr(windows, windows_subsystem = "windows")]

use std::{
    env, fs,
    path::{Path, PathBuf},
    process::Command,
};

#[cfg(windows)]
#[link(name = "user32")]
extern "system" {
    fn MessageBoxW(
        hwnd: *mut core::ffi::c_void,
        text: *const u16,
        caption: *const u16,
        kind: u32,
    ) -> i32;
}

#[cfg(windows)]
fn wide(value: &str) -> Vec<u16> {
    value.encode_utf16().chain(std::iter::once(0)).collect()
}

fn fail(message: &str) -> ! {
    #[cfg(windows)]
    unsafe {
        let text = wide(message);
        let caption = wide("VERTEX WORKS");
        MessageBoxW(
            std::ptr::null_mut(),
            text.as_ptr(),
            caption.as_ptr(),
            0x00000010,
        );
    }

    #[cfg(not(windows))]
    eprintln!("{message}");

    std::process::exit(1);
}

fn launcher_root() -> PathBuf {
    let exe =
        env::current_exe().unwrap_or_else(|e| fail(&format!("Cannot resolve launcher path: {e}")));
    exe.parent()
        .map(Path::to_path_buf)
        .unwrap_or_else(|| fail("Cannot resolve Vertex Works project root."))
}

fn main() {
    let root = launcher_root();
    let current_path = root.join("current.json");

    let text = fs::read_to_string(&current_path).unwrap_or_else(|e| {
        fail(&format!(
            "Vertex Works current.json could not be read.\n\n{}\n\n{}",
            current_path.display(),
            e
        ))
    });

    let value: serde_json::Value = serde_json::from_str(&text)
        .unwrap_or_else(|e| fail(&format!("Vertex Works current.json is invalid:\n\n{e}")));

    let release = value
        .get("release_exe")
        .and_then(|v| v.as_str())
        .filter(|v| !v.trim().is_empty())
        .unwrap_or_else(|| fail("current.json does not contain a valid release_exe pointer."));

    let target = PathBuf::from(release);
    if !target.is_file() {
        fail(&format!(
            "The active Verified Vertex Works release is missing.\n\n{}",
            target.display()
        ));
    }

    let self_exe = env::current_exe().unwrap_or_default();
    if self_exe
        .canonicalize()
        .ok()
        .zip(target.canonicalize().ok())
        .map(|(a, b)| a == b)
        .unwrap_or(false)
    {
        fail("current.json points back to the launcher itself. Launch was blocked.");
    }

    let mut cmd = Command::new(&target);
    cmd.args(env::args_os().skip(1));
    if let Some(parent) = target.parent() {
        cmd.current_dir(parent);
    }

    cmd.spawn().unwrap_or_else(|e| {
        fail(&format!(
            "Vertex Works could not start the active Verified release.\n\n{}\n\n{}",
            target.display(),
            e
        ))
    });
}
