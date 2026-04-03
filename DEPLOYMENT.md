# 部署文档

## 环境要求

- Python 3.10+
- 网络访问 OpenAI API (或代理)

## 部署步骤

### 1. 克隆项目

```bash
git clone <repository_url>
cd food_recall
```

### 2. 创建虚拟环境 (推荐)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate   # Windows
```

### 3. 安装依赖

```bash
pip install -e .
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# LLM 配置
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=  # 可选，用于代理或自定义端点
LLM_TEMPERATURE=0.7

# 召回配置
MAX_CANDIDATES=60
LOWER_EXPAND=150
UPPER_EXPAND=100

# 核验配置
MAX_CONCURRENCY=20
VALIDATION_TIMEOUT_MS=3000

# 路由配置
FALLBACK_THRESHOLD=1
FALLBACK_RATIO=0.5
FALLBACK_MIN_MATCH=2

# 生成配置
TOP_K=5
```

### 5. 验证安装

```bash
python scripts/benchmark_validation.py
```

### 6. 启动服务

#### Web 服务 (端口 8000)

```bash
python scripts/web_server.py
```

服务地址: `http://localhost:8000`

#### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | Web 界面 |
| POST | `/api/recommend` | 推荐接口 |
| GET | `/api/health` | 健康检查 |

#### 请求示例

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_input": "我要一份带鸡腿的 700 大卡左右的套餐"}'
```

## 生产环境部署

### 使用 Gunicorn (异步支持)

```bash
pip install gunicorn
gunicorn -w 1 -k uvicorn.workers.UvicornWorker scripts.web_server:app
```

### 使用 Docker (可选)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8000
CMD ["python", "scripts/web_server.py"]
```

### Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 性能调优

### 并发数配置

`MAX_CONCURRENCY` 控制异步核验的并发数，默认 20。

```env
MAX_CONCURRENCY=20
```

### 超时配置

`VALIDATION_TIMEOUT_MS` 控制核验阶段超时，默认 3000ms。

```env
VALIDATION_TIMEOUT_MS=5000
```

### 日志管理

日志自动保存在 `logs/` 目录，支持日志轮转。

查看日志：

```bash
tail -f logs/food_recall_$(date +%Y%m%d).log
```

## 监控

### 健康检查

```bash
curl http://localhost:8000/api/health
```

### 耗时统计

日志中包含各阶段耗时统计：

```
【耗时汇总】
  extract_calorie: 1.348s
  calculate_range: 0.000s
  sql_recall: 0.000s
  extract_demands: 1.771s
  validate_batch: 2.279s
  route_decision: 0.000s
  generate_response: 3.667s
  总耗时: 9.073s
```

## 故障排查

### LLM 调用失败

1. 检查 `LLM_API_KEY` 是否正确
2. 检查网络连接
3. 查看日志中的错误信息

### 核验超时

1. 增加 `VALIDATION_TIMEOUT_MS`
2. 减少 `MAX_CONCURRENCY`
3. 检查 LLM 响应时间

### 内存问题

如果候选套餐数量很大 (>1000)，考虑：
1. 减少 `MAX_CANDIDATES`
2. 增加 `VALIDATION_TIMEOUT_MS`
