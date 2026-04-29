# Alpha158DL 特征速查表

本文根据 [qlib/contrib/data/loader.py](../qlib/contrib/data/loader.py) 中 `Alpha158DL.get_feature_config` 整理，方便快速查看 `Alpha158DL` 的特征结构、数学形式和直观含义。

## 总览

`Alpha158DL` 的特征分为 4 大块：

1. `kbar`：9 个 K 线形态特征
2. `price`：原始价格相对特征
3. `volume`：原始成交量相对特征
4. `rolling`：滚动窗口统计特征

默认配置下的总特征数为 158：

- `kbar`: 9
- `price`: 4
- `rolling`: 29 类 x 5 个窗口（`5/10/20/30/60`）= 145

## 默认配置

```python
config = {
    "kbar": {},
    "price": {
        "windows": [0],
        "feature": ["OPEN", "HIGH", "LOW", "VWAP"],
    },
    "rolling": {},
}
```

## 1. Kbar 特征

| 特征名 | 数学形式 | 直观含义 | 大值通常意味着 |
| --- | --- | --- | --- |
| `KMID` | `($close-$open)/$open` | K 线实体涨跌幅 | 阳线实体大，收盘高于开盘更多 |
| `KLEN` | `($high-$low)/$open` | 日内整体振幅 | 当天波动更大 |
| `KMID2` | `($close-$open)/($high-$low+1e-12)` | 实体占振幅比例 | 实体在整根 K 线中占比高 |
| `KUP` | `($high-Greater($open, $close))/$open` | 上影线长度 | 冲高后回落更多 |
| `KUP2` | `($high-Greater($open, $close))/($high-$low+1e-12)` | 上影线占振幅比例 | 上影线在振幅中更显著 |
| `KLOW` | `(Less($open, $close)-$low)/$open` | 下影线长度 | 下探后回升更多 |
| `KLOW2` | `(Less($open, $close)-$low)/($high-$low+1e-12)` | 下影线占振幅比例 | 下影线在振幅中更显著 |
| `KSFT` | `(2*$close-$high-$low)/$open` | 收盘相对区间中枢的偏移 | 收盘更靠近日内高位 |
| `KSFT2` | `(2*$close-$high-$low)/($high-$low+1e-12)` | 归一化收盘中枢偏移 | 收盘在日内区间位置更高 |

## 2. Price 原始价格特征

统一形式：

- `d = 0` 时：`$field / $close`
- `d > 0` 时：`Ref($field, d) / $close`

默认配置只启用 `windows=[0]`，字段为 `OPEN/HIGH/LOW/VWAP`。

| 特征名模式 | 数学形式 | 直观含义 | 大值通常意味着 |
| --- | --- | --- | --- |
| `OPENd` | `Ref($open, d)/$close` 或 `$open/$close` | 第 `d` 天前开盘价相对当前收盘价 | 历史开盘价相对当前收盘更高 |
| `HIGHd` | `Ref($high, d)/$close` 或 `$high/$close` | 第 `d` 天前最高价相对当前收盘价 | 历史高点相对当前收盘更高 |
| `LOWd` | `Ref($low, d)/$close` 或 `$low/$close` | 第 `d` 天前最低价相对当前收盘价 | 历史低点相对当前收盘更高 |
| `CLOSEd` | `Ref($close, d)/$close` 或 `$close/$close` | 第 `d` 天前收盘价相对当前收盘价 | 历史收盘相对当前收盘更高 |
| `VWAPd` | `Ref($vwap, d)/$close` 或 `$vwap/$close` | 第 `d` 天前均价相对当前收盘价 | 历史成交均价相对当前收盘更高 |

## 3. Volume 原始成交量特征

统一形式：

- `d = 0` 时：`$volume / ($volume+1e-12)`
- `d > 0` 时：`Ref($volume, d) / ($volume+1e-12)`

| 特征名模式 | 数学形式 | 直观含义 | 大值通常意味着 |
| --- | --- | --- | --- |
| `VOLUMEd` | `Ref($volume, d)/($volume+1e-12)` 或 `$volume/($volume+1e-12)` | 历史成交量相对今天成交量的比例 | 历史量相对今天更大，今天偏缩量 |

## 4. Rolling 滚动特征

