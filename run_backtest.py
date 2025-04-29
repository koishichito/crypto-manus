#!/usr/bin/env python
"""
汎用バックテストエンジン
exit code:
 90 = YAML バリデーション失敗
 91 = データ取得エラー
 92 = Strategy 生成エラー
"""
import sys, yaml, traceback, datetime as dt
import pandas as pd, ccxt, backtrader as bt
from libs.strategy_factory import make_strategy

# ---------- YAML 読込＋簡易バリデーション ----------
try:
    spec = yaml.safe_load(open(sys.argv[1]))
    assert "signal" in spec and "type" in spec["signal"]
except Exception as e:
    print("[YAML-ERR]", e); sys.exit(90)

# ---------- データ取得関数 ----------
def fetch_ohlcv(exchange, symbol, tf, since_iso):
    ex = getattr(ccxt, exchange)()
    ohlc = ex.fetch_ohlcv(symbol, timeframe=tf, since=ex.parse8601(since_iso))
    df = pd.DataFrame(ohlc, columns=["ts","o","h","l","c","v"]).set_index("ts")
    df.index = pd.to_datetime(df.index, unit="ms")
    return df

# ---------- データロード (単銘柄 or ペア) ----------
sig_type = spec["signal"]["type"]
try:
    if sig_type == "pair_spread":
        a = spec["datasource"]["asset1"]; b = spec["datasource"]["asset2"]
        dfA = fetch_ohlcv(**a); dfB = fetch_ohlcv(**b)
        df = pd.DataFrame({"a_close": dfA["c"], "b_close": dfB["c"]}).dropna()
    else:
        ds = spec["datasource"]
        df = fetch_ohlcv(ds["exchange"], ds["symbol"], ds["timeframe"], ds["since"])
except Exception as e:
    print("[DATA-ERR]", e); traceback.print_exc(limit=1); sys.exit(91)

# ---------- Strategy 生成 ----------
try:
    Strat, kwargs = make_strategy(spec["signal"], spec.get("execution", {}))
except Exception as e:
    print("[STRAT-ERR]", e); sys.exit(92)

# ---------- Backtrader ----------
cerebro = bt.Cerebro(stdstats=False)
if sig_type == "pair_spread":
    cerebro.adddata(bt.feeds.PandasData(dataname=df["a_close"].to_frame("close")), name="A")
    cerebro.adddata(bt.feeds.PandasData(dataname=df["b_close"].to_frame("close")), name="B")
else:
    cerebro.adddata(bt.feeds.PandasData(dataname=df))
cerebro.addstrategy(Strat, **kwargs)
cerebro.broker.setcash(spec.get("backtest", {}).get("initial_capital", 10_000))
res = cerebro.run()[0]

# ---------- レポート ----------
start = cerebro.broker.startingcash
end   = cerebro.broker.getvalue()
ta    = res.analyzers.tradeanalyzer.get_analysis()
print(f"\n=== Backtest Report [{sig_type}] ===")
print(f"Trades {ta.total.closed} | Win {ta.won.total} / Loss {ta.lost.total}")
print(f"Equity  {end:,.2f}  (PnL {end-start:+,.2f})")
print("====================================\n")
