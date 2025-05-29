# DeepResearch 贡献指南

## 🤝 欢迎贡献

感谢您对 DeepResearch 项目的关注！我们欢迎各种形式的贡献，包括但不限于：

- 🐛 报告和修复 Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🧪 编写测试
- 🔧 代码优化
- 🌍 国际化支持

## 📋 贡献方式

### 1. 报告问题

如果您发现了 Bug 或有功能建议，请：

1. 检查 [Issues](https://github.com/your-repo/deepresearch/issues) 是否已有相关问题
2. 如果没有，创建新的 Issue
3. 使用合适的 Issue 模板
4. 提供详细的描述和复现步骤

#### Bug 报告模板

```markdown
## Bug 描述
简要描述遇到的问题

## 复现步骤
1. 执行命令: `./run.sh interactive "主题"`
2. 选择选项: ...
3. 出现错误: ...

## 预期行为
描述您期望的正确行为

## 实际行为
描述实际发生的情况

## 环境信息
- 操作系统: macOS 14.0
- Python 版本: 3.11.5
- DeepResearch 版本: 2.0.0

## 错误日志
```
粘贴相关错误信息
```

## 附加信息
其他可能有用的信息
```

#### 功能请求模板

```markdown
## 功能描述
清晰描述您希望添加的功能

## 使用场景
描述这个功能的使用场景和价值

## 建议实现
如果有想法，描述可能的实现方式

## 替代方案
是否考虑过其他解决方案

## 附加信息
其他相关信息
```

### 2. 代码贡献

#### 开发环境设置

```bash
# 1. Fork 项目到您的 GitHub 账户

# 2. 克隆您的 Fork
git clone https://github.com/your-username/deepresearch.git
cd deepresearch

# 3. 添加上游仓库
git remote add upstream https://github.com/original-repo/deepresearch.git

# 4. 创建开发环境
./setup.sh

# 5. 安装开发依赖
pip install -r requirements-dev.txt

# 6. 安装 pre-commit hooks
pre-commit install
```

#### 开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/your-feature-name

# 2. 进行开发
# 编写代码、测试、文档

# 3. 运行测试
pytest tests/

# 4. 运行代码检查
flake8 .
black .
isort .

# 5. 提交更改
git add .
git commit -m "feat: add your feature description"

# 6. 推送到您的 Fork
git push origin feature/your-feature-name

# 7. 创建 Pull Request
```

## 📝 代码规范

### Python 代码风格

我们使用以下工具确保代码质量：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码检查
- **mypy**: 类型检查

#### 配置文件

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

#### 代码示例

```python
from typing import Dict, List, Optional, Union
import asyncio
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ResearchConfig:
    """研究配置类"""
    
    topic: str
    provider: str = "openai"
    max_sections: int = 5
    language: str = "zh-CN"


class ResearchAgent:
    """研究代理类"""
    
    def __init__(self, config: ResearchConfig) -> None:
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
    async def generate_outline(self, topic: str) -> Dict[str, Union[str, List[str]]]:
        """生成研究提纲
        
        Args:
            topic: 研究主题
            
        Returns:
            包含提纲信息的字典
            
        Raises:
            ValueError: 当主题为空时
        """
        if not topic.strip():
            raise ValueError("研究主题不能为空")
        
        self.logger.info(f"开始生成提纲: {topic}")
        
        # 实现逻辑
        outline = {
            "title": topic,
            "sections": ["引言", "现状分析", "发展趋势", "结论"]
        }
        
        return outline
```

### 命名规范

- **类名**: 使用 PascalCase (如 `ResearchAgent`)
- **函数名**: 使用 snake_case (如 `generate_outline`)
- **变量名**: 使用 snake_case (如 `research_config`)
- **常量**: 使用 UPPER_SNAKE_CASE (如 `MAX_RETRIES`)
- **私有方法**: 以下划线开头 (如 `_internal_method`)

### 文档字符串

使用 Google 风格的文档字符串：

```python
def search_information(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """搜索相关信息
    
    Args:
        query: 搜索查询字符串
        max_results: 最大结果数量，默认为 10
        
    Returns:
        包含搜索结果的字典列表，每个字典包含 title、url、snippet 字段
        
    Raises:
        SearchError: 当搜索失败时
        ValueError: 当查询字符串为空时
        
    Example:
        >>> results = search_information("人工智能", max_results=5)
        >>> print(len(results))
        5
    """
    pass
```

## 🧪 测试要求

### 测试结构

```
tests/
├── unit/                 # 单元测试
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_utils.py
├── integration/          # 集成测试
│   ├── test_workflow.py
│   └── test_api.py
├── e2e/                 # 端到端测试
│   └── test_research_flow.py
└── fixtures/            # 测试数据
    ├── sample_configs.py
    └── mock_responses.py
```

### 测试示例

```python
import pytest
from unittest.mock import Mock, patch
from agents.research_agent import ResearchAgent
from config import ResearchConfig


class TestResearchAgent:
    """研究代理测试类"""
    
    @pytest.fixture
    def config(self):
        """测试配置"""
        return ResearchConfig(
            topic="测试主题",
            provider="openai",
            max_sections=3
        )
    
    @pytest.fixture
    def agent(self, config):
        """研究代理实例"""
        return ResearchAgent(config)
    
    def test_init(self, agent, config):
        """测试初始化"""
        assert agent.config == config
        assert agent.logger is not None
    
    @pytest.mark.asyncio
    async def test_generate_outline_success(self, agent):
        """测试成功生成提纲"""
        topic = "人工智能发展趋势"
        
        with patch.object(agent, '_call_llm') as mock_llm:
            mock_llm.return_value = {
                "title": topic,
                "sections": ["引言", "现状", "趋势"]
            }
            
            result = await agent.generate_outline(topic)
            
            assert result["title"] == topic
            assert len(result["sections"]) == 3
            mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_outline_empty_topic(self, agent):
        """测试空主题异常"""
        with pytest.raises(ValueError, match="研究主题不能为空"):
            await agent.generate_outline("")
    
    @pytest.mark.parametrize("topic,expected_sections", [
        ("AI技术", 3),
        ("区块链应用", 4),
        ("量子计算", 5),
    ])
    @pytest.mark.asyncio
    async def test_generate_outline_various_topics(self, agent, topic, expected_sections):
        """测试不同主题的提纲生成"""
        with patch.object(agent, '_call_llm') as mock_llm:
            mock_llm.return_value = {
                "title": topic,
                "sections": ["section"] * expected_sections
            }
            
            result = await agent.generate_outline(topic)
            assert len(result["sections"]) == expected_sections
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_agents.py

# 运行特定测试类
pytest tests/unit/test_agents.py::TestResearchAgent

# 运行特定测试方法
pytest tests/unit/test_agents.py::TestResearchAgent::test_generate_outline_success

# 生成覆盖率报告
pytest --cov=. --cov-report=html

# 运行性能测试
pytest tests/performance/ --benchmark-only
```

## 📚 文档贡献

### 文档结构

```
docs/
├── installation.md       # 安装指南
├── quickstart.md        # 快速入门
├── api-reference.md     # API 参考
├── contributing.md      # 贡献指南
├── architecture.md      # 架构设计
└── examples/           # 示例代码
    ├── basic_usage.py
    └── advanced_features.py
```

### 文档规范

1. **使用 Markdown 格式**
2. **添加目录结构**
3. **包含代码示例**
4. **提供清晰的步骤说明**
5. **使用适当的表情符号增强可读性**

#### 文档模板

```markdown
# 文档标题

## 📋 概览
简要描述文档内容

## 🚀 快速开始
提供快速上手的步骤

### 步骤 1: 准备工作
详细说明

### 步骤 2: 执行操作
```bash
# 代码示例
command --option value
```

## 🔧 详细配置
深入的配置说明

## 💡 最佳实践
使用建议和技巧

## 🆘 常见问题
FAQ 部分

## 📚 相关文档
链接到其他相关文档
```

## 🔄 Pull Request 流程

### PR 检查清单

在提交 PR 之前，请确保：

- [ ] 代码通过所有测试
- [ ] 代码符合项目风格规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确
- [ ] PR 描述详细完整

### PR 模板

```markdown
## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 性能优化
- [ ] 代码重构

## 变更描述
简要描述您的更改

## 相关 Issue
关闭 #issue_number

## 测试
描述您如何测试这些更改

## 检查清单
- [ ] 代码通过所有测试
- [ ] 代码符合风格规范
- [ ] 添加了测试
- [ ] 更新了文档

## 截图（如适用）
添加截图帮助解释您的更改

## 附加信息
其他相关信息
```

### 代码审查

所有 PR 都需要经过代码审查：

1. **自动检查**: CI/CD 流水线会自动运行测试和代码检查
2. **人工审查**: 至少需要一位维护者的批准
3. **反馈处理**: 根据审查意见进行修改
4. **合并**: 审查通过后合并到主分支

## 🏷️ 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 提交类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

### 示例

```bash
# 新功能
git commit -m "feat(agents): add sentiment analysis agent"

# Bug 修复
git commit -m "fix(search): handle rate limit errors properly"

# 文档更新
git commit -m "docs(api): update authentication examples"

# 重构
git commit -m "refactor(tools): simplify browser tool interface"
```

## 🚀 发布流程

### 版本号规范

使用 [Semantic Versioning](https://semver.org/)：

- `MAJOR.MINOR.PATCH` (如 2.1.0)
- `MAJOR`: 不兼容的 API 更改
- `MINOR`: 向后兼容的功能添加
- `PATCH`: 向后兼容的 Bug 修复

### 发布步骤

1. **更新版本号**
2. **更新 CHANGELOG.md**
3. **创建 Release Tag**
4. **发布到 PyPI**
5. **更新文档**

## 🌍 国际化

### 添加新语言支持

1. **创建翻译文件**
   ```
   locales/
   ├── en_US/
   │   └── messages.po
   ├── zh_CN/
   │   └── messages.po
   └── ja_JP/
       └── messages.po
   ```

2. **更新代码**
   ```python
   from utils.i18n import _
   
   message = _("Research completed successfully")
   ```

3. **测试翻译**
   ```bash
   # 提取翻译字符串
   pybabel extract -F babel.cfg -o messages.pot .
   
   # 更新翻译文件
   pybabel update -i messages.pot -d locales
   ```

## 🎯 开发最佳实践

### 1. 代码组织

- 保持函数和类的单一职责
- 使用清晰的命名
- 避免深层嵌套
- 适当使用设计模式

### 2. 错误处理

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ResearchError(Exception):
    """研究相关错误基类"""
    pass

class APIError(ResearchError):
    """API 调用错误"""
    pass

def safe_api_call(func, *args, **kwargs) -> Optional[dict]:
    """安全的 API 调用"""
    try:
        return func(*args, **kwargs)
    except APIError as e:
        logger.error(f"API 调用失败: {e}")
        return None
    except Exception as e:
        logger.exception(f"未预期的错误: {e}")
        raise ResearchError(f"操作失败: {e}") from e
```

### 3. 性能优化

- 使用异步编程
- 实现适当的缓存
- 避免不必要的计算
- 监控内存使用

### 4. 安全考虑

- 验证所有输入
- 使用参数化查询
- 保护敏感信息
- 实现适当的权限控制

## 🆘 获取帮助

如果您在贡献过程中遇到问题：

1. **查看文档**: 首先查看相关文档
2. **搜索 Issues**: 查看是否有类似问题
3. **提问**: 在 Discussions 中提问
4. **联系维护者**: 通过 Email 或 GitHub 联系

### 联系方式

- **GitHub Issues**: [项目 Issues](https://github.com/your-repo/deepresearch/issues)
- **GitHub Discussions**: [项目讨论区](https://github.com/your-repo/deepresearch/discussions)
- **Email**: maintainers@deepresearch.org

## 🙏 致谢

感谢所有为 DeepResearch 项目做出贡献的开发者！

### 贡献者列表

- [@contributor1](https://github.com/contributor1) - 核心开发
- [@contributor2](https://github.com/contributor2) - 文档改进
- [@contributor3](https://github.com/contributor3) - Bug 修复

### 特别感谢

- 所有提供反馈和建议的用户
- 开源社区的支持和帮助
- 相关技术栈的维护者

---

**让我们一起让 DeepResearch 变得更好！** 🚀✨ 