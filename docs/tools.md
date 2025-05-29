# DeepResearch 工具系统

## 🛠️ 工具概览

DeepResearch 拥有强大的工具系统，支持代码执行、网页浏览、文件操作、数据分析、智能浏览器自动化等多种功能。

## 🔧 核心工具

### 1. 代码执行工具 (CodeTool)

**功能：** 安全执行 Python 代码，支持数据分析、可视化等任务

**配置：**
```yaml
tools:
  code_tool:
    enabled: true
    execution_environment: "docker"  # docker, local, sandbox
    timeout: 30
    max_memory_mb: 512
    allowed_packages:
      - "numpy"
      - "pandas"
      - "matplotlib"
      - "seaborn"
      - "scikit-learn"
```

**使用示例：**
```python
# 数据分析代码
import pandas as pd
import matplotlib.pyplot as plt

# 创建示例数据
data = {'年份': [2020, 2021, 2022, 2023], 
        '用户数': [100, 250, 500, 800]}
df = pd.DataFrame(data)

# 绘制图表
plt.figure(figsize=(10, 6))
plt.plot(df['年份'], df['用户数'], marker='o')
plt.title('用户增长趋势')
plt.xlabel('年份')
plt.ylabel('用户数（万）')
plt.grid(True)
plt.show()
```

### 2. Browser-Use 工具 ⭐ **全新功能**

**功能：** AI 驱动的智能浏览器自动化，支持复杂的网页操作任务

**配置：**
```yaml
tools:
  browser_use_tool:
    enabled: true
    llm_provider: "deepseek"  # openai, claude, gemini, deepseek
    llm_model: "deepseek-chat"
    browser:
      headless: true
      timeout: 300
      max_steps: 50
    features:
      search_and_extract: true
      form_filling: true
      custom_tasks: true
      screenshots: true
```

**核心功能：**

#### 搜索和提取
```python
# 搜索和内容提取
task_config = {
    "search_query": "人工智能最新发展",
    "target_websites": ["arxiv.org", "scholar.google.com"],
    "extract_elements": ["title", "abstract", "authors"],
    "max_pages": 5
}

result = await browser_tool.search_and_extract(task_config)
```

#### 表单填写
```python
# 智能表单填写
form_config = {
    "url": "https://example.com/contact",
    "form_data": {
        "name": "研究助手",
        "email": "research@example.com",
        "message": "自动化研究查询"
    },
    "submit": True
}

result = await browser_tool.fill_form(form_config)
```

#### 自定义任务
```python
# 复杂自定义任务
custom_task = {
    "task_description": "在GitHub上搜索Python机器学习项目，提取项目信息",
    "steps": [
        {"action": "navigate", "url": "https://github.com"},
        {"action": "search", "query": "python machine learning"},
        {"action": "extract", "selector": ".repo-list-item", "limit": 10}
    ]
}

result = await browser_tool.execute_custom_task(custom_task)
```

### 3. 传统浏览器工具 (BrowserTool)

**功能：** 基础的网页浏览、数据抓取、截图等

**配置：**
```yaml
tools:
  browser_tool:
    enabled: true
    headless: true
    timeout: 30
    max_pages: 10
    options:
      window_size: "1920x1080"
      user_agent: "DeepResearch Bot 1.0"
```

**使用示例：**
```json
{
  "action": "navigate",
  "url": "https://example.com",
  "wait_for": "body"
}

{
  "action": "extract_text",
  "selector": ".content",
  "attribute": "text"
}

{
  "action": "screenshot",
  "filename": "page_screenshot.png"
}
```

### 4. 智能搜索工具 (SearchTool)

**功能：** 多搜索引擎集成，智能搜索策略

**支持的搜索引擎：**
- **Tavily Search** ⭐ 专为 AI 应用设计的专业搜索
- **DuckDuckGo** - 注重隐私的免费搜索
- **ArXiv** ⭐ 专业学术论文搜索
- **Google Search** - 通过 SerpAPI 集成
- **Bing Search** - 微软必应搜索
- **Brave Search** ⭐ 注重隐私的独立搜索
- **Google Docs** ⭐ 专门的文档搜索
- **Authority Sites** ⭐ 权威网站搜索

