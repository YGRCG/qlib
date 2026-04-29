# Qlib 快速入门指南

## 环境准备

### 系统要求
- **操作系统**: Linux, Windows, MacOS
- **Python版本**: 3.8, 3.9, 3.10, 3.11, 3.12
- **推荐**: 使用Conda管理Python环境

### 安装方式

#### 方式1: 使用pip安装（推荐新手）
```bash
pip install pyqlib
```

#### 方式2: 从源码安装（推荐开发者）
```bash
# 安装依赖
pip install numpy
pip install --upgrade cython

# 克隆仓库并安装
git clone https://github.com/microsoft/qlib.git
cd qlib
pip install .

# 开发模式安装（推荐）
pip install -e .[dev]
```

#### 方式3: 使用Docker
```bash
# 拉取镜像
docker pull pyqlib/qlib_image_stable:stable

# 启动容器
docker run -it --name qlib_container -v /your/local/path:/app pyqlib/qlib_image_stable:stable
```

### Mac M1特殊说明
如果遇到LightGBM安装问题：
```bash
# 先安装OpenMP
brew install libomp

# 然后安装Qlib
pip install .
```

## 数据准备

### 方式1: 使用社区数据源（推荐）
```bash
# 下载最新数据
wget https://github.com/chenditc/investment_data/releases/latest/download/qlib_bin.tar.gz

# 创建目录
mkdir -p ~/.qlib/qlib_data/cn_data

# 解压数据
tar -zxvf qlib_bin.tar.gz -C ~/.qlib/qlib_data/cn_data --strip-components=1

# 清理压缩包
rm -f qlib_bin.tar.gz
```

### 方式2: 使用官方脚本（官方数据暂时禁用）
```bash
# 获取日线数据
python -m qlib.cli.data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn

# 获取分钟数据
python -m qlib.cli.data qlib_data --target_dir ~/.qlib/qlib_data/cn_data_1min --region cn --interval 1min
```

### 数据健康检查
```bash
# 检查数据完整性
python scripts/check_data_health.py check_data --qlib_dir ~/.qlib/qlib_data/cn_data
```

### 自动更新数据（可选）
```bash
# 手动更新
python scripts/data_collector/yahoo/collector.py update_data_to_bin \
    --qlib_data_1d_dir ~/.qlib/qlib_data/cn_data \
    --trading_date 2021-05-25 \
    --end_date 2021-06-01

# Linux定时任务（每个交易日自动更新）
crontab -e
# 添加: * * * * 1-5 python <script_path> update_data_to_bin --qlib_data_1d_dir <data_dir>
```

## 第一个Qlib程序

### 初始化Qlib
```python
import qlib
from qlib.constant import REG_CN

# 初始化
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=REG_CN)
```

### 获取数据
```python
from qlib.data import D

# 获取交易日历
calendar = D.calendar(start_time='2020-01-01', end_time='2020-12-31', freq='day')
print(calendar[:5])

# 获取股票列表
instruments = D.instruments('csi300')
stock_list = D.list_instruments(
    instruments=instruments, 
    start_time='2020-01-01', 
    end_time='2020-12-31', 
    as_list=True
)
print(stock_list[:5])

# 获取股票特征数据
instruments = ['SH600000']
fields = ['$close', '$volume', 'Ref($close, 1)', 'Mean($close, 3)', '$high-$low']
data = D.features(
    instruments, 
    fields, 
    start_time='2020-01-01', 
    end_time='2020-12-31', 
    freq='day'
)
print(data.head())
```

## 使用qrun运行工作流

### 运行LightGBM示例
```bash
# 进入examples目录
cd examples

# 运行工作流
qrun benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml
```

### 调试模式
```bash
python -m pdb qlib/cli/run.py examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml
```

### 预期输出
```
'The following are analysis results of the excess return without cost.'
                       risk
mean               0.000708
std                0.005626
annualized_return  0.178316
information_ratio  1.996555
max_drawdown      -0.081806

'The following are analysis results of the excess return with cost.'
                       risk
mean               0.000512
std                0.005626
annualized_return  0.128982
information_ratio  1.444287
max_drawdown      -0.091078
```

## 代码化工作流

