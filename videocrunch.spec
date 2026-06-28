name: Build VideoСrunch

on:
  push:
    tags:
      - "v*.*.*"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build:
    name: Build — ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: windows-latest
            artifact_name: videocrunch-windows-x64.exe
            ffmpeg_url: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip

          - os: macos-latest
            artifact_name: videocrunch-macos-arm64

          - os: ubuntu-latest
            artifact_name: videocrunch-linux-x64

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      # ==================== FFmpeg Setup ====================
      - name: Download FFmpeg (Windows)
        if: runner.os == 'Windows'
        shell: pwsh
        run: |
          Invoke-WebRequest -Uri "${{ matrix.ffmpeg_url }}" -OutFile ffmpeg.zip
          Expand-Archive ffmpeg.zip -DestinationPath ffmpeg_tmp
          New-Item -ItemType Directory -Force -Path bin | Out-Null
          Copy-Item "ffmpeg_tmp\ffmpeg-*-essentials_build\bin\ffmpeg.exe" -Destination "bin\ffmpeg.exe"
          Copy-Item "ffmpeg_tmp\ffmpeg-*-essentials_build\bin\ffprobe.exe" -Destination "bin\ffprobe.exe"

      - name: Install FFmpeg (macOS)
        if: runner.os == 'macOS'
        run: |
          brew install ffmpeg
          mkdir -p bin
          cp "$(which ffmpeg)" bin/ffmpeg
          cp "$(which ffprobe)" bin/ffprobe
          chmod +x bin/ffmpeg bin/ffprobe

      - name: Install FFmpeg (Linux)
        if: runner.os == 'Linux'
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y ffmpeg
          mkdir -p bin
          cp "$(which ffmpeg)" bin/ffmpeg
          cp "$(which ffprobe)" bin/ffprobe
          chmod +x bin/ffmpeg bin/ffprobe

      # ==================== Build ====================
      - name: Build with PyInstaller
        run: pyinstaller videocrunch.spec --clean

      # ==================== Rename Artifact ====================
      - name: Rename output (Windows)
        if: runner.os == 'Windows'
        shell: pwsh
        run: Move-Item "dist\videocrunch.exe" "dist\${{ matrix.artifact_name }}"

      - name: Rename output (Unix)
        if: runner.os != 'Windows'
        run: mv dist/videocrunch dist/${{ matrix.artifact_name }}

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.artifact_name }}
          path: dist/${{ matrix.artifact_name }}
          retention-days: 30

  release:
    name: Create GitHub Release
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')

    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          path: release-assets

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          name: "VideoСrunch ${{ github.ref_name }}"
          body: |
            **VideoСrunch ${{ github.ref_name }}**

            Interactive CLI video compressor — no resolution change.

            ### Downloads
            | Platform          | File                          |
            |-------------------|-------------------------------|
            | Windows 64-bit    | `videocrunch-windows-x64.exe` |
            | macOS Apple Silicon | `videocrunch-macos-arm64`   |
            | Linux 64-bit      | `videocrunch-linux-x64`       |

            > **macOS / Linux**: `chmod +x videocrunch-*`
          files: release-assets/**/*
