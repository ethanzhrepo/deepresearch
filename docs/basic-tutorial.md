# DeepResearch 基础教程

## 📚 教程概览

本教程将通过实际示例，带您深入了解 DeepResearch 的核心功能和使用技巧。

## 🎯 学习目标

完成本教程后，您将能够：
- 熟练使用交互式和自动化研究模式
- 理解系统的工作流程和配置选项
- 掌握高级功能和优化技巧
- 解决常见问题和故障排除

## 📖 教程内容

### 第一部分：基础操作

#### 1.1 第一个研究项目

让我们从一个简单的研究项目开始：

```bash
# 启动交互式研究
./run.sh interactive "人工智能在教育领域的应用"
```

**步骤详解：**

1. **系统启动**
   ```
   🔬 DeepResearch 自动化深度研究系统
   ╔══════════════════════════════════════════════════════════════╗
   ║                    系统启动脚本                               ║
   ╚══════════════════════════════════════════════════════════════╝
   ```

2. **偏好设置**
   ```
   🎯 研究偏好设置
   
   请选择研究深度:
   1. 🔍 基础 - 快速概览 (3-4章节)
   2. 📚 标准 - 平衡深度 (5-6章节)  ← 推荐
   3. 🔬 深入 - 详细分析 (7-8章节)
   
   请输入选择 (1-3): 2
   ```

3. **提纲生成**
   ```
   📋 正在生成研究提纲...
   ✅ 提纲生成完成
   
   📊 研究提纲预览:
   ┌─────────────────────────────────────────────────────────────┐
   │ 人工智能在教育领域的应用                                      │
   ├─────────────────────────────────────────────────────────────┤
   │ 1. 引言与背景                                               │
   │ 2. AI教育技术概述                                           │
   │ 3. 个性化学习系统                                           │
   │ 4. 智能评估与反馈                                           │
   │ 5. 挑战与未来发展                                           │
   │ 6. 结论与建议                                               │
   └─────────────────────────────────────────────────────────────┘
   ```

4. **提纲确认**
   ```
   🤔 请选择您的操作:
   1. ✅ 确认并继续 - 使用当前提纲开始研究
   2. 🔄 自动改进 - 让AI优化提纲
   3. ✏️ 手动编辑 - 直接编辑提纲内容
   4. 🔁 重新生成 - 完全重新生成提纲
   5. ⏭️ 跳过交互 - 继续使用当前提纲
   
   请输入选择 (1-5): 1
   ```

5. **内容生成**
   ```
   🚀 开始生成研究内容...
   📝 正在研究: 引言与背景
   📝 正在研究: AI教育技术概述
   📝 正在研究: 个性化学习系统
   ...
   ✅ 研究完成！
   ```

#### 1.2 查看研究结果

研究完成后，您会在 `output` 目录找到以下文件：

```bash
output/
├── research_report.md      # 主要研究报告
├── outline.json           # 结构化提纲
├── metadata.json          # 研究元数据
└── research.log           # 执行日志
```

**查看报告：**
```bash
# 使用文本编辑器查看
nano output/research_report.md

# 或使用 Markdown 预览工具
markdown-preview output/research_report.md
```

#### 1.3 自动化模式对比

现在尝试自动化模式：

```bash
./run.sh auto "人工智能在教育领域的应用"
```

**对比分析：**

| 特性 | 交互模式 | 自动模式 |
|------|----------|----------|
| 用户参与 | 🤝 高度参与 | 🤖 无需参与 |
| 执行时间 | ⏱️ 较长 | ⚡ 快速 |
| 结果定制 | 🎯 高度定制 | 📊 标准化 |
| 适用场景 | 📚 重要研究 | 🔄 批量处理 |

### 第二部分：高级功能

#### 2.1 指定 LLM 提供商

不同的 LLM 提供商有不同的优势：

