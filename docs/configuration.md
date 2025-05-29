# DeepResearch 配置文件详解

## 📋 配置概览

DeepResearch 使用多层配置系统，支持灵活的配置管理和环境适配。

## 🔧 配置文件结构

### 主配置文件 (`config.yml`)

```yaml
# DeepResearch 主配置文件
# 版本: 2.0

# LLM 配置
llm:
  # 默认提供商
  default_provider: "openai"
  
  # 提供商配置
  openai:
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 4000
    timeout: 60
    retry_attempts: 3
    
  anthropic:
    model: "claude-3-5-sonnet-20241022"
    temperature: 0.7
    max_tokens: 4000
    timeout: 60
    retry_attempts: 3
    
  google:
    model: "gemini-1.5-pro"
    temperature: 0.7
    max_tokens: 4000
    timeout: 60
    retry_attempts: 3
    
  ollama:
    base_url: "http://localhost:11434"
    model: "llama2"
    temperature: 0.7
    timeout: 120
    
  # Agent 特定 LLM 配置
  agent_llms:
    outline_agent: "claude"
    content_agent: "openai"
    search_agent: "gemini"
    analysis_agent: "claude"
    
  # 任务特定模型配置
  task_specific_models:
    creative_writing:
      provider: "claude"
      temperature: 0.9
    technical_analysis:
      provider: "openai"
      temperature: 0.3
    data_analysis:
      provider: "gemini"
      temperature: 0.5

# 搜索引擎配置
search:
  # 默认搜索引擎
  default_engine: "google"
  
  # 搜索引擎配置
  engines:
    google:
      enabled: true
      timeout: 30
      max_results: 10
      
    bing:
      enabled: true
      timeout: 30
      max_results: 10
      
    duckduckgo:
      enabled: true
      timeout: 30
      max_results: 10
      rate_limit_delay: 2.0
      max_retries: 3
      
    serpapi:
      enabled: true
      timeout: 30
      max_results: 10
      
  # 搜索策略
  strategy:
    # 搜索引擎选择策略
    selection: "round_robin"  # round_robin, priority, random
    
    # 结果合并策略
    merge_strategy: "relevance"  # relevance, chronological, source_diversity
    
    # 去重配置
    deduplication:
      enabled: true
      similarity_threshold: 0.8
      
    # 缓存配置
    cache:
      enabled: true
      ttl: 3600  # 1小时

# 工具配置
tools:
  # 代码执行工具
  code_tool:
    enabled: true
    execution_environment: "docker"  # docker, local, sandbox
    timeout: 30
    max_memory_mb: 512
    allowed_packages:
      - "numpy"
      - "pandas"
      - "matplotlib"
      - "requests"
      
  # 搜索工具
  search_tool:
    enabled: true
    timeout: 30
    max_concurrent_searches: 3
    
  # 浏览器工具
  browser_tool:
    enabled: true
    headless: true
    timeout: 30
    max_pages: 10
    
  # 文件工具
  file_tool:
    enabled: true
    allowed_extensions:
      - ".txt"
      - ".md"
      - ".json"
      - ".csv"
      - ".pdf"
    max_file_size_mb: 10

# 系统配置
system:
  # 输出配置
  output_dir: "./output"
  log_dir: "./logs"
  cache_dir: "./cache"
  
  # 性能配置
  max_concurrent_requests: 5
  request_timeout: 60
  max_memory_mb: 2048
  
  # 流式输出
  enable_streaming: true
  streaming_chunk_size: 1024
  
  # 交互模式
  interactive_mode: true
  default_research_depth: "standard"
  
  # 日志配置
  logging:
    level: "INFO"  # DEBUG, INFO, WARNING, ERROR
    file: "deepresearch.log"
    max_size_mb: 100
    backup_count: 5
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 安全配置
security:
  # API 密钥保护
  api_key_encryption: true
  
  # 代码执行安全
  code_execution:
    sandbox_enabled: true
    network_access: false
    file_system_access: "restricted"
    
  # 数据保护
  data_protection:
    encrypt_cache: true
    auto_cleanup: true
    retention_days: 30

# 缓存配置
cache:
  enabled: true
  backend: "file"  # file, redis, memory
  ttl: 3600  # 默认TTL (秒)
  max_size: 1000  # 最大条目数
  
  # 分层缓存
  layers:
    search_results:
      ttl: 7200  # 2小时
      max_size: 500
      
    llm_responses:
      ttl: 3600  # 1小时
      max_size: 200
      
    analysis_results:
      ttl: 86400  # 24小时
      max_size: 100

# 资源管理
resources:
  # 资源池配置
  pools:
    browser_pool:
      max_size: 5
      min_size: 1
      max_idle_time: 300  # 5分钟
      
    http_pool:
      max_size: 20
      timeout: 30
      
  # 资源限制
  limits:
    max_memory_mb: 2048
    max_cpu_percent: 80
    max_disk_mb: 1024

# 监控配置
monitoring:
  enabled: true
  
  # 性能监控
  performance:
    track_response_times: true
    track_memory_usage: true
    track_api_usage: true
    
  # 错误监控
  error_tracking:
    enabled: true
    max_error_logs: 1000
    
  # 统计收集
  statistics:
    enabled: true
    collection_interval: 60  # 秒
```

