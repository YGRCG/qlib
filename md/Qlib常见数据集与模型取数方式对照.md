# Qlib 常见数据集与模型取数方式对照

本文是对 [Qlib数据集机制与模型适配说明.md](./Qlib数据集机制与模型适配说明.md) 的补充，重点放在更实操的两个问题：

1. `DatasetH` 和 `TSDatasetH` 到底有什么区别
2. 常见模型在 `fit()` / `predict()` 里分别是怎么取数据的

涉及的关键代码位置：

- [qlib/data/dataset/__init__.py](../qlib/data/dataset/__init__.py)
- [qlib/contrib/model/linear.py](../qlib/contrib/model/linear.py)
- [qlib/contrib/model/gbdt.py](../qlib/contrib/model/gbdt.py)
- [qlib/contrib/model/pytorch_lstm.py](../qlib/contrib/model/pytorch_lstm.py)
- [qlib/contrib/model/pytorch_lstm_ts.py](../qlib/contrib/model/pytorch_lstm_ts.py)

## 1. 先给结论

最实用的区分方式是：

- `DatasetH`：返回按 `(instrument, datetime)` 平铺好的表格数据，适合直接做截面监督学习
- `TSDatasetH`：在 `DatasetH` 的基础上，把平铺表格进一步组织成时间序列样本，适合时序模型

换句话说：

- `DatasetH` 更像给你一张研究表
- `TSDatasetH` 更像给你一个“滑动窗口样本集”

## 2. DatasetH：平铺表格数据

`DatasetH` 的职责是：

1. 绑定一个 `handler`
2. 定义 `train / valid / test` 分段
3. 通过 `prepare(...)` 从 handler 中取出指定 segment 和列组的数据

典型调用形式是：

```python
df_train = dataset.prepare("train", col_set=["feature", "label"], data_key=DataHandlerLP.DK_L)
```

返回结果通常是一个 `DataFrame`，逻辑上可以理解为：

| instrument | datetime | feature | label |
| --- | --- | --- | --- |
| SH600000 | 2020-01-02 | F维向量 | y |
| SH600000 | 2020-01-03 | F维向量 | y |
| SH600001 | 2020-01-02 | F维向量 | y |

这类数据最适合：

- Linear
- LightGBM
- XGBoost
- CatBoost
- MLP

它们普遍把每一行视为一个独立样本。

## 3. TSDatasetH：时间序列样本

`TSDatasetH` 定义在 [qlib/data/dataset/__init__.py](../qlib/data/dataset/__init__.py) 中，本质上是 `DatasetH` 的扩展。

它增加了两个关键行为：

### 3.1 增加 `step_len`

`step_len` 表示每个样本往前看多少个时间步。

比如：

- `step_len = 30`

那么某个时点的一个样本，不再只是“当天这一行 feature”，而是：

```text
过去 30 个时间步的特征序列
```

### 3.2 取数时自动补前序历史

`TSDatasetH` 会在你请求一个 segment 时，自动把开始时间往前扩展 `step_len`，以保证最前面的样本也有完整历史窗口。

这就是它和普通 `DatasetH` 的关键差异：

- `DatasetH`：你要哪段，就取哪段
- `TSDatasetH`：你要哪段，我会额外往前补一截历史，保证时序窗口完整

### 3.3 返回 TSDataSampler，而不是普通 DataFrame

`TSDatasetH.prepare(...)` 最终返回的是 `TSDataSampler` 这类时序采样对象，不是简单平铺表。

这个对象更像一个可索引的数据集：

- 每次取一个样本，会返回一个时间窗口
- 多个样本可组成 batch

因此它更适合被：

- `torch.utils.data.DataLoader`
- 自定义 batch 逻辑

这类组件直接消费。

## 4. DatasetH 与 TSDatasetH 的对照

| 维度 | DatasetH | TSDatasetH |
| --- | --- | --- |
| 数据组织 | 平铺表格 | 时间序列窗口 |
| 典型返回 | `DataFrame` | `TSDataSampler` |
| 单样本含义 | 单日单股票样本 | 单股票一段历史序列 |
| 典型形状 | `[N, F]` | `[N, T, F]` |
| 是否自动补历史 | 否 | 是 |
| 适合模型 | 线性、树模型、MLP | LSTM、GRU、Transformer TS、TCN TS |

## 5. 常见模型的取数方式

下面按模型类型看它们在 `fit()` 中到底怎么取数据。

### 5.1 LinearModel：标准表格取数

`LinearModel.fit()` 的典型代码结构是：

```python
df_train = dataset.prepare("train", col_set=["feature", "label"], data_key=DataHandlerLP.DK_L)
df_train = df_train.dropna()
X, y = df_train["feature"].values, df_train["label"].values
```

特点：

- 直接从 `DatasetH` 取 `DataFrame`
- 每一行是独立样本
- 再转成 `numpy` 做回归

适配关系：

- 常配 `DatasetH`
- 不要求时序 sampler

