# Qlib 深入研究流程

## 研究目标设定

在开始之前，明确你的研究方向：
- [ ] **应用导向**: 使用Qlib进行量化投资研究
- [ ] **技术导向**: 理解Qlib的架构和实现
- [ ] **算法导向**: 研究和改进量化模型
- [ ] **工程导向**: 优化性能或扩展功能
- [ ] **综合研究**: 全面掌握Qlib

---

## 第一阶段：基础搭建（1-2周）

### Week 1: 环境搭建与基础运行

#### Day 1-2: 环境准备
- [ ] 安装Qlib（推荐从源码安装）
```bash
git clone https://github.com/microsoft/qlib.git
cd qlib
pip install -e .[dev]
```

- [ ] 配置开发环境
```bash
# 安装所有可选依赖
pip install -e .[dev,rl,analysis,test]

# 配置IDE（推荐VSCode或PyCharm）
# 安装Python插件、代码格式化工具
```

- [ ] 下载数据并验证
```bash
# 下载数据
wget https://github.com/chenditc/investment_data/releases/latest/download/qlib_bin.tar.gz
mkdir -p ~/.qlib/qlib_data/cn_data
tar -zxvf qlib_bin.tar.gz -C ~/.qlib/qlib_data/cn_data --strip-components=1

# 验证数据健康
python scripts/check_data_health.py check_data --qlib_dir ~/.qlib/qlib_data/cn_data
```

#### Day 3-4: 运行基础示例
- [ ] 运行第一个示例
```bash
cd examples
qrun benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml
```

- [ ] 理解输出结果
  - IC、ICIR指标含义
  - 回测报告解读
  - MLflow实验记录

- [ ] 运行Jupyter教程
```bash
jupyter notebook examples/tutorial/detailed_workflow.ipynb
```

#### Day 5-7: 代码化工作流
- [ ] 学习workflow_by_code.py
- [ ] 修改参数重新运行
  - 改变时间范围
  - 改变股票池（csi300 -> csi500）
  - 改变模型参数

- [ ] 创建自己的第一个实验
```python
# 创建 my_first_experiment.py
# 使用不同的特征组合
# 记录实验结果
```

**阶段目标**: 能够独立运行Qlib的基础工作流，理解基本概念

---

## 第二阶段：核心模块理解（2-3周）

### Week 2: 数据层深入研究

#### Day 1-2: 数据结构理解
- [ ] 研究Qlib数据格式
```bash
# 查看数据文件结构
ls -lh ~/.qlib/qlib_data/cn_data/

# 阅读源码
# qlib/data/storage/file_storage.py
# qlib/data/cache.py
```

- [ ] 理解数据提供者模式
```python
# 阅读并运行
examples/data_demo/data_cache_demo.py
examples/data_demo/data_mem_resuse_demo.py
```

#### Day 3-4: 特征工程
- [ ] 研究Alpha158特征定义
```python
# qlib/contrib/data/handler.py
# 找到Alpha158类，理解每个特征的含义
```

- [ ] 创建自定义特征
```python
# 创建 custom_features.py
# 定义新的技术指标
# 测试特征有效性
```

- [ ] 特征重要性分析
```python
# 使用LightGBM分析特征重要性
# 可视化Top 20特征
```

#### Day 5-7: 数据处理流程
- [ ] 研究DataHandler
  - DataHandlerLP
  - Alpha158
  - Alpha360

- [ ] 研究Processor
  - DropnaProcessor
  - CSZScoreNorm
  - 自定义Processor

- [ ] 实践：创建自定义DataHandler
```python
# 创建 my_handler.py
# 实现自定义的数据处理逻辑
```

**阶段任务**: 
- 绘制数据流程图
- 编写数据处理文档
- 创建至少一个自定义Handler

### Week 3: 模型层深入研究

#### Day 1-3: 模型架构研究
- [ ] 研究Model基类
```python
# qlib/model/base.py
# 理解fit、predict接口
```

- [ ] 深入研究3个不同类型的模型
  - **树模型**: LightGBM (qlib/contrib/model/gbdt.py)
  - **深度学习**: LSTM (examples/benchmarks/LSTM/)
  - **图神经网络**: GATs (examples/benchmarks/GATs/)

- [ ] 对比模型实现差异
  - 数据输入格式
  - 训练流程
  - 预测输出

