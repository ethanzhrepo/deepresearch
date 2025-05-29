# DeepResearch 安装指南

## 📋 系统要求

### 硬件要求
- **CPU**: 2 核心以上（推荐 4 核心）
- **内存**: 4GB 以上（推荐 8GB）
- **存储**: 10GB 可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: Linux, macOS, Windows (WSL)
- **Python**: 3.8+ （推荐 3.11）
- **Conda**: Anaconda 或 Miniconda
- **Git**: 用于克隆项目

## 🚀 一键安装（推荐）

### 自动安装脚本

DeepResearch 提供了自动化安装脚本，会自动安装所有依赖，包括 Browser-Use 集成：

```bash
# 克隆项目
git clone <repository-url>
cd deepresearch

# 运行安装脚本
./setup.sh
```

安装脚本会自动完成以下步骤：
- ✅ 检查 conda 环境
- ✅ 创建 Python 3.11 虚拟环境
- ✅ 安装所有 Python 依赖
- ✅ 安装 Browser-Use 集成（browser-use + Playwright）
- ✅ 安装 Playwright 浏览器引擎
- ✅ 创建配置文件模板
- ✅ 验证安装完整性

### Browser-Use 集成

安装脚本会自动安装以下 Browser-Use 相关组件：

1. **browser-use 库** (>=0.2.0)
   - AI 驱动的浏览器自动化核心库

2. **Playwright** (>=1.40.0)
   - 浏览器引擎和自动化框架

3. **LangChain 集成**
   - langchain-openai
   - langchain-anthropic  
   - langchain-google-genai

4. **Chromium 浏览器**
   - 自动下载和配置 Chromium 浏览器

5. **输出目录**
   - browser_outputs/
   - research_outputs/

## 🔧 手动安装

如果自动安装失败，您也可以手动安装：

### 1. 环境准备

```bash
# 创建 conda 环境
conda create -n deep-research-dev python=3.11 -y
conda activate deep-research-dev

# 升级 pip
pip install --upgrade pip
```

### 2. 安装基础依赖

```bash
# 安装项目依赖
pip install -r requirements.txt
```

### 3. 手动安装 Browser-Use

```bash
# 安装 browser-use 库
pip install browser-use>=0.2.0

# 安装 Playwright
pip install playwright>=1.40.0

# 安装 LangChain 集成
pip install langchain-openai>=0.1.0
pip install langchain-anthropic>=0.1.0
pip install langchain-google-genai>=1.0.0

# 安装 Playwright 浏览器
playwright install chromium --with-deps
```

### 4. 创建配置文件

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env
```

## 🔍 验证安装

### 自动验证

```bash
# 运行完整测试
python scripts/test_browser_use.py

# 检查配置
python main.py config-check
```

### 手动验证

```bash
# 激活环境
conda activate deep-research-dev

# 测试核心模块
python -c "from tools.browser_use_tool import BrowserUseTool; print('✅ BrowserUseTool 可用')"

# 测试 Playwright
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright 可用')"

# 测试 browser-use
python -c "import browser_use; print('✅ browser-use 可用')"
```

## 🛠️ 故障排除

### 常见问题

#### 1. Playwright 浏览器安装失败

```bash
# 手动安装浏览器
playwright install chromium --with-deps

# 如果仍然失败，尝试系统级安装
sudo playwright install-deps chromium
```

#### 2. browser-use 导入失败

```bash
# 检查版本
pip show browser-use

# 重新安装
pip uninstall browser-use -y
pip install browser-use>=0.2.0
```

#### 3. LangChain 依赖问题

```bash
# 更新 LangChain 相关包
pip install --upgrade langchain langchain-openai langchain-anthropic langchain-google-genai
```

#### 4. 权限问题

```bash
# 设置目录权限
chmod 755 browser_outputs research_outputs

# 如果在 Linux/macOS 上遇到权限问题
sudo chown -R $USER:$USER browser_outputs research_outputs
```

### 系统要求

#### 最低要求
- **Python**: 3.8+（推荐 3.11）
- **内存**: 4GB+
- **存储**: 2GB 可用空间
- **网络**: 稳定的互联网连接

#### 推荐配置
- **Python**: 3.11
- **内存**: 8GB+
- **存储**: 5GB 可用空间
- **CPU**: 4 核心+

### 操作系统支持

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip

# CentOS/RHEL
sudo yum install -y python3-devel python3-pip
```