### 5.2 LGBModel：也是表格取数，但多了 valid 集和权重

`LGBModel.fit()` 的典型逻辑是：

```python
for key in ["train", "valid"]:
    df = dataset.prepare(key, col_set=["feature", "label"], data_key=DataHandlerLP.DK_L)
    x, y = df["feature"], df["label"]
```

特点：

- 仍然是平铺 `DataFrame`
- 常常同时取 `train` 和 `valid`
- 再包装成 LightGBM 的 `Dataset`

适配关系：

- 常配 `DatasetH`
- 对模型来说，样本仍然是表格样本，不是时序窗口

### 5.3 pytorch_lstm.py：名字是 LSTM，但仍然吃平铺表格

这一点很容易误解。

在 [qlib/contrib/model/pytorch_lstm.py](../qlib/contrib/model/pytorch_lstm.py) 中，训练时取数方式是：

```python
df_train, df_valid, df_test = dataset.prepare(
    ["train", "valid", "test"],
    col_set=["feature", "label"],
    data_key=DataHandlerLP.DK_L,
)
```

后面直接做：

```python
x_train, y_train = df_train["feature"], df_train["label"]
```

这说明它虽然是 PyTorch 模型，虽然名字叫 `lstm`，但它这一版接口仍然依赖：

- 平铺表格特征
- 然后在模型内部自行解释 feature 维度

所以这类模型通常仍然可以和 `DatasetH` 配合。

关键结论：

> “模型名字里有 LSTM” 不等于 “它一定要求 TSDatasetH”

真正要看的是它的 `fit()` 到底拿的是 `DataFrame` 还是 `TSDataSampler`。

### 5.4 pytorch_lstm_ts.py：真正按时序 Dataset 取数

在 [qlib/contrib/model/pytorch_lstm_ts.py](../qlib/contrib/model/pytorch_lstm_ts.py) 中，训练取数方式是：

```python
dl_train = dataset.prepare("train", col_set=["feature", "label"], data_key=DataHandlerLP.DK_L)
dl_valid = dataset.prepare("valid", col_set=["feature", "label"], data_key=DataHandlerLP.DK_L)
```

随后直接：

```python
train_loader = DataLoader(...)
valid_loader = DataLoader(...)
```

并且还会对返回对象执行：

```python
dl_train.config(fillna_type="ffill+bfill")
```

这说明这里的 `dataset.prepare(...)` 返回的已经不是普通 `DataFrame`，而是可进一步喂给 `DataLoader` 的时序数据对象。

这类模型通常更适合：

- `TSDatasetH`
- 或其他返回 sampler/dataloader 友好对象的 dataset

## 6. 一个容易踩坑的点：模型名不能直接代表数据组织方式

很多人会自然地认为：

- `LinearModel` -> 表格
- `LSTM` -> 时序

但在 Qlib 里不能只看名字，必须看实现。

例如：

- `pytorch_lstm.py`：虽然是 LSTM，但取的是平铺 `DataFrame`
- `pytorch_lstm_ts.py`：才是显式面向时序 dataset 的版本

所以最稳妥的判断方式永远是：

1. 看 `fit()` 里 `dataset.prepare(...)` 的返回对象怎么被使用
2. 看后面是否直接进入 `DataLoader`
3. 看是否有 `step_len`、补历史窗口、时序 sampler 等机制

## 7. 快速判断一类模型该用哪种 dataset

可以用下面这个速查规则。

### 7.1 如果模型这样取数

```python
df_train = dataset.prepare(...)
X = df_train["feature"].values
```

那么它大概率适合：

- `DatasetH`

### 7.2 如果模型这样取数

```python
dl_train = dataset.prepare(...)
train_loader = DataLoader(dl_train, ...)
```

那么它大概率适合：

- `TSDatasetH`
- 或其他 sampler 型 dataset

### 7.3 如果模型除了 feature 还要图结构

那么它通常需要：

- 自定义图 dataset

### 7.4 如果模型工作在环境交互中

那么它通常需要：

- 专门的 RL / 高频 dataset 或环境接口

## 8. 建议的阅读顺序

如果你要自己判断某个模型和数据集是否兼容，建议按这个顺序看源码：

1. `task.model.class`
2. 该模型文件中的 `fit()`
3. 该模型文件中的 `predict()`
4. `task.dataset.class`
5. dataset 的 `prepare()`
6. dataset 背后的 `handler`

这个顺序的好处是：

- 先看模型需要什么
- 再看 dataset 能不能给出来

而不是先猜名字。

## 9. 一句话总结

- `DatasetH` 适合平铺表格样本
- `TSDatasetH` 适合时间窗口样本
- 判断模型该配哪种 dataset，核心看 `fit()` 怎么消费 `dataset.prepare(...)` 的结果

因此，真正决定兼容性的不是“模型名”或“论文名”，而是：

> 数据返回结构是否和模型的训练接口一致