```bash
# 使用 Claude 进行深度分析
./run.sh interactive "区块链技术发展趋势" --provider claude

# 使用 GPT-4 进行综合研究
./run.sh auto "量子计算应用前景" --provider openai

# 使用 Gemini 进行多模态研究
./run.sh interactive "虚拟现实技术应用" --provider gemini
```

**提供商选择建议：**
- **Claude**: 长文本分析、深度思考、学术研究
- **GPT-4**: 综合能力、创意写作、技术文档
- **Gemini**: 多模态处理、数据分析、科学研究

#### 2.2 自定义输出配置

```bash
# 设置输出目录
./run.sh interactive "AI伦理研究" --output ./ethics_research

# 调整章节数量
./run.sh auto "机器学习算法比较" --max-sections 8

# 设置语言
./run.sh interactive "人工智能发展" --language en-US

# 组合使用
./run.sh interactive "深度学习应用" \
  --provider claude \
  --max-sections 6 \
  --output ./deep_learning_study \
  --language zh-CN
```

#### 2.3 调试和监控

启用调试模式获取详细信息：

```bash
# 启用调试模式
./run.sh interactive "研究主题" --debug

# 查看实时日志
tail -f deepresearch.log

# 检查系统状态
./run.sh config-check
```

### 第三部分：交互功能深入

#### 3.1 提纲编辑实战

当您选择"手动编辑"时：

```
✏️ 手动编辑提纲

当前提纲:
1. 引言与背景
2. 技术概述
3. 应用案例
4. 挑战分析
5. 未来展望

请输入您的修改 (输入 'done' 完成):
> 在第3章后增加"商业模式分析"章节
> 将第5章改为"发展趋势与未来展望"
> done

✅ 提纲已更新
```

#### 3.2 反馈优化流程

选择"自动改进"时的交互：

```
🔄 AI 自动改进提纲

请描述您希望的改进方向:
> 增加更多技术细节和实际案例，减少理论部分

🤖 AI 分析中...
✅ 提纲已优化

📊 改进说明:
- 增加了"技术实现细节"章节
- 扩展了"实际应用案例"内容
- 精简了理论背景部分
- 添加了"案例分析"子章节
```

#### 3.3 多轮迭代示例

```
第一轮:
用户: "请增加关于安全性的内容"
系统: ✅ 已添加"安全性考虑"章节

第二轮:
用户: "将安全性章节拆分为技术安全和数据安全"
系统: ✅ 已拆分为两个独立章节

第三轮:
用户: "在数据安全章节增加隐私保护内容"
系统: ✅ 已添加隐私保护子章节
```

### 第四部分：实际应用场景

#### 4.1 学术研究项目

**场景**: 撰写学术论文的文献综述

```bash
./run.sh interactive "深度学习在自然语言处理中的应用综述" \
  --provider claude \
  --max-sections 8 \
  --output ./academic_review
```

**配置偏好**:
- 研究深度: 深入
- 输出风格: 学术风格
- 章节重点: 文献分析、方法比较、实验结果

#### 4.2 商业分析报告

**场景**: 市场调研和竞争分析

```bash
./run.sh interactive "电动汽车市场分析报告" \
  --provider openai \
  --max-sections 6 \
  --output ./market_analysis
```

**配置偏好**:
- 研究深度: 标准
- 输出风格: 商业风格
- 章节重点: 市场数据、竞争对手、发展趋势

#### 4.3 技术调研文档

**场景**: 技术选型和架构设计

```bash
./run.sh interactive "微服务架构设计最佳实践" \
  --provider gemini \
  --max-sections 7 \
  --output ./tech_research
```

**配置偏好**:
- 研究深度: 深入
- 输出风格: 技术风格
- 章节重点: 技术对比、实现方案、代码示例

### 第五部分：优化技巧

#### 5.1 提高研究质量

**1. 精确的主题描述**
```bash
# 好的主题描述
./run.sh interactive "基于Transformer架构的大语言模型在代码生成任务中的应用与优化"

# 避免过于宽泛
./run.sh interactive "人工智能"  # 太宽泛
```