默认窗口为：`5, 10, 20, 30, 60`。  
以下每一类都会生成 `xxx5/xxx10/xxx20/xxx30/xxx60`。

### 4.1 趋势与回归类

| 特征名 | 数学形式 | 直观含义 | 大值通常意味着 |
| --- | --- | --- | --- |
| `ROCd` | `Ref($close, d)/$close` | `d` 天前收盘相对当前收盘 | 若当前价格上涨较多，该值更小；若当前价格下跌较多，该值更大 |
| `MAd` | `Mean($close, d)/$close` | `d` 日均价相对当前收盘 | 当前价格低于过去均价更多 |
| `STDd` | `Std($close, d)/$close` | `d` 日收盘波动率 | 过去 `d` 日价格更不稳定 |
| `BETAd` | `Slope($close, d)/$close` | `d` 日线性趋势斜率 | 趋势斜率更陡，方向更明确 |
| `RSQRd` | `Rsquare($close, d)` | 线性回归拟合优度 | 走势更接近线性趋势 |
| `RESId` | `Resi($close, d)/$close` | 线性回归残差 | 当前偏离线性趋势更明显 |

### 4.2 价格区间与分位类

| 特征名 | 数学形式 | 直观含义 | 大值通常意味着 |
| --- | --- | --- | --- |
| `MAXd` | `Max($high, d)/$close` | `d` 日最高价相对当前收盘 | 当前离阶段高点更远，或历史高点更高 |
| `MINd` | `Min($low, d)/$close` | `d` 日最低价相对当前收盘 | 阶段低点相对当前收盘更高 |
| `QTLUd` | `Quantile($close, d, 0.8)/$close` | `d` 日收盘 80% 分位相对当前收盘 | 当前价格低于高分位更多 |
| `QTLDd` | `Quantile($close, d, 0.2)/$close` | `d` 日收盘 20% 分位相对当前收盘 | 当前价格低于低分位更多，或低分位本身较高 |
| `RANKd` | `Rank($close, d)` | 当前收盘在 `d` 日窗口中的分位位置 | 当前价格在近期位置更高 |
| `RSVd` | `($close-Min($low, d))/(Max($high, d)-Min($low, d)+1e-12)` | 当前价格在近期高低区间中的位置 | 当前更接近区间上沿 |

### 4.3 极值时序类

`IdxMax/IdxMin` 在 `qlib` 中返回的是窗口内位置编号，最早位置为 `1`，当前位置约为 `d`。

| 特征名 | 数学形式 | 直观含义 | 大值通常意味着 |
| --- | --- | --- | --- |
| `IMAXd` | `IdxMax($high, d)/d` | 近期最高点出现得有多靠后 | 最高点更接近当前时点 |
| `IMINd` | `IdxMin($low, d)/d` | 近期最低点出现得有多靠后 | 最低点更接近当前时点 |
| `IMXDd` | `(IdxMax($high, d)-IdxMin($low, d))/d` | 高点相对低点出现的先后顺序 | 低点在前、高点在后，走势更偏上行 |

### 4.4 价量相关类

| 特征名 | 数学形式 | 直观含义 | 大值通常意味着 |
| --- | --- | --- | --- |
| `CORRd` | `Corr($close, Log($volume+1), d)` | 收盘价水平与成交量水平的相关性 | 价高时量也更大，价量更同向 |
| `CORDd` | `Corr($close/Ref($close,1), Log($volume/Ref($volume, 1)+1), d)` | 价格变化与成交量变化的相关性 | 上涨时更偏放量，或下跌时更偏缩量 |

### 4.5 涨跌天数统计类

| 特征名 | 数学形式 | 直观含义 | 大值通常意味着 |
| --- | --- | --- | --- |
| `CNTPd` | `Mean($close>Ref($close, 1), d)` | 上涨天数占比 | 近期上涨天数更多 |
| `CNTNd` | `Mean($close<Ref($close, 1), d)` | 下跌天数占比 | 近期下跌天数更多 |
| `CNTDd` | `Mean($close>Ref($close, 1), d)-Mean($close<Ref($close, 1), d)` | 上涨占比减下跌占比 | 上涨天数相对更占优 |

### 4.6 涨跌幅度统计类

