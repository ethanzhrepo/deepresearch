# DeepResearch API 参考文档

## 📋 API 概览

DeepResearch 提供完整的 REST API 和 Python SDK，支持程序化访问所有功能。

## 🚀 快速开始

### Python SDK

```python
from deepresearch import DeepResearchClient

# 初始化客户端
client = DeepResearchClient(
    api_key="your-api-key",
    base_url="http://localhost:8000"
)

# 创建研究任务
research = client.research.create(
    topic="人工智能发展趋势",
    mode="interactive",
    provider="openai"
)

# 获取结果
result = client.research.get(research.id)
print(result.content)
```

### REST API

```bash
# 创建研究任务
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "人工智能发展趋势",
    "mode": "auto",
    "provider": "openai",
    "max_sections": 5
  }'
```

## 🔧 核心 API

### 研究 API

#### 创建研究任务

**POST** `/api/v1/research`

```json
{
  "topic": "研究主题",
  "mode": "interactive|auto",
  "provider": "openai|claude|gemini|ollama",
  "max_sections": 5,
  "template": "default|academic|business",
  "language": "zh-CN|en-US",
  "output_format": "markdown|json|pdf"
}
```

**响应：**
```json
{
  "id": "research_123456",
  "status": "created",
  "topic": "研究主题",
  "created_at": "2024-01-01T00:00:00Z",
  "estimated_duration": 300
}
```

#### 获取研究状态

**GET** `/api/v1/research/{research_id}`

**响应：**
```json
{
  "id": "research_123456",
  "status": "processing|completed|failed",
  "progress": 75,
  "current_step": "content_generation",
  "estimated_remaining": 60,
  "result_url": "/api/v1/research/research_123456/result"
}
```

#### 获取研究结果

**GET** `/api/v1/research/{research_id}/result`

**响应：**
```json
{
  "id": "research_123456",
  "topic": "研究主题",
  "content": "# 研究报告\n\n...",
  "outline": {
    "sections": [...]
  },
  "metadata": {
    "word_count": 5000,
    "generation_time": 180,
    "quality_score": 0.85
  },
  "references": [...]
}
```

#### 流式获取研究进度

**WebSocket** `/api/v1/research/{research_id}/stream`

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/research/123456/stream');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Progress:', data.progress);
  console.log('Current step:', data.current_step);
};
```

### 配置 API

#### 获取系统配置

**GET** `/api/v1/config`

**响应：**
```json
{
  "llm_providers": ["openai", "claude", "gemini"],
  "search_engines": ["google", "bing", "serpapi"],
  "supported_languages": ["zh-CN", "en-US"],
  "max_concurrent_requests": 5,
  "default_provider": "openai"
}
```

#### 验证 API 密钥

**POST** `/api/v1/config/validate`

```json
{
  "provider": "openai",
  "api_key": "sk-..."
}
```

**响应：**
```json
{
  "valid": true,
  "provider": "openai",
  "model_access": ["gpt-4", "gpt-3.5-turbo"],
  "quota_remaining": 1000000
}
```

### 工具 API

#### 执行代码

**POST** `/api/v1/tools/code/execute`

```json
{
  "code": "import pandas as pd\nprint('Hello World')",
  "language": "python",
  "timeout": 30
}
```

**响应：**
```json
{
  "success": true,
  "output": "Hello World\n",
  "execution_time": 0.5,
  "memory_usage": 1024
}
```

#### 搜索信息

**POST** `/api/v1/tools/search`

```json
{
  "query": "人工智能发展趋势",
  "engine": "google",
  "max_results": 10
}
```

**响应：**
```json
{
  "results": [
    {
      "title": "标题",
      "url": "https://example.com",
      "snippet": "摘要",
      "relevance_score": 0.95
    }
  ],
  "total_results": 10,
  "search_time": 1.2
}
```

#### 浏览网页

**POST** `/api/v1/tools/browser/extract`

```json
{
  "url": "https://example.com",
  "extract_text": true,
  "extract_images": false,
  "wait_for": "body"
}
```

**响应：**
```json
{
  "success": true,
  "content": "网页文本内容",
  "title": "网页标题",
  "meta": {
    "description": "网页描述",
    "keywords": ["关键词1", "关键词2"]
  }
}
```

## 🐍 Python SDK

### 安装

```bash
pip install deepresearch-sdk
```

### 基本使用

```python
from deepresearch import DeepResearchClient

