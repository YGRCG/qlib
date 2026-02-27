# Qlib 技术架构详解

## 配置系统

### 配置层级
Qlib采用分层配置系统，支持灵活的配置管理：

1. **默认配置** (_default_config)
   - 数据提供者配置
   - 缓存配置
   - 日志配置
   - 实验管理配置
   - Redis配置

2. **模式配置** (MODE_CONF)
   - **Server模式**: 用于数据服务器部署
   - **Client模式**: 用于客户端研究
   - **High-Freq模式**: 用于高频数据处理

3. **区域配置** (_default_region_config)
   - **中国市场** (REG_CN): 交易单位100股，涨跌停限制9.5%
   - **美国市场** (REG_US): 交易单位1股，无涨跌停限制
   - **台湾市场** (REG_TW): 交易单位1000股，涨跌停限制10%

### 配置管理类

#### QlibConfig
核心配置管理类，提供：
- 配置的读取和设置
- 路径解析和管理
- 模式切换
- 区域配置
- 注册机制

#### DataPathManager
数据路径管理器，负责：
- URI类型识别（本地/NFS）
- 路径格式化
- 多频率数据路径管理
- 跨平台路径处理

### 环境变量支持
通过Pydantic Settings支持环境变量配置：
- 前缀: `QLIB_`
- 嵌套分隔符: `_`
- 示例: `QLIB_MLFLOW_URI`, `QLIB_PROVIDER_URI`

## 数据架构

### 数据提供者 (Data Provider)

#### 提供者类型
1. **CalendarProvider**: 交易日历提供者
2. **InstrumentProvider**: 股票列表提供者
3. **FeatureProvider**: 特征数据提供者
4. **PITProvider**: Point-in-Time数据提供者
5. **ExpressionProvider**: 表达式计算提供者
6. **DatasetProvider**: 数据集提供者

#### 实现方式
- **LocalProvider**: 本地文件系统
- **RemoteProvider**: 远程数据服务（Qlib-Server）

### 数据存储格式

#### 二进制格式
Qlib使用自定义的紧凑二进制格式存储数据：
- 高效的数组组合
- 减少格式转换开销
- 优化的磁盘I/O

#### PIT记录类型
```python
pit_record_type = {
    "date": "I",      # uint32
    "period": "I",    # uint32
    "value": "d",     # float64
    "index": "I",     # uint32
}
```

### 缓存系统

#### 多层缓存架构
1. **内存缓存**
   - 大小限制: 500 (可配置)
   - 限制类型: length/size
   - 过期时间: 3600秒 (1小时)

2. **磁盘缓存**
   - ExpressionCache: 表达式计算结果缓存
   - DatasetCache: 数据集缓存
   - SimpleDatasetCache: 简单数据集缓存

3. **Redis缓存**
   - 分布式缓存支持
   - 用于Server模式
   - 支持多客户端共享

#### 缓存目录
- dataset_cache: 数据集缓存目录
- features_cache: 特征缓存目录
- 默认路径: `~/.cache/qlib_simple_cache`

## 计算架构

### 并行计算

#### 多进程支持
- 默认核心数: `max(cpu_count - 2, 1)`
- 可配置的kernels参数
- 支持频率相关的核心数配置

#### 任务分配
- maxtasksperchild: 每个进程的最大任务数
- 高频数据推荐设置为1
- 日线数据推荐设置为None

#### Joblib后端
- 默认: multiprocessing
- 可选: loky
- 支持自定义后端

### 表达式计算

#### 自定义算子
支持用户自定义算子扩展：
```python
custom_ops = [
    # Type[ExpressionOps] 或
    {
        "class": "CustomOp",
        "module_path": "path.to.module"
    }
]
```

#### 内置算子
- 技术指标算子
- 统计算子
- 时间序列算子
- 滚动窗口算子

## 工作流架构

### 实验管理

#### MLflow集成
```python
exp_manager = {
    "class": "MLflowExpManager",
    "module_path": "qlib.workflow.expm",
    "kwargs": {
        "uri": "file:./mlruns",
        "default_exp_name": "Experiment"
    }
}
```

#### 记录器 (Recorder)
- QlibRecorder: 实验记录器
- 自动记录实验参数、指标、模型
- 支持实验对比和分析

#### 实验退出处理
- 自动清理资源
- 保存实验状态
- 异常处理

### 任务管理

#### MongoDB支持
```python
mongo = {
    "task_url": "mongodb://localhost:27017/",
    "task_db_name": "default_task_db"
}
```

#### 任务调度
- 分布式任务执行
- 任务状态跟踪
- 失败重试机制

## 日志系统

### 日志配置

