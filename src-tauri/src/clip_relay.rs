use serde::Serialize;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Mutex, OnceLock,
};
use std::thread;
use std::time::Duration;

#[derive(Debug, Clone, Serialize)]
pub struct ClipRelayStatus {
    pub enabled: bool,
    pub armed: bool,
    pub kind: String,
    pub priority: bool,
    pub bytes: usize,
    pub source_count: usize,
}

#[derive(Debug, Clone)]
struct ClipPayload {
    kind: String,
    text: String,
    files: Vec<String>,
    priority: bool,
}

#[derive(Debug, Default)]
struct RelayState {
    payload: Option<ClipPayload>,
}

static STATE: OnceLock<Mutex<RelayState>> = OnceLock::new();
static STARTED: AtomicBool = AtomicBool::new(false);
static SUPPRESS_MIDDLE_UP: AtomicBool = AtomicBool::new(false);

fn relay_state() -> &'static Mutex<RelayState> {
    STATE.get_or_init(|| Mutex::new(RelayState::default()))
}

pub fn set_priority(text: String, kind: String) -> Result<ClipRelayStatus, String> {
    let mut state = relay_state()
        .lock()
        .map_err(|_| "clip relay state poisoned".to_string())?;
    state.payload = Some(ClipPayload {
        kind,
        text,
        files: Vec::new(),
        priority: true,
    });
    Ok(status_from_state(&state))
}

pub fn status() -> ClipRelayStatus {
    relay_state()
        .lock()
        .map(|state| status_from_state(&state))
        .unwrap_or(ClipRelayStatus {
            enabled: STARTED.load(Ordering::SeqCst),
            armed: false,
            kind: "ERROR".into(),
            priority: false,
            bytes: 0,
            source_count: 0,
        })
}

fn status_from_state(state: &RelayState) -> ClipRelayStatus {
    if let Some(payload) = &state.payload {
        ClipRelayStatus {
            enabled: STARTED.load(Ordering::SeqCst),
            armed: true,
            kind: payload.kind.clone(),
            priority: payload.priority,
            bytes: payload.text.len(),
            source_count: if payload.files.is_empty() {
                1
            } else {
                payload.files.len()
            },
        }
    } else {
        ClipRelayStatus {
            enabled: STARTED.load(Ordering::SeqCst),
            armed: false,
            kind: "EMPTY".into(),
            priority: false,
            bytes: 0,
            source_count: 0,
        }
    }
}

#[cfg(windows)]
mod win {
    use super::*;
    use std::ffi::c_void;
    use std::mem::{size_of, zeroed};
    use std::ptr::{copy_nonoverlapping, null, null_mut};
    use std::slice;

    const WH_MOUSE_LL: i32 = 14;
    const WM_MBUTTONDOWN: u32 = 0x0207;
    const WM_MBUTTONUP: u32 = 0x0208;

    const VK_CONTROL: u8 = 0x11;
    const VK_C: u8 = 0x43;
    const VK_V: u8 = 0x56;
    const KEYEVENTF_KEYUP: u32 = 0x0002;

    const CF_UNICODETEXT: u32 = 13;
    const CF_HDROP: u32 = 15;
    const GMEM_MOVEABLE: u32 = 0x0002;
    const INVALID_FILE_INDEX: u32 = 0xFFFF_FFFF;

    type HHook = isize;
    type HGlobal = isize;
    type HDrop = isize;
    type HModule = isize;
    type HWnd = isize;
    type HookProc = unsafe extern "system" fn(i32, usize, isize) -> isize;

    #[repr(C)]
    #[derive(Clone, Copy)]
    struct Point {
        x: i32,
        y: i32,
    }

    #[repr(C)]
    struct Msg {
        hwnd: HWnd,
        message: u32,
        w_param: usize,
        l_param: isize,
        time: u32,
        pt: Point,
        l_private: u32,
    }

    #[repr(C)]
    struct DropFiles {
        p_files: u32,
        pt: Point,
        f_nc: i32,
        f_wide: i32,
    }

    #[link(name = "user32")]
    extern "system" {
        fn SetWindowsHookExW(
            id_hook: i32,
            hook_proc: Option<HookProc>,
            module: HModule,
            thread_id: u32,
        ) -> HHook;
        fn CallNextHookEx(hook: HHook, code: i32, w_param: usize, l_param: isize) -> isize;
        fn UnhookWindowsHookEx(hook: HHook) -> i32;
        fn GetMessageW(msg: *mut Msg, hwnd: HWnd, min: u32, max: u32) -> i32;
        fn TranslateMessage(msg: *const Msg) -> i32;
        fn DispatchMessageW(msg: *const Msg) -> isize;

        fn keybd_event(vk: u8, scan: u8, flags: u32, extra_info: usize);

        fn OpenClipboard(hwnd: HWnd) -> i32;
        fn CloseClipboard() -> i32;
        fn EmptyClipboard() -> i32;
        fn GetClipboardData(format: u32) -> isize;
        fn SetClipboardData(format: u32, mem: isize) -> isize;
        fn IsClipboardFormatAvailable(format: u32) -> i32;
        fn GetClipboardSequenceNumber() -> u32;
    }

