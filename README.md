# 🔬 DeepResearch - 自动化深度研究系统

[![Installation Status](https://img.shields.io/badge/Installation-✅%20Success-brightgreen)](./INSTALLATION_STATUS.md)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

DeepResearch 是一个功能强大的自动化深度研究系统，集成了多种大语言模型、搜索引擎和智能工具，能够自动进行深度研究并生成结构化的研究报告。

## ✨ 核心特性

- 🤖 **多LLM支持**: OpenAI GPT、Anthropic Claude、Google Gemini、DeepSeek、Ollama
- 🔍 **智能搜索**: DuckDuckGo、Google (SerpAPI)、Bing 搜索集成
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
SERPAPI_KEY=your_serpapi_key_here
BING_SEARCH_KEY=your_bing_search_key_here
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

# 自定义输出目录
python main.py research "机器学习算法" --output ./my_reports
```

## 📋 命令参考

| 命令 | 描述 | 示例 |
|------|------|------|
| `interactive` | 🤝 交互式研究模式 | `./run.sh interactive "AI趋势"` |
| `auto` | 🤖 自动研究模式 | `./run.sh auto "区块链"` |
| `demo` | 🚀 运行演示 | `./run.sh demo` |
| `config-check` | 🔧 检查配置 | `./run.sh config-check` |
| `config-show` | 📋 显示配置 | `./run.sh config-show` |
| `config-edit` | ✏️ 编辑配置 | `./run.sh config-edit` |
| `version` | 📦 版本信息 | `./run.sh version` |

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
│   ├── openai_wrapper.py   # OpenAI 集成
│   ├── claude_wrapper.py   # Claude 集成
│   └── gemini_wrapper.py   # Gemini 集成
├── tools/               # 工具集成
│   ├── search_engines.py   # 搜索引擎
│   ├── code_runner.py      # 代码执行
│   └── file_reader.py      # 文件读取
├── utils/               # 实用工具
│   ├── logger.py           # 日志系统
│   └── user_interaction.py # 用户交互
├── workflow/            # 研究工作流
│   └── graph.py            # LangGraph 工作流
├── main.py             # 主程序入口
├── run.sh              # 启动脚本
└── setup.sh            # 安装脚本
```

## 🔧 技术栈

- **核心框架**: Python 3.11+
- **LLM集成**: LangChain、LangGraph
- **用户界面**: Typer、Rich
- **搜索引擎**: DuckDuckGo Search、SerpAPI
- **配置管理**: Pydantic、python-dotenv
- **文档生成**: Markdown
- **环境管理**: Conda

## 📊 功能特性

### LLM 支持
- ✅ OpenAI GPT (gpt-3.5-turbo, gpt-4, gpt-4-turbo)
- ✅ Anthropic Claude (claude-3-sonnet, claude-3-opus)
- ✅ Google Gemini (gemini-pro, gemini-pro-vision)
- ✅ Ollama 本地模型 (llama2, mistral 等)

### 搜索引擎
- ✅ DuckDuckGo (免费，无需 API)
- ✅ Google Search (需要 SerpAPI 密钥)
- ✅ Bing Search (需要 Azure API 密钥)

### 工具集成
- ✅ Python 代码执行
- ✅ 文件读取和写入
- ✅ 网页内容抓取
- ✅ 数据可视化生成
- ✅ 文档格式转换

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
./run.sh auto "量子计算发展现状" --provider openai --max-sections 5
```
系统将自动执行完整的研究流程并生成报告。

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
- `output/研究报告.md` - 主研究报告
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

3. **依赖冲突**
   ```bash
   # 重新安装环境
   ./setup.sh
   ```

### 获取帮助
- 查看安装状态: [INSTALLATION_STATUS.md](./INSTALLATION_STATUS.md)
- 检查配置: `./run.sh config-check`
- 查看日志: `cat logs/deepresearch.log`

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎贡献代码！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献指南。

---

**状态**: ✅ 可用 | **版本**: v1.0.0 | **最后更新**: 2025-05-28 