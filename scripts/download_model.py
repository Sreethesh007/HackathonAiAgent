#!/usr/bin/env python3
"""
llama.cpp Model Downloader
--------------------------
Downloads recommended GGUF model files from HuggingFace for use with
the llama.cpp server backend.

Usage:
    python scripts/download_model.py --list
    python scripts/download_model.py --model llama3.1-8b-q4
    python scripts/download_model.py --model llama3.1-8b-q4 --dir models/

Models are saved to ./models/ by default. After downloading, start the
llama.cpp server with:

    ./build/bin/llama-server -m models/<filename>.gguf --port 8080

Then switch your .env:
    LLM_PROVIDER=llamacpp
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.request
from pathlib import Path

# ── Curated model catalogue ───────────────────────────────────────────────────
# Format: id → {display name, HuggingFace URL, RAM required, quality notes}
MODELS: dict[str, dict] = {
    # ── Llama 3.1 ──────────────────────────────────────────────────────────
    "llama3.1-8b-q4": {
        "name":     "Llama 3.1 8B Instruct Q4_K_M  (RECOMMENDED)",
        "filename": "llama-3.1-8b-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "ram_gb":   6,
        "size_gb":  4.7,
        "quality":  "Good — best balance of quality and speed for 8GB machines",
    },
    "llama3.1-8b-q8": {
        "name":     "Llama 3.1 8B Instruct Q8_0",
        "filename": "llama-3.1-8b-instruct.Q8_0.gguf",
        "url":      "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q8_0.gguf",
        "ram_gb":   8,
        "size_gb":  8.5,
        "quality":  "Better quality, needs 8GB RAM",
    },
    # ── Mistral ────────────────────────────────────────────────────────────
    "mistral-7b-q4": {
        "name":     "Mistral 7B Instruct v0.3 Q4_K_M",
        "filename": "mistral-7b-instruct-v0.3.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
        "ram_gb":   5,
        "size_gb":  4.1,
        "quality":  "Good — strong instruction following, slightly faster than Llama",
    },
    # ── Phi-3 (lightweight) ────────────────────────────────────────────────
    "phi3-mini-q4": {
        "name":     "Phi-3 Mini 4K Instruct Q4_K_M  (LIGHTWEIGHT)",
        "filename": "phi-3-mini-4k-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Phi-3-mini-4k-instruct-GGUF/resolve/main/Phi-3-mini-4k-instruct-Q4_K_M.gguf",
        "ram_gb":   3,
        "size_gb":  2.2,
        "quality":  "Basic — for machines with only 4GB RAM; lower reasoning quality",
    },
    # ── Gemma 2 ───────────────────────────────────────────────────────────
    "gemma2-9b-q4": {
        "name":     "Gemma 2 9B Instruct Q4_K_M",
        "filename": "gemma-2-9b-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/gemma-2-9b-it-GGUF/resolve/main/gemma-2-9b-it-Q4_K_M.gguf",
        "ram_gb":   7,
        "size_gb":  5.4,
        "quality":  "Very good — Google's model, excellent at instruction following",
    },
}


def list_models() -> None:
    """Print the model catalogue in a readable table."""
    print("\n┌─────────────────────────────────────────────────────────────────────┐")
    print("│            Available llama.cpp GGUF Models                          │")
    print("├──────────────────┬────────┬────────┬──────────────────────────────── ┤")
    print("│ ID               │ RAM    │ Size   │ Notes                           │")
    print("├──────────────────┼────────┼────────┼──────────────────────────────── ┤")
    for mid, m in MODELS.items():
        print(f"│ {mid:<16s} │ {m['ram_gb']}GB    │ {m['size_gb']}GB  │ {m['quality'][:32]:<32s} │")
    print("└──────────────────┴────────┴────────┴──────────────────────────────── ┘")
    print()
    print("Usage: python scripts/download_model.py --model llama3.1-8b-q4")
    print()


def download_model(model_id: str, dest_dir: str = "models") -> Path:
    """
    Download a GGUF model file with progress display.

    Args:
        model_id:  Key from MODELS dict (e.g. "llama3.1-8b-q4")
        dest_dir:  Local directory to save the file

    Returns:
        Path to the downloaded file
    """
    if model_id not in MODELS:
        print(f"\n✗ Unknown model '{model_id}'")
        print(f"  Valid options: {', '.join(MODELS.keys())}")
        list_models()
        sys.exit(1)

    model    = MODELS[model_id]
    dest     = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    out_path = dest / model["filename"]

    print(f"\n{'─'*60}")
    print(f"  Model   : {model['name']}")
    print(f"  Size    : {model['size_gb']} GB")
    print(f"  RAM req : {model['ram_gb']} GB")
    print(f"  Quality : {model['quality']}")
    print(f"  Saving  : {out_path}")
    print(f"{'─'*60}")

    if out_path.exists():
        existing_mb = out_path.stat().st_size / 1_000_000
        print(f"\n  File already exists ({existing_mb:.0f} MB). Use --force to re-download.")
        return out_path

    # Check available disk space
    import shutil
    free_gb = shutil.disk_usage(dest).free / 1_000_000_000
    if free_gb < model["size_gb"] + 0.5:
        print(f"\n✗ Insufficient disk space. Need {model['size_gb']} GB, have {free_gb:.1f} GB free.")
        sys.exit(1)

    print(f"\n  Downloading from HuggingFace...")
    print(f"  (This may take a while on slow connections — {model['size_gb']} GB)\n")

    def _progress(block_num: int, block_size: int, total_size: int) -> None:
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(downloaded / total_size * 100, 100)
            mb_done  = downloaded / 1_000_000
            mb_total = total_size / 1_000_000
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            print(f"\r  [{bar}] {pct:5.1f}%  {mb_done:.0f}/{mb_total:.0f} MB", end="", flush=True)

    try:
        urllib.request.urlretrieve(model["url"], out_path, reporthook=_progress)
        print(f"\n\n  ✓ Download complete: {out_path}")
    except KeyboardInterrupt:
        print(f"\n\n  Download interrupted. Removing partial file...")
        out_path.unlink(missing_ok=True)
        sys.exit(1)
    except Exception as e:
        print(f"\n\n  ✗ Download failed: {e}")
        out_path.unlink(missing_ok=True)
        sys.exit(1)

    # Print next steps
    print(f"\n{'─'*60}")
    print("  NEXT STEPS:")
    print()
    print("  1. Build llama.cpp (if not done yet):")
    print("       git clone https://github.com/ggerganov/llama.cpp")
    print("       cd llama.cpp && cmake -B build && cmake --build build -j$(nproc)")
    print()
    print("  2. Start the server:")
    print(f"       ./build/bin/llama-server \\")
    print(f"           -m {out_path} \\")
    print(f"           --host 0.0.0.0 --port 8080 \\")
    print(f"           --n-gpu-layers 0 \\")
    print(f"           --threads {os.cpu_count() or 4} \\")
    print(f"           --ctx-size 4096")
    print()
    print("  3. Switch provider in .env:")
    print("       LLM_PROVIDER=llamacpp")
    print()
    print("  4. Verify connectivity:")
    print("       python scripts/check_env.py")
    print(f"{'─'*60}\n")

    return out_path


def check_llamacpp_server(base_url: str = "http://localhost:8080") -> bool:
    """Quick check if the llama.cpp server is running and responding."""
    import urllib.error
    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=3) as resp:
            return resp.status == 200
    except (urllib.error.URLError, Exception):
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download GGUF models for llama.cpp local inference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--model",  type=str, help="Model ID to download (see --list)")
    parser.add_argument("--dir",    type=str, default="models", help="Destination directory (default: ./models)")
    parser.add_argument("--list",   action="store_true", help="List available models")
    parser.add_argument("--force",  action="store_true", help="Re-download even if file exists")
    parser.add_argument("--check",  action="store_true", help="Check if llama.cpp server is running")
    parser.add_argument("--url",    type=str, default="http://localhost:8080", help="llama.cpp server URL for --check")

    args = parser.parse_args()

    if args.list or (not args.model and not args.check):
        list_models()
        sys.exit(0)

    if args.check:
        ok = check_llamacpp_server(args.url)
        if ok:
            print(f"  ✓ llama.cpp server is running at {args.url}")
        else:
            print(f"  ✗ llama.cpp server not reachable at {args.url}")
            print("    Start it with: ./build/bin/llama-server -m models/<file>.gguf --port 8080")
        sys.exit(0 if ok else 1)

    if args.model:
        if args.force:
            # Remove existing file to force re-download
            m = MODELS.get(args.model, {})
            if m:
                p = Path(args.dir) / m["filename"]
                p.unlink(missing_ok=True)
        download_model(args.model, args.dir)