### 环境变量文件 (`.env`)

```env
# DeepResearch 环境变量配置

# ================================
# LLM 提供商 API 密钥
# ================================

# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_ORG_ID=org-your-org-id  # 可选

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-claude-key-here

# Google Gemini
GOOGLE_API_KEY=your-gemini-key-here

# ================================
# 搜索引擎 API 密钥
# ================================

# SerpAPI (推荐)
SERPAPI_KEY=your-serpapi-key-here

# Bing Search
BING_SEARCH_API_KEY=your-bing-search-key-here

# Google Custom Search (可选)
GOOGLE_CSE_ID=your-custom-search-engine-id
GOOGLE_CSE_API_KEY=your-google-cse-api-key

# ================================
# 云存储配置
# ================================

# Google Drive
GOOGLE_DRIVE_CREDENTIALS=path/to/google-drive-credentials.json

# Dropbox
DROPBOX_ACCESS_TOKEN=your-dropbox-access-token

# ================================
# 本地模型配置
# ================================

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# ================================
# 数据库配置 (可选)
# ================================

# Redis (用于缓存)
REDIS_URL=redis://localhost:6379/0

# PostgreSQL (用于数据存储)
DATABASE_URL=postgresql://user:password@localhost:5432/deepresearch

# ================================
# 安全配置
# ================================

# 加密密钥
ENCRYPTION_KEY=your-32-character-encryption-key

# JWT 密钥 (如果使用 API)
JWT_SECRET=your-jwt-secret-key

# ================================
# 监控和日志
# ================================

# Sentry (错误监控)
SENTRY_DSN=your-sentry-dsn

# 日志级别
LOG_LEVEL=INFO

# ================================
# 代理配置 (如需要)
# ================================

# HTTP 代理
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=https://proxy.example.com:8080

# 不使用代理的地址
NO_PROXY=localhost,127.0.0.1,.local
```

## 🎯 配置详解

### LLM 配置

#### 提供商选择

```yaml
llm:
  default_provider: "openai"  # 默认提供商
  
  # 按任务类型选择提供商
  task_specific_models:
    creative_writing:
      provider: "claude"      # Claude 擅长创意写作
      temperature: 0.9        # 高创造性
    technical_analysis:
      provider: "openai"      # GPT-4 技术分析能力强
      temperature: 0.3        # 低随机性，更准确
    data_analysis:
      provider: "gemini"      # Gemini 数据处理能力强
      temperature: 0.5        # 中等创造性
```

#### 模型参数调优

```yaml
openai:
  model: "gpt-4"
  temperature: 0.7          # 控制输出随机性 (0-1)
  max_tokens: 4000          # 最大输出长度
  top_p: 0.9               # 核采样参数
  frequency_penalty: 0.0    # 频率惩罚
  presence_penalty: 0.0     # 存在惩罚
  timeout: 60              # 请求超时时间
  retry_attempts: 3        # 重试次数
```

### 搜索引擎配置

#### 搜索策略

```yaml
search:
  strategy:
    # 引擎选择策略
    selection: "round_robin"  # 轮询使用不同引擎
    # selection: "priority"   # 按优先级选择
    # selection: "random"     # 随机选择
    
    # 结果合并策略
    merge_strategy: "relevance"     # 按相关性排序
    # merge_strategy: "chronological" # 按时间排序
    # merge_strategy: "source_diversity" # 按来源多样性
```

#### 速率限制配置

```yaml
engines:
  duckduckgo:
    enabled: true
    rate_limit_delay: 2.0    # 请求间隔 (秒)
    max_retries: 3           # 最大重试次数
    backoff_factor: 2        # 退避因子
```

### 工具配置

#### 代码执行安全

```yaml
tools:
  code_tool:
    execution_environment: "docker"  # 推荐使用 Docker
    # execution_environment: "local"   # 本地执行 (不安全)
    # execution_environment: "sandbox" # 沙箱执行
    
    timeout: 30              # 执行超时
    max_memory_mb: 512       # 内存限制
    network_access: false    # 禁止网络访问
    
    # 允许的包
    allowed_packages:
      - "numpy"
      - "pandas"
      - "matplotlib"
      - "seaborn"
      - "scikit-learn"
```

#### 浏览器工具配置

```yaml
tools:
  browser_tool:
    enabled: true
    headless: true           # 无头模式
    timeout: 30             # 页面加载超时
    max_pages: 10           # 最大页面数
    
    # 浏览器选项
    options:
      window_size: "1920x1080"
      user_agent: "DeepResearch Bot 1.0"
      disable_images: true   # 禁用图片加载
      disable_javascript: false
```

