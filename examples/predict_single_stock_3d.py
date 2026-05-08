"""
Predict 3-day forward return of a single stock using market-wide daily data.

Pipeline:
    qlib.init -> Alpha158 (custom 3-day label) on csi300 -> LGBModel
    -> fit on full universe -> predict full universe (test segment)
    -> filter by instrument -> evaluate & save csv

Run from the repo root:
    python examples/predict_single_stock_3d.py

Requires `pip install pyqlib` (or `pip install -e .` with the C extensions
compiled for your platform).
"""
import os
import sys

# When run from the repo root, Python finds the un-compiled `qlib` source first
# and fails on the missing C extensions. Strip the repo dir from sys.path so the
# installed pyqlib (with compiled extensions) is used instead.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _REPO_ROOT]

import pandas as pd  # noqa: E402

import qlib  # noqa: E402
from qlib.constant import REG_CN  # noqa: E402
from qlib.utils import init_instance_by_config  # noqa: E402
from qlib.data.dataset.handler import DataHandlerLP  # noqa: E402
from qlib.tests.data import GetData  # noqa: E402


# -------- user-tunable parameters --------
STOCK_CODE = "SH600536"
PROVIDER_URI = "~/.qlib/qlib_data/cn_data"
# MARKET = "csi300"
MARKET = "csi500"

TRAIN_PERIOD = ("2008-01-01", "2020-12-31")
VALID_PERIOD = ("2021-01-01", "2021-12-31")
TEST_PERIOD = ("2022-01-01", "2026-05-08")

OUTPUT_DIR = "outputs"
# -----------------------------------------


def build_task_config():
    """Alpha158 + 3-day label, LGBModel with the qlib-tuned baseline hyperparams."""
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


def cross_section_ic(pred: pd.Series, label: pd.Series) -> pd.DataFrame:
    """Per-day cross-sectional IC and RankIC across the full universe."""
    df = pd.concat([pred.rename("pred"), label.rename("label")], axis=1).dropna()
    by_date = df.groupby(level="datetime")
    ic = by_date.apply(lambda g: g["pred"].corr(g["label"]))
    rank_ic = by_date.apply(lambda g: g["pred"].corr(g["label"], method="spearman"))
    return pd.DataFrame({"IC": ic, "RankIC": rank_ic})


def evaluate_single_stock(stock: str, pred: pd.Series, label: pd.Series):
    pred_s = pred.xs(stock, level="instrument") if stock in pred.index.get_level_values("instrument") else pd.Series(dtype=float)
    label_s = label.xs(stock, level="instrument") if stock in label.index.get_level_values("instrument") else pd.Series(dtype=float)

    df = pd.concat([pred_s.rename("pred"), label_s.rename("label_3d_return")], axis=1).dropna()
    if df.empty:
        print(f"[warn] no overlapping (pred, label) rows for {stock}; it may not be in {MARKET} over the test window.")
        return df

    pearson = df["pred"].corr(df["label_3d_return"])
    spearman = df["pred"].corr(df["label_3d_return"], method="spearman")
    mse = ((df["pred"] - df["label_3d_return"]) ** 2).mean()

    print(f"\n=== Single-stock evaluation: {stock} ===")
    print(f"rows: {len(df)}")
    print(f"Pearson  corr(pred, actual_3d_return): {pearson:+.4f}")
    print(f"Spearman corr(pred, actual_3d_return): {spearman:+.4f}")
    print(f"MSE (note: pred is in z-score space, label is raw return): {mse:.6f}")
    print("\nLast 10 rows:")
    print(df.tail(10).to_string())
    return df


def main():
    GetData().qlib_data(target_dir=PROVIDER_URI, region=REG_CN, exists_skip=True)
    qlib.init(provider_uri=PROVIDER_URI, region=REG_CN)

    model_cfg, dataset_cfg = build_task_config()
    model = init_instance_by_config(model_cfg)
    dataset = init_instance_by_config(dataset_cfg)

    print("[step] fitting LGBModel on full csi300 universe...")
    model.fit(dataset)

    print("[step] predicting on test segment...")
    pred = model.predict(dataset, segment="test")

    # Raw (un-normalized) label for human-readable evaluation
    label_df = dataset.prepare("test", col_set="label", data_key=DataHandlerLP.DK_R)
    label = label_df.iloc[:, 0]
    label.name = "label_3d_return"

    # ---- universe-level metrics ----
    ic_df = cross_section_ic(pred, label)
    print("\n=== Universe (csi300) cross-sectional metrics ===")
    print(f"IC mean:     {ic_df['IC'].mean():+.4f}   ICIR: {ic_df['IC'].mean() / ic_df['IC'].std():+.4f}")
    print(f"RankIC mean: {ic_df['RankIC'].mean():+.4f}   RankICIR: {ic_df['RankIC'].mean() / ic_df['RankIC'].std():+.4f}")

    # ---- single-stock evaluation & export ----
    stock = STOCK_CODE.upper()
    df_stock = evaluate_single_stock(stock, pred, label)

    if not df_stock.empty:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        out_path = os.path.join(OUTPUT_DIR, f"pred_{stock}.csv")
        df_stock.to_csv(out_path)
        print(f"\nSaved single-stock prediction to: {out_path}")


if __name__ == "__main__":
    main()