**配置：**
```yaml
search:
  default_engine: tavily  # 推荐使用 Tavily
  engines:
    tavily:
      enabled: true
      include_answer: true
      include_raw_content: false
    duckduckgo:
      enabled: true
      region: cn-zh
      safe_search: moderate
    arxiv:
      enabled: true
      max_results: 10
      sort_by: "relevance"
    google:
      enabled: false  # 需要 SerpAPI
    bing:
      enabled: false  # 需要 Bing API
    brave:
      enabled: false  # 需要 Brave API
```

**搜索策略：**
- **智能策略**: 根据查询类型自动选择最佳搜索引擎
- **轮询策略**: 依次使用不同搜索引擎
- **优先级策略**: 按配置的优先级选择
- **多引擎对比**: 同时使用多个搜索引擎并对比结果

**使用示例：**
```python
# 基础搜索
results = search_tool.search("人工智能发展趋势", max_results=10)

# 指定搜索引擎
results = search_tool.search("machine learning", engine="arxiv")

# 多引擎搜索
multi_results = search_tool.search_multiple_engines(
    "quantum computing",
    engines=["tavily", "arxiv", "google"]
)

# 学术论文搜索
papers = search_tool.search("deep learning", engine="arxiv", max_results=20)
```

### 5. 文件工具 (FileTool)

**功能：** 本地文件和云存储操作

**配置：**
```yaml
tools:
  file_tool:
    enabled: true
    allowed_extensions:
      - ".txt"
      - ".md"
      - ".json"
      - ".csv"
      - ".pdf"
    max_file_size_mb: 10
    cloud_storage:
      google_drive: true
      dropbox: true
```

**支持操作：**
- 读取本地文件
- 写入文件
- Google Drive 集成
- Dropbox 集成
- PDF 文档解析

## 🔍 专业分析工具

### 数据分析工具

**统计分析：**
```python
def statistical_analysis(data):
    """统计分析功能"""
    import pandas as pd
    import numpy as np
    
    # 基础统计
    stats = {
        'count': len(data),
        'mean': np.mean(data),
        'median': np.median(data),
        'std': np.std(data),
        'min': np.min(data),
        'max': np.max(data)
    }
    
    return stats
```

**内容分析：**
```python
def content_analysis(text_data):
    """内容分析功能"""
    from collections import Counter
    import re
    
    # 词频分析
    words = re.findall(r'\w+', text_data.lower())
    word_freq = Counter(words)
    
    # 关键词提取
    keywords = word_freq.most_common(10)
    
    return {
        'word_count': len(words),
        'unique_words': len(word_freq),
        'keywords': keywords
    }
```

**趋势分析：**
```python
def trend_analysis(time_series_data):
    """趋势分析功能"""
    import pandas as pd
    from scipy import stats
    
    # 线性趋势
    x = range(len(time_series_data))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, time_series_data)
    
    return {
        'trend_slope': slope,
        'correlation': r_value,
        'p_value': p_value,
        'trend_direction': 'increasing' if slope > 0 else 'decreasing'
    }
```

### 可视化工具

**图表生成：**
```python
def create_visualization(data, chart_type='line'):
    """创建可视化图表"""
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    plt.figure(figsize=(12, 8))
    
    if chart_type == 'line':
        plt.plot(data['x'], data['y'])
    elif chart_type == 'bar':
        plt.bar(data['x'], data['y'])
    elif chart_type == 'scatter':
        plt.scatter(data['x'], data['y'])
    elif chart_type == 'heatmap':
        sns.heatmap(data, annot=True)
    
    plt.title('数据可视化')
    plt.xlabel('X轴')
    plt.ylabel('Y轴')
    plt.grid(True)
    plt.show()
```

## 🔒 安全机制

### 代码执行安全

**Docker 沙箱（推荐）：**
```yaml
tools:
  code_tool:
    execution_environment: "docker"
    docker_config:
      image: "python:3.11-slim"
      memory_limit: "512m"
      cpu_limit: "0.5"
      network_mode: "none"
      read_only: true
```

**本地沙箱：**
```yaml
tools:
  code_tool:
    execution_environment: "sandbox"
    sandbox_config:
      restricted_imports: true
      no_file_access: true
      no_network_access: true
      timeout: 30
```

### 网络访问控制

**浏览器安全：**
```yaml
tools:
  browser_tool:
    security:
      allowed_domains:
        - "*.wikipedia.org"
        - "*.github.com"
        - "*.stackoverflow.com"
      blocked_domains:
        - "*.malicious-site.com"
      max_redirects: 5
```

