# 餐品推荐系统 (food_recall)

基于 LangGraph 的智能餐品推荐工作流系统。

## 项目结构

```
food_recall/
├── src/food_recall/              # 核心代码
│   ├── __init__.py               # 包导出
│   ├── config.py                 # 配置管理
│   ├── llm.py                    # LLM 客户端
│   ├── logging_config.py         # 日志配置
│   ├── models.py                 # 数据模型
│   ├── state.py                  # LangGraph State 定义
│   ├── workflow.py               # 工作流定义
│   ├── nodes/                    # 工作流节点
│   │   ├── __init__.py
│   │   ├── recall.py             # 阶段一：粗排召回
│   │   ├── validation.py         # 阶段二：精排核验
│   │   ├── response.py           # 阶段三：决策生成
│   │   └── timing.py             # 耗时统计装饰器
│   └── prompts/                  # Prompt 模板
│       └── __init__.py
├── scripts/                      # 脚本
│   ├── web_server.py             # Web 服务
│   ├── benchmark_validation.py    # 性能测试
│   ├── debug_chicken_leg.py      # 调试脚本
│   └── templates/                # HTML 模板
├── tests/                        # 测试
├── logs/                         # 日志目录 (自动生成)
├── .env.example                  # 环境变量示例
├── pyproject.toml               # 项目配置
└── README.md                    # 项目文档
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- OpenAI API Key 或兼容 API

### 2. 安装依赖

```bash
pip install -e .
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 4. 运行测试

```bash
python scripts/benchmark_validation.py
```

### 5. 启动 Web 服务

```bash
python scripts/web_server.py
```

## 工作流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────────┐
│ 阶段一：粗排召回                          │
│ extract_calorie → calculate_range       │
│ → sql_recall                            │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 阶段二：精排核验                          │
│ extract_demands → validate_batch        │
│ (异步并发核验每个候选套餐)                  │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 阶段三：决策生成                          │
│ route_decision → generate_response       │
└─────────────────────────────────────────┘
    │
    ▼
  最终响应
```

## 配置说明

所有配置通过环境变量设置，复制 `.env.example` 为 `.env` 后填入值。

### LLM 配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_PROVIDER` | LLM 提供商 (openai/anthropic) | openai |
| `LLM_MODEL` | 模型名称 | gpt-4o-mini |
| `LLM_BASE_URL` | 自定义 API 地址（用于代理或兼容 API） | - |
| `LLM_API_KEY` | API Key | - |
| `LLM_TEMPERATURE` | 生成温度（0.0-1.0） | 0.7 |

### 召回配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MAX_CANDIDATES` | SQL 召回候选套餐上限 | 60 |
| `LOWER_EXPAND` | 热量下界扩展（目标热量 - LOWER_EXPAND） | 150 |
| `UPPER_EXPAND` | 热量上界扩展（目标热量 + UPPER_EXPAND） | 100 |

### 核验配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MAX_CONCURRENCY` | 异步核验最大并发数 | 20 |
| `VALIDATION_TIMEOUT_MS` | 核验阶段超时时间（毫秒） | 3000 |
| `VALIDATION_ENABLE_CACHE` | 是否启用核验结果缓存 | true |
| `VALIDATION_CACHE_TTL_SEC` | 缓存有效期（秒） | 300 |
| `VALIDATION_ALLOW_PARTIAL` | 是否允许部分匹配进入候选 | true |

### 路由配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FALLBACK_THRESHOLD` | 进入 fallback 的绝对阈值（满足几条需求） | 1 |
| `FALLBACK_RATIO` | 进入 fallback 的比例阈值（0.0-1.0） | 0.5 |
| `FALLBACK_MIN_MATCH` | fallback 最低匹配条数（确保至少满足几条） | 2 |

### 生成配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TOP_K` | 最终推荐的套餐数量 | 5 |

### 数据库配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_PATH` | 数据库路径（绝对路径或相对于项目根目录） | food_recall.db |

## 日志

日志保存在 `logs/` 目录，按日期分片：

```
logs/food_recall_20260403.log
```

查看实时日志：

```bash
tail -f logs/food_recall_$(date +%Y%m%d).log
```