**2. 合理的章节设置**
```bash
# 根据主题复杂度调整章节数
./run.sh interactive "简单主题" --max-sections 4
./run.sh interactive "复杂主题" --max-sections 8
```

**3. 选择合适的提供商**
```bash
# 技术深度分析使用 Claude
./run.sh interactive "技术主题" --provider claude

# 创意和综合分析使用 GPT-4
./run.sh interactive "创新主题" --provider openai
```

#### 5.2 批量处理技巧

**创建批处理脚本**:
```bash
#!/bin/bash
# batch_research.sh

topics=(
  "人工智能在医疗领域的应用"
  "区块链技术发展趋势"
  "量子计算商业化前景"
)

for topic in "${topics[@]}"; do
  echo "开始研究: $topic"
  ./run.sh auto "$topic" --output "./batch_output/$(echo $topic | tr ' ' '_')"
  echo "完成研究: $topic"
done
```

#### 5.3 结果后处理

**合并多个研究报告**:
```bash
# 创建合并脚本
cat > merge_reports.py << 'EOF'
import os
import glob

def merge_reports(output_dir):
    reports = glob.glob(f"{output_dir}/*/research_report.md")
    
    with open(f"{output_dir}/merged_report.md", "w") as merged:
        merged.write("# 综合研究报告\n\n")
        
        for report in reports:
            with open(report, "r") as f:
                content = f.read()
                merged.write(content + "\n\n---\n\n")

if __name__ == "__main__":
    merge_reports("./batch_output")
EOF

python merge_reports.py
```

### 第六部分：故障排除

#### 6.1 常见错误及解决方案

**错误 1: API 密钥无效**
```
❌ Error: Invalid API key for OpenAI

解决方案:
1. 检查 .env 文件中的 API 密钥
2. 确认密钥格式正确 (sk-...)
3. 验证密钥是否有效: ./run.sh config-check
```

**错误 2: 网络连接问题**
```
❌ Error: Connection timeout

解决方案:
1. 检查网络连接
2. 配置代理 (如需要)
3. 尝试不同的搜索引擎
```

**错误 3: 内存不足**
```
❌ Error: Out of memory

解决方案:
1. 减少章节数量: --max-sections 4
2. 使用自动模式而非交互模式
3. 清理缓存: rm -rf cache/*
```

#### 6.2 性能优化

**1. 缓存配置**
```yaml
# config.yml
cache:
  enabled: true
  ttl: 3600  # 1小时
  max_size: 1000  # 最大条目数
```

**2. 并发设置**
```yaml
# config.yml
system:
  max_concurrent_requests: 5
  request_timeout: 30
```

**3. 资源限制**
```yaml
# config.yml
resources:
  max_memory_mb: 2048
  max_cpu_percent: 80
```

## 🎓 进阶学习

### 推荐练习

1. **基础练习**
   - 完成 5 个不同主题的交互式研究
   - 尝试所有 LLM 提供商
   - 练习提纲编辑和反馈

2. **进阶练习**
   - 创建批处理脚本
   - 自定义配置文件
   - 集成外部工具

3. **高级练习**
   - 开发自定义插件
   - 优化系统性能
   - 贡献开源代码

### 下一步学习

完成基础教程后，建议继续学习：

1. [高级使用指南](advanced-usage.md) - 深入功能和配置
2. [工具系统](tools.md) - 了解工具扩展
3. [架构设计](architecture.md) - 理解系统架构
4. [扩展开发](development.md) - 开发自定义功能

## 📝 总结

通过本教程，您已经学会了：

- ✅ 基本的交互式和自动化研究流程
- ✅ 高级配置和优化技巧
- ✅ 实际应用场景的最佳实践
- ✅ 常见问题的故障排除方法

现在您可以开始使用 DeepResearch 进行专业的研究工作了！

---

**继续探索 DeepResearch 的强大功能！** 🚀 