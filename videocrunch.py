#!/usr/bin/env python3
"""
VideoСrunch — Interactive Video Compressor CLI
Reduces file size while preserving resolution and quality.
Requires: FFmpeg (bundled in EXE build via PyInstaller)
"""

import os
import sys
import json
import shutil
import subprocess
import platform
from pathlib import Path

# ── Terminal colors (Windows-safe) ──────────────────────────────────────────
if platform.system() == "Windows":
    os.system("color")  # enable ANSI in cmd.exe


class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    BLUE   = "\033[94m"
    DIM    = "\033[2m"
    MAGENTA = "\033[95m"


def print_banner():
    banner = f"""
{C.CYAN}{C.BOLD}
  ██╗   ██╗██╗██████╗ ███████╗ ██████╗ ██████╗ ██╗   ██╗███╗   ██╗ ██████╗██╗  ██╗
  ██║   ██║██║██╔══██╗██╔════╝██╔═══██╗██╔══██╗██║   ██║████╗  ██║██╔════╝██║  ██║
  ██║   ██║██║██║  ██║█████╗  ██║   ██║██║  ██║██║   ██║██╔██╗ ██║██║     ███████║
  ╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║██║  ██║██║   ██║██║╚██╗██║██║     ██╔══██║
   ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝██████╔╝╚██████╔╝██║ ╚████║╚██████╗██║  ██║
    ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
{C.RESET}"""
    print(banner)
    print(f"  {C.DIM}Compress videos without changing resolution — powered by FFmpeg{C.RESET}")
    print(f"  {C.DIM}{'─' * 70}{C.RESET}\n")


# ── Helpers ──────────────────────────────────────────────────────────────────
def err(msg: str):
    print(f"\n  {C.RED}✗  {msg}{C.RESET}")


def ok(msg: str):
    print(f"  {C.GREEN}✓  {msg}{C.RESET}")


def info(msg: str):
    print(f"  {C.CYAN}→  {msg}{C.RESET}")


def warn(msg: str):
    print(f"  {C.YELLOW}⚠  {msg}{C.RESET}")


def section(title: str):
    print(f"\n  {C.BOLD}{C.BLUE}[ {title} ]{C.RESET}")
    print(f"  {C.DIM}{'─' * 50}{C.RESET}")


