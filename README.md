# 🔬 DeepResearch - 自动化深度研究系统

[![Installation Status](https://img.shields.io/badge/Installation-✅%20Success-brightgreen)](./INSTALLATION_STATUS.md)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

DeepResearch 是一个功能强大的自动化深度研究系统，集成了多种大语言模型、搜索引擎和智能工具，能够自动进行深度研究并生成结构化的研究报告。

## ✨ 核心特性

- 🤖 **多LLM支持**: OpenAI GPT、Anthropic Claude、Google Gemini、DeepSeek、Ollama
- 🔍 **智能搜索**: Tavily、DuckDuckGo、ArXiv、Google、Bing、Brave 等多引擎集成
- 🌐 **Browser-Use**: AI 驱动的智能浏览器自动化
- 📊 **自动化工作流**: 基于 LangGraph 的智能研究流程
- 📝 **结构化输出**: 自动生成 Markdown 格式的研究报告
- 🛠️ **工具集成**: 代码执行、文件读取、浏览器自动化
- 🌐 **交互模式**: 支持完全交互式和自动化两种研究模式
- 🎨 **美观界面**: 基于 Rich 的现代化命令行界面

## 🚀 快速开始

### 1. 安装系统
```bash
# 克隆项目
git clone <repository-url>
cd deepresearch

# 运行安装脚本
chmod +x setup.sh
./setup.sh
```

### 2. 配置 API 密钥
编辑 `.env` 文件，配置至少一个 LLM 提供商：
```env
# 主要LLM提供商（至少配置一个）
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 搜索引擎 (可选，提升搜索质量)
TAVILY_API_KEY=your_tavily_api_key_here
SERPAPI_KEY=your_serpapi_key_here
BING_SEARCH_KEY=your_bing_search_key_here
BRAVE_SEARCH_API_KEY=your_brave_search_key_here
```

### 3. 验证安装
```bash
./run.sh config-check
```

### 4. 开始研究
```bash
# 交互式研究
./run.sh interactive "人工智能发展趋势"

# 自动化研究
./run.sh auto "区块链技术应用"

# 运行演示
./run.sh demo

# 指定LLM提供商
python main.py research "人工智能发展趋势" --provider claude
python main.py research "区块链技术应用" --provider gemini
python main.py research "量子计算前景" --provider deepseek

# 启用 Browser-Use 工具
python main.py research "最新技术趋势" --enable-browser-use

# 自定义输出目录
python main.py research "机器学习算法" --output ./my_reports
```

## 🎨 LangGraph Studio 可视化调试 ⭐ **新功能**

DeepResearch 现已完整集成 LangGraph Studio，提供可视化的工作流调试和状态管理功能。

### Studio 快速启动

#### 统一启动方式 (推荐)
```bash
# 检查 Studio 环境配置
./run.sh studio-check

# 设置 Studio 环境
./run.sh studio-setup

# 运行 Studio 演示研究
./run.sh studio-demo

# 启动 Studio 研究（支持参数化）
./run.sh studio-research "人工智能发展" --provider deepseek --depth advanced

# 显示 Studio 使用指南
./run.sh studio-info
```

#### Python API 调用
```bash
# 显示 Studio 使用指南
python studio.py --info

# 运行研究工作流
python studio.py --run "人工智能发展趋势" --provider deepseek --depth intermediate

# 高级研究
python studio.py --run "量子计算前景" --provider claude --depth advanced
```

### Studio 安装和配置

1. **下载 LangGraph Studio**
   ```bash
   # 访问官方下载页面（仅支持 macOS Apple Silicon）
   open https://github.com/langchain-ai/langgraph-studio/releases
   ```

2. **配置环境**
   ```bash
   # 一键设置 Studio 环境
   ./run.sh studio-setup
   ```

3. **配置 LangSmith**
   ```bash
   # 在 .env 文件中添加（studio-setup 会自动创建模板）
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your_langsmith_api_key
   LANGCHAIN_PROJECT=DeepResearch-Studio
   ```

4. **在 Studio 中打开项目**
   - 启动 LangGraph Studio 应用
   - 点击 "Open Directory"
   - 选择 DeepResearch 项目目录
   - 选择 `studio_research_workflow` 图

### Studio 工作流特性

- 🏗️ **可视化节点**: 8个专门设计的研究节点
- 🎮 **交互式调试**: 设置断点、单步执行
- 📊 **实时状态监控**: 查看工作流状态和数据流
- ⚡ **性能分析**: 节点执行时间、API调用统计
- 🔧 **状态管理**: 手动修改状态进行实验
- 📝 **执行日志**: 详细的时间线日志记录

### Studio 工作流节点说明

| 节点 | 功能 | 描述 |
|------|------|------|
| 🚀 `initialize` | 初始化 | 设置研究参数和环境 |
| 📋 `generate_outline` | 生成大纲 | AI生成结构化研究提纲 |
| 🔍 `review_outline` | 审核大纲 | 质量检查和用户确认 |
| 🔍 `search_information` | 信息搜索 | 多引擎并行搜索 |
| ✍️ `generate_content` | 内容生成 | 基于搜索结果生成内容 |
| 📝 `review_content` | 内容审核 | 质量评估和优化建议 |
| 📄 `finalize_report` | 完成报告 | 整合最终研究报告 |
| ❌ `handle_error` | 错误处理 | 异常恢复和错误信息 |

### Studio 使用示例

```bash
# 快速测试 Studio 工作流
python examples/studio_quickstart.py

# 在 Studio 中可视化调试具体研究
./run.sh studio-research "区块链技术发展" --depth advanced

# 导出 Studio 配置
python studio.py --export-config my_studio_config.json
```

## 📋 命令参考

| 命令 | 描述 | 示例 |
|------|------|------|
| `interactive` | 🤝 交互式研究模式 | `./run.sh interactive "AI趋势"` |
| `auto` | 🤖 自动研究模式 | `./run.sh auto "区块链"` |
| `demo` | 🚀 运行演示 | `./run.sh demo` |
| `studio-demo` | 🎨 Studio 演示研究 | `./run.sh studio-demo` |
| `studio-research` | 🎨 Studio 研究模式 | `./run.sh studio-research "主题" --provider deepseek` |
| `studio-check` | 🔧 检查 Studio 环境 | `./run.sh studio-check` |
| `studio-setup` | ⚙️ 设置 Studio 环境 | `./run.sh studio-setup` |
| `studio-info` | 📖 Studio 使用指南 | `./run.sh studio-info` |
| `config-check` | 🔧 检查配置 | `./run.sh config-check` |
| `config-show` | 📋 显示配置 | `./run.sh config-show` |
| `config-edit` | ✏️ 编辑配置 | `./run.sh config-edit` |
| `version` | 📦 版本信息 | `./run.sh version` |

### Studio 参数支持

| 参数 | 描述 | 可选值 | 示例 |
|------|------|--------|------|
| `--provider` | LLM 提供商 | openai, claude, gemini, deepseek, ollama | `--provider deepseek` |
| `--depth` | 研究深度 | basic, intermediate, advanced | `--depth advanced` |
| `--language` | 研究语言 | zh-CN, en-US, 等 | `--language zh-CN` |

### 使用示例

```bash
# 传统研究
./run.sh interactive "人工智能发展趋势"
./run.sh auto "区块链技术应用"

# Studio 可视化研究
./run.sh studio-demo
./run.sh studio-research "量子计算前景" --provider claude --depth advanced
./run.sh studio-research "机器学习应用" --provider deepseek --depth intermediate

# 系统管理
./run.sh config-check
./run.sh studio-setup
```

## 🏗️ 系统架构

```
DeepResearch/
├── agents/              # 智能代理
│   ├── outline_agent.py    # 大纲生成代理
│   ├── content_agent.py    # 内容生成代理
│   └── review_agent.py     # 审核代理
├── config/              # 配置管理
│   └── config.py           # 系统配置
├── llm/                 # LLM 包装器
│   ├── openai.py           # OpenAI 集成
│   ├── claude.py           # Claude 集成
│   ├── gemini.py           # Gemini 集成
│   └── deepseek.py         # DeepSeek 集成
├── tools/               # 工具集成
│   ├── search_engines.py   # 搜索引擎
│   ├── browser_use_tool.py # Browser-Use 集成
│   ├── code_runner.py      # 代码执行
│   └── file_reader.py      # 文件读取
├── utils/               # 实用工具
│   ├── logger.py           # 日志系统
│   └── user_interaction.py # 用户交互
├── workflow/            # 研究工作流
│   ├── graph.py            # 传统 LangGraph 工作流
│   └── studio_workflow.py  # Studio 优化工作流 ⭐ **新增**
├── examples/            # 示例文件
│   └── studio_quickstart.py # Studio 快速开始 ⭐ **新增**
├── main.py             # 主程序入口
├── studio.py           # Studio Python API ⭐ **新增**
├── langgraph.json      # Studio 配置文件 ⭐ **新增**
├── run.sh              # 统一启动脚本 ⭐ **更新**
└── setup.sh            # 安装脚本
```

## 🔧 技术栈

- **核心框架**: Python 3.11+
- **LLM集成**: LangChain、LangGraph
- **可视化调试**: LangGraph Studio ⭐ **新增**
- **用户界面**: Typer、Rich
- **搜索引擎**: Tavily、DuckDuckGo Search、SerpAPI、ArXiv
- **浏览器自动化**: Browser-Use、Playwright
- **配置管理**: Pydantic、python-dotenv
- **文档生成**: Markdown
- **环境管理**: Conda

## 📊 功能特性

### LLM 支持
- ✅ OpenAI GPT (gpt-4, gpt-4-turbo, gpt-3.5-turbo)
- ✅ Anthropic Claude (claude-3.5-sonnet, claude-3-opus, claude-3-haiku)
- ✅ Google Gemini (gemini-1.5-pro, gemini-1.0-pro)
- ✅ DeepSeek (deepseek-chat) ⭐ **新增**
- ✅ Ollama 本地模型 (llama2, mistral 等)

### 搜索引擎
- ✅ Tavily Search (AI 优化的专业搜索) ⭐ **新增**
- ✅ DuckDuckGo (免费，无需 API)
- ✅ ArXiv (学术论文搜索) ⭐ **新增**
- ✅ Google Search (需要 SerpAPI 密钥)
- ✅ Bing Search (需要 Azure API 密钥)
- ✅ Brave Search (需要 Brave API 密钥) ⭐ **新增**
- ✅ Google Docs 搜索 ⭐ **新增**
- ✅ Authority Sites 搜索 ⭐ **新增**

### 工具集成
- ✅ Python 代码执行
- ✅ Browser-Use 智能浏览器自动化 ⭐ **新增**
- ✅ 传统浏览器工具（截图、抓取）
- ✅ 文件读取和写入
- ✅ 网页内容抓取
- ✅ 数据可视化生成
- ✅ 文档格式转换

### Studio 功能 ⭐ **新增**
- ✅ 可视化工作流调试
- ✅ 实时状态监控
- ✅ 交互式断点调试
- ✅ 性能指标分析
- ✅ 状态时间旅行
- ✅ 自定义节点开发
- ✅ 工作流模板系统

## 🌟 使用示例

### 交互式研究
```bash
./run.sh interactive "人工智能在医疗领域的应用"
```
系统将引导您逐步完成研究过程，包括：
1. 研究范围确认
2. 大纲生成和调整
3. 内容搜索和生成
4. 报告审核和优化

### 自动化研究
```bash
./run.sh auto "量子计算发展现状" --provider deepseek --max-sections 5
```
系统将自动执行完整的研究流程并生成报告。

### Studio 可视化研究 ⭐ **新功能**
```bash
# 启动 Studio 可视化研究
./scripts/launch_studio.sh --demo --topic "人工智能发展趋势" --provider deepseek

# 高级研究
python studio.py --run "量子计算前景" --depth advanced --provider claude
```
在 LangGraph Studio 中观察完整的研究过程，包括节点执行、状态变化和性能指标。

### 使用 Browser-Use 工具
```bash
python main.py research "最新AI技术趋势" --enable-browser-use --provider deepseek
```
使用 AI 驱动的浏览器自动化进行深度网页内容抓取。

### 配置管理
```bash
# 检查系统状态
./run.sh config-check

# 显示当前配置
./run.sh config-show

# 编辑配置文件
./run.sh config-edit
```

## 📁 输出文件

研究完成后，系统将生成以下文件：
- `output/研究报告.md` - 主研究报告（包含引用来源）
- `output/outline.json` - 结构化大纲
- `logs/research.log` - 详细日志
- `demo_output/` - 演示文件 (如果运行演示)

## 🔍 故障排除

### 常见问题

1. **conda 命令不存在**
   ```bash
   # 手动激活 conda
   source /opt/homebrew/anaconda3/etc/profile.d/conda.sh
   conda activate deep-research-dev
   ```

2. **API 密钥错误**
   ```bash
   # 检查配置
   ./run.sh config-check
   # 编辑 .env 文件
   nano .env
   ```

3. **Studio 无法启动**
   ```bash
   # 检查 Studio 环境
   ./scripts/launch_studio.sh --check
   # 设置 Studio 环境
   ./scripts/launch_studio.sh --setup
   ```

4. **依赖冲突**
   ```bash
   # 重新安装环境
   ./setup.sh
   ```

### 测试功能
```bash
# 测试所有工具
python -c "from tools.search_engines import SearchEngineManager; manager = SearchEngineManager(); print('可用搜索引擎:', list(manager.engines.keys()))"

# 测试 Browser-Use
python -c "from tools.browser_use_tool import BrowserUseTool; tool = BrowserUseTool(); print('Browser-Use 工具已就绪')"

# 测试搜索结果源显示
python -c "from tools.search_engines import SearchEngineManager; manager = SearchEngineManager(); results = manager.search('test', max_results=1); print('来源显示:', results[0].source if results else 'No results')"

# 测试 Studio 工作流
python workflow/studio_workflow.py
```

### 获取帮助
- 查看完整文档: [docs/](./docs/)
- Studio 使用指南: [docs/langgraph-studio-customization.md](./docs/langgraph-studio-customization.md) ⭐ **新增**
- 查看工具测试指南: [TOOLS_TESTING_GUIDE.md](./TOOLS_TESTING_GUIDE.md)
- 检查配置: `./run.sh config-check`
- 查看日志: `cat logs/deepresearch.log`

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎贡献代码！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献指南。

---

**状态**: ✅ 可用 | **版本**: v1.0.0 | **最后更新**: 2025-05-28 