### 完整示例
```python
import qlib
from qlib.constant import REG_CN
from qlib.utils import init_instance_by_config
from qlib.workflow import R
from qlib.workflow.record_temp import SignalRecord, PortAnaRecord

# 1. 初始化
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=REG_CN)

# 2. 定义市场和基准
market = "csi300"
benchmark = "SH000300"

# 3. 数据处理器配置
data_handler_config = {
    "start_time": "2008-01-01",
    "end_time": "2020-08-01",
    "fit_start_time": "2008-01-01",
    "fit_end_time": "2014-12-31",
    "instruments": market,
}

# 4. 任务配置
task = {
    "model": {
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
    },
    "dataset": {
        "class": "DatasetH",
        "module_path": "qlib.data.dataset",
        "kwargs": {
            "handler": {
                "class": "Alpha158",
                "module_path": "qlib.contrib.data.handler",
                "kwargs": data_handler_config,
            },
            "segments": {
                "train": ("2008-01-01", "2014-12-31"),
                "valid": ("2015-01-01", "2016-12-31"),
                "test": ("2017-01-01", "2020-08-01"),
            },
        },
    },
}

# 5. 训练模型
with R.start(experiment_name="workflow_by_code"):
    # 初始化模型
    model = init_instance_by_config(task["model"])
    dataset = init_instance_by_config(task["dataset"])
    
    # 训练
    model.fit(dataset)
    
    # 预测
    pred = model.predict(dataset)
    
    # 记录信号
    sr = SignalRecord(model, dataset, recorder=R.get_recorder())
    sr.generate()
    
    # 回测
    port_analysis_config = {
        "strategy": {
            "class": "TopkDropoutStrategy",
            "module_path": "qlib.contrib.strategy",
            "kwargs": {
                "signal": pred,
                "topk": 50,
                "n_drop": 5,
            },
        },
        "backtest": {
            "start_time": "2017-01-01",
            "end_time": "2020-08-01",
            "account": 100000000,
            "benchmark": benchmark,
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
    
    # 投资组合分析
    par = PortAnaRecord(
        recorder=R.get_recorder(),
        config=port_analysis_config,
    )
    par.generate()
```

## 图形化分析

### 安装分析依赖
```bash
pip install pyqlib[analysis]
```

### 使用Jupyter Notebook
```bash
# 启动Jupyter
jupyter notebook examples/workflow_by_code.ipynb
```

### 可视化内容
1. **预测信号分析**
   - 分组累计收益
   - 收益分布
   - 信息系数(IC)
   - 月度IC
   - 自相关性

2. **投资组合分析**
   - 回测收益曲线
   - 风险分析
   - 持仓分析
   - 交易分析

## 运行多个模型

### 使用run_all_model.py
```bash
# 运行单个模型
python examples/run_all_model.py run --models=lightgbm

# 运行多个模型
python examples/run_all_model.py run --models=lightgbm,xgboost,catboost

# 运行所有模型10次
python examples/run_all_model.py run 10

# 运行特定模型在CSI500上
python examples/run_all_model.py run 3 lightgbm Alpha158 csi500
```

## 常见配置

### 配置文件示例 (config.yaml)
```yaml
# 基础配置
provider_uri: "~/.qlib/qlib_data/cn_data"
region: cn
auto_mount: False

# 实验管理
exp_manager:
  class: MLflowExpManager
  module_path: qlib.workflow.expm
  kwargs:
    uri: "file:./mlruns"
    default_exp_name: "Experiment"

# 缓存配置
expression_cache: null
dataset_cache: null

# 日志级别
logging_level: INFO
```

### 使用配置文件初始化
```python
import qlib

# 从配置文件初始化
qlib.init_from_yaml_conf("config.yaml")

# 或者自动初始化（会自动查找config.yaml）
qlib.auto_init()
```

## 自定义数据集