def ask(prompt: str, default: str = "") -> str:
    default_hint = f" {C.DIM}[{default}]{C.RESET}" if default else ""
    try:
        answer = input(f"  {C.CYAN}▶{C.RESET}  {prompt}{default_hint}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        print(f"\n  {C.YELLOW}Cancelled by user. Goodbye!{C.RESET}\n")
        sys.exit(0)
    return answer if answer else default


def choose(prompt: str, options: list[dict], default_index: int = 0) -> dict:
    """Display a numbered menu and return the chosen option dict."""
    print(f"\n  {C.CYAN}▶{C.RESET}  {prompt}")
    for i, opt in enumerate(options):
        marker = f"{C.GREEN}●{C.RESET}" if i == default_index else f"{C.DIM}○{C.RESET}"
        label  = opt.get("label", "")
        desc   = opt.get("desc", "")
        tag    = f"  {C.DIM}{opt.get('tag', '')}{C.RESET}" if opt.get("tag") else ""
        print(f"    {marker} {C.BOLD}{i + 1}{C.RESET}. {label:<20} {C.DIM}{desc}{C.RESET}{tag}")
    print()
    while True:
        raw = ask(f"Enter number (1–{len(options)})", str(default_index + 1))
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        warn(f"Please enter a number between 1 and {len(options)}.")


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def confirm(prompt: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    ans = ask(f"{prompt} [{hint}]").lower()
    if not ans:
        return default
    return ans in ("y", "yes")


# ── FFmpeg detection ─────────────────────────────────────────────────────────
def find_ffmpeg() -> tuple[str, str]:
    """
    Search order:
      1. Bundled alongside the EXE (sys._MEIPASS for PyInstaller)
      2. System PATH
    """
    candidates = []

    # PyInstaller bundle
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        suffix = ".exe" if platform.system() == "Windows" else ""
        candidates.append((str(base / f"ffmpeg{suffix}"), str(base / f"ffprobe{suffix}")))

    # System PATH
    candidates.append((shutil.which("ffmpeg") or "", shutil.which("ffprobe") or ""))

    for ffmpeg, ffprobe in candidates:
        if ffmpeg and ffprobe and Path(ffmpeg).exists() and Path(ffprobe).exists():
            return ffmpeg, ffprobe

    err("FFmpeg not found!")
    print(f"""
  {C.DIM}Please install FFmpeg:
    Windows : https://www.gyan.dev/ffmpeg/builds/
    macOS   : brew install ffmpeg
    Linux   : sudo apt install ffmpeg{C.RESET}
""")
    sys.exit(1)


# ── Video probe ──────────────────────────────────────────────────────────────
def probe_video(ffprobe: str, path: Path) -> dict:
    cmd = [
        ffprobe, "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        str(path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data   = json.loads(result.stdout)
    except subprocess.CalledProcessError:
        err(f"Cannot read video: {path}")
        sys.exit(1)

    out = {"size": int(data["format"].get("size", 0)),
           "duration": float(data["format"].get("duration", 0))}

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            out["width"]    = stream.get("width", "?")
            out["height"]   = stream.get("height", "?")
            out["codec"]    = stream.get("codec_name", "?")
            out["fps"]      = stream.get("r_frame_rate", "?")
            out["bit_rate"] = int(stream.get("bit_rate") or data["format"].get("bit_rate", 0))
            break

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "audio":
            out["audio_codec"]   = stream.get("codec_name", "?")
            out["audio_rate"]    = stream.get("sample_rate", "?")
            out["audio_channels"]= stream.get("channels", "?")
            break

    return out


def print_video_info(vinfo: dict, label: str = "Input Video"):
    section(label)
    w   = vinfo.get("width", "?")
    h   = vinfo.get("height", "?")
    fps = vinfo.get("fps", "?")
    if "/" in str(fps):
        num, den = fps.split("/")
        try:
            fps = f"{int(num)/int(den):.2f}"
        except (ValueError, ZeroDivisionError):
            pass
    print(f"  {'Resolution':<18} {w}×{h}")
    print(f"  {'Codec':<18} {vinfo.get('codec', '?')}")
    print(f"  {'Frame rate':<18} {fps} fps")
    print(f"  {'Bit rate':<18} {vinfo.get('bit_rate', 0) // 1000} kbps")
    print(f"  {'Duration':<18} {vinfo.get('duration', 0):.1f} s  ({vinfo.get('duration', 0)/60:.1f} min)")
    print(f"  {'File size':<18} {human_size(vinfo.get('size', 0))}")
    print(f"  {'Audio':<18} {vinfo.get('audio_codec','?')}  {vinfo.get('audio_rate','?')} Hz  {vinfo.get('audio_channels','?')}ch")


# ── Codec / quality menus ────────────────────────────────────────────────────
CODECS = [
    {"id": "h265", "label": "H.265 / HEVC",  "desc": "Best compression — recommended", "tag": "libx265"},
    {"id": "h264", "label": "H.264 / AVC",   "desc": "Widest compatibility",            "tag": "libx264"},
    {"id": "av1",  "label": "AV1",            "desc": "Next-gen, very slow to encode",   "tag": "libaom-av1"},
]

QUALITY_PROFILES = [
    {"id": "lossless", "label": "Lossless",  "crf": 0,  "desc": "No quality loss — largest file"},
    {"id": "high",     "label": "High",      "crf": 18, "desc": "Visually transparent — great quality"},
    {"id": "balanced", "label": "Balanced",  "crf": 23, "desc": "Good trade-off — default"},
    {"id": "small",    "label": "Small",     "crf": 28, "desc": "Smaller file — slight quality drop"},
    {"id": "tiny",     "label": "Tiny",      "crf": 35, "desc": "Minimum size — noticeable compression"},
]

PRESETS = [
    {"id": "ultrafast", "label": "Ultra Fast", "desc": "Fastest encode, larger file"},
    {"id": "fast",      "label": "Fast",       "desc": "Quick encode"},
    {"id": "medium",    "label": "Medium",     "desc": "Balanced — default"},
    {"id": "slow",      "label": "Slow",       "desc": "Better compression, takes longer"},
    {"id": "veryslow",  "label": "Very Slow",  "desc": "Best compression, longest encode"},
]

AUDIO_PROFILES = [
    {"id": "96k",  "label": "96 kbps",  "desc": "Minimum — voice / podcasts"},
    {"id": "128k", "label": "128 kbps", "desc": "Standard — default"},
    {"id": "192k", "label": "192 kbps", "desc": "High quality audio"},
    {"id": "320k", "label": "320 kbps", "desc": "Near lossless audio"},
    {"id": "copy", "label": "Copy",     "desc": "Keep original audio stream unchanged"},
]


# ── Build FFmpeg command ─────────────────────────────────────────────────────
def build_cmd(ffmpeg: str, src: Path, dst: Path, cfg: dict) -> list[str]:
    cmd = [ffmpeg, "-y", "-i", str(src)]

    codec_id = cfg["codec"]
    crf      = cfg["crf"]
    preset   = cfg["preset"]
    audio    = cfg["audio"]

    if codec_id == "h265":
        cmd += ["-c:v", "libx265", "-crf", str(crf),
                "-preset", preset, "-tag:v", "hvc1"]
    elif codec_id == "h264":
        cmd += ["-c:v", "libx264", "-crf", str(crf), "-preset", preset]
    elif codec_id == "av1":
        cmd += ["-c:v", "libaom-av1", "-crf", str(crf),
                "-b:v", "0", "-cpu-used", "4"]

    # keep original resolution — only ensure even dimensions (H.265 requirement)
    cmd += ["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2"]

    if audio == "copy":
        cmd += ["-c:a", "copy"]
    else:
        cmd += ["-c:a", "aac", "-b:a", audio]

    cmd.append(str(dst))
    return cmd


# ── Progress bar runner ──────────────────────────────────────────────────────
def run_ffmpeg(cmd: list[str], duration: float):
    import re
    process = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1,
    )
    time_re = re.compile(r"time=(\d+):(\d+):([\d.]+)")
    speed_re = re.compile(r"speed=\s*([\d.]+)x")

    try:
        for line in process.stderr:  # type: ignore[union-attr]
            tm = time_re.search(line)
            if tm and duration > 0:
                h, mn, s = int(tm.group(1)), int(tm.group(2)), float(tm.group(3))
                elapsed  = h * 3600 + mn * 60 + s
                pct      = min(100.0, elapsed / duration * 100)
                bar_len  = 35
                filled   = int(bar_len * pct / 100)
                bar      = "█" * filled + "░" * (bar_len - filled)
                sp       = speed_re.search(line)
                speed    = f"  {sp.group(1)}x" if sp else ""
                eta      = ""
                if sp:
                    try:
                        remaining = (duration - elapsed) / float(sp.group(1))
                        eta = f"  ETA {remaining:.0f}s"
                    except ZeroDivisionError:
                        pass
                print(
                    f"\r  {C.CYAN}[{bar}]{C.RESET} {pct:5.1f}%"
                    f"{C.DIM}{speed}{eta}{C.RESET}   ",
                    end="", flush=True,
                )
    except KeyboardInterrupt:
        process.kill()
        print()
        warn("Compression cancelled by user.")
        sys.exit(0)

    process.wait()
    print()

    if process.returncode != 0:
        err("FFmpeg exited with an error. Check the input file or settings.")
        sys.exit(1)


# ── Summary ──────────────────────────────────────────────────────────────────
def print_summary(orig_size: int, new_size: int, dst: Path, cfg: dict):
    saved     = orig_size - new_size
    saved_pct = (saved / orig_size * 100) if orig_size else 0
    ratio     = orig_size / new_size if new_size else 0

    section("Compression Complete")
    print(f"  {'Original size':<22} {human_size(orig_size)}")
    print(f"  {'Compressed size':<22} {human_size(new_size)}")
    print(f"  {'Space saved':<22} {C.GREEN}{human_size(saved)}  ({saved_pct:.1f}%){C.RESET}")
    print(f"  {'Compression ratio':<22} {ratio:.2f}×")
    print(f"  {'Codec used':<22} {cfg['codec'].upper()}  CRF {cfg['crf']}")
    print(f"  {'Output file':<22} {dst}")
    print()

    if saved_pct < 5:
        warn("Less than 5% size reduction. The input may already be compressed.")
        warn("Try a lower quality profile (e.g. 'Small') or slower preset.")
    else:
        ok(f"Done! Saved {saved_pct:.1f}% without changing resolution.")


# ── Interactive wizard ────────────────────────────────────────────────────────
def wizard(ffmpeg: str, ffprobe: str):
    print_banner()

    # ── STEP 1: Input file ───────────────────────────────────────────────────
    section("Step 1 of 5 — Input File")
    while True:
        raw = ask("Drag & drop your video file here (or type the path)")
        # strip surrounding quotes that Windows drag-n-drop may add
        raw = raw.strip('"').strip("'")
        src = Path(raw)
        if src.exists() and src.is_file():
            break
        err(f"File not found: {raw}")

    vinfo = probe_video(ffprobe, src)
    print_video_info(vinfo)

    # ── STEP 2: Output file ──────────────────────────────────────────────────
    section("Step 2 of 5 — Output File")
    default_out = src.with_name(src.stem + "_compressed.mp4")
    raw_out = ask("Output path", str(default_out))
    raw_out = raw_out.strip('"').strip("'")
    dst = Path(raw_out)

    if dst == src:
        err("Output must differ from input. Appending '_compressed'.")
        dst = src.with_name(src.stem + "_compressed.mp4")
        info(f"Output set to: {dst}")

    if dst.exists():
        if not confirm(f"'{dst.name}' already exists. Overwrite?"):
            info("Aborted. Change the output path and try again.")
            sys.exit(0)

    # ── STEP 3: Codec ────────────────────────────────────────────────────────
    section("Step 3 of 5 — Video Codec")
    codec_opt = choose("Which codec do you want to use?", CODECS, default_index=0)

    # ── STEP 4: Quality ──────────────────────────────────────────────────────
    section("Step 4 of 5 — Quality & Speed")

    quality_opt = choose("Quality profile:", QUALITY_PROFILES, default_index=2)
    crf = quality_opt["crf"]

    # allow manual CRF override
    manual = ask(f"Manual CRF override? (leave blank to keep {crf})")
    if manual.isdigit():
        crf = int(manual)
        info(f"CRF set to {crf}")

    preset_opt  = choose("Encoding speed preset:", PRESETS, default_index=2)
    audio_opt   = choose("Audio quality:", AUDIO_PROFILES, default_index=1)

    # ── STEP 5: Confirm ──────────────────────────────────────────────────────
    section("Step 5 of 5 — Review & Start")
    cfg = {
        "codec":  codec_opt["id"],
        "crf":    crf,
        "preset": preset_opt["id"],
        "audio":  audio_opt["id"],
    }
    print(f"  {'Input':<18} {src}")
    print(f"  {'Output':<18} {dst}")
    print(f"  {'Codec':<18} {codec_opt['label']}")
    print(f"  {'Quality (CRF)':<18} {crf}  — {quality_opt['desc']}")
    print(f"  {'Preset':<18} {preset_opt['label']}")
    print(f"  {'Audio':<18} {audio_opt['label']}")
    print(f"  {'Resolution':<18} Unchanged ({vinfo.get('width')}×{vinfo.get('height')})")
    print()

    if not confirm("Start compression?"):
        info("Aborted.")
        sys.exit(0)

    # ── Encode ───────────────────────────────────────────────────────────────
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = build_cmd(ffmpeg, src, dst, cfg)
    print()
    info("Starting FFmpeg...\n")
    run_ffmpeg(cmd, vinfo.get("duration", 0))

    # ── Summary ───────────────────────────────────────────────────────────────
    if dst.exists():
        print_summary(vinfo["size"], dst.stat().st_size, dst, cfg)
    else:
        err("Output file was not created. Something went wrong.")
        sys.exit(1)

    # ── Another file? ─────────────────────────────────────────────────────────
    print()
    if confirm("Compress another video?"):
        wizard(ffmpeg, ffprobe)
    else:
        print(f"\n  {C.MAGENTA}Thanks for using VideoСrunch! Goodbye.{C.RESET}\n")


# ── Entry point ──────────────────────────────────────────────────────────────
def main():
    ffmpeg, ffprobe = find_ffmpeg()
    wizard(ffmpeg, ffprobe)


if __name__ == "__main__":
    main()