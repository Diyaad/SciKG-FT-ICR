#!/bin/bash
# submit_pdf_eval.sh - SLURM batch job: run PDF extraction (02d) on the 8
# ground-truth papers using a LOCAL Ollama model, then score with the eval
# harness. No API key, no external quota.
#
# Submit with:
#   sbatch submit_pdf_eval.sh
#
# Output appears in slurm-<jobid>.out and in docs/PDF_EXTRACTION_EVAL.md.
#
# ==========================================================================
# On RCC the -A "account" IS the queue/partition (they're synonymous). backfill2
# is the only GENERAL-ACCESS queue with GPU nodes: 4-hour cap, preemptible.
# There is no general-access "gpu" partition, so do NOT use --partition here.
# Verify you have backfill2 with:  rcctool my:queues
# ==========================================================================
#SBATCH -A backfill2
#SBATCH --job-name=scikg_pdf_eval
#SBATCH --gres=gpu:1                  # one GPU. Do NOT add -N/--nodes on backfill2, or GPUs are refused.
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00               # 8 papers is well under 1h; shorter = sooner start + smaller preemption window
#SBATCH --output=slurm-%j.out

set -e

echo "=== SciKG PDF eval job starting on $(hostname) ==="
date

# ---------------------------------------------------------------------------
# Paths - must match setup_rcc.sh
# ---------------------------------------------------------------------------
SCIKG_DIR="$HOME/scikg"
OLLAMA_DIR="$HOME/ollama"
VENV_DIR="$HOME/scikg-venv"

cd "$SCIKG_DIR"

# ---------------------------------------------------------------------------
# Modules + environment
# ---------------------------------------------------------------------------
module load cuda || echo "WARN: cuda module not loaded"
export PATH="$OLLAMA_DIR/bin:$PATH"
export LD_LIBRARY_PATH="$OLLAMA_DIR/lib/ollama:$LD_LIBRARY_PATH"
export OLLAMA_MODELS="$OLLAMA_DIR/models"
source "$VENV_DIR/bin/activate"

# Point 02d at the local Ollama backend instead of Gemini.
export LANGEXTRACT_BACKEND="ollama"
export OLLAMA_MODEL_ID="llama3.1:8b"
export OLLAMA_URL="http://localhost:11434"
# Silence the Windows-style HF symlink warning (harmless, and we're on Linux now).
export HF_HUB_DISABLE_SYMLINKS_WARNING=1

# ---------------------------------------------------------------------------
# Start the Ollama server on this compute node, in the background.
# ---------------------------------------------------------------------------
echo "Starting Ollama server..."
ollama serve > ollama_serve.log 2>&1 &
OLLAMA_PID=$!

# Wait until the server responds before running extraction.
echo "Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
  if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Ollama is up."
    break
  fi
  sleep 2
done

# Fail loudly instead of silently extracting nothing if the server never came up.
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
  echo "ERROR: Ollama never became ready; aborting." >&2
  cat ollama_serve.log >&2 || true
  kill $OLLAMA_PID 2>/dev/null || true
  exit 1
fi

# Confirm a GPU is actually visible (catches silent CPU fallback / missing --gres).
nvidia-smi || echo "WARN: nvidia-smi unavailable — verify the GPU is attached"

# ---------------------------------------------------------------------------
# Run extraction on the 8 ground-truth DOIs, then score.
# ---------------------------------------------------------------------------
echo "Running 02d extraction..."
python scripts/02d_extract_pdf.py \
  10.1016/j.mcpro.2024.100875 \
  10.1021/acs.analchem.5c02420 \
  10.1002/rcm.4655 \
  10.21037/atm.2019.12.67 \
  10.1021/acs.jproteome.6b00696 \
  10.1016/j.jbc.2022.102768 \
  10.1021/acs.analchem.5c06165 \
  10.1021/ac0108461

echo "Running eval harness..."
mkdir -p outputs   # eval writes outputs/pdf_eval_results.jsonl
python scripts/eval_pdf_extraction.py

# ---------------------------------------------------------------------------
# Clean shutdown of the Ollama server.
# ---------------------------------------------------------------------------
echo "Stopping Ollama server..."
kill $OLLAMA_PID 2>/dev/null || true

echo "=== Job complete ==="
date
echo "See docs/PDF_EXTRACTION_EVAL.md for the scored results."