#### Day 4-5: 模型训练与评估
- [ ] 研究训练流程
```python
# qlib/workflow/task/train.py
# 理解训练循环
```

- [ ] 研究评估指标
```python
# qlib/contrib/evaluate.py
# IC、ICIR计算方法
```

- [ ] 实现模型对比实验
```python
# 创建 model_comparison.py
# 在相同数据上对比多个模型
# 生成对比报告
```

#### Day 6-7: 实践项目
- [ ] 实现一个简单的自定义模型
```python
# 创建 my_model.py
# 可以是简单的线性模型或集成模型
# 完整的训练和预测流程
```

- [ ] 在Alpha158上测试
- [ ] 记录实验结果并分析

**阶段任务**:
- 绘制模型训练流程图
- 编写模型对比报告
- 实现并测试自定义模型

---

## 第三阶段：高级功能探索（2-3周）

### Week 4: 策略与回测

#### Day 1-2: 策略系统研究
- [ ] 研究Strategy基类
```python
# qlib/strategy/base.py
# qlib/contrib/strategy/signal_strategy.py
```

- [ ] 理解TopkDropoutStrategy
```python
# qlib/contrib/strategy/rule_strategy.py
# 理解选股逻辑
```

#### Day 3-4: 回测系统
- [ ] 研究Executor
```python
# qlib/backtest/executor.py
# 理解订单执行逻辑
```

- [ ] 研究Exchange
```python
# qlib/backtest/exchange.py
# 理解交易规则、手续费、滑点
```

- [ ] 运行回测示例
```python
# examples/nested_decision_execution/workflow.py
```

#### Day 5-7: 自定义策略
- [ ] 实现自定义交易策略
```python
# 创建 my_strategy.py
# 实现：
# - 动态仓位管理
# - 止损止盈逻辑
# - 风险控制
```

- [ ] 回测并分析结果
- [ ] 优化策略参数

**阶段任务**:
- 绘制回测流程图
- 实现2-3个不同的交易策略
- 编写策略对比报告

### Week 5: 强化学习（可选）

#### Day 1-3: RL基础
- [ ] 研究RL框架
```python
# qlib/rl/
# 理解环境、策略、训练循环
```

- [ ] 运行订单执行示例
```bash
cd examples/rl_order_execution
# 研究配置文件
# 运行TWAP、PPO、OPDS
```

#### Day 4-7: RL实践
- [ ] 理解订单执行环境
```python
# qlib/rl/order_execution/
```

- [ ] 修改奖励函数
- [ ] 训练自定义RL策略
- [ ] 对比不同RL算法

**阶段任务**:
- 理解RL在量化交易中的应用
- 实现并测试RL策略
- 编写RL实验报告

### Week 6: 在线服务与生产化

#### Day 1-3: 在线模型服务
- [ ] 研究在线服务架构
```python
# qlib/workflow/online/
# examples/online_srv/
```

- [ ] 理解模型滚动更新
```python
# examples/online_srv/rolling_online_management.py
```

#### Day 4-7: 实践部署
- [ ] 搭建本地在线服务
- [ ] 实现模型自动更新
- [ ] 监控模型性能

**阶段任务**:
- 搭建完整的在线服务
- 编写部署文档

---

## 第四阶段：源码深入与优化（3-4周）

### Week 7-8: 核心源码研究

#### 重点模块源码阅读清单

**数据模块** (优先级: ⭐⭐⭐⭐⭐)
```
qlib/data/
├── __init__.py           # 数据接口入口
├── data.py              # 核心数据类
├── cache.py             # 缓存机制 ⭐
├── dataset/
│   ├── handler.py       # 数据处理器 ⭐⭐⭐
│   ├── processor.py     # 数据预处理
│   └── loader.py        # 数据加载器
├── storage/
│   └── file_storage.py  # 文件存储 ⭐⭐
└── ops.py               # 算子定义 ⭐⭐
```

**模型模块** (优先级: ⭐⭐⭐⭐)
```
qlib/model/
├── base.py              # 模型基类 ⭐⭐⭐
└── ens/
    └── ensemble.py      # 集成学习

qlib/contrib/model/
├── gbdt.py             # GBDT实现 ⭐⭐
├── pytorch_*.py        # PyTorch模型
└── tensorflow_*.py     # TensorFlow模型
```

