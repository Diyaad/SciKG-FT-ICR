#!/usr/bin/env bash
# setup_rcc_venv.sh -- rebuild the SciKG venv on RCC. Correctly. Every time.
#
# WHY THIS EXISTS (read before "simplifying" it):
#
#   requirements.txt pulls torch from PyPI, and PyPI's default torch ships the
#   CUDA 13 build. RCC's GPU driver is CUDA 12.9. The cu13 build installs
#   perfectly, imports fine on the login node, and then crashes on the GPU node.
#
#   The fix is to override torch from the cu128 wheel index AFTER requirements.
#   Two traps, both of which have already cost us a node:
#
#     1. ORDER. The override must come after `-r requirements.txt`, or
#        requirements re-installs the wrong torch on top of the right one.
#
#     2. --reinstall. Without it, uv sees torch already present and silently
#        does nothing -- it prints "Audited 2 packages" and exits 0. Looks like
#        success. Leaves the broken cu13 build in place.
#
#   This has bitten twice. Run this script instead of doing it by hand.
#
# WHERE: login node only. Compute nodes have no outbound internet.
#
# USAGE:
#   bash scripts/setup_rcc_venv.sh
#   source scikg-venv/bin/activate     # this script can't activate your shell

set -uo pipefail

VENV=scikg-venv
CUDA_WHEEL=https://download.pytorch.org/whl/cu128

cd "$(dirname "$0")/.." || exit 1   # repo root, regardless of where invoked

echo "== repo: $(pwd)"

module load python-uv/0.9.7 || { echo "FAIL: could not load python-uv"; exit 1; }

# 1. fresh venv (3.12 -- RCC's system python/3 is too old for docling)
uv venv "$VENV" --python 3.12 || exit 1
# shellcheck disable=SC1090,SC1091
source "$VENV/bin/activate" || exit 1

# 2. requirements FIRST. This installs the WRONG torch. That is expected.
echo "== installing requirements.txt (will pull cu13 torch -- overridden next)"
uv pip install -r requirements.txt || exit 1

# 3. override torch LAST, with --reinstall. Do not remove --reinstall.
echo "== overriding torch/torchvision from cu128 index"
uv pip install --reinstall torch torchvision --index-url "$CUDA_WHEEL" || exit 1

# 4. verify. Refuse to hand back a venv that will crash on the GPU node.
python - <<'PY' || exit 1
import sys
try:
    import torch
except Exception as e:
    sys.exit(f"FAIL: torch will not import: {e}")

got = torch.version.cuda or "none"
print(f"   torch {torch.__version__}   cuda {got}")
if not got.startswith("12.8"):
    sys.exit(f"FAIL: expected CUDA 12.8, got {got}. Do NOT sbatch -- "
             f"the --reinstall override did not take.")

# the cu128 override downgrades numpy/pillow/setuptools; docling was resolved
# against the newer ones, so confirm the stack still imports before a 2.5h job.
for mod in ("docling", "langextract"):
    try:
        __import__(mod)
    except Exception as e:
        sys.exit(f"FAIL: {mod} broken after torch override: {e}")
print("   docling + langextract import OK")
PY

echo
echo "== venv OK -- safe to sbatch"
echo "   run: source $VENV/bin/activate"