    #[link(name = "kernel32")]
    extern "system" {
        fn GetModuleHandleW(module_name: *const u16) -> HModule;
        fn GlobalAlloc(flags: u32, bytes: usize) -> HGlobal;
        fn GlobalFree(mem: HGlobal) -> HGlobal;
        fn GlobalLock(mem: HGlobal) -> *mut c_void;
        fn GlobalUnlock(mem: HGlobal) -> i32;
        fn GlobalSize(mem: HGlobal) -> usize;
    }

    #[link(name = "shell32")]
    extern "system" {
        fn DragQueryFileW(
            drop: HDrop,
            file_index: u32,
            file_name: *mut u16,
            file_name_chars: u32,
        ) -> u32;
    }

    pub fn start() -> Result<(), String> {
        if STARTED.swap(true, Ordering::SeqCst) {
            return Ok(());
        }

        relay_state();

        thread::Builder::new()
            .name("vertex-clip-relay".into())
            .spawn(|| {
                let result = unsafe { hook_loop() };
                if let Err(error) = result {
                    eprintln!("Vertex Clip Relay stopped: {error}");
                    STARTED.store(false, Ordering::SeqCst);
                }
            })
            .map_err(|e| format!("spawn clip relay: {e}"))?;

        Ok(())
    }

    unsafe fn hook_loop() -> Result<(), String> {
        let module = GetModuleHandleW(null());
        let hook = SetWindowsHookExW(WH_MOUSE_LL, Some(mouse_proc), module, 0);
        if hook == 0 {
            return Err("SetWindowsHookExW(WH_MOUSE_LL) failed".into());
        }

        let mut msg: Msg = zeroed();
        loop {
            let result = GetMessageW(&mut msg, 0, 0, 0);
            if result == -1 {
                UnhookWindowsHookEx(hook);
                return Err("GetMessageW failed".into());
            }
            if result == 0 {
                break;
            }
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }

        UnhookWindowsHookEx(hook);
        Ok(())
    }

    unsafe extern "system" fn mouse_proc(code: i32, w_param: usize, l_param: isize) -> isize {
        if code >= 0 {
            match w_param as u32 {
                WM_MBUTTONDOWN => {
                    let handled = handle_middle_click();
                    SUPPRESS_MIDDLE_UP.store(handled, Ordering::SeqCst);
                    if handled {
                        return 1;
                    }
                }
                WM_MBUTTONUP => {
                    if SUPPRESS_MIDDLE_UP.swap(false, Ordering::SeqCst) {
                        return 1;
                    }
                }
                _ => {}
            }
        }

        CallNextHookEx(0, code, w_param, l_param)
    }

    fn handle_middle_click() -> bool {
        let priority_armed = relay_state()
            .lock()
            .ok()
            .and_then(|state| state.payload.as_ref().map(|payload| payload.priority))
            .unwrap_or(false);

        if priority_armed {
            return release_payload();
        }

        if let Some(payload) = capture_current_selection() {
            if let Ok(mut state) = relay_state().lock() {
                state.payload = Some(payload);
                return true;
            }
        }

        let armed = relay_state()
            .lock()
            .ok()
            .map(|state| state.payload.is_some())
            .unwrap_or(false);

        if armed {
            return release_payload();
        }

        false
    }

    fn capture_current_selection() -> Option<ClipPayload> {
        let before = unsafe { GetClipboardSequenceNumber() };
        send_ctrl_key(VK_C);
        thread::sleep(Duration::from_millis(90));
        let after = unsafe { GetClipboardSequenceNumber() };

        if after == before {
            return None;
        }

        for _ in 0..6 {
            if let Some(payload) = read_clipboard_payload() {
                if !payload.text.trim().is_empty() || !payload.files.is_empty() {
                    return Some(payload);
                }
            }
            thread::sleep(Duration::from_millis(20));
        }

        None
    }

    fn release_payload() -> bool {
        let payload = match relay_state().lock() {
            Ok(state) => state.payload.clone(),
            Err(_) => None,
        };

        let Some(payload) = payload else {
            return false;
        };

        if write_payload_to_clipboard(&payload).is_err() {
            return false;
        }

        thread::sleep(Duration::from_millis(20));
        send_ctrl_key(VK_V);

        if let Ok(mut state) = relay_state().lock() {
            state.payload = None;
        }

        true
    }

