# DeepResearch 快速入门指南

## 🚀 5分钟快速上手

### 第一步：安装系统
```bash
# 克隆项目
git clone <repository-url>
cd deepresearch

# 一键安装
./setup.sh
```

### 第二步：配置 API 密钥
```bash
# 编辑配置文件
nano .env

# 至少配置一个 LLM API 密钥
OPENAI_API_KEY=sk-your-key-here
# 或
ANTHROPIC_API_KEY=sk-ant-your-key-here
# 或
GOOGLE_API_KEY=your-gemini-key-here
```

### 第三步：开始使用
```bash
# 交互式研究（推荐新手）
./run.sh interactive "人工智能发展趋势"

# 自动化研究（快速生成）
./run.sh auto "区块链技术应用"

# 运行演示
./run.sh demo
```

## 📋 基本使用

### 交互式研究模式

交互式模式让您在关键节点参与决策：

```bash
./run.sh interactive "您的研究主题"
```

**流程说明：**
1. 🎯 **设置偏好** - 选择研究深度、章节数量等
2. 📋 **确认提纲** - 查看并确认生成的研究提纲
3. 🔧 **提供反馈** - 如需要，可以修改或重新生成提纲
4. ⚡ **生成内容** - 确认后开始生成详细内容
5. 📄 **导出报告** - 获得完整的 Markdown 研究报告

### 自动化研究模式

自动化模式完全无需用户干预：

```bash
./run.sh auto "您的研究主题"
```

**特点：**
- 🤖 完全自动化，无需用户交互
- ⚡ 快速生成，适合批量处理
- 📊 标准化输出格式
- 🔄 适合重复性研究任务

### 演示模式

体验系统功能：

```bash
./run.sh demo
```

## 🎯 使用示例

### 学术研究
```bash
# 深度学术研究
./run.sh interactive "深度学习在医学影像诊断中的应用" \
  --provider claude \
  --max-sections 6 \
  --output ./academic_research
```

### 商业分析
```bash
# 市场分析报告
./run.sh auto "电商行业发展趋势分析" \
  --provider openai \
  --max-sections 4
```

### 技术调研
```bash
# 技术方案调研
./run.sh interactive "云原生架构设计最佳实践"
```

## 🔧 常用命令

### 基本命令
```bash
# 显示帮助
./run.sh help

# 检查配置状态
./run.sh config-check

# 显示配置摘要
./run.sh config-show

# 运行安装测试
./run.sh test

# 进入开发环境
./run.sh shell
```

### 高级选项
```bash
# 指定 LLM 提供商
./run.sh interactive "研究主题" --provider claude

# 设置输出目录
./run.sh auto "研究主题" --output ./my_research

# 调整章节数量
./run.sh interactive "研究主题" --max-sections 6

# 启用调试模式
./run.sh interactive "研究主题" --debug

# 设置语言
./run.sh auto "研究主题" --language en-US
```

## 🎨 交互功能详解

### 用户偏好设置

在交互模式中，系统会询问您的偏好：

1. **研究深度**
   - 🔍 基础：快速概览，3-4个章节
   - 📚 标准：平衡深度，5-6个章节
   - 🔬 深入：详细分析，7-8个章节

2. **输出风格**
   - 📖 学术风格：严谨、引用丰富
   - 💼 商业风格：实用、数据驱动
   - 🎯 技术风格：详细、代码示例

3. **语言偏好**
   - 🇨🇳 中文
   - 🇺🇸 英文
   - 🌍 其他语言

### 提纲确认流程

生成提纲后，您可以选择：

- ✅ **确认并继续** - 使用当前提纲开始研究
- 🔄 **自动改进** - AI 自动优化提纲
- ✏️ **手动编辑** - 直接编辑提纲内容
- 🔁 **重新生成** - 完全重新生成提纲
- ⏭️ **跳过交互** - 继续使用当前提纲

### 反馈和修改

您可以提供具体的修改意见：

```
请在第二章增加关于技术挑战的内容
请将第三章拆分为两个独立章节
请增加更多实际应用案例
```

## 📊 输出格式

### Markdown 报告结构

```markdown
# 研究主题

## 摘要
- 研究背景
- 主要发现
- 结论建议

## 目录
- 自动生成的章节导航

## 第一章：背景介绍
- 详细内容...

## 第二章：现状分析
- 详细内容...

## 结论
- 总结和建议

## 参考资料
- 自动收集的参考链接
```

### 输出文件

研究完成后，您将获得：

- 📄 `research_report.md` - 主要研究报告
- 📋 `outline.json` - 结构化提纲数据
- 📊 `metadata.json` - 研究元数据
- 📝 `research.log` - 详细执行日志

## 🔍 配置管理

### 检查配置状态
```bash
./run.sh config-check
```

输出示例：
```
🔍 检查系统配置...

📊 API 密钥状态:
✅ OpenAI API - 已配置
✅ SerpAPI - 已配置
❌ Claude API - 未配置
❌ Gemini API - 未配置

🛠️ 工具配置:
✅ 搜索引擎 - 已启用
✅ 代码执行 - 已启用
✅ 浏览器工具 - 已启用

📁 目录结构:
✅ output/ - 存在
✅ logs/ - 存在
✅ cache/ - 存在
```

### 编辑配置
```bash
# 编辑主配置文件
nano config.yml

# 编辑环境变量
nano .env
```

## 🆘 常见问题

### Q: 如何选择最佳的 LLM 提供商？

**A:** 不同提供商有各自优势：
- **OpenAI GPT-4**: 综合能力强，适合大多数任务
- **Claude**: 长文本处理优秀，适合深度分析
- **Gemini**: 多模态能力强，适合复杂研究
- **Ollama**: 本地部署，隐私性好

### Q: 交互模式和自动模式如何选择？

**A:** 选择建议：
- **交互模式**: 重要研究、需要精确控制、首次使用
- **自动模式**: 批量处理、标准化任务、快速生成

### Q: 如何提高研究质量？

**A:** 优化建议：
1. 配置多个搜索引擎 API
2. 使用交互模式提供详细反馈
3. 选择合适的研究深度
4. 提供具体明确的研究主题

### Q: 遇到错误怎么办？

**A:** 故障排除步骤：
1. 运行 `./run.sh config-check` 检查配置
2. 查看日志文件 `deepresearch.log`
3. 尝试重新安装 `./setup.sh`
4. 查看 [故障排除指南](troubleshooting.md)

## 📚 进阶学习

### 推荐阅读顺序

1. **新手用户**
   - [安装指南](installation.md) ← 您在这里
   - [API 密钥配置](api-keys.md)
   - [基础教程](basic-tutorial.md)

2. **进阶用户**
   - [高级使用指南](advanced-usage.md)
   - [配置文件详解](configuration.md)
   - [工具系统](tools.md)

3. **开发者**
   - [架构设计](architecture.md)
   - [扩展开发](development.md)
   - [API 参考](api-reference.md)

### 实用资源

- 🎥 **视频教程**: [YouTube 频道](#)
- 💬 **社区讨论**: [GitHub Discussions](#)
- 📖 **示例库**: [examples/](../examples/)
- 🔧 **工具插件**: [plugins/](../plugins/)

## 🎉 开始您的研究之旅

现在您已经掌握了基本使用方法，可以开始您的智能研究之旅了！

```bash
# 开始您的第一个研究项目
./run.sh interactive "您感兴趣的研究主题"
```

---

**祝您研究愉快！** 🔬✨ 