#### macOS
```bash
# 使用 Homebrew
brew install python@3.11

# 或使用 conda
conda install python=3.11
```

#### Windows
```powershell
# 使用 conda（推荐）
conda create -n deep-research-dev python=3.11
conda activate deep-research-dev

# 或使用 WSL
wsl --install
# 然后在 WSL 中按 Linux 步骤安装
```

## 🔑 API 密钥配置

安装完成后，需要配置 API 密钥：

### 必需的 API 密钥（至少一个）

```bash
# 编辑 .env 文件
nano .env

# 配置 LLM 提供商
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_claude_key_here
GOOGLE_API_KEY=your_gemini_key_here
```

### 可选的 API 密钥

```bash
# 搜索引擎（提升搜索质量）
SERPAPI_KEY=your_serpapi_key_here
BING_SEARCH_API_KEY=your_bing_key_here

# 云存储集成
GOOGLE_DRIVE_CREDENTIALS=path/to/credentials.json
DROPBOX_ACCESS_TOKEN=your_dropbox_token_here
```

## 🎯 下一步

安装完成后，您可以：

1. **运行演示**
   ```bash
   python main.py demo
   ```

2. **开始研究**
   ```bash
   ./run.sh interactive "您的研究主题"
   ```

3. **测试 Browser-Use**
   ```bash
   python examples/browser_use_integration.py
   ```

4. **查看文档**
   - [快速入门](quickstart.md)
   - [工具系统](tools.md)
   - [配置详解](configuration.md)

---

**安装完成后，您就可以开始使用 DeepResearch 的强大功能了！** 🚀✨

## 🔧 详细安装步骤

### 1. 安装前置软件

#### 安装 Conda

**Linux/macOS:**
```bash
# 下载 Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# 安装
bash Miniconda3-latest-Linux-x86_64.sh

# 重新加载 shell
source ~/.bashrc
```