    fn send_ctrl_key(key: u8) {
        unsafe {
            keybd_event(VK_CONTROL, 0, 0, 0);
            keybd_event(key, 0, 0, 0);
            keybd_event(key, 0, KEYEVENTF_KEYUP, 0);
            keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0);
        }
    }

    fn open_clipboard_retry() -> bool {
        for _ in 0..8 {
            if unsafe { OpenClipboard(0) } != 0 {
                return true;
            }
            thread::sleep(Duration::from_millis(10));
        }
        false
    }

    fn read_clipboard_payload() -> Option<ClipPayload> {
        if !open_clipboard_retry() {
            return None;
        }

        let result = unsafe {
            if IsClipboardFormatAvailable(CF_HDROP) != 0 {
                read_file_drop_payload()
            } else if IsClipboardFormatAvailable(CF_UNICODETEXT) != 0 {
                read_unicode_text().map(|text| ClipPayload {
                    kind: "TEXT".into(),
                    text,
                    files: Vec::new(),
                    priority: false,
                })
            } else {
                None
            }
        };

        unsafe {
            CloseClipboard();
        }

        result
    }

    unsafe fn read_unicode_text() -> Option<String> {
        let handle = GetClipboardData(CF_UNICODETEXT);
        if handle == 0 {
            return None;
        }

        let bytes = GlobalSize(handle);
        if bytes < 2 {
            return None;
        }

        let ptr = GlobalLock(handle) as *const u16;
        if ptr.is_null() {
            return None;
        }

        let max_units = bytes / 2;
        let units = slice::from_raw_parts(ptr, max_units);
        let len = units
            .iter()
            .position(|value| *value == 0)
            .unwrap_or(max_units);
        let text = String::from_utf16_lossy(&units[..len]);

        GlobalUnlock(handle);
        Some(text)
    }

    unsafe fn read_file_drop_payload() -> Option<ClipPayload> {
        let drop = GetClipboardData(CF_HDROP);
        if drop == 0 {
            return None;
        }

        let count = DragQueryFileW(drop, INVALID_FILE_INDEX, null_mut(), 0);
        if count == 0 {
            return None;
        }

        let mut files = Vec::with_capacity(count as usize);

        for index in 0..count {
            let chars = DragQueryFileW(drop, index, null_mut(), 0);
            if chars == 0 {
                continue;
            }

            let mut buffer = vec![0u16; chars as usize + 1];
            let written = DragQueryFileW(drop, index, buffer.as_mut_ptr(), buffer.len() as u32);
            if written > 0 {
                files.push(String::from_utf16_lossy(&buffer[..written as usize]));
            }
        }

        if files.is_empty() {
            return None;
        }

        Some(ClipPayload {
            kind: "FILES".into(),
            text: files.join("\n"),
            files,
            priority: false,
        })
    }

    fn write_payload_to_clipboard(payload: &ClipPayload) -> Result<(), String> {
        if !open_clipboard_retry() {
            return Err("OpenClipboard failed".into());
        }

        let result = unsafe {
            if EmptyClipboard() == 0 {
                Err("EmptyClipboard failed".into())
            } else {
                write_unicode_text_format(&payload.text)?;
                if !payload.files.is_empty() {
                    write_hdrop_format(&payload.files)?;
                }
                Ok(())
            }
        };

        unsafe {
            CloseClipboard();
        }

        result
    }

    unsafe fn write_unicode_text_format(text: &str) -> Result<(), String> {
        let mut wide: Vec<u16> = text.encode_utf16().collect();
        wide.push(0);

        let bytes = wide.len() * size_of::<u16>();
        let mem = GlobalAlloc(GMEM_MOVEABLE, bytes);
        if mem == 0 {
            return Err("GlobalAlloc unicode text failed".into());
        }

        let ptr = GlobalLock(mem) as *mut u16;
        if ptr.is_null() {
            GlobalFree(mem);
            return Err("GlobalLock unicode text failed".into());
        }

        copy_nonoverlapping(wide.as_ptr(), ptr, wide.len());
        GlobalUnlock(mem);

        if SetClipboardData(CF_UNICODETEXT, mem) == 0 {
            GlobalFree(mem);
            return Err("SetClipboardData(CF_UNICODETEXT) failed".into());
        }

        Ok(())
    }

    unsafe fn write_hdrop_format(files: &[String]) -> Result<(), String> {
        let mut list = Vec::<u16>::new();
        for file in files {
            list.extend(file.encode_utf16());
            list.push(0);
        }
        list.push(0);

        let header_size = size_of::<DropFiles>();
        let bytes = header_size + list.len() * size_of::<u16>();
        let mem = GlobalAlloc(GMEM_MOVEABLE, bytes);
        if mem == 0 {
            return Err("GlobalAlloc HDROP failed".into());
        }

        let ptr = GlobalLock(mem) as *mut u8;
        if ptr.is_null() {
            GlobalFree(mem);
            return Err("GlobalLock HDROP failed".into());
        }

        let header = DropFiles {
            p_files: header_size as u32,
            pt: Point { x: 0, y: 0 },
            f_nc: 0,
            f_wide: 1,
        };

        copy_nonoverlapping(&header as *const DropFiles as *const u8, ptr, header_size);

        copy_nonoverlapping(
            list.as_ptr() as *const u8,
            ptr.add(header_size),
            list.len() * size_of::<u16>(),
        );

        GlobalUnlock(mem);

        if SetClipboardData(CF_HDROP, mem) == 0 {
            GlobalFree(mem);
            return Err("SetClipboardData(CF_HDROP) failed".into());
        }

        Ok(())
    }
}

#[cfg(not(windows))]
mod win {
    use super::*;

    pub fn start() -> Result<(), String> {
        STARTED.store(false, Ordering::SeqCst);
        Err("Vertex Clip Relay requires Windows".into())
    }
}

pub fn start() -> Result<(), String> {
    win::start()
}
