# DeepResearch 快速启动指南 ⚡

## 🚀 三步启动

### 1️⃣ 安装环境
```bash
./setup.sh
```

### 2️⃣ 配置密钥
编辑 `.env` 文件，至少配置一个 LLM API 密钥：
```env
OPENAI_API_KEY=sk-your-key-here
# 或
ANTHROPIC_API_KEY=sk-ant-your-key-here
# 或
GOOGLE_API_KEY=your-gemini-key-here
```

### 3️⃣ 开始研究
```bash
# 交互式研究（推荐新手）
./run.sh interactive "人工智能发展趋势"

# 自动化研究（快速生成）
./run.sh auto "区块链技术应用"

# 运行演示
./run.sh demo
```

## 📋 常用命令

```bash
# 显示帮助
./run.sh help

# 检查配置
./run.sh config-check

# 进入开发环境
./run.sh shell

# 交互功能演示
./run.sh interactive-demo
```

## 🔧 高级选项

```bash
# 指定 LLM 提供商
./run.sh interactive "研究主题" --provider claude

# 设置输出目录
./run.sh auto "研究主题" --output ./my_research

# 调整章节数量
./run.sh interactive "研究主题" --max-sections 6

# 启用调试模式
./run.sh interactive "研究主题" --debug
```

## 🆘 遇到问题？

1. **conda 未安装**: 下载 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
2. **环境问题**: 运行 `conda env remove -n deep-research-dev && ./setup.sh`
3. **API 密钥错误**: 运行 `./run.sh config-check` 检查配置
4. **模块错误**: 确保运行 `conda activate deep-research-dev`

## 📚 更多信息

- 详细安装指南: [INSTALL.md](INSTALL.md)
- 完整用户手册: [README.md](README.md)
- 交互功能说明: [docs/interactive-features.md](docs/interactive-features.md)

---

**开始您的智能研究之旅！** 🔬✨ 