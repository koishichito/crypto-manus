import backtrader as bt, math

# --------------------------------------------------
# Strategy implementations
# --------------------------------------------------
class VWAPDeviation(bt.Strategy):
    params = ("threshold", "tp", "sl")
    def __init__(self):
        self.vwap = bt.ind.VWAP(self.data)
    def next(self):
        dev = (self.data.close[0]-self.vwap[0])/self.vwap[0]*100
        if not self.position and dev <= -self.p.threshold:
            self.buy()
        if self.position:
            if dev >= self.p.tp or dev <= -self.p.sl:
                self.close()

class EMA_ATR_Trend(bt.Strategy):
    params = ("fast", "slow", "atr_mul")
    def __init__(self):
        self.fast = bt.ind.EMA(self.data, period=self.p.fast)
        self.slow = bt.ind.EMA(self.data, period=self.p.slow)
        self.atr  = bt.ind.ATR(self.data)
    def next(self):
        if not self.position and self.fast[0] > self.slow[0]:
            self.buy()
            self.sl = self.data.close[0] - self.p.atr_mul*self.atr[0]
        elif self.position and self.data.close[0] < self.sl:
            self.close()

class BollingerMR(bt.Strategy):
    params = ("period", "dev")
    def __init__(self):
        self.mid = bt.ind.SMA(self.data, period=self.p.period)
        self.sd  = bt.ind.StandardDeviation(self.data, period=self.p.period)
    def next(self):
        lower = self.mid[0]-self.p.dev*self.sd[0]
        upper = self.mid[0]+self.p.dev*self.sd[0]
        if not self.position and self.data.close[0] < lower:
            self.buy()
        elif self.position and self.data.close[0] > self.mid[0]:
            self.close()

class PairSpread(bt.Strategy):
    params = ("entry_z", "exit_z")
    def __init__(self):
        self.a, self.b = self.datas[0].close, self.datas[1].close
        self.spread = self.a / self.b
        self.z = bt.ind.zscore.ZScore(self.spread, period=200)
    def next(self):
        if not self.position and self.z[0] > self.p.entry_z:
            self.sell(data=self.datas[0]); self.buy(data=self.datas[1])
        elif not self.position and self.z[0] < -self.p.entry_z:
            self.buy(data=self.datas[0]); self.sell(data=self.datas[1])
        elif self.position and abs(self.z[0]) < self.p.exit_z:
            self.close(self.datas[0]); self.close(self.datas[1])

# --------------------------------------------------
# Factory
# --------------------------------------------------
def make_strategy(sig_cfg, exe_cfg):
    """Returns (StrategyClass, kwargs)"""
    t = sig_cfg["type"]
    if t == "vwap_deviation":
        return VWAPDeviation, dict(
            threshold=sig_cfg["params"]["threshold"],
            tp=exe_cfg.get("take_profit", 0.15),
            sl=exe_cfg.get("stop_loss", 0.10))
    if t == "ema_atr_tf":
        return EMA_ATR_Trend, dict(
            fast=sig_cfg["params"]["fast"],
            slow=sig_cfg["params"]["slow"],
            atr_mul=sig_cfg["params"]["atr_mult"])
    if t == "bollinger_mr":
        return BollingerMR, dict(
            period=sig_cfg["params"]["period"],
            dev=sig_cfg["params"]["dev"])
    if t == "pair_spread":
        return PairSpread, dict(
            entry_z=sig_cfg["params"]["entry_z"],
            exit_z=sig_cfg["params"]["exit_z"])
    raise ValueError(f"unknown signal.type: {t}")
