"""
Backtest a top-3 daily-rebalance portfolio driven by 3-day forward-return
predictions on csi300.

Pipeline:
    qlib.init -> Alpha158 (3-day label) on csi300 -> LGBModel.fit
    -> SignalRecord (predictions) -> PortAnaRecord (TopkDropoutStrategy, topk=3, n_drop=1)
    -> load report_normal & port_analysis from recorder -> print metrics + save csvs

Run:
    python examples/backtest_top3_3d.py

Requires `pip install pyqlib`.
"""
import os
import sys

# Strip repo root from sys.path so we use the installed pyqlib (compiled
# C extensions) rather than the un-compiled source tree.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _REPO_ROOT]

import pandas as pd  # noqa: E402

import qlib  # noqa: E402
from qlib.constant import REG_CN  # noqa: E402
from qlib.utils import init_instance_by_config, flatten_dict  # noqa: E402
from qlib.workflow import R  # noqa: E402
from qlib.workflow.record_temp import SignalRecord, SigAnaRecord, PortAnaRecord  # noqa: E402
from qlib.tests.data import GetData  # noqa: E402


# -------- user-tunable parameters --------
PROVIDER_URI = "~/.qlib/qlib_data/cn_data"
MARKET = "csi300"
BENCHMARK = "SH000300"

TRAIN_PERIOD = ("2008-01-01", "2014-12-31")
VALID_PERIOD = ("2015-01-01", "2016-12-31")
TEST_PERIOD = ("2017-01-01", "2020-08-01")

TOPK = 5
N_DROP = 1            # how many of the held stocks to replace each day
HOLD_THRESH = 1       # minimum holding days before a stock can be sold
ACCOUNT = 100_000_000
EXPERIMENT_NAME = "top3_3d_backtest"
OUTPUT_DIR = "outputs"
# -----------------------------------------


def build_task_config():
    label_expr = ["Ref($close, -3) / $close - 1"]
    label_name = ["LABEL0_3D"]

    handler_kwargs = {
        "start_time": TRAIN_PERIOD[0],
        "end_time": TEST_PERIOD[1],
        "fit_start_time": TRAIN_PERIOD[0],
        "fit_end_time": TRAIN_PERIOD[1],
        "instruments": MARKET,
        "label": (label_expr, label_name),
    }

    dataset_config = {
        "class": "DatasetH",
        "module_path": "qlib.data.dataset",
        "kwargs": {
            "handler": {
                "class": "Alpha158",
                "module_path": "qlib.contrib.data.handler",
                "kwargs": handler_kwargs,
            },
            "segments": {
                "train": TRAIN_PERIOD,
                "valid": VALID_PERIOD,
                "test": TEST_PERIOD,
            },
        },
    }

    model_config = {
        "class": "LGBModel",
        "module_path": "qlib.contrib.model.gbdt",
        "kwargs": {
            "loss": "mse",
            "colsample_bytree": 0.8879,
            "learning_rate": 0.0421,
            "subsample": 0.8789,
            "lambda_l1": 205.6999,
            "lambda_l2": 580.9768,
            "max_depth": 8,
            "num_leaves": 210,
            "num_threads": 20,
        },
    }

    return model_config, dataset_config


def build_port_analysis_config():
    return {
        "executor": {
            "class": "SimulatorExecutor",
            "module_path": "qlib.backtest.executor",
            "kwargs": {
                "time_per_step": "day",
                "generate_portfolio_metrics": True,
            },
        },
        "strategy": {
            "class": "TopkDropoutStrategy",
            "module_path": "qlib.contrib.strategy.signal_strategy",
            "kwargs": {
                "signal": "<PRED>",      # filled by PortAnaRecord with the saved predictions
                "topk": TOPK,
                "n_drop": N_DROP,
                "hold_thresh": HOLD_THRESH,
                "only_tradable": True,    # skip suspended / limit-up / limit-down on decision
            },
        },
        "backtest": {
            "start_time": TEST_PERIOD[0],
            "end_time": TEST_PERIOD[1],
            "account": ACCOUNT,
            "benchmark": BENCHMARK,
            "exchange_kwargs": {
                "freq": "day",
                "limit_threshold": 0.095,
                "deal_price": "close",
                "open_cost": 0.0005,
                "close_cost": 0.0015,
                "min_cost": 5,
            },
        },
    }