**Windows:**
1. 下载 [Miniconda for Windows](https://docs.conda.io/en/latest/miniconda.html)
2. 运行安装程序
3. 重启命令提示符

#### 安装 Git

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install git
```

**macOS:**
```bash
# 使用 Homebrew
brew install git

# 或使用 Xcode Command Line Tools
xcode-select --install
```

**Windows:**
下载并安装 [Git for Windows](https://git-scm.com/download/win)

### 2. 克隆项目

```bash
# 使用 HTTPS
git clone https://github.com/your-repo/deepresearch.git

# 或使用 SSH
git clone git@github.com:your-repo/deepresearch.git

# 进入项目目录
cd deepresearch
```

### 3. 环境配置

#### 使用安装脚本

```bash
# 运行安装脚本
chmod +x setup.sh
./setup.sh
```

安装脚本会自动：
- 检查 conda 是否已安装
- 创建 `deep-research-dev` 环境
- 安装 Python 3.11 和所有依赖
- 创建配置文件模板
- 验证安装是否成功

#### 手动环境配置

```bash
# 创建环境
conda create -n deep-research-dev python=3.11 -y

# 激活环境
conda activate deep-research-dev

# 升级 pip
pip install --upgrade pip

# 安装核心依赖
pip install -r requirements.txt

# 安装开发依赖（可选）
pip install -r requirements-dev.txt
```

### 4. 配置文件设置

#### 创建 .env 文件

```bash
# 复制示例文件（如果存在）
cp .env.example .env

# 或手动创建
touch .env
```

#### 配置 API 密钥

编辑 `.env` 文件：

```env
# LLM 提供商 (至少配置一个)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-claude-key-here
GOOGLE_API_KEY=your-gemini-key-here

# 搜索引擎 (可选，提升搜索质量)
SERPAPI_KEY=your-serpapi-key-here
BING_SEARCH_API_KEY=your-bing-key-here

# 云存储 (可选，支持文件集成)
GOOGLE_DRIVE_CREDENTIALS=path/to/credentials.json
DROPBOX_ACCESS_TOKEN=your-dropbox-token-here

# Ollama 配置 (如果使用本地模型)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

#### 创建目录结构

```bash
# 创建必要的目录
mkdir -p output
mkdir -p logs
mkdir -p demo_output
mkdir -p cache
```

### 5. 验证安装

#### 使用测试脚本

```bash
# 运行安装测试
./run.sh test

# 或直接运行测试脚本
python test_installation.py
```

#### 手动验证

```bash
# 激活环境
conda activate deep-research-dev

# 测试核心模块导入
python -c "
from utils.user_interaction import get_user_interaction
from workflow.graph import ResearchWorkflow
from agents.outline_agent import OutlineAgent
print('✅ 所有核心模块导入成功')
"

# 检查配置
python main.py config-check
```

## 🔑 API 密钥配置

### 必需的 API 密钥

至少需要配置一个 LLM 提供商：

#### OpenAI
1. 访问 [OpenAI API](https://platform.openai.com/api-keys)
2. 创建新的 API 密钥
3. 添加到 `.env` 文件：`OPENAI_API_KEY=sk-...`

#### Anthropic Claude
1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 创建 API 密钥
3. 添加到 `.env` 文件：`ANTHROPIC_API_KEY=sk-ant-...`

#### Google Gemini
1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建 API 密钥
3. 添加到 `.env` 文件：`GOOGLE_API_KEY=...`

### 可选的 API 密钥

#### SerpAPI (推荐)
1. 访问 [SerpAPI](https://serpapi.com/)
2. 注册并获取 API 密钥
3. 添加到 `.env` 文件：`SERPAPI_KEY=...`

#### Bing Search
1. 访问 [Azure Cognitive Services](https://azure.microsoft.com/en-us/services/cognitive-services/bing-web-search-api/)
2. 创建 Bing Search 资源
3. 添加到 `.env` 文件：`BING_SEARCH_API_KEY=...`

## 🐳 Docker 安装（可选）

### 使用 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  deepresearch:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

```bash
# 构建和运行
docker-compose up -d
```

### 使用 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py", "demo"]
```

```bash
# 构建镜像
docker build -t deepresearch .

# 运行容器
docker run -it --rm \
  -v $(pwd)/output:/app/output \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  deepresearch
```

## 🔧 故障排除

### 常见问题

#### 1. conda 命令未找到
```bash
# 解决方案：安装 conda
# 下载 Miniconda: https://docs.conda.io/en/latest/miniconda.html
```

#### 2. 环境创建失败
```bash
# 清理 conda 缓存
conda clean --all

# 重新创建环境
conda env remove -n deep-research-dev
./setup.sh
```

#### 3. 依赖安装失败
```bash
# 升级 pip
pip install --upgrade pip

# 清理缓存
pip cache purge

# 重新安装
pip install -r requirements.txt
```

#### 4. 模块导入错误
```bash
# 确保环境已激活
conda activate deep-research-dev

# 检查 Python 路径
python -c "import sys; print(sys.path)"

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

#### 5. API 密钥错误
```bash
# 检查配置
./run.sh config-check

# 验证 .env 文件格式
cat .env | grep -v "^#" | grep "="
```

### 调试模式

```bash
# 启用详细日志
export DEBUG=1
./run.sh interactive "测试主题" --debug

# 查看日志文件
tail -f deepresearch.log
```

### 重新安装

```bash
# 完全重新安装
conda env remove -n deep-research-dev
rm -rf output logs demo_output cache
./setup.sh
```

## 📚 下一步

安装完成后，您可以：

1. **运行演示**: `./run.sh demo`
2. **开始研究**: `./run.sh interactive "您的研究主题"`
3. **查看文档**: [快速入门指南](quickstart.md)
4. **配置系统**: [配置文件详解](configuration.md)

## 🆘 获取帮助

如果遇到问题：

1. 查看 [故障排除指南](troubleshooting.md)
2. 运行 `./run.sh config-check` 检查配置
3. 查看日志文件 `deepresearch.log`
4. 提交 Issue 到项目仓库

---

**祝您安装顺利！** 🚀 