# 初始化客户端
client = DeepResearchClient(
    api_key="your-api-key",
    base_url="http://localhost:8000"
)

# 同步研究
result = client.research.create_and_wait(
    topic="人工智能在医疗领域的应用",
    provider="claude",
    max_sections=6
)

print(result.content)
```

### 异步使用

```python
import asyncio
from deepresearch import AsyncDeepResearchClient

async def main():
    client = AsyncDeepResearchClient(
        api_key="your-api-key",
        base_url="http://localhost:8000"
    )
    
    # 创建研究任务
    research = await client.research.create(
        topic="区块链技术发展趋势",
        mode="auto"
    )
    
    # 监听进度
    async for progress in client.research.stream_progress(research.id):
        print(f"进度: {progress.percentage}%")
        print(f"当前步骤: {progress.current_step}")
    
    # 获取结果
    result = await client.research.get_result(research.id)
    return result

result = asyncio.run(main())
```

### 批量处理

```python
from deepresearch import DeepResearchClient

client = DeepResearchClient(api_key="your-api-key")

# 批量创建研究任务
topics = [
    "人工智能伦理问题",
    "量子计算商业应用",
    "可持续能源技术"
]

# 并行处理
research_tasks = []
for topic in topics:
    task = client.research.create(topic=topic, mode="auto")
    research_tasks.append(task)

# 等待所有任务完成
results = client.research.wait_for_completion(research_tasks)

for result in results:
    print(f"主题: {result.topic}")
    print(f"状态: {result.status}")
    print(f"内容长度: {len(result.content)}")
```

## 🔧 工具 SDK

### 代码执行工具

```python
from deepresearch.tools import CodeTool

code_tool = CodeTool(client)

# 执行 Python 代码
result = code_tool.execute("""
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title('正弦函数')
plt.savefig('sin_wave.png')
plt.show()
""")

print(result.output)
print(f"执行时间: {result.execution_time}s")
```

### 搜索工具

```python
from deepresearch.tools import SearchTool

search_tool = SearchTool(client)

# 多引擎搜索
results = search_tool.search(
    query="人工智能发展趋势",
    engines=["google", "bing"],
    max_results=20
)

for result in results:
    print(f"标题: {result.title}")
    print(f"URL: {result.url}")
    print(f"相关性: {result.relevance_score}")
```

### 浏览器工具

```python
from deepresearch.tools import BrowserTool

browser_tool = BrowserTool(client)

# 提取网页内容
content = browser_tool.extract_content(
    url="https://example.com",
    wait_for="body",
    extract_images=True
)

print(content.text)
print(f"图片数量: {len(content.images)}")
```

## 📊 监控和分析 API

### 获取系统状态

**GET** `/api/v1/system/status`

**响应：**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 86400,
  "active_research_tasks": 5,
  "queue_length": 2,
  "system_load": {
    "cpu": 45.2,
    "memory": 68.5,
    "disk": 23.1
  }
}
```

### 获取使用统计

**GET** `/api/v1/analytics/usage`

**响应：**
```json
{
  "total_research_tasks": 1250,
  "completed_tasks": 1200,
  "failed_tasks": 50,
  "average_completion_time": 180,
  "api_calls_today": 5000,
  "top_providers": [
    {"provider": "openai", "usage": 60},
    {"provider": "claude", "usage": 30},
    {"provider": "gemini", "usage": 10}
  ]
}
```

### 获取性能指标

**GET** `/api/v1/analytics/performance`

**响应：**
```json
{
  "response_times": {
    "p50": 120,
    "p95": 300,
    "p99": 500
  },
  "throughput": {
    "requests_per_minute": 50,
    "tasks_per_hour": 20
  },
  "error_rates": {
    "api_errors": 0.1,
    "llm_errors": 0.5,
    "tool_errors": 0.2
  }
}
```

## 🔒 认证和安全

### API 密钥认证

```bash
# 在请求头中包含 API 密钥
curl -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     "http://localhost:8000/api/v1/research"
```

### JWT 令牌认证

```bash
# 获取 JWT 令牌
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# 使用 JWT 令牌
curl -H "Authorization: Bearer jwt-token" \
     "http://localhost:8000/api/v1/research"
```