### 创建自定义Handler
```python
from qlib.data.dataset.handler import DataHandlerLP

class MyHandler(DataHandlerLP):
    def __init__(
        self,
        instruments="csi300",
        start_time=None,
        end_time=None,
        freq="day",
        infer_processors=[],
        learn_processors=[],
        fit_start_time=None,
        fit_end_time=None,
        drop_raw=False,
    ):
        # 定义特征
        data_loader = {
            "class": "QlibDataLoader",
            "kwargs": {
                "config": {
                    "feature": self.get_feature_config(),
                    "label": ["Ref($close, -2)/Ref($close, -1) - 1"],
                },
                "freq": freq,
            },
        }
        
        super().__init__(
            instruments=instruments,
            start_time=start_time,
            end_time=end_time,
            data_loader=data_loader,
            infer_processors=infer_processors,
            learn_processors=learn_processors,
            fit_start_time=fit_start_time,
            fit_end_time=fit_end_time,
            drop_raw=drop_raw,
        )
    
    def get_feature_config(self):
        # 自定义特征
        fields = []
        names = []
        
        # 价格特征
        for field in ["open", "high", "low", "close", "volume"]:
            fields.append(f"${field}")
            names.append(field)
        
        # 技术指标
        fields.append("Mean($close, 5)")
        names.append("ma5")
        
        fields.append("Mean($close, 10)")
        names.append("ma10")
        
        return fields, names
```

## 自定义模型

### 创建自定义模型
```python
from qlib.model.base import Model
import lightgbm as lgb

class MyModel(Model):
    def __init__(self, **kwargs):
        self.params = kwargs
        self.model = None
    
    def fit(self, dataset):
        # 获取训练数据
        df_train, df_valid = dataset.prepare(
            ["train", "valid"],
            col_set=["feature", "label"],
            data_key="infer",
        )
        
        x_train, y_train = df_train["feature"], df_train["label"]
        x_valid, y_valid = df_valid["feature"], df_valid["label"]
        
        # 训练模型
        dtrain = lgb.Dataset(x_train, label=y_train)
        dvalid = lgb.Dataset(x_valid, label=y_valid)
        
        self.model = lgb.train(
            self.params,
            dtrain,
            valid_sets=[dtrain, dvalid],
            valid_names=["train", "valid"],
        )
    
    def predict(self, dataset):
        # 获取测试数据
        x_test = dataset.prepare("test", col_set="feature")
        
        # 预测
        return self.model.predict(x_test)
```

## 常见问题排查

### 问题1: 数据未找到
```bash
# 检查数据路径
ls ~/.qlib/qlib_data/cn_data

# 重新下载数据
python -m qlib.cli.data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn
```

### 问题2: Redis连接失败
```python
# 禁用Redis缓存
qlib.init(
    provider_uri="~/.qlib/qlib_data/cn_data",
    region=REG_CN,
    expression_cache=None,
    dataset_cache=None
)
```

### 问题3: 内存不足
```python
# 减少并行进程数
qlib.init(
    provider_uri="~/.qlib/qlib_data/cn_data",
    region=REG_CN,
    kernels=2  # 减少核心数
)
```

### 问题4: 模型训练慢
```python
# 使用更少的特征
# 使用更简单的模型（如LightGBM而不是深度学习）
# 减少数据量（缩短时间范围）
```

## 下一步学习

### 教程资源
1. **官方文档**: https://qlib.readthedocs.io/
2. **Jupyter教程**: examples/tutorial/
3. **示例代码**: examples/
4. **API文档**: https://qlib.readthedocs.io/en/latest/reference/api.html

### 进阶主题
- 高频数据处理
- 强化学习订单执行
- 投资组合优化
- 在线模型服务
- 自定义策略开发
- 分布式训练

### 社区资源
- **GitHub**: https://github.com/microsoft/qlib
- **Gitter**: https://gitter.im/Microsoft/qlib
- **Issues**: 报告问题和功能请求
- **Discussions**: 技术讨论

## 最佳实践建议

### 开发流程
1. 从简单模型开始（如LightGBM）
2. 使用小数据集快速迭代
3. 逐步增加复杂度
4. 记录所有实验结果
5. 使用版本控制

### 性能优化
1. 启用适当的缓存
2. 使用并行计算
3. 优化特征工程
4. 选择合适的模型

### 代码组织
1. 使用配置文件管理参数
2. 模块化代码结构
3. 编写单元测试
4. 添加文档注释

---

**文档版本**: 1.0
**生成时间**: 2026-02-27
**适用人群**: Qlib初学者和中级用户