**工作流模块** (优先级: ⭐⭐⭐⭐)
```
qlib/workflow/
├── task/
│   ├── train.py        # 训练任务 ⭐⭐⭐
│   └── collect.py      # 结果收集
├── record_temp.py      # 记录模板 ⭐⭐
├── recorder.py         # 记录器
└── expm.py            # 实验管理 ⭐⭐
```

**回测模块** (优先级: ⭐⭐⭐⭐)
```
qlib/backtest/
├── executor.py         # 执行器 ⭐⭐⭐
├── exchange.py         # 交易所 ⭐⭐⭐
├── account.py          # 账户管理
└── decision.py         # 决策系统
```

#### 源码阅读方法
1. **自顶向下**: 从qlib/__init__.py开始
2. **场景驱动**: 跟踪一个完整的workflow执行流程
3. **调试学习**: 使用断点调试理解代码执行
4. **绘制流程图**: 将理解的流程可视化

#### 每日任务
- [ ] Day 1-2: 数据加载流程（从init到数据返回）
- [ ] Day 3-4: 特征计算流程（表达式解析到结果）
- [ ] Day 5-6: 模型训练流程（数据准备到模型保存）
- [ ] Day 7-8: 回测执行流程（信号到交易）
- [ ] Day 9-10: 缓存机制（多层缓存如何工作）
- [ ] Day 11-12: 实验管理（MLflow集成）
- [ ] Day 13-14: 整理文档和流程图

### Week 9-10: 性能优化研究

#### 性能分析
- [ ] 使用profiler分析性能瓶颈
```python
import cProfile
import pstats

# 分析数据加载性能
cProfile.run('dataset.prepare("train")', 'stats')
p = pstats.Stats('stats')
p.sort_stats('cumulative').print_stats(20)
```

- [ ] 内存使用分析
```python
from memory_profiler import profile

@profile
def load_data():
    # 你的数据加载代码
    pass
```

#### 优化方向
- [ ] 数据加载优化
  - 缓存策略优化
  - 并行加载
  - 数据预取

- [ ] 计算优化
  - 向量化计算
  - 算子融合
  - GPU加速（如果适用）

- [ ] 内存优化
  - 减少数据复制
  - 及时释放内存
  - 使用生成器

#### 实践项目
- [ ] 实现一个性能优化
- [ ] 对比优化前后的性能
- [ ] 提交PR到Qlib仓库

**阶段任务**:
- 完成核心模块的源码阅读笔记
- 绘制完整的系统架构图
- 实现至少一个性能优化

---

## 第五阶段：研究与创新（持续）

### 研究方向选择

#### 方向1: 新模型研究
- [ ] 调研最新的量化模型论文
- [ ] 在Qlib上实现新模型
- [ ] 在Alpha158/360上测试
- [ ] 对比现有模型
- [ ] 贡献到Qlib

**推荐论文来源**:
- arXiv (cs.LG, q-fin)
- KDD, ICML, NeurIPS (金融相关)
- Journal of Finance, Quantitative Finance

#### 方向2: 特征工程研究
- [ ] 研究新的技术指标
- [ ] 基于深度学习的特征提取
- [ ] 因子挖掘
- [ ] 特征选择方法

#### 方向3: 策略优化
- [ ] 投资组合优化算法
- [ ] 风险管理策略
- [ ] 高频交易策略
- [ ] 多因子策略

#### 方向4: 系统优化
- [ ] 分布式训练
- [ ] 实时预测系统
- [ ] 数据流处理
- [ ] 云原生部署

### 项目实践建议

#### 小型项目（1-2周）
1. **因子有效性研究**
   - 实现10个新因子
   - 测试IC和收益
   - 编写研究报告

2. **模型集成研究**
   - 实现Stacking/Blending
   - 对比单模型和集成
   - 分析集成效果

3. **回测框架扩展**
   - 添加新的交易成本模型
   - 实现更真实的滑点模拟
   - 支持融资融券

#### 中型项目（1-2月）
1. **端到端量化系统**
   - 数据采集
   - 特征工程
   - 模型训练
   - 策略回测
   - 在线部署

2. **多市场研究**
   - 扩展到美股/港股
   - 跨市场因子研究
   - 市场对比分析

3. **深度学习模型库**
   - 实现5-10个深度学习模型
   - 统一接口
   - 性能对比

#### 大型项目（3-6月）
1. **自动化因子挖掘系统**
   - 集成RD-Agent
   - 自动特征生成
   - 自动模型优化
   - 持续学习