## 🚀 工具扩展

### 自定义工具开发

**创建自定义工具：**
```python
from tools.base_tool import BaseTool
from typing import Dict, Any

class CustomAnalysisTool(BaseTool):
    """自定义分析工具"""
    
    name = "custom_analysis"
    description = "执行自定义数据分析"
    
    def _run(self, data: str, analysis_type: str) -> str:
        """执行分析"""
        if analysis_type == "sentiment":
            return self._sentiment_analysis(data)
        elif analysis_type == "keyword":
            return self._keyword_extraction(data)
        else:
            return "不支持的分析类型"
    
    def _sentiment_analysis(self, text: str) -> str:
        """情感分析"""
        # 实现情感分析逻辑
        pass
    
    def _keyword_extraction(self, text: str) -> str:
        """关键词提取"""
        # 实现关键词提取逻辑
        pass
```

**注册自定义工具：**
```python
from tools.registry import ToolRegistry

# 注册工具
registry = ToolRegistry()
registry.register_tool(CustomAnalysisTool())

# 在 Agent 中使用
tools = registry.get_tools(['custom_analysis'])
```

### 工具组合

**创建工具链：**
```python
class ResearchToolChain:
    """研究工具链"""
    
    def __init__(self):
        self.search_tool = SearchTool()
        self.browser_tool = BrowserTool()
        self.analysis_tool = AnalysisTool()
    
    async def research_workflow(self, topic: str):
        """完整研究流程"""
        # 1. 搜索相关信息
        search_results = await self.search_tool.search(topic)
        
        # 2. 浏览详细页面
        detailed_info = []
        for result in search_results[:5]:
            content = await self.browser_tool.extract_content(result.url)
            detailed_info.append(content)
        
        # 3. 分析数据
        analysis = await self.analysis_tool.analyze(detailed_info)
        
        return analysis
```

## 📊 工具监控

### 性能监控

**工具使用统计：**
```python
class ToolMonitor:
    """工具监控器"""
    
    def __init__(self):
        self.usage_stats = {}
        self.performance_metrics = {}
    
    def track_tool_usage(self, tool_name: str, execution_time: float):
        """跟踪工具使用"""
        if tool_name not in self.usage_stats:
            self.usage_stats[tool_name] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0
            }
        
        stats = self.usage_stats[tool_name]
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['count']
    
    def get_performance_report(self):
        """获取性能报告"""
        return {
            'usage_stats': self.usage_stats,
            'top_used_tools': sorted(
                self.usage_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:5]
        }
```

### 错误处理

**工具错误恢复：**
```python
class ToolErrorHandler:
    """工具错误处理器"""
    
    def __init__(self):
        self.retry_strategies = {
            'network_error': self._network_retry,
            'timeout_error': self._timeout_retry,
            'resource_error': self._resource_retry
        }
    
    async def handle_tool_error(self, tool, error, context):
        """处理工具错误"""
        error_type = self._classify_error(error)
        
        if error_type in self.retry_strategies:
            return await self.retry_strategies[error_type](tool, context)
        else:
            return self._fallback_strategy(tool, context)
    
    def _classify_error(self, error):
        """分类错误类型"""
        if "network" in str(error).lower():
            return "network_error"
        elif "timeout" in str(error).lower():
            return "timeout_error"
        elif "memory" in str(error).lower():
            return "resource_error"
        else:
            return "unknown_error"
```

## 🎯 最佳实践

### 1. 工具选择策略

```python
def select_optimal_tool(task_type: str, context: Dict[str, Any]):
    """选择最优工具"""
    if task_type == "data_analysis":
        if context.get('data_size', 0) > 1000000:
            return "distributed_analysis_tool"
        else:
            return "standard_analysis_tool"
    
    elif task_type == "web_scraping":
        if context.get('javascript_required', False):
            return "browser_tool"
        else:
            return "http_tool"
    
    elif task_type == "text_processing":
        if context.get('language') != 'en':
            return "multilingual_nlp_tool"
        else:
            return "standard_nlp_tool"
```

### 2. 资源管理

