# Qlib 数据集机制与模型适配说明

本文整理 Qlib 中与“数据集”相关的核心内容，重点回答以下问题：

1. Qlib 中 `handler / dataset / model` 分别负责什么
2. 不同模型为什么可以使用不同数据集
3. 同一份底层市场数据为什么能服务不同模型
4. 如何快速判断一个模型应该配什么数据集

涉及的关键代码位置：

- [qlib/model/trainer.py](../qlib/model/trainer.py)
- [qlib/model/base.py](../qlib/model/base.py)
- [qlib/data/dataset/__init__.py](../qlib/data/dataset/__init__.py)
- [qlib/contrib/data/handler.py](../qlib/contrib/data/handler.py)
- [qlib/contrib/data/loader.py](../qlib/contrib/data/loader.py)
- [qlib/contrib/model/linear.py](../qlib/contrib/model/linear.py)

## 1. 训练流程中的数据集位置

对于基于 YAML 的典型 Qlib 工作流，训练过程的核心入口在 `qlib/model/trainer.py`。

其关键逻辑可以概括为：

```python
model = init_instance_by_config(task_config["model"])
dataset = init_instance_by_config(task_config["dataset"])
model.fit(dataset)
```

这说明 Qlib 的训练调度本身并不关心“这个模型应该搭配哪个数据集”，它只负责：

1. 根据配置实例化 `model`
2. 根据配置实例化 `dataset`
3. 调用 `model.fit(dataset)`

也就是说，模型和数据集的兼容性并不是由 trainer 硬编码决定的，而是由两者的接口契约决定的。

## 2. 三层分工：handler / dataset / model

Qlib 中与数据相关的职责可以分成三层。

### 2.1 handler：定义“底层数据长什么样”

`handler` 的职责是把原始市场数据加工成标准研究数据。

它通常负责：

- 特征定义
- 标签定义
- 预处理流程
- 数据列组管理，例如 `feature`、`label`、`weight`

以 `Alpha158` 为例：

- `Alpha158DL` 负责构造特征表达式
- `Alpha158` handler 负责把这些表达式组织成可训练的数据表

可以把 handler 理解为：

> 原始行情数据 -> 研究底表

它回答的问题是：

> “学什么数据”

而不是：

> “怎么训练”

### 2.2 dataset：定义“如何切分和组织数据”

`dataset` 的职责是在 handler 提供的数据基础上，进一步完成：

- `train / valid / test` 分段
- 按需取数
- 按模型需要组织输出形式

Qlib 的基类接口是：

- `Dataset.prepare(...)`

对于 `DatasetH`，它通常会：

1. 根据 segment 解析时间范围
2. 调用 handler 取出对应区间的数据
3. 只保留模型请求的列组
4. 返回给模型

它回答的问题是：

> “把数据按什么形式交给模型”

### 2.3 model：定义“如何消费 dataset”

模型自己决定如何从 `dataset` 中取数据，以及如何解释这些数据。

例如 `LinearModel.fit()` 中，核心逻辑是：

```python
df_train = dataset.prepare("train", col_set=["feature", "label"], ...)
X = df_train["feature"].values
y = df_train["label"].values
```

这说明线性模型要求：

- `dataset.prepare(...)` 能返回 `DataFrame`
- 数据中有 `feature` 和 `label`
- `feature` 能转换成二维数值矩阵

因此模型这一层回答的是：

> “我要什么格式的数据才能训练”

## 3. 为什么不同模型可以使用不同数据集

核心原因是：Qlib 并不要求所有模型共享同一种数据格式。

`Dataset.prepare(...)` 的返回类型并不固定，源码注释已经说明：

- 它可以是 `pd.DataFrame`
- 也可以是 `pytorch.DataLoader`
- 也可以是其他模型需要的对象

因此，不同模型可以通过自己的 `fit()` / `predict()` 逻辑，约定自己接受的数据结构。

换句话说，Qlib 的机制不是：

> “某个模型固定只能绑定某个数据集类”

而是：

> “只要 dataset.prepare() 产出的结构，正好是 model.fit() 期待的结构，它们就能配合”

## 4. 同一份底层数据为什么能服务不同模型

这是因为三层职责是解耦的：

- `handler` 决定特征内容
- `dataset` 决定组织方式
- `model` 决定消费方式

举例来说，同样是 `Alpha158` 生成的因子底表：

| instrument | datetime | feature | label |
| --- | --- | --- | --- |
| SH600000 | 2020-01-02 | 158维 | y |
| SH600000 | 2020-01-03 | 158维 | y |
| SH600001 | 2020-01-02 | 158维 | y |

这张底表可以被不同 dataset 组织成不同样子。

### 4.1 给表格模型

直接平铺成：

```text
[N, F]
```

每一行是一个 `(股票, 日期)` 样本。

适合：

- LinearModel
- LightGBM
- XGBoost
- CatBoost
- 简单 MLP

### 4.2 给时序模型

按股票分组，再切成时间窗口：

```text
[N, T, F]
```

每个样本表示某只股票过去 `T` 天的一段序列。

适合：

