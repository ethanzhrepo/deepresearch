# DeepResearch 安装和使用指南

## 🚀 快速开始

### 1. 安装系统

使用提供的安装脚本一键安装：

```bash
# 克隆项目（如果还没有）
git clone <repository-url>
cd deepresearch

# 运行安装脚本
./setup.sh
```

安装脚本会自动：
- 检查 conda 是否已安装
- 创建 `deep-research-dev` conda 环境
- 安装 Python 3.11 和所有依赖包
- 创建配置文件模板
- 验证安装是否成功

### 2. 配置 API 密钥

编辑 `.env` 文件，配置您的 API 密钥：

```bash
# 编辑配置文件
nano .env
# 或使用您喜欢的编辑器
```

至少需要配置一个 LLM 提供商：

```env
# LLM 提供商 (至少配置一个)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-claude-key-here
GOOGLE_API_KEY=your-gemini-key-here

# 搜索引擎 (可选，但推荐)
SERPAPI_KEY=your-serpapi-key-here
BING_SEARCH_API_KEY=your-bing-key-here
```

### 3. 启动系统

使用启动脚本运行系统：

```bash
# 交互式研究
./run.sh interactive "人工智能发展趋势"

# 自动化研究
./run.sh auto "区块链技术应用"

# 运行演示
./run.sh demo

# 检查配置
./run.sh config-check
```

## 📋 详细安装步骤

### 前置要求

1. **操作系统**: Linux, macOS, 或 Windows (WSL)
2. **Conda**: Anaconda 或 Miniconda
   - 下载地址: https://docs.conda.io/en/latest/miniconda.html
3. **Git**: 用于克隆项目

### 手动安装步骤

如果自动安装脚本遇到问题，可以手动安装：

```bash
# 1. 创建 conda 环境
conda create -n deep-research-dev python=3.11 -y

# 2. 激活环境
conda activate deep-research-dev

# 3. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. 创建配置文件
cp .env.example .env  # 如果有示例文件
# 或手动创建 .env 文件

# 5. 创建输出目录
mkdir -p output logs demo_output

# 6. 验证安装
python -c "from utils.user_interaction import get_user_interaction; print('✅ 安装成功')"
```

## 🔧 使用方法

### 命令行使用

#### 使用启动脚本 (推荐)

```bash
# 显示帮助
./run.sh help

# 交互式研究 - 用户可以在关键节点提供反馈
./run.sh interactive "研究主题"

# 自动化研究 - 完全自动化，无需用户干预
./run.sh auto "研究主题"

# 运行演示
./run.sh demo

# 配置管理
./run.sh config-check    # 检查配置状态
./run.sh config-show     # 显示配置摘要

# 进入开发环境
./run.sh shell
```

#### 直接使用 Python

```bash
# 首先激活环境
conda activate deep-research-dev

# 然后运行命令
python main.py interactive "研究主题"
python main.py auto "研究主题"
python main.py demo
```

### 编程接口使用

```python
import asyncio
from workflow.graph import ResearchWorkflow
from agents.outline_agent import OutlineAgent, OutlineConfig

# 交互式工作流
async def main():
    workflow = ResearchWorkflow(
        llm_provider="openai",
        interactive_mode=True
    )
    
    outline, content = await workflow.run_full_workflow("研究主题")
    print(f"生成了 {len(outline.sections)} 个章节")

# 运行
asyncio.run(main())
```

## 🎯 使用示例

### 1. 学术研究

```bash
./run.sh interactive "深度学习在医学影像诊断中的应用" \
  --provider claude \
  --max-sections 6 \
  --output ./academic_research
```

### 2. 商业分析

```bash
./run.sh auto "电商行业发展趋势分析" \
  --provider openai \
  --max-sections 4
```

### 3. 技术调研

```bash
./run.sh interactive "云原生架构设计最佳实践"
```

## 🔍 故障排除

### 常见问题

1. **conda 命令未找到**
   ```bash
   # 解决方案：安装 conda
   # 下载 Miniconda: https://docs.conda.io/en/latest/miniconda.html
   ```

2. **环境创建失败**
   ```bash
   # 解决方案：清理 conda 缓存
   conda clean --all
   ./setup.sh  # 重新运行安装脚本
   ```

3. **模块导入错误**
   ```bash
   # 解决方案：确保环境已激活
   conda activate deep-research-dev
   pip install -r requirements.txt
   ```

4. **API 密钥错误**
   ```bash
   # 解决方案：检查配置
   ./run.sh config-check
   # 编辑 .env 文件，确保 API 密钥正确
   ```

### 调试模式

```bash
# 启用详细日志
./run.sh interactive "测试主题" --debug

# 查看日志文件
tail -f deepresearch.log
```

### 重新安装

```bash
# 完全重新安装
conda env remove -n deep-research-dev
./setup.sh
```

## 📚 更多资源

- **用户手册**: [README.md](README.md)
- **交互功能指南**: [docs/interactive-features.md](docs/interactive-features.md)
- **API 文档**: [docs/api-reference.md](docs/api-reference.md)
- **开发指南**: [docs/development.md](docs/development.md)

## 🆘 获取帮助

如果遇到问题：

1. 查看 [故障排除](#故障排除) 部分
2. 运行 `./run.sh config-check` 检查配置
3. 查看日志文件 `deepresearch.log`
4. 提交 Issue 到项目仓库

---

**祝您使用愉快！** 🔬✨ 