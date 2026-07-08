#!/bin/bash
# setup_rcc.sh - ONE-TIME environment setup for SciKG PDF extraction on FSU RCC.
#
# Run this ONCE, on a login node or an interactive GPU session, BEFORE submitting
# the batch job. It installs Ollama locally (no root needed), pulls the local
# model, creates a Python virtual environment with the pipeline dependencies, and
# pre-downloads Docling's models so the batch job never needs the internet
# (compute nodes are typically offline).
#
# Nothing here requires sudo. Everything installs under your home directory.
#
# Usage:
#   bash setup_rcc.sh
#
# After it finishes, submit the job with:
#   sbatch submit_pdf_eval.sh

set -e  # stop on first error

echo "=== SciKG RCC setup starting ==="

# ---------------------------------------------------------------------------
# 0. Where things live. Adjust SCIKG_DIR if your repo is elsewhere on RCC.
# ---------------------------------------------------------------------------
SCIKG_DIR="$HOME/scikg"          # the project repo on RCC
OLLAMA_DIR="$HOME/ollama"        # Ollama binary + models go here
VENV_DIR="$HOME/scikg-venv"      # Python virtual environment

echo "Project dir : $SCIKG_DIR"
echo "Ollama dir  : $OLLAMA_DIR"
echo "Venv dir    : $VENV_DIR"

# ---------------------------------------------------------------------------
# 1. Load the modules RCC provides. These names are from the RCC software
#    catalog; adjust the versions if `module avail` shows different ones.
# ---------------------------------------------------------------------------
module load python || echo "WARN: could not module load python; using system python"
module load cuda   || echo "WARN: could not module load cuda; GPU may be unavailable"

# ---------------------------------------------------------------------------
# 2. Install Ollama locally (no root). Downloads the binary into $OLLAMA_DIR.
#    NOTE: this download step needs internet, so run setup on a LOGIN node
#    (login nodes have internet; compute nodes usually do not).
# ---------------------------------------------------------------------------
mkdir -p "$OLLAMA_DIR"
if [ ! -f "$OLLAMA_DIR/bin/ollama" ]; then
  echo "Downloading Ollama (tarball WITH bundled CUDA libraries)..."
  # The bare 'ollama-linux-amd64' binary has NO GPU runtime; the .tgz ships
  # bin/ollama plus lib/ollama/cuda_v*/ (libcudart, libcublas, libggml-cuda).
  curl -L https://ollama.com/download/ollama-linux-amd64.tgz \
    -o "$OLLAMA_DIR/ollama-linux-amd64.tgz"
  tar -C "$OLLAMA_DIR" -xzf "$OLLAMA_DIR/ollama-linux-amd64.tgz"
  rm -f "$OLLAMA_DIR/ollama-linux-amd64.tgz"
else
  echo "Ollama already present, skipping download."
fi

# Tell Ollama to store its models under our home dir, not a system path.
export OLLAMA_MODELS="$OLLAMA_DIR/models"
mkdir -p "$OLLAMA_MODELS"
export PATH="$OLLAMA_DIR/bin:$PATH"
# GPU runners live in lib/ollama; the binary needs them on the library path.
export LD_LIBRARY_PATH="$OLLAMA_DIR/lib/ollama:$LD_LIBRARY_PATH"

# ---------------------------------------------------------------------------
# 3. Pull the local model. Start Ollama's server briefly to download weights,
#    then stop it. llama3.1:8b is ~5GB (fits the free-tier GPUs).
# ---------------------------------------------------------------------------
echo "Starting Ollama server to pull the model..."
ollama serve > "$OLLAMA_DIR/serve_setup.log" 2>&1 &
OLLAMA_PID=$!
sleep 8   # give the server a moment to come up

echo "Pulling llama3.1:8b (this downloads a few GB, one time)..."
ollama pull llama3.1:8b

echo "Stopping the setup Ollama server..."
kill $OLLAMA_PID 2>/dev/null || true
sleep 2

# ---------------------------------------------------------------------------
# 4. Python environment with the pipeline dependencies.
# ---------------------------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating Python virtual environment..."
  python -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install docling langextract requests

# ---------------------------------------------------------------------------
# 5. Pre-download Docling's models NOW (on the login node, with internet), so
#    the offline compute node never has to fetch them. We do this by running
#    Docling once on any PDF in the repo.
# ---------------------------------------------------------------------------
FIRST_PDF=$(ls "$SCIKG_DIR"/data/raw/pdfs/*.pdf 2>/dev/null | head -n 1 || true)
if [ -n "$FIRST_PDF" ]; then
  echo "Warming Docling models on: $FIRST_PDF"
  python - <<PYEOF
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
opts = PdfPipelineOptions()
opts.do_ocr = False
conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
r = conv.convert("$FIRST_PDF")
print("Docling model warm-up OK; produced", len(r.document.export_to_markdown()), "chars")
PYEOF
else
  echo "WARN: no PDFs found in $SCIKG_DIR/data/raw/pdfs/ to warm Docling."
  echo "      Copy your 8 PDFs there first, then re-run this warm-up step."
fi

echo ""
echo "=== Setup complete ==="
echo "Ollama binary : $OLLAMA_DIR/bin/ollama"
echo "Ollama models : $OLLAMA_MODELS"
echo "Python venv   : $VENV_DIR"
echo ""
echo "Next: submit the batch job with  sbatch submit_pdf_eval.sh"
