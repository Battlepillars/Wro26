#!/usr/bin/env python3
"""
sysmon.py – tiny overlay for Raspberry Pi CM5
Shows CPU temp, throttle state, and runtime in a small top-left window.
"""

import tkinter as tk
import subprocess
import time


def read_temp() -> float:
    """Read CPU temperature in °C from the thermal zone sysfs node."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read().strip()) / 1000.0
    except OSError:
        return float("nan")


_cpu_prev: tuple = (0, 0)   # (idle, total) from last sample


def read_cpu_usage() -> float:
    """Return overall CPU usage % since the last call (delta measurement)."""
    global _cpu_prev
    try:
        with open("/proc/stat") as f:
            fields = list(map(int, f.readline().split()[1:]))
        idle  = fields[3]                     # idle + iowait
        total = sum(fields)
        d_idle  = idle  - _cpu_prev[0]
        d_total = total - _cpu_prev[1]
        _cpu_prev = (idle, total)
        if d_total == 0:
            return 0.0
        return max(0.0, 100.0 * (1.0 - d_idle / d_total))
    except OSError:
        return float("nan")


def read_throttled() -> str:
    """
    Return a human-readable throttle summary via vcgencmd.
    Bit meanings (active bits in the low nibble = current state):
      0 – under-voltage
      1 – frequency capped
      2 – throttled
      3 – soft temp limit
    """
    try:
        raw = subprocess.check_output(
            ["vcgencmd", "get_throttled"], text=True
        ).strip()
        # raw looks like "throttled=0x50000"
        val = int(raw.split("=")[1], 16)
    except Exception:
        return "n/a"

    current = val & 0xF          # low nibble = right-now flags
    occurred = (val >> 16) & 0xF # high nibble = ever-happened flags

    if current == 0:
        label = "OK"
    else:
        parts = []
        if current & 0x1:
            parts.append("UV")        # under-voltage
        if current & 0x2:
            parts.append("FCAP")      # freq capped
        if current & 0x4:
            parts.append("THRTL")     # throttled
        if current & 0x8:
            parts.append("TLIM")      # soft temp limit
        label = " ".join(parts)

    # Dim indicator when issue occurred in the past but not right now
    if occurred and not current:
        label = f"({occurred:#x} hist)"

    return label


class SysMonApp:
    REFRESH_MS = 1000   # update interval in milliseconds
    BG        = "#1a1a1a"
    FG_NORMAL = "#00e676"
    FG_WARN   = "#ffeb3b"
    FG_CRIT   = "#f44336"
    FONT      = ("Monospace", 10, "bold")

    def __init__(self, root: tk.Tk):
        self.root = root
        self.start = time.monotonic()

        root.title("sysmon")
        root.configure(bg=self.BG)
        root.resizable(False, False)
        root.wm_attributes("-topmost", True)
        root.wm_attributes("-alpha", 0.88)

        # Remove window decorations for a minimal overlay feel
        root.overrideredirect(True)

        # Position at bottom-right after the window has been rendered
        root.after(0, self._position_bottom_right)

        self.lbl_temp     = tk.Label(root, font=self.FONT, bg=self.BG, anchor="w", width=22)
        self.lbl_cpu      = tk.Label(root, font=self.FONT, bg=self.BG, anchor="w", width=22)
        self.lbl_throttle = tk.Label(root, font=self.FONT, bg=self.BG, anchor="w", width=22)
        self.lbl_runtime  = tk.Label(root, font=self.FONT, bg=self.BG, anchor="w", width=22)

        self.lbl_temp.grid    (row=0, column=0, padx=6, pady=(4, 0), sticky="w")
        self.lbl_cpu.grid     (row=1, column=0, padx=6, pady=0,      sticky="w")
        self.lbl_throttle.grid(row=2, column=0, padx=6, pady=0,      sticky="w")
        self.lbl_runtime.grid (row=3, column=0, padx=6, pady=(0, 4), sticky="w")

        # Click-and-drag to reposition
        root.bind("<ButtonPress-1>",   self._drag_start)
        root.bind("<B1-Motion>",        self._drag_motion)
        # Right-click to close
        root.bind("<ButtonRelease-3>",  lambda _: root.destroy())

        self._update()

    def _position_bottom_right(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        ww = self.root.winfo_reqwidth()
        wh = self.root.winfo_reqheight()
        x = sw - ww - 4
        y = sh - wh - 4
        self.root.geometry(f"+{x}+{y}")

    def _color_for_temp(self, t: float) -> str:
        if t >= 80:
            return self.FG_CRIT
        if t >= 70:
            return self.FG_WARN
        return self.FG_NORMAL

    def _color_for_cpu(self, pct: float) -> str:
        if pct >= 90:
            return self.FG_CRIT
        if pct >= 70:
            return self.FG_WARN
        return self.FG_NORMAL

    def _color_for_throttle(self, label: str) -> str:
        if label in ("OK", "n/a"):
            return self.FG_NORMAL
        if "hist" in label:
            return self.FG_WARN
        return self.FG_CRIT

    def _format_runtime(self, seconds: float) -> str:
        s = int(seconds)
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        if h:
            return f"Runtime : {h:02d}h {m:02d}m {sec:02d}s"
        return f"Runtime : {m:02d}m {sec:02d}s"

    def _update(self):
        temp     = read_temp()
        cpu      = read_cpu_usage()
        throttle = read_throttled()
        elapsed  = time.monotonic() - self.start

        self.lbl_temp.config(
            text=f"Temp    : {temp:.1f} °C",
            fg=self._color_for_temp(temp),
        )
        self.lbl_cpu.config(
            text=f"CPU     : {cpu:.1f} %",
            fg=self._color_for_cpu(cpu),
        )
        self.lbl_throttle.config(
            text=f"Throttle: {throttle}",
            fg=self._color_for_throttle(throttle),
        )
        self.lbl_runtime.config(
            text=self._format_runtime(elapsed),
            fg=self.FG_NORMAL,
        )

        self.root.after(self.REFRESH_MS, self._update)

    # Drag support -------------------------------------------------------
    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_motion(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    root = tk.Tk()
    SysMonApp(root)
    root.mainloop()