- LSTM
- GRU
- ALSTM
- Transformer
- TCN
- TFT

### 4.3 给图模型

除了特征外，还加入股票之间的关系结构，例如：

- 邻接矩阵
- 边列表
- 关系图

适合：

- GATs 等图模型

因此，“一份底层数据服务不同模型”的本质不是底层数据自动适配，而是 dataset 在中间完成了不同的组织。

## 5. Alpha158 + DatasetH + LinearModel 的典型链路

以 `Alpha158 + LinearModel` 为例，数据链路可以概括为：

```text
YAML
  -> trainer
  -> model = LinearModel(...)
  -> dataset = DatasetH(...)
  -> handler = Alpha158(...)
  -> data loader = Alpha158DL(...)
  -> 生成 feature / label
  -> dataset.prepare("train")
  -> model.fit(...)
```

这条链里每一层作用如下：

### 5.1 Alpha158DL

负责定义 `Alpha158` 需要用到的特征表达式，例如：

- K 线形态特征
- rolling 统计特征
- 价量关系特征

### 5.2 Alpha158 handler

负责：

- 组织 `feature`
- 组织 `label`
- 配置预处理器

### 5.3 DatasetH

负责：

- 根据 `train / valid / test` 切时间段
- 调 handler 取数据
- 把指定列组提供给模型

### 5.4 LinearModel

负责：

- 从 dataset 中取 `feature` 和 `label`
- 组装成 `X, y`
- 调 sklearn 线性回归训练

## 6. 常见模型与数据组织方式对应关系

下表比“模型名对应什么数据集类”更有用，因为它描述的是模型真正需要的数据结构。

| 模型类型 | 常见模型 | 常见数据组织方式 | 典型 Dataset | 适合的数据形态 |
| --- | --- | --- | --- | --- |
| 线性/树模型 | `LinearModel`, `LGBModel`, `XGBModel`, `CatBoostModel` | 表格特征 | `DatasetH` | `[N, F]` |
| MLP 类 | 简单前馈神经网络 | 表格特征 | `DatasetH` | `[N, F]` |
| 时序模型 | `LSTM`, `GRU`, `ALSTM`, `Transformer`, `TCN`, `TFT` | 时间窗口样本 | 通常为时序 Dataset | `[N, T, F]` |
| 图模型 | `GATs` 等 | 特征 + 图结构 | 自定义图 Dataset | `[N, F] + graph` |
| RL/高频模型 | 交易执行/强化学习类 | 状态流/环境交互 | 专用 dataset/env | `state/action/reward` |

## 7. 如何判断一个模型应该配什么数据集

最有效的方法不是看文件名，而是直接看模型源码中的 `fit()` / `predict()`。

重点看三件事：

1. 它如何调用 `dataset.prepare(...)`
2. 它期待拿到什么类型的数据
3. 它后续如何解析这些数据

可以用下面这个判断框架：

### 7.1 如果拿到的是平铺表格

典型形式：

```python
df_train = dataset.prepare("train", col_set=["feature", "label"], ...)
X = df_train["feature"].values
```

那它通常属于：

- 截面表格模型
- 常配 `DatasetH`

### 7.2 如果拿到的是时间窗口

典型形态是每个样本带有一段历史序列：

```text
[N, T, F]
```

那它通常属于：

- 时序模型
- 常配时序数据集

### 7.3 如果还需要关系结构

比如还要邻接矩阵、边列表、图 batch，那么它属于：

- 图模型
- 需要专门的数据集组织方式

### 7.4 如果不是监督学习样本，而是状态流

那通常属于：

- RL / 高频执行类模型
- 需要环境而不是普通表格数据集

## 8. 换模型时，通常换哪一层

可以按下面的经验规则理解：

### 8.1 想换算法，但数据组织不变

例如：

- `LinearModel -> LightGBM`

通常只需要换：

- `model`

一般不需要换：

- `handler`
- `dataset`

### 8.2 想保留因子内容，但改成时序模型

例如：

- `Alpha158 + LinearModel`
- 改成 `Alpha158 + LSTM`

通常：

- `handler` 可以继续复用
- `dataset` 需要改成时序组织
- `model` 换成时序模型

### 8.3 想引入资产间关系

通常：

- `handler` 可以继续提供基础特征
- `dataset` 增加图结构组织
- `model` 换成图模型

## 9. 读取一个 Qlib 配置时，建议优先看哪三处

建议按这个顺序读：

1. `task.model.class`
2. `task.dataset.class`
3. `task.dataset.kwargs.handler.class`

这三项分别回答：

- 用什么训练器
- 用什么数据组织方式
- 用什么底层特征来源

## 10. 一句话总结

Qlib 不是“模型自动匹配某个固定数据集”，而是：

> `handler` 负责产出底层研究数据，  
> `dataset` 负责把这些数据组织成模型需要的形式，  
> `model` 负责消费这种形式的数据。

因此，判断模型和数据集是否兼容，核心不是看名字，而是看：

- `dataset.prepare(...)` 产出什么
- `model.fit(...)` 期待什么

这两者对上了，就能工作。
