# API 密钥配置指南

## 🔑 概览

DeepResearch 需要配置各种服务的 API 密钥才能正常工作。本指南将详细介绍如何获取和配置这些密钥。

## 📋 必需的 API 密钥

### LLM 提供商（至少配置一个）

#### 1. OpenAI API
**获取步骤：**
1. 访问 [OpenAI API 平台](https://platform.openai.com/api-keys)
2. 登录或注册账户
3. 点击 "Create new secret key"
4. 复制生成的密钥（格式：`sk-...`）

**配置：**
```env
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_ORG_ID=org-your-org-id  # 可选
```

**费用：** 按使用量计费，GPT-4 约 $0.03/1K tokens

#### 2. Anthropic Claude API
**获取步骤：**
1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册账户并完成验证
3. 在 API Keys 页面创建新密钥
4. 复制密钥（格式：`sk-ant-...`）

**配置：**
```env
ANTHROPIC_API_KEY=sk-ant-your-claude-key-here
```

**费用：** 按使用量计费，Claude-3.5-Sonnet 约 $0.003/1K tokens

#### 3. Google Gemini API
**获取步骤：**
1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 使用 Google 账户登录
3. 点击 "Create API Key"
4. 复制生成的密钥

**配置：**
```env
GOOGLE_API_KEY=your-gemini-key-here
```

**费用：** 有免费额度，超出后按使用量计费

## 🔍 搜索引擎 API（推荐配置）

#### 1. SerpAPI（推荐）
**获取步骤：**
1. 访问 [SerpAPI](https://serpapi.com/)
2. 注册账户
3. 在 Dashboard 中查看 API Key
4. 复制密钥

**配置：**
```env
SERPAPI_KEY=your-serpapi-key-here
```

**费用：** 免费额度 100 次/月，付费计划从 $50/月开始

#### 2. Bing Search API
**获取步骤：**
1. 访问 [Azure Portal](https://portal.azure.com/)
2. 创建 "Bing Search v7" 资源
3. 在资源的 "Keys and Endpoint" 页面获取密钥
4. 复制 Key 1 或 Key 2

**配置：**
```env
BING_SEARCH_API_KEY=your-bing-search-key-here
```

**费用：** 免费层 3000 次/月，付费层从 $4/1000 次开始

#### 3. Google Custom Search（可选）
**获取步骤：**
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 启用 Custom Search API
3. 创建 API 密钥
4. 创建自定义搜索引擎并获取 Search Engine ID

**配置：**
```env
GOOGLE_CSE_API_KEY=your-google-cse-api-key
GOOGLE_CSE_ID=your-custom-search-engine-id
```

**费用：** 免费额度 100 次/天，超出后 $5/1000 次

## ☁️ 云存储 API（可选）

#### 1. Google Drive API
**获取步骤：**
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建项目并启用 Google Drive API
3. 创建服务账户
4. 下载 JSON 凭据文件

**配置：**
```env
GOOGLE_DRIVE_CREDENTIALS=path/to/credentials.json
```

#### 2. Dropbox API
**获取步骤：**
1. 访问 [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. 创建新应用
3. 生成访问令牌
4. 复制令牌

**配置：**
```env
DROPBOX_ACCESS_TOKEN=your-dropbox-access-token
```

## 🏠 本地模型配置

#### Ollama（本地 LLM）
**安装步骤：**
1. 访问 [Ollama 官网](https://ollama.ai/)
2. 下载并安装 Ollama
3. 运行 `ollama pull llama2` 下载模型
4. 启动服务 `ollama serve`

**配置：**
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

**优势：** 完全本地运行，无需网络，隐私性好

## 🔧 配置方法

### 方法一：环境变量文件（推荐）

创建 `.env` 文件：
```bash
# 创建配置文件
touch .env

# 编辑配置文件
nano .env
```

添加您的 API 密钥：
```env
# LLM 提供商
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-claude-key-here
GOOGLE_API_KEY=your-gemini-key-here

# 搜索引擎
SERPAPI_KEY=your-serpapi-key-here
BING_SEARCH_API_KEY=your-bing-key-here

# 云存储
GOOGLE_DRIVE_CREDENTIALS=./credentials/google-drive.json
DROPBOX_ACCESS_TOKEN=your-dropbox-token-here

# 本地模型
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### 方法二：系统环境变量

```bash
# 临时设置（当前会话）
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 方法三：配置文件

在 `config.yml` 中配置（不推荐，安全性较低）：
```yaml
llm:
  openai:
    api_key: "sk-your-key-here"  # 不推荐
```

## ✅ 验证配置

### 检查配置状态
```bash
# 使用启动脚本检查
./run.sh config-check

# 或直接运行检查
python main.py config-check
```

### 测试 API 连接
```bash
# 测试 OpenAI
python -c "
import openai
openai.api_key = 'your-key'
print(openai.Model.list())
"

# 测试 Claude
python -c "
import anthropic
client = anthropic.Anthropic(api_key='your-key')
print('Claude API 连接成功')
"

# 测试 Gemini
python -c "
import google.generativeai as genai
genai.configure(api_key='your-key')
print('Gemini API 连接成功')
"
```

## 🔒 安全最佳实践

### 1. 密钥保护
```bash
# 设置文件权限
chmod 600 .env

# 添加到 .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
echo "credentials/" >> .gitignore
```

### 2. 密钥轮换
```bash
# 定期更换 API 密钥
# 1. 在服务商平台生成新密钥
# 2. 更新 .env 文件
# 3. 删除旧密钥
```

### 3. 环境分离
```bash
# 开发环境
cp .env .env.dev

# 生产环境
cp .env .env.prod

# 使用不同的密钥
```

### 4. 密钥加密
```bash
# 使用 GPG 加密敏感文件
gpg --symmetric .env
rm .env

# 使用时解密
gpg --decrypt .env.gpg > .env
```

## 💰 成本优化

### 1. 选择合适的模型
```yaml
# 成本对比（每1K tokens）
# GPT-4: $0.03 (最贵，最强)
# GPT-3.5-turbo: $0.002 (便宜，性能好)
# Claude-3.5-Sonnet: $0.003 (中等，长文本好)
# Gemini-1.5-pro: $0.0025 (便宜，多模态)
```

### 2. 使用缓存
```yaml
cache:
  enabled: true
  ttl: 3600  # 缓存1小时，减少重复调用
```

### 3. 设置使用限制
```yaml
system:
  max_concurrent_requests: 3  # 限制并发请求
  request_timeout: 30         # 设置超时
```

### 4. 监控使用量
```bash
# 定期检查 API 使用情况
./run.sh config-check

# 查看使用统计
python -c "
from config import config
print(config.get_api_usage_stats())
"
```

## 🆘 常见问题

### Q: 如何选择 LLM 提供商？
**A:** 建议配置多个提供商：
- **OpenAI**: 综合能力强，适合大多数任务
- **Claude**: 长文本处理好，适合深度分析
- **Gemini**: 成本较低，多模态能力强
- **Ollama**: 本地运行，隐私性好

### Q: 搜索引擎 API 是必需的吗？
**A:** 不是必需的，但强烈推荐：
- 没有搜索 API：只能使用 DuckDuckGo（免费但有限制）
- 有搜索 API：可以获得更好的搜索结果和更高的成功率

### Q: API 密钥泄露了怎么办？
**A:** 立即采取以下措施：
1. 在服务商平台删除泄露的密钥
2. 生成新的密钥
3. 更新配置文件
4. 检查是否有异常使用

### Q: 如何减少 API 成本？
**A:** 优化建议：
1. 启用缓存减少重复调用
2. 选择合适的模型（不一定要最贵的）
3. 设置合理的 token 限制
4. 使用本地模型处理简单任务

## 📚 相关文档

- [配置文件详解](configuration.md)
- [安全最佳实践](security-best-practices.md)
- [故障排除指南](troubleshooting.md)

---

**正确配置 API 密钥是使用 DeepResearch 的第一步！** 🔑✨ 