def summarize_holdings(positions: dict) -> pd.DataFrame:
    """positions is a dict {pd.Timestamp: Position}. Return a DataFrame with
    (date, n_holdings, holdings_list)."""
    rows = []
    for date, pos in positions.items():
        # qlib >=0.9 stores `position` dict on Position, plus 'cash' / 'now_account_value' keys
        try:
            stock_dict = pos.position  # dict-like
        except AttributeError:
            stock_dict = pos
        stocks = [k for k in stock_dict.keys() if k not in ("cash", "now_account_value")]
        rows.append({"date": date, "n_holdings": len(stocks), "holdings": ",".join(stocks)})
    return pd.DataFrame(rows).set_index("date").sort_index()


def main():
    GetData().qlib_data(target_dir=PROVIDER_URI, region=REG_CN, exists_skip=True)
    qlib.init(provider_uri=PROVIDER_URI, region=REG_CN)

    model_cfg, dataset_cfg = build_task_config()
    model = init_instance_by_config(model_cfg)
    dataset = init_instance_by_config(dataset_cfg)

    port_cfg = build_port_analysis_config()

    with R.start(experiment_name=EXPERIMENT_NAME):
        R.log_params(**flatten_dict({"model": model_cfg, "dataset": dataset_cfg, "port": port_cfg}))

        print("[step] training LGBModel on full csi300 universe...")
        model.fit(dataset)
        R.save_objects(**{"trained_model.pkl": model})

        recorder = R.get_recorder()

        print("[step] generating predictions (SignalRecord)...")
        sr = SignalRecord(model, dataset, recorder)
        sr.generate()

        print("[step] signal analysis (IC / RankIC) ...")
        SigAnaRecord(recorder).generate()

        print(f"[step] backtest: TopkDropoutStrategy(topk={TOPK}, n_drop={N_DROP}) daily rebalance...")
        par = PortAnaRecord(recorder, port_cfg, "day")
        par.generate()

        # ---- pull artifacts back out of the recorder ----
        report_normal = recorder.load_object("portfolio_analysis/report_normal_1day.pkl")
        port_analysis = recorder.load_object("portfolio_analysis/port_analysis_1day.pkl")
        positions_normal = recorder.load_object("portfolio_analysis/positions_normal_1day.pkl")

    # ---- print risk analysis (annualized return / IR / max drawdown / etc.) ----
    print("\n=== Risk analysis (1day, top-3 daily) ===")
    # port_analysis is a DataFrame indexed by metric, columns = ['risk']
    # rows include excess_return_without_cost, excess_return_with_cost, return, cost, bench
    print(port_analysis.to_string())

    # ---- daily-level diagnostics ----
    rep = report_normal.copy()
    # rep columns typically: return, cost, bench, turnover, account, value
    cum_strategy = (1 + rep["return"] - rep["cost"]).cumprod()
    cum_bench = (1 + rep["bench"]).cumprod()
    excess_net = rep["return"] - rep["cost"] - rep["bench"]

    print("\n=== Daily diagnostics ===")
    print(f"backtest days:                 {len(rep)}")
    print(f"strategy total return (net):   {cum_strategy.iloc[-1] - 1:+.4%}")
    print(f"benchmark total return:        {cum_bench.iloc[-1] - 1:+.4%}")
    print(f"excess (net) total return:     {(cum_strategy.iloc[-1] / cum_bench.iloc[-1] - 1):+.4%}")
    print(f"avg daily turnover:            {rep['turnover'].mean():.4f}")
    print(f"avg daily cost (drag):         {rep['cost'].mean():+.6f}")

    # ---- holdings concentration ----
    holdings_df = summarize_holdings(positions_normal)
    print("\n=== Holdings concentration ===")
    print(f"avg #holdings per day:         {holdings_df['n_holdings'].mean():.2f}")
    print(f"median #holdings per day:      {holdings_df['n_holdings'].median():.0f}")
    print(f"days with <{TOPK} holdings:        {(holdings_df['n_holdings'] < TOPK).sum()} (suspensions / limit-up-down)")

    print("\nLast 10 days of holdings:")
    print(holdings_df.tail(10).to_string())

    # ---- save outputs ----
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rep_out = os.path.join(OUTPUT_DIR, "backtest_top3_report.csv")
    holdings_out = os.path.join(OUTPUT_DIR, "backtest_top3_holdings.csv")
    rep[["return", "cost", "bench", "turnover"]].assign(
        cum_strategy=cum_strategy, cum_bench=cum_bench, excess_net=excess_net
    ).to_csv(rep_out)
    holdings_df.to_csv(holdings_out)
    print(f"\nSaved daily report to:   {rep_out}")
    print(f"Saved holdings log to:   {holdings_out}")


if __name__ == "__main__":
    main()