#### 格式化器
```
[进程ID:线程名](时间戳) 日志级别 - 模块名 - [文件名:行号] - 消息
```

#### 过滤器
- field_not_found: 过滤数据未找到警告
- 支持正则表达式过滤

#### 处理器
- Console Handler: 控制台输出
- 支持自定义Handler

#### 日志级别
- DEBUG
- INFO (默认)
- WARNING
- ERROR
- CRITICAL

### 模块化日志
每个模块有独立的logger：
- qlib.data
- qlib.model
- qlib.workflow
- qlib.backtest
- 等等

## 回测系统

### 时间处理

#### 分钟数据偏移
```python
min_data_shift = 0  # 默认不偏移
# 市场时间: [9:30, 11:29, 1:00, 2:59]
# 偏移后: [9:30, 11:29, 1:00, 2:59] - shift*minute
```

#### 时间常量
```python
ONE_DAY = pd.Timedelta("1day")
ONE_MIN = pd.Timedelta("1min")
EPS_T = pd.Timedelta("1s")  # 排除右区间点
```

### 交易规则

#### 区域特定规则
- **交易单位** (trade_unit)
  - CN: 100股 (1手)
  - US: 1股
  - TW: 1000股

- **涨跌停限制** (limit_threshold)
  - CN: 9.5%
  - US: None
  - TW: 10%

- **成交价格** (deal_price)
  - 默认使用收盘价

## 性能优化

### 数据访问优化

#### 缓存策略
1. 优先使用内存缓存
2. 内存不足时使用磁盘缓存
3. 分布式场景使用Redis缓存

#### 预加载机制
- 数据预取
- 批量加载
- 异步I/O

### 计算优化

#### 向量化计算
- 使用NumPy进行向量化操作
- 避免Python循环
- 利用Pandas优化

#### 并行化
- 多进程并行计算
- 任务级并行
- 数据级并行

### 内存管理

#### 内存限制
```python
mem_cache_size_limit = 500
mem_cache_limit_type = "length"  # 或 "size"
```

#### 垃圾回收
- 自动清理过期缓存
- 手动清理接口: `H.clear()`

## 扩展性设计

### 插件系统

#### 自定义组件
- 自定义数据提供者
- 自定义模型
- 自定义策略
- 自定义执行器

#### 注册机制
```python
# 注册自定义算子
register_all_ops(config)

# 注册数据包装器
register_all_wrappers(config)
```

### 模块化设计

#### 松耦合架构
- 各模块独立开发
- 接口标准化
- 易于替换和扩展

#### 依赖注入
- 配置驱动
- 动态实例化
- 灵活组合

## 安全性

### 数据安全

#### 访问控制
- 路径验证
- URI格式检查
- 权限管理

#### 数据隔离
- 多租户支持
- 数据分区
- 访问日志

### 代码安全

#### 输入验证
- 正则表达式验证
- 类型检查
- 范围检查

#### 异常处理
- 完善的错误处理
- 异常日志记录
- 优雅降级

## 跨平台支持

### 操作系统适配

#### Windows
- 驱动器路径处理
- NFS挂载支持
- 路径分隔符处理

#### Linux/Unix
- NFS自动挂载
- 权限管理
- 依赖检查 (nfs-common)

#### MacOS
- M1芯片支持
- OpenMP依赖处理
- 路径解析

### 平台检测
```python
sys_type = platform.system()
# 'Windows', 'Linux', 'Darwin'
```

## 版本管理

### 版本控制
使用setuptools-scm进行版本管理：
- 基于Git标签
- 自动版本号生成
- 开发版本标识

### 版本重置
支持连接旧版本服务器：
```python
qlib_reset_version = "0.8.0"
```

## 协议与序列化

### Pickle协议
```python
PROTOCOL_VERSION = 4
dump_protocol_version = 4
```

### 数据序列化
- 高效的二进制序列化
- 跨平台兼容性
- 版本兼容性

## 常量定义

### 数值常量
```python
EPS = 1e-12      # 避免除零
INF = int(1e18)  # 整数无穷大
```

### 类型定义
```python
float_or_ndarray = TypeVar("float_or_ndarray", float, np.ndarray)
```

## 最佳实践

### 配置建议
1. 生产环境使用Server模式
2. 研究环境使用Client模式
3. 高频数据使用专用配置
4. 启用适当的缓存策略

### 性能调优
1. 根据数据频率调整kernels
2. 合理设置缓存大小
3. 使用Redis提升分布式性能
4. 启用表达式缓存

### 开发建议
1. 使用配置文件管理参数
2. 利用日志系统调试
3. 遵循模块化设计原则
4. 编写单元测试

---

**文档版本**: 1.0
**生成时间**: 2026-02-27
**适用版本**: Qlib 主分支