2. **生产级量化平台**
   - 高可用架构
   - 实时数据处理
   - 自动化运维
   - 监控告警

3. **研究论文**
   - 提出新方法
   - 充分实验验证
   - 撰写论文
   - 投稿会议/期刊

---

## 学习资源推荐

### 官方资源
- **文档**: https://qlib.readthedocs.io/
- **GitHub**: https://github.com/microsoft/qlib
- **论文**: Qlib: An AI-oriented Quantitative Investment Platform
- **视频**: RD-Agent演示视频

### 量化投资基础
- **书籍**:
  - 《量化投资：以Python为工具》
  - 《机器学习与量化投资》
  - 《Advances in Financial Machine Learning》

- **课程**:
  - Coursera: Machine Learning for Trading
  - Udacity: AI for Trading

### 机器学习
- **深度学习**: Deep Learning (Ian Goodfellow)
- **强化学习**: Reinforcement Learning (Sutton & Barto)
- **时间序列**: Time Series Analysis and Its Applications

### 金融知识
- **技术分析**: Technical Analysis of the Financial Markets
- **投资组合**: Modern Portfolio Theory
- **风险管理**: Risk Management and Financial Institutions

---

## 研究记录与输出

### 日常记录
- [ ] 建立研究笔记（推荐使用Notion/Obsidian）
- [ ] 每日记录学习内容和问题
- [ ] 整理代码片段和示例

### 周期性输出
- [ ] 每周总结（学到什么、遇到什么问题）
- [ ] 每月报告（完成的项目、实验结果）
- [ ] 季度回顾（研究方向调整、成果展示）

### 成果输出形式
1. **技术博客**: 分享学习心得和实践经验
2. **开源贡献**: 向Qlib提交PR
3. **研究报告**: 详细的实验报告和分析
4. **学术论文**: 如果有创新性研究成果
5. **技术分享**: 在团队或社区分享

---

## 进度检查清单

### 第一个月
- [ ] 能够独立运行所有基础示例
- [ ] 理解Qlib的基本概念和工作流
- [ ] 完成至少3个自定义实验
- [ ] 阅读完核心模块文档

### 第二个月
- [ ] 深入理解数据层和模型层
- [ ] 实现至少1个自定义Handler
- [ ] 实现至少1个自定义Model
- [ ] 完成模型对比实验

### 第三个月
- [ ] 掌握策略和回测系统
- [ ] 实现至少2个自定义策略
- [ ] 理解RL框架（如果选择此方向）
- [ ] 完成一个小型项目

### 第四个月
- [ ] 完成核心源码阅读
- [ ] 绘制完整的系统架构图
- [ ] 实现至少1个性能优化
- [ ] 开始中型项目

### 长期目标（6个月+）
- [ ] 成为Qlib的贡献者
- [ ] 发表研究成果（论文/博客）
- [ ] 构建自己的量化系统
- [ ] 在实际场景中应用

---

## 常见陷阱与建议

### 避免的陷阱
1. **过度追求完美**: 不要试图一次性理解所有代码
2. **忽视基础**: 不要跳过基础直接研究高级功能
3. **缺乏实践**: 不要只看代码不动手
4. **孤立学习**: 不要闭门造车，多交流
5. **目标不清**: 不要漫无目的地学习

### 学习建议
1. **循序渐进**: 按照流程一步步来
2. **动手实践**: 每学一个概念就写代码验证
3. **记录总结**: 及时记录学习心得
4. **主动交流**: 在GitHub/Gitter提问和讨论
5. **持续迭代**: 不断回顾和改进

### 遇到困难时
1. **查看文档**: 先查官方文档
2. **搜索Issues**: GitHub Issues中可能有答案
3. **调试代码**: 使用断点调试理解执行流程
4. **简化问题**: 将复杂问题分解为简单问题
5. **寻求帮助**: 在社区提问

---

## 总结

这个研究流程设计为**4-6个月**的深入学习计划，但可以根据你的：
- **时间投入**: 全职研究 vs 业余学习
- **背景知识**: 金融/机器学习/编程基础
- **研究目标**: 应用/理论/工程

灵活调整进度。关键是**保持持续学习**和**动手实践**。

祝你研究顺利！🚀

---

**文档版本**: 1.0
**创建时间**: 2026-02-27
**适用对象**: Qlib深入研究者
