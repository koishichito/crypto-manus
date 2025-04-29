set -euo pipefail
trap 'echo "[BOOTSTRAP-ERR] $?" >&2' ERR   # 99 を返して Manus に異常終了を通知

# 1. deps
python -m pip install -q --upgrade pip
python -m pip install -q ccxt==4.* backtrader==1.9.* pandas ta pyyaml

# 2. YAML 取得
if [[ $# -lt 1 ]]; then
  echo "[BOOTSTRAP-ERR] YAML URL required" >&2; exit 99
fi
curl -fsSL "$1" -o /tmp/strategy.yaml

# 3. 実行
python run_backtest.py /tmp/strategy.yaml
