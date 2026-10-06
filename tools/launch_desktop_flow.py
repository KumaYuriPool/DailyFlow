"""Launch the local DailyFlow development bundle in the existing AI desktop.

No business logic, model keys, or profiles are copied. The launcher owns a lock
for the child's lifetime, stages an ephemeral local catalog, and preserves data.
"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import native_runtime

from desktop_flow_probe import ROOT, WORKSPACE, stage_local_catalog


def process_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        # Access denied still means there may be a process using the data.
        return ctypes.get_last_error() == 5
    try:
        code = ctypes.c_ulong()
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
    finally:
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle(handle)


class DataLock:
    def __init__(self, root):
        self.root = root
        self.file = None

    def __enter__(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.file = (self.root / ".launcher.lock").open("a+b", buffering=0)
        self.file.seek(0, 2)
        if self.file.tell() == 0:
            self.file.write(b"0")
        self.file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise RuntimeError("此数据目录已有 DailyFlow 启动器运行，请使用已打开的窗口。") from None
        return self

    def __exit__(self, *_):
        self.file.close()


def default_core_dir():
    explicit = os.environ.get("OCTOS_APP_CORE_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return Path.home() / ".octosense/octos-home/.octos"


def launch(args):
    root = args.data_dir.expanduser().resolve()
    binary = args.binary.expanduser().resolve()
    bundle = args.bundle.expanduser().resolve()
    core = args.core_dir.expanduser().resolve()
    if not binary.is_file():
        raise RuntimeError(f"未找到已有桌面程序：{binary}")
    if not (bundle / "manifest.json").is_file():
        raise RuntimeError(f"未找到 DailyFlow bundle：{bundle}")
    if not (core / "profiles/_main.json").is_file():
        raise RuntimeError("未找到已有 AI Provider 配置；请在 OctoSense 配置，或传入 --core-dir。")
    with DataLock(root):
        process_file = root / "launcher-process.json"
        if process_file.exists():
            try:
                previous = json.loads(process_file.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                raise RuntimeError("启动记录损坏，请检查 launcher-process.json 后再启动。") from None
            if previous.get("running") and process_alive(previous.get("pid")):
                raise RuntimeError("此前 DailyFlow 桌面仍在运行，请先关闭其窗口，避免同时写入。")
        app_id, _, anchor = stage_local_catalog(bundle, root / "apps")
        env = dict(os.environ)
        for key in ("MAKEPAD_REMOTE", "MAKEPAD_HIDE_WINDOWS", "MAKEPAD_WM_TEST_APP", "OCTOS_APP_CORE_BIN"):
            env.pop(key, None)
        env.update(OCTOSENSE_HOME=str(root / "home"), OCTOSENSE_APP_DATA=str(root / "apps"),
                   OCTOSENSE_HUB=str(root / "apps"), OCTOSENSE_HUB_ANCHOR=anchor,
                   OCTOS_APP_CORE_DIR=str(core))
        if args.hidden:
            env["MAKEPAD_HIDE_WINDOWS"] = "1"
        if args.test_remote_port:
            env["MAKEPAD_REMOTE"] = str(args.test_remote_port)
        log_path = root / "desktop-launch.log"
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n--- DailyFlow local launch {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            log.flush()
            child = subprocess.Popen([str(binary), "--test-action", "launch-hub:" + app_id],
                                     cwd=binary.parent, env=env, stdout=log, stderr=subprocess.STDOUT,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            metadata = {"pid": child.pid, "launcher_pid": os.getpid(), "running": True,
                        "remote_enabled": bool(args.test_remote_port)}
            process_file.write_text(json.dumps(metadata), encoding="utf-8")
            print(f"DailyFlow 已启动。数据：{root}\n关闭桌面窗口后启动器自动退出。", flush=True)
            try:
                while True:
                    try:
                        code = child.wait()
                        break
                    except KeyboardInterrupt:
                        print("请关闭 DailyFlow 桌面窗口；启动器会等待保存并退出。", flush=True)
            finally:
                if child.poll() is not None:
                    metadata.update(running=False, exit_code=child.returncode)
                    process_file.write_text(json.dumps(metadata), encoding="utf-8")
            if code:
                raise RuntimeError(f"桌面程序退出码 {code}；日志：{log_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT / "bundle")
    parser.add_argument("--data-dir", type=Path, default=ROOT / ".local-state/desktop")
    parser.add_argument("--core-dir", type=Path, default=default_core_dir())
    parser.add_argument("--binary", type=Path, default=native_runtime.binary("shell"))
    parser.add_argument("--hidden", action="store_true", help="Developer test: hide the window")
    parser.add_argument("--test-remote-port", type=int, default=0, help="Developer test only: enable local UI test API")
    args = parser.parse_args()
    if args.test_remote_port and not 1 <= args.test_remote_port <= 65535:
        parser.error("test remote port must be 1–65535")
    try:
        launch(args)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"启动失败：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