| 特征名 | 数学形式 | 直观含义 | 大值通常意味着 |
| --- | --- | --- | --- |
| `SUMPd` | `Sum(Greater($close-Ref($close, 1), 0), d)/(Sum(Abs($close-Ref($close, 1)), d)+1e-12)` | 上涨幅度占总绝对波动的比例 | 波动主要来自上涨 |
| `SUMNd` | `Sum(Greater(Ref($close, 1)-$close, 0), d)/(Sum(Abs($close-Ref($close, 1)), d)+1e-12)` | 下跌幅度占总绝对波动的比例 | 波动主要来自下跌 |
| `SUMDd` | `(Sum(Greater($close-Ref($close, 1), 0), d)-Sum(Greater(Ref($close, 1)-$close, 0), d))/(Sum(Abs($close-Ref($close, 1)), d)+1e-12)` | 上涨贡献减下跌贡献 | 上涨力度相对更强 |

### 4.7 成交量状态类

| 特征名 | 数学形式 | 直观含义 | 大值通常意味着 |
| --- | --- | --- | --- |
| `VMAd` | `Mean($volume, d)/($volume+1e-12)` | 过去均量相对今天量 | 今天较过去更缩量 |
| `VSTDd` | `Std($volume, d)/($volume+1e-12)` | 过去成交量波动相对今天量的大小 | 历史量波动更大，或今天量不高 |
| `WVMAd` | `Std(Abs($close/Ref($close, 1)-1)*$volume, d)/(Mean(Abs($close/Ref($close, 1)-1)*$volume, d)+1e-12)` | 量加权价格波动强度的变异系数 | 量价联动波动更不稳定 |

### 4.8 成交量增减统计类

| 特征名 | 数学形式 | 直观含义 | 大值通常意味着 |
| --- | --- | --- | --- |
| `VSUMPd` | `Sum(Greater($volume-Ref($volume, 1), 0), d)/(Sum(Abs($volume-Ref($volume, 1)), d)+1e-12)` | 放量贡献占成交量总变化的比例 | 最近量能变化主要来自放量 |
| `VSUMNd` | `Sum(Greater(Ref($volume, 1)-$volume, 0), d)/(Sum(Abs($volume-Ref($volume, 1)), d)+1e-12)` | 缩量贡献占成交量总变化的比例 | 最近量能变化主要来自缩量 |
| `VSUMDd` | `(Sum(Greater($volume-Ref($volume, 1), 0), d)-Sum(Greater(Ref($volume, 1)-$volume, 0), d))/(Sum(Abs($volume-Ref($volume, 1)), d)+1e-12)` | 放量贡献减缩量贡献 | 最近整体更偏放量 |

## 5. 速记版

| 大类 | 子类 | 关键词 |
| --- | --- | --- |
| `kbar` | `KMID` ~ `KSFT2` | 实体、上下影、收盘位置 |
| `price` | `OPEN/HIGH/LOW/CLOSE/VWAP` | 历史价格相对当前收盘 |
| `volume` | `VOLUME` | 历史量相对今天量 |
| `rolling` 趋势类 | `ROC/MA/STD/BETA/RSQR/RESI` | 趋势、波动、线性拟合 |
| `rolling` 区间类 | `MAX/MIN/QTLU/QTLD/RANK/RSV` | 区间位置、分位、相对高低 |
| `rolling` 极值时序类 | `IMAX/IMIN/IMXD` | 高低点出现顺序 |
| `rolling` 价量相关类 | `CORR/CORD` | 价量同向性 |
| `rolling` 次数统计类 | `CNTP/CNTN/CNTD` | 涨跌天数占比 |
| `rolling` 幅度统计类 | `SUMP/SUMN/SUMD` | 涨跌力度占比 |
| `rolling` 量状态类 | `VMA/VSTD/WVMA` | 放量缩量、量波动、量价波动稳定性 |
| `rolling` 量变化统计类 | `VSUMP/VSUMN/VSUMD` | 放量缩量贡献占比 |

## 6. 说明

- 文中“值大意味着什么”是便于直观理解的经验性解释，不等同于单独可交易信号。
- 很多特征都做了归一化处理，例如除以 `$close`、`$volume` 或波动总和，以弱化量纲影响。
- `loader.py` 中个别注释与实际实现存在方向性歧义时，应以运算实现为准。