```python
class ToolResourceManager:
    """工具资源管理器"""
    
    def __init__(self):
        self.resource_pools = {}
        self.usage_limits = {
            'browser_tool': 5,  # 最多5个浏览器实例
            'code_tool': 3,     # 最多3个代码执行环境
        }
    
    async def acquire_tool_resource(self, tool_name: str):
        """获取工具资源"""
        if tool_name not in self.resource_pools:
            self.resource_pools[tool_name] = asyncio.Semaphore(
                self.usage_limits.get(tool_name, 10)
            )
        
        return await self.resource_pools[tool_name].acquire()
```

### 3. 缓存策略

```python
class ToolCache:
    """工具缓存系统"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = {
            'search_results': 3600,    # 搜索结果缓存1小时
            'web_content': 1800,       # 网页内容缓存30分钟
            'analysis_results': 7200,  # 分析结果缓存2小时
        }
    
    def get_cached_result(self, tool_name: str, input_hash: str):
        """获取缓存结果"""
        cache_key = f"{tool_name}:{input_hash}"
        
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            ttl = self.cache_ttl.get(tool_name, 3600)
            
            if time.time() - timestamp < ttl:
                return result
            else:
                del self.cache[cache_key]
        
        return None
```

## 🔧 配置示例

### 完整工具配置

```yaml
tools:
  # 代码执行工具
  code_tool:
    enabled: true
    execution_environment: "docker"
    timeout: 60
    max_memory_mb: 1024
    allowed_packages:
      - "numpy"
      - "pandas"
      - "matplotlib"
      - "seaborn"
      - "scikit-learn"
      - "requests"
      - "beautifulsoup4"
    
  # 浏览器工具
  browser_tool:
    enabled: true
    headless: true
    timeout: 30
    max_pages: 20
    options:
      window_size: "1920x1080"
      user_agent: "DeepResearch Bot 2.0"
      disable_images: false
      disable_javascript: false
    
  # 搜索工具
  search_tool:
    enabled: true
    timeout: 30
    max_concurrent_searches: 5
    engines:
      google:
        priority: 1
        enabled: true
      bing:
        priority: 2
        enabled: true
      serpapi:
        priority: 3
        enabled: true
    
  # 文件工具
  file_tool:
    enabled: true
    allowed_extensions:
      - ".txt"
      - ".md"
      - ".json"
      - ".csv"
      - ".pdf"
      - ".docx"
    max_file_size_mb: 50
    
  # 分析工具
  analysis_tool:
    enabled: true
    analysis_types:
      - "statistical"
      - "content"
      - "trend"
      - "sentiment"
    max_data_points: 100000
```

## 🌐 BrowserUseTool - AI 驱动的浏览器自动化

### 概述