### 权限控制

```python
from deepresearch import DeepResearchClient

# 使用受限权限的客户端
client = DeepResearchClient(
    api_key="limited-api-key",
    permissions=["research:read", "research:create"]
)

# 检查权限
if client.has_permission("research:create"):
    research = client.research.create(topic="主题")
```

## 📝 错误处理

### 错误响应格式

```json
{
  "error": {
    "code": "INVALID_API_KEY",
    "message": "提供的 API 密钥无效",
    "details": {
      "provider": "openai",
      "suggestion": "请检查 API 密钥格式"
    }
  },
  "request_id": "req_123456",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 常见错误代码

| 错误代码 | HTTP 状态 | 描述 |
|---------|----------|------|
| `INVALID_API_KEY` | 401 | API 密钥无效 |
| `QUOTA_EXCEEDED` | 429 | 配额超限 |
| `INVALID_REQUEST` | 400 | 请求参数无效 |
| `RESOURCE_NOT_FOUND` | 404 | 资源不存在 |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |

### Python SDK 错误处理

```python
from deepresearch import DeepResearchClient
from deepresearch.exceptions import (
    APIKeyError,
    QuotaExceededError,
    InvalidRequestError
)

client = DeepResearchClient(api_key="your-api-key")

try:
    research = client.research.create(topic="主题")
except APIKeyError:
    print("API 密钥无效，请检查配置")
except QuotaExceededError:
    print("配额已用完，请稍后重试")
except InvalidRequestError as e:
    print(f"请求参数错误: {e.message}")
```

## 🔄 Webhooks

### 配置 Webhook

**POST** `/api/v1/webhooks`

```json
{
  "url": "https://your-app.com/webhook",
  "events": ["research.completed", "research.failed"],
  "secret": "webhook-secret"
}
```

### Webhook 事件

#### 研究完成事件

```json
{
  "event": "research.completed",
  "data": {
    "research_id": "research_123456",
    "topic": "研究主题",
    "status": "completed",
    "result_url": "/api/v1/research/research_123456/result"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 研究失败事件

```json
{
  "event": "research.failed",
  "data": {
    "research_id": "research_123456",
    "topic": "研究主题",
    "error": {
      "code": "LLM_ERROR",
      "message": "LLM 服务不可用"
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 📚 示例和教程

### 完整示例：学术研究

```python
from deepresearch import DeepResearchClient

# 初始化客户端
client = DeepResearchClient(api_key="your-api-key")

# 创建学术研究
research = client.research.create(
    topic="深度学习在医学影像诊断中的应用",
    mode="interactive",
    provider="claude",
    template="academic",
    max_sections=8,
    language="zh-CN"
)

# 监听进度
for progress in client.research.stream_progress(research.id):
    print(f"进度: {progress.percentage}%")
    
    # 处理用户交互
    if progress.requires_interaction:
        if progress.interaction_type == "outline_confirmation":
            # 确认提纲
            client.research.confirm_outline(
                research.id,
                action="confirm"
            )

# 获取结果
result = client.research.get_result(research.id)

# 导出为 PDF
pdf_data = client.research.export(
    research.id,
    format="pdf",
    template="academic"
)

with open("research_report.pdf", "wb") as f:
    f.write(pdf_data)
```

### 批量商业分析

```python
import asyncio
from deepresearch import AsyncDeepResearchClient

async def analyze_markets():
    client = AsyncDeepResearchClient(api_key="your-api-key")
    
    markets = [
        "电动汽车市场分析",
        "人工智能芯片市场趋势",
        "可再生能源投资前景"
    ]
    
    # 并行创建研究任务
    tasks = []
    for market in markets:
        task = await client.research.create(
            topic=market,
            mode="auto",
            template="business",
            provider="openai"
        )
        tasks.append(task)
    
    # 等待所有任务完成
    results = await client.research.wait_for_all(
        [task.id for task in tasks]
    )
    
    # 生成综合报告
    combined_report = client.research.combine_reports(
        results,
        title="市场分析综合报告"
    )
    
    return combined_report

# 运行分析
report = asyncio.run(analyze_markets())
print(report.content)
```

---

**通过 API 集成，让 DeepResearch 成为您应用的智能研究引擎！** 🔌✨ 