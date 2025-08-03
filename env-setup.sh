#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Installing Homebrew dependencies..."
brew install llvm libomp

echo "🌐 Setting Clang/OpenMP toolchain vars..."
export CC="$(brew --prefix llvm)/bin/clang"
export CXX="$(brew --prefix llvm)/bin/clang++"
export LDFLAGS="-L$(brew --prefix libomp)/lib"
export CPPFLAGS="-I$(brew --prefix libomp)/include"
export PATH="$(brew --prefix llvm)/bin:$PATH"

echo "🧹 Removing old venv..."
rm -rf venv

echo "🐍 Creating fresh venv..."
python3 -m venv venv
source venv/bin/activate

echo "⬆️  Upgrading pip..."
pip install --upgrade pip

echo "📦 Pre‑installing scientific wheels..."
pip install \
  numpy==2.3.2 \
  scipy==1.16.1 \
  pandas==2.3.1 \
  scikit-learn==1.7.1 \
  matplotlib==3.10.5 \
  --only-binary :all:

echo "📄 Installing the rest of requirements.txt..."
pip install -r requirements.txt

echo "🧪 Quick import test..."
python - <<'PY'
import numpy, scipy, pandas, sklearn, matplotlib, flask, whisper
print("✅  All core imports succeeded.")
PY

echo "✅ Environment setup complete."