BrowserUseTool 集成了 [browser-use](https://github.com/browser-use/browser-use) 库，提供 AI 驱动的智能浏览器自动化功能。这个工具可以让 AI 代理像人类一样操作浏览器，执行复杂的网页交互任务。

### 核心特性

- **智能网页导航**: AI 自动理解页面结构并执行导航
- **表单自动填写**: 智能识别和填写各种表单
- **数据提取**: 从复杂网页中提取结构化数据
- **工作流自动化**: 执行多步骤的复杂浏览器操作
- **实时监控**: 监控网页变化并自动响应
- **多搜索引擎支持**: 在不同搜索引擎上执行智能搜索

### 配置

```yaml
tools:
  browser_use_tool:
    enabled: true
    llm_provider: openai  # 可选: openai, anthropic, google
    llm_model: gpt-4o
    browser:
      headless: true
      timeout: 300
      max_steps: 50
      save_screenshots: true
      extract_data: true
    output_dir: browser_outputs
    features:
      search_and_extract: true
      navigate_and_extract: true
      fill_form: true
      monitor_changes: true
      automate_workflow: true
      custom_task: true
    security:
      allowed_domains: []  # 空数组表示允许所有域名
      blocked_domains:
        - malicious-site.com
      max_execution_time: 600
      enable_content_filtering: true
```

### 主要功能

#### 1. 智能搜索和提取

```python
# 在多个搜索引擎上搜索并提取信息
result = browser_tool.execute(
    action="search_and_extract",
    query="人工智能在医疗诊断中的应用",
    search_engine="google"
)

print(f"搜索结果: {result['extracted_data']}")
```

#### 2. 网页导航和数据提取

```python
# 导航到指定网页并提取信息
result = browser_tool.execute(
    action="navigate_and_extract",
    url="https://example.com/research-paper",
    extraction_task="提取论文标题、作者、摘要和关键词"
)

print(f"提取的数据: {result['extracted_data']}")
```

#### 3. 表单自动填写

```python
# 自动填写表单
result = browser_tool.execute(
    action="fill_form",
    url="https://example.com/contact",
    form_data={
        "name": "研究员",
        "email": "researcher@example.com",
        "message": "请提供更多关于AI研究的信息"
    },
    submit=True
)

print(f"表单提交结果: {result['result']}")
```

#### 4. 页面监控

```python
# 监控页面变化
result = browser_tool.execute(
    action="monitor_changes",
    url="https://news.example.com",
    element_selector="新闻标题",
    check_interval=3600,  # 每小时检查一次
    max_checks=24  # 最多检查24次
)

print(f"监控设置: {result}")
```

#### 5. 复杂工作流自动化

```python
# 执行复杂的自动化工作流
workflow_steps = [
    {'action': 'navigate', 'target': 'https://scholar.google.com'},
    {'action': 'type', 'target': '搜索框', 'value': 'machine learning healthcare'},
    {'action': 'click', 'target': '搜索按钮'},
    {'action': 'wait', 'target': '搜索结果'},
    {'action': 'extract', 'target': '前10个搜索结果的标题和链接'},
    {'action': 'click', 'target': '第一个搜索结果'},
    {'action': 'extract', 'target': '论文摘要和引用信息'}
]

result = browser_tool.execute(
    action="automate_workflow",
    workflow_steps=workflow_steps
)

print(f"工作流执行结果: {result}")
```

#### 6. 自定义任务

```python
# 执行自定义浏览器任务
result = browser_tool.execute(
    action="custom_task",
    task_description="""
    访问 GitHub 上的 browser-use 项目页面，
    提取项目描述、星标数、fork数、最新发布版本信息，
    并查看 README 文件中的安装说明。
    """,
    url="https://github.com/browser-use/browser-use",
    max_steps=30,
    headless=True,
    timeout=300
)

print(f"任务执行结果: {result}")
```

### 高级用例

#### 竞争对手分析

```python
async def competitive_analysis():
    """自动化竞争对手分析"""
    
    competitors = [
        'https://competitor1.com',
        'https://competitor2.com',
        'https://competitor3.com'
    ]
    
    analysis_results = []
    
    for competitor in competitors:
        # 分析每个竞争对手的网站
        workflow = [
            {'action': 'navigate', 'target': competitor},
            {'action': 'extract', 'target': '公司信息和产品介绍'},
            {'action': 'navigate', 'target': f'{competitor}/pricing'},
            {'action': 'extract', 'target': '价格信息'},
            {'action': 'navigate', 'target': f'{competitor}/about'},
            {'action': 'extract', 'target': '团队和公司背景'}
        ]
        
        result = browser_tool.execute(
            action="automate_workflow",
            workflow_steps=workflow
        )
        
        analysis_results.append({
            'competitor': competitor,
            'analysis': result
        })
    
    return analysis_results
```

#### 市场研究自动化

```python
async def market_research():
    """自动化市场研究"""
    
    research_sites = [
        'https://statista.com',
        'https://marketresearch.com',
        'https://gartner.com'
    ]
    
    market_data = []
    
    for site in research_sites:
        result = browser_tool.execute(
            action="custom_task",
            task_description=f"""
            在 {site} 上搜索人工智能市场数据，提取：
            1. 市场规模和增长预测
            2. 主要参与者和市场份额
            3. 趋势和预测
            4. 下载可用的报告
            """,
            url=site,
            max_steps=40
        )
        
        market_data.append({
            'source': site,
            'data': result
        })
    
    return market_data
```

#### 社交媒体监控

```python
async def social_media_monitoring():
    """社交媒体监控"""
    
    platforms = [
        {
            'url': 'https://twitter.com',
            'search_query': '#AI #healthcare',
            'monitor_task': '监控AI医疗相关的推文和讨论'
        },
        {
            'url': 'https://linkedin.com',
            'search_query': 'AI healthcare trends',
            'monitor_task': '监控LinkedIn上的AI医疗趋势讨论'
        }
    ]
    
    monitoring_results = []
    
    for platform in platforms:
        result = browser_tool.execute(
            action="monitor_changes",
            url=platform['url'],
            element_selector=platform['search_query'],
            check_interval=3600  # 每小时检查一次
        )
        
        monitoring_results.append({
            'platform': platform['url'],
            'monitoring_id': result.get('monitoring_id'),
            'status': result.get('status')
        })
    
    return monitoring_results
```

### 安全考虑

#### 域名限制

```yaml
security:
  allowed_domains:
    - "*.edu"
    - "*.gov"
    - "scholar.google.com"
    - "arxiv.org"
  blocked_domains:
    - "malicious-site.com"
    - "spam-site.org"
```

#### 内容过滤

```yaml
security:
  enable_content_filtering: true
  content_filters:
    - block_adult_content: true
    - block_malware_sites: true
    - block_phishing_sites: true
```

#### 执行限制

```yaml
security:
  max_execution_time: 600  # 最大执行时间（秒）
  max_pages_per_session: 50  # 每个会话最大页面数
  rate_limiting:
    requests_per_minute: 30
    concurrent_sessions: 3
```

### 错误处理

```python
try:
    result = browser_tool.execute(
        action="navigate_and_extract",
        url="https://example.com",
        extraction_task="提取页面主要内容"
    )
    
    if result['success']:
        print(f"提取成功: {result['extracted_data']}")
    else:
        print(f"提取失败: {result['error']}")
        
except Exception as e:
    print(f"工具执行异常: {e}")
```

### 性能优化

#### 缓存配置

```yaml
browser_use_tool:
  caching:
    enabled: true
    cache_duration: 3600  # 缓存1小时
    cache_size_limit: 100MB
```

#### 并发控制

```yaml
browser_use_tool:
  concurrency:
    max_concurrent_tasks: 3
    task_queue_size: 10
    timeout_per_task: 300
```

### 监控和日志

#### 执行日志

```python
# 启用详细日志
import logging
logging.getLogger('browser_use_tool').setLevel(logging.DEBUG)

# 查看执行步骤
result = browser_tool.execute(
    action="custom_task",
    task_description="执行复杂任务",
    verbose=True  # 启用详细输出
)

print(f"执行步骤: {result['steps_taken']}")
```

#### 性能监控

```python
# 获取性能指标
performance = browser_tool.get_performance_metrics()
print(f"平均执行时间: {performance['avg_execution_time']}")
print(f"成功率: {performance['success_rate']}")
print(f"资源使用: {performance['resource_usage']}")
```

### 最佳实践

1. **任务描述要清晰具体**
   ```python
   # 好的任务描述
   task = "访问GitHub项目页面，提取项目名称、描述、星标数和最新版本号"
   
   # 避免模糊的描述
   task = "获取一些项目信息"
   ```

2. **合理设置超时和步骤限制**
   ```python
   # 根据任务复杂度调整参数
   simple_task = {'max_steps': 10, 'timeout': 60}
   complex_task = {'max_steps': 50, 'timeout': 300}
   ```

3. **使用错误重试机制**
   ```python
   def execute_with_retry(action, max_retries=3, **kwargs):
       for attempt in range(max_retries):
           result = browser_tool.execute(action=action, **kwargs)
           if result['success']:
               return result
           time.sleep(2 ** attempt)  # 指数退避
       return result
   ```

4. **定期清理资源**
   ```python
   # 定期清理浏览器缓存和临时文件
   browser_tool.cleanup_resources()
   ```

### 故障排除

#### 常见问题

1. **浏览器启动失败**
   ```bash
   # 安装 Playwright 浏览器
   playwright install chromium --with-deps
   ```

2. **页面加载超时**
   ```python
   # 增加超时时间
   result = browser_tool.execute(
       action="navigate_and_extract",
       url="slow-website.com",
       timeout=600  # 增加到10分钟
   )
   ```

3. **元素定位失败**
   ```python
   # 使用更具体的任务描述
   task = "等待页面完全加载后，查找包含'提交'文字的按钮并点击"
   ```

### 集成示例

完整的研究流程集成示例请参考 `examples/browser_use_integration.py` 文件。

---

**BrowserUseTool 让 AI 代理具备了人类级别的浏览器操作能力，大大扩展了自动化研究的可能性！** 🌐🤖

**强大的工具系统让 DeepResearch 能够处理各种复杂的研究任务！** 🛠️✨ 