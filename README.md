# VideoСrunch 🎬

> **Compress videos without changing resolution** — an interactive CLI tool powered by FFmpeg and packaged as a single executable.

[![Build](https://github.com/1amir2026/videocrunch/actions/workflows/build.yml/badge.svg)](https://github.com/YOUR_USERNAME/videocrunch/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#download)

---

## What it does

VideoСrunch walks you through **5 simple steps** in the terminal and produces a smaller video file with the **exact same resolution** as the original — no scripting, no flags to memorize.

```
  [ Step 1 of 5 — Input File ]
  ──────────────────────────────────────────────────
  ▶  Drag & drop your video file here: /Users/me/vacation.mp4

  Resolution         1920×1080
  Codec              h264
  Frame rate         29.97 fps
  Bit rate           8 240 kbps
  Duration           183.4 s  (3.1 min)
  File size          187.3 MB

  [ Step 3 of 5 — Video Codec ]
  ──────────────────────────────────────────────────
  ▶  Which codec do you want to use?
    ● 1. H.265 / HEVC        Best compression — recommended     libx265
    ○ 2. H.264 / AVC         Widest compatibility               libx264
    ○ 3. AV1                 Next-gen, very slow to encode      libaom-av1

  [ Compression Complete ]
  ──────────────────────────────────────────────────
  Original size          187.3 MB
  Compressed size         72.1 MB
  Space saved            115.2 MB  (61.5%)
  Compression ratio       2.60×
```

---

## Download

Pre-built single-file executables — **no Python or FFmpeg installation required**.

| Platform | Download |
|----------|----------|
| 🪟 Windows 64-bit | [videocrunch-windows-x64.exe](https://github.com/YOUR_USERNAME/videocrunch/releases/latest) |
| 🍎 macOS (Apple Silicon) | [videocrunch-macos-arm64](https://github.com/YOUR_USERNAME/videocrunch/releases/latest) |
| 🐧 Linux 64-bit | [videocrunch-linux-x64](https://github.com/YOUR_USERNAME/videocrunch/releases/latest) |

> **macOS / Linux:** make the file executable after downloading:
> ```bash
> chmod +x videocrunch-macos-arm64
> ./videocrunch-macos-arm64
> ```

---

## Features

- ✅ **No resolution change** — width × height stays identical
- ✅ **Interactive wizard** — no CLI flags to remember
- ✅ **H.265 / H.264 / AV1** codec support
- ✅ **Quality profiles** — from Lossless → High → Balanced → Small → Tiny
- ✅ **Speed presets** — Ultra Fast to Very Slow
- ✅ **Audio control** — keep original stream or re-encode at chosen bitrate
- ✅ **Live progress bar** with speed and ETA
- ✅ **Compress another file** loop — batch-process without restarting
- ✅ **Single binary** — FFmpeg is bundled inside the EXE

---

## Quality Profiles

| Profile | CRF | Description |
|---------|-----|-------------|
| **Lossless** | 0 | No quality loss — largest file |
| **High** | 18 | Visually transparent — great quality |
| **Balanced** | 23 | Good trade-off — **default** |
| **Small** | 28 | Smaller file — slight quality drop |
| **Tiny** | 35 | Minimum size — noticeable compression |

> Lower CRF = better quality and larger file.  
> H.265 typically achieves **40–60% smaller files** than the same video in H.264 at equivalent visual quality.

---

## Encoding Speed Presets

| Preset | Trade-off |
|--------|-----------|
| Ultra Fast | Fastest encode — larger output |
| Fast | Quick with decent compression |
| **Medium** | Balanced — default |
| Slow | Better compression, longer wait |
| Very Slow | Best compression — slowest |

---

## Build from Source

### Prerequisites

- Python 3.10+
- FFmpeg installed and on PATH (or placed in `./bin/`)

```bash
git clone https://github.com/YOUR_USERNAME/videocrunch.git
cd videocrunch

pip install -r requirements.txt

# Run directly without building
python videocrunch.py
```

### Build EXE

```bash
# Windows — place ffmpeg.exe + ffprobe.exe in ./bin/ first
pyinstaller videocrunch.spec

# macOS / Linux — ffmpeg must be on PATH
pyinstaller videocrunch.spec

# Output: dist/videocrunch (or dist/videocrunch.exe on Windows)
```

The spec file bundles FFmpeg and FFprobe directly into the binary so end users do not need to install anything separately.

---

## CI/CD

The included [`.github/workflows/build.yml`](.github/workflows/build.yml) automatically:

1. Downloads FFmpeg for each platform
2. Runs PyInstaller
3. Uploads artifacts
4. Creates a GitHub Release with all three binaries whenever a `v*.*.*` tag is pushed

**To release a new version:**

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## Project Structure

```
videocrunch/
├── videocrunch.py              # Main CLI application
├── videocrunch.spec            # PyInstaller build spec
├── requirements.txt            # Python deps (PyInstaller only)
├── README.md
└── .github/
    └── workflows/
        └── build.yml           # CI/CD — builds on Windows, macOS, Linux
```

---

## How it works

1. Uses **FFprobe** to read the input video's metadata (resolution, codec, duration, bitrate)
2. Asks the user to configure codec, quality (CRF), speed preset, and audio
3. Builds an **FFmpeg** command with `-vf scale=trunc(iw/2)*2:trunc(ih/2)*2` — this ensures even dimensions required by H.265 while keeping the original size
4. Streams FFmpeg's stderr to render a live progress bar
5. Reports the final size reduction after encoding

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