### 性能配置

#### 并发控制

```yaml
system:
  max_concurrent_requests: 5    # 最大并发请求数
  request_timeout: 60          # 请求超时时间
  
  # 资源限制
  max_memory_mb: 2048          # 最大内存使用
  max_cpu_percent: 80          # 最大CPU使用率
```

#### 缓存优化

```yaml
cache:
  enabled: true
  backend: "file"              # 缓存后端
  
  # 分层缓存配置
  layers:
    search_results:
      ttl: 7200               # 搜索结果缓存2小时
      max_size: 500
      
    llm_responses:
      ttl: 3600               # LLM响应缓存1小时
      max_size: 200
      
    analysis_results:
      ttl: 86400              # 分析结果缓存24小时
      max_size: 100
```

## 🔒 安全配置

### API 密钥保护

```yaml
security:
  api_key_encryption: true     # 启用API密钥加密
  
  # 密钥轮换
  key_rotation:
    enabled: true
    interval_days: 30
    
  # 访问控制
  access_control:
    rate_limiting: true
    max_requests_per_hour: 1000
```

### 代码执行安全

```yaml
security:
  code_execution:
    sandbox_enabled: true      # 启用沙箱
    network_access: false      # 禁止网络访问
    file_system_access: "restricted"  # 限制文件系统访问
    
    # 资源限制
    max_execution_time: 30     # 最大执行时间
    max_memory_mb: 256         # 最大内存
    max_cpu_percent: 50        # 最大CPU使用
```

## 📊 监控配置

### 性能监控

```yaml
monitoring:
  performance:
    track_response_times: true
    track_memory_usage: true
    track_api_usage: true
    
    # 性能阈值
    thresholds:
      response_time_ms: 5000   # 响应时间阈值
      memory_usage_mb: 1024    # 内存使用阈值
      error_rate_percent: 5    # 错误率阈值
```

### 日志配置

```yaml
system:
  logging:
    level: "INFO"              # 日志级别
    file: "deepresearch.log"   # 日志文件
    max_size_mb: 100          # 最大文件大小
    backup_count: 5           # 备份文件数量
    
    # 日志格式
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 分类日志
    loggers:
      search: "search.log"
      llm: "llm.log"
      tools: "tools.log"
```

## 🔧 配置管理

### 环境特定配置

```yaml
# config.dev.yml (开发环境)
llm:
  default_provider: "ollama"  # 使用本地模型
system:
  logging:
    level: "DEBUG"            # 详细日志

# config.prod.yml (生产环境)
llm:
  default_provider: "openai"  # 使用云端模型
system:
  logging:
    level: "WARNING"          # 简化日志
security:
  api_key_encryption: true    # 启用加密
```

### 配置验证

```bash
# 验证配置文件
./run.sh config-validate

# 检查配置状态
./run.sh config-check

# 显示配置摘要
./run.sh config-show
```

### 配置热重载

```python
# 在代码中动态更新配置
from config import config

# 重新加载配置
config.reload()

# 更新特定配置
config.update({
    'llm.default_provider': 'claude',
    'system.max_concurrent_requests': 10
})
```

## 🎯 最佳实践

### 1. 环境分离

```bash
# 开发环境
export CONFIG_ENV=development
./run.sh interactive "测试主题"

# 生产环境
export CONFIG_ENV=production
./run.sh auto "生产主题"
```

### 2. 敏感信息保护

```bash
# 使用环境变量而非配置文件存储密钥
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# 加密配置文件
gpg --symmetric config.yml
```

### 3. 配置版本控制

```bash
# 配置文件版本控制
git add config.yml
git commit -m "Update LLM configuration"

# 排除敏感文件
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
```

### 4. 配置备份

```bash
# 定期备份配置
cp config.yml config.yml.backup.$(date +%Y%m%d)
cp .env .env.backup.$(date +%Y%m%d)
```

## 🔍 故障排除

### 配置错误诊断

```bash
# 检查配置语法
python -c "import yaml; yaml.safe_load(open('config.yml'))"

# 验证环境变量
./run.sh config-check

# 测试 API 连接
python -c "from config import config; print(config.validate_api_keys())"
```

### 常见配置问题

1. **YAML 语法错误**
   ```bash
   # 检查缩进和语法
   yamllint config.yml
   ```

2. **API 密钥无效**
   ```bash
   # 验证密钥格式
   echo $OPENAI_API_KEY | grep -E "^sk-[a-zA-Z0-9]{48}$"
   ```

3. **路径配置错误**
   ```bash
   # 检查路径是否存在
   ls -la ./output ./logs ./cache
   ```

---

**通过合理的配置，让 DeepResearch 发挥最佳性能！** ⚙️✨ 