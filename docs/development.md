# DeepResearch 开发指南

## 🎯 概览

本指南面向开发者，介绍如何扩展 DeepResearch 系统、开发自定义插件和贡献代码。

## 🏗️ 开发环境设置

### 克隆和安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/deepresearch.git
cd deepresearch

# 创建开发环境
conda create -n deepresearch-dev python=3.11 -y
conda activate deepresearch-dev

# 安装开发依赖
pip install -r requirements-dev.txt

# 安装预提交钩子
pre-commit install

# 运行测试
pytest
```

### 开发依赖

```txt
# requirements-dev.txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.0.0
pre-commit>=3.0.0
sphinx>=6.0.0
sphinx-rtd-theme>=1.2.0
```

## 🧩 插件开发

### 基础插件结构

```python
# plugins/example_plugin.py
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class BasePlugin(ABC):
    """插件基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.enabled = config.get("enabled", True)
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行插件逻辑"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理资源"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "description": self.__doc__ or "No description"
        }

class ExamplePlugin(BasePlugin):
    """示例插件"""
    
    async def initialize(self) -> bool:
        """初始化插件"""
        print(f"初始化插件: {self.name}")
        return True
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行插件逻辑"""
        topic = context.get("topic", "")
        
        # 插件逻辑
        result = f"插件处理结果: {topic}"
        
        return {
            "plugin_result": result,
            "status": "success"
        }
    
    async def cleanup(self) -> None:
        """清理资源"""
        print(f"清理插件: {self.name}")
```

### 插件管理器

```python
# core/plugin_manager.py
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Type
from plugins.base_plugin import BasePlugin

class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, BasePlugin] = {}
        self.hooks: Dict[str, List[BasePlugin]] = {}
    
    async def load_plugins(self) -> None:
        """加载所有插件"""
        
        if not self.plugin_dir.exists():
            return
        
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            
            await self._load_plugin_file(plugin_file)
    
    async def _load_plugin_file(self, plugin_file: Path) -> None:
        """加载单个插件文件"""
        
        try:
            # 动态导入模块
            module_name = f"plugins.{plugin_file.stem}"
            module = importlib.import_module(module_name)
            
            # 查找插件类
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BasePlugin) and 
                    obj != BasePlugin):
                    
                    # 创建插件实例
                    config = self._get_plugin_config(name)
                    plugin = obj(config)
                    
                    if plugin.enabled:
                        await plugin.initialize()
                        self.plugins[name] = plugin
                        print(f"加载插件: {name}")
        
        except Exception as e:
            print(f"加载插件失败 {plugin_file}: {e}")
    
    def _get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件配置"""
        # 从配置文件或环境变量获取配置
        return {
            "enabled": True,
            "debug": False
        }
    
    async def execute_hook(self, hook_name: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行钩子"""
        
        results = []
        
        for plugin in self.plugins.values():
            if hasattr(plugin, f"on_{hook_name}"):
                try:
                    hook_method = getattr(plugin, f"on_{hook_name}")
                    result = await hook_method(context)
                    results.append(result)
                except Exception as e:
                    print(f"插件 {plugin.name} 执行钩子 {hook_name} 失败: {e}")
        
        return results
    
    async def cleanup_all(self) -> None:
        """清理所有插件"""
        
        for plugin in self.plugins.values():
            try:
                await plugin.cleanup()
            except Exception as e:
                print(f"清理插件 {plugin.name} 失败: {e}")
```

## 🛠️ 自定义工具开发

### 工具基类

```python
# tools/base_tool.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
import asyncio

class BaseTool(ABC):
    """工具基类"""
    
    name: str = ""
    description: str = ""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
    
    @abstractmethod
    def _run(self, *args, **kwargs) -> Any:
        """同步执行工具"""
        pass
    
    async def _arun(self, *args, **kwargs) -> Any:
        """异步执行工具"""
        # 默认实现：在线程池中运行同步方法
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, *args, **kwargs)
    
    def run(self, *args, **kwargs) -> Any:
        """运行工具（同步）"""
        if not self.enabled:
            raise RuntimeError(f"工具 {self.name} 已禁用")
        
        return self._run(*args, **kwargs)
    
    async def arun(self, *args, **kwargs) -> Any:
        """运行工具（异步）"""
        if not self.enabled:
            raise RuntimeError(f"工具 {self.name} 已禁用")
        
        return await self._arun(*args, **kwargs)
    
    def get_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "config": self.config
        }
```

### 自定义工具示例

```python
# tools/custom_analyzer.py
import re
import json
from typing import Dict, Any, List
from tools.base_tool import BaseTool

class TextAnalyzer(BaseTool):
    """文本分析工具"""
    
    name = "text_analyzer"
    description = "分析文本的各种特征"
    
    def _run(self, text: str, analysis_types: List[str] = None) -> Dict[str, Any]:
        """执行文本分析"""
        
        if analysis_types is None:
            analysis_types = ["basic", "sentiment", "keywords"]
        
        results = {}
        
        if "basic" in analysis_types:
            results["basic"] = self._basic_analysis(text)
        
        if "sentiment" in analysis_types:
            results["sentiment"] = self._sentiment_analysis(text)
        
        if "keywords" in analysis_types:
            results["keywords"] = self._keyword_extraction(text)
        
        if "readability" in analysis_types:
            results["readability"] = self._readability_analysis(text)
        
        return results
    
    def _basic_analysis(self, text: str) -> Dict[str, Any]:
        """基础文本分析"""
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')
        
        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "paragraph_count": len([p for p in paragraphs if p.strip()]),
            "avg_words_per_sentence": len(words) / max(len(sentences), 1),
            "avg_chars_per_word": len(text) / max(len(words), 1)
        }
    
    def _sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """情感分析"""
        
        positive_words = ["好", "优秀", "成功", "增长", "创新", "有效", "重要"]
        negative_words = ["差", "失败", "下降", "问题", "困难", "错误", "危险"]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        sentiment_score = (positive_count - negative_count) / max(total_words, 1)
        
        if sentiment_score > 0.05:
            sentiment = "positive"
        elif sentiment_score < -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": sentiment_score,
            "positive_indicators": positive_count,
            "negative_indicators": negative_count,
            "confidence": abs(sentiment_score)
        }
    
    def _keyword_extraction(self, text: str) -> Dict[str, Any]:
        """关键词提取"""
        
        # 简单的关键词提取
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 过滤停用词
        stop_words = {"的", "是", "在", "有", "和", "与", "或", "但", "而", "了", "着", "过"}
        filtered_words = [w for w in words if w not in stop_words and len(w) > 1]
        
        # 统计词频
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 排序获取关键词
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "keywords": keywords,
            "total_unique_words": len(word_freq),
            "word_frequency": word_freq
        }
    
    def _readability_analysis(self, text: str) -> Dict[str, Any]:
        """可读性分析"""
        
        sentences = re.split(r'[.!?]+', text)
        words = text.split()
        
        if not sentences or not words:
            return {"readability_score": 0, "level": "unknown"}
        
        avg_sentence_length = len(words) / len(sentences)
        
        # 简化的可读性评分
        if avg_sentence_length <= 15:
            level = "easy"
            score = 0.9
        elif avg_sentence_length <= 25:
            level = "medium"
            score = 0.7
        else:
            level = "hard"
            score = 0.5
        
        return {
            "readability_score": score,
            "level": level,
            "avg_sentence_length": avg_sentence_length,
            "total_sentences": len(sentences),
            "total_words": len(words)
        }

class DataVisualizer(BaseTool):
    """数据可视化工具"""
    
    name = "data_visualizer"
    description = "创建数据可视化图表"
    
    def _run(self, data: Dict[str, Any], chart_type: str = "bar") -> str:
        """生成可视化图表"""
        
        try:
            import matplotlib.pyplot as plt
            import json
            from pathlib import Path
            
            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if chart_type == "bar":
                self._create_bar_chart(ax, data)
            elif chart_type == "line":
                self._create_line_chart(ax, data)
            elif chart_type == "pie":
                self._create_pie_chart(ax, data)
            else:
                raise ValueError(f"不支持的图表类型: {chart_type}")
            
            # 保存图表
            output_dir = Path("output/charts")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            chart_file = output_dir / f"chart_{chart_type}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_file)
        
        except ImportError:
            return "错误: 需要安装 matplotlib"
        except Exception as e:
            return f"生成图表失败: {e}"
    
    def _create_bar_chart(self, ax, data):
        """创建柱状图"""
        if "x" in data and "y" in data:
            ax.bar(data["x"], data["y"])
            ax.set_xlabel("X轴")
            ax.set_ylabel("Y轴")
            ax.set_title("柱状图")
    
    def _create_line_chart(self, ax, data):
        """创建折线图"""
        if "x" in data and "y" in data:
            ax.plot(data["x"], data["y"], marker='o')
            ax.set_xlabel("X轴")
            ax.set_ylabel("Y轴")
            ax.set_title("折线图")
            ax.grid(True)
    
    def _create_pie_chart(self, ax, data):
        """创建饼图"""
        if "labels" in data and "values" in data:
            ax.pie(data["values"], labels=data["labels"], autopct='%1.1f%%')
            ax.set_title("饼图")
```

### 工具注册

```python
# tools/registry.py
from typing import Dict, List, Type, Optional
from tools.base_tool import BaseTool

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._instances: Dict[str, BaseTool] = {}
    
    def register(self, tool_class: Type[BaseTool]) -> None:
        """注册工具类"""
        if not issubclass(tool_class, BaseTool):
            raise ValueError("工具必须继承自 BaseTool")
        
        tool_name = tool_class.name or tool_class.__name__.lower()
        self._tools[tool_name] = tool_class
        print(f"注册工具: {tool_name}")
    
    def get_tool(self, name: str, config: Optional[Dict] = None) -> BaseTool:
        """获取工具实例"""
        if name not in self._tools:
            raise ValueError(f"未找到工具: {name}")
        
        # 使用缓存的实例或创建新实例
        cache_key = f"{name}_{hash(str(config))}"
        
        if cache_key not in self._instances:
            tool_class = self._tools[name]
            self._instances[cache_key] = tool_class(config)
        
        return self._instances[cache_key]
    
    def list_tools(self) -> List[str]:
        """列出所有注册的工具"""
        return list(self._tools.keys())
    
    def get_tool_info(self, name: str) -> Dict:
        """获取工具信息"""
        if name not in self._tools:
            raise ValueError(f"未找到工具: {name}")
        
        tool_class = self._tools[name]
        return {
            "name": tool_class.name or name,
            "description": tool_class.description,
            "class": tool_class.__name__
        }

# 全局工具注册表
tool_registry = ToolRegistry()

# 注册内置工具
from tools.custom_analyzer import TextAnalyzer, DataVisualizer

tool_registry.register(TextAnalyzer)
tool_registry.register(DataVisualizer)
```

## 🤖 自定义 Agent 开发

### Agent 基类

```python
# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from llm.base import BaseLLM
from tools.registry import tool_registry

class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, 
                 llm: BaseLLM,
                 tools: Optional[List[str]] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.llm = llm
        self.config = config or {}
        self.tools = {}
        
        # 初始化工具
        if tools:
            for tool_name in tools:
                self.tools[tool_name] = tool_registry.get_tool(tool_name)
    
    @abstractmethod
    async def execute(self, input_data: Any) -> Any:
        """执行 Agent 任务"""
        pass
    
    async def use_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """使用工具"""
        if tool_name not in self.tools:
            raise ValueError(f"Agent 未配置工具: {tool_name}")
        
        tool = self.tools[tool_name]
        return await tool.arun(*args, **kwargs)
    
    def get_available_tools(self) -> List[str]:
        """获取可用工具列表"""
        return list(self.tools.keys())

class CustomAnalysisAgent(BaseAgent):
    """自定义分析 Agent"""
    
    async def execute(self, text: str) -> Dict[str, Any]:
        """执行文本分析"""
        
        # 使用文本分析工具
        analysis_result = await self.use_tool(
            "text_analyzer", 
            text, 
            ["basic", "sentiment", "keywords", "readability"]
        )
        
        # 使用 LLM 生成分析报告
        prompt = f"""
        基于以下文本分析结果，生成一份详细的分析报告：
        
        分析结果：
        {analysis_result}
        
        原文本：
        {text[:500]}...
        
        请提供：
        1. 文本特征总结
        2. 情感倾向分析
        3. 关键主题识别
        4. 可读性评估
        5. 改进建议
        """
        
        report = await self.llm.agenerate([prompt])
        
        return {
            "analysis_data": analysis_result,
            "analysis_report": report.generations[0][0].text,
            "agent": self.__class__.__name__
        }
```

## 🔄 工作流扩展

### 自定义工作流节点

```python
# workflow/custom_nodes.py
from typing import Dict, Any
from workflow.base_node import BaseNode

class DataCollectionNode(BaseNode):
    """数据收集节点"""
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据收集"""
        
        topic = context.get("topic", "")
        
        # 多源数据收集
        search_results = await self._search_web(topic)
        academic_papers = await self._search_academic(topic)
        news_articles = await self._search_news(topic)
        
        collected_data = {
            "web_results": search_results,
            "academic_papers": academic_papers,
            "news_articles": news_articles,
            "collection_timestamp": self._get_timestamp()
        }
        
        context["collected_data"] = collected_data
        return context
    
    async def _search_web(self, topic: str) -> List[Dict]:
        """搜索网页"""
        # 实现网页搜索逻辑
        return []
    
    async def _search_academic(self, topic: str) -> List[Dict]:
        """搜索学术论文"""
        # 实现学术搜索逻辑
        return []
    
    async def _search_news(self, topic: str) -> List[Dict]:
        """搜索新闻文章"""
        # 实现新闻搜索逻辑
        return []

class QualityAssuranceNode(BaseNode):
    """质量保证节点"""
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行质量检查"""
        
        content = context.get("content", "")
        
        # 质量检查
        quality_score = await self._assess_quality(content)
        
        if quality_score < 0.7:
            # 质量不达标，触发改进流程
            improved_content = await self._improve_content(content)
            context["content"] = improved_content
            context["quality_improved"] = True
        
        context["quality_score"] = quality_score
        return context
    
    async def _assess_quality(self, content: str) -> float:
        """评估内容质量"""
        # 实现质量评估逻辑
        return 0.8
    
    async def _improve_content(self, content: str) -> str:
        """改进内容"""
        # 实现内容改进逻辑
        return content
```

### 工作流编排

```python
# workflow/custom_workflow.py
from typing import List, Dict, Any
from workflow.base_workflow import BaseWorkflow
from workflow.custom_nodes import DataCollectionNode, QualityAssuranceNode

class EnhancedResearchWorkflow(BaseWorkflow):
    """增强研究工作流"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.setup_nodes()
    
    def setup_nodes(self):
        """设置工作流节点"""
        
        # 添加自定义节点
        self.add_node("data_collection", DataCollectionNode())
        self.add_node("quality_assurance", QualityAssuranceNode())
        
        # 定义节点执行顺序
        self.add_edge("start", "data_collection")
        self.add_edge("data_collection", "outline_generation")
        self.add_edge("outline_generation", "content_generation")
        self.add_edge("content_generation", "quality_assurance")
        self.add_edge("quality_assurance", "end")
        
        # 条件分支
        self.add_conditional_edge(
            "quality_assurance",
            self._should_improve_quality,
            {
                True: "content_generation",  # 重新生成内容
                False: "end"                 # 结束流程
            }
        )
    
    def _should_improve_quality(self, context: Dict[str, Any]) -> bool:
        """判断是否需要改进质量"""
        quality_score = context.get("quality_score", 0)
        return quality_score < 0.8
```

## 🧪 测试开发

### 单元测试

```python
# tests/test_custom_tools.py
import pytest
from tools.custom_analyzer import TextAnalyzer, DataVisualizer

class TestTextAnalyzer:
    """文本分析工具测试"""
    
    @pytest.fixture
    def analyzer(self):
        return TextAnalyzer()
    
    def test_basic_analysis(self, analyzer):
        """测试基础分析"""
        text = "这是一个测试文本。它包含两个句子。"
        result = analyzer._basic_analysis(text)
        
        assert result["word_count"] > 0
        assert result["sentence_count"] == 2
        assert result["character_count"] == len(text)
    
    def test_sentiment_analysis(self, analyzer):
        """测试情感分析"""
        positive_text = "这是一个非常好的产品，效果优秀。"
        negative_text = "这个产品很差，存在很多问题。"
        
        positive_result = analyzer._sentiment_analysis(positive_text)
        negative_result = analyzer._sentiment_analysis(negative_text)
        
        assert positive_result["sentiment"] == "positive"
        assert negative_result["sentiment"] == "negative"
    
    @pytest.mark.asyncio
    async def test_async_run(self, analyzer):
        """测试异步运行"""
        text = "测试异步执行功能。"
        result = await analyzer.arun(text, ["basic"])
        
        assert "basic" in result
        assert result["basic"]["word_count"] > 0

class TestDataVisualizer:
    """数据可视化工具测试"""
    
    @pytest.fixture
    def visualizer(self):
        return DataVisualizer()
    
    def test_bar_chart_creation(self, visualizer):
        """测试柱状图创建"""
        data = {
            "x": ["A", "B", "C"],
            "y": [1, 2, 3]
        }
        
        result = visualizer._run(data, "bar")
        assert "chart_bar.png" in result
```

### 集成测试

```python
# tests/test_integration.py
import pytest
from workflow.custom_workflow import EnhancedResearchWorkflow

class TestEnhancedWorkflow:
    """增强工作流集成测试"""
    
    @pytest.fixture
    def workflow(self):
        config = {
            "llm_provider": "openai",
            "max_sections": 5,
            "quality_threshold": 0.8
        }
        return EnhancedResearchWorkflow(config)
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, workflow):
        """测试完整工作流"""
        topic = "人工智能发展趋势"
        
        result = await workflow.run({"topic": topic})
        
        assert "content" in result
        assert "quality_score" in result
        assert result["quality_score"] >= 0.7
    
    @pytest.mark.asyncio
    async def test_quality_improvement_loop(self, workflow):
        """测试质量改进循环"""
        # 模拟低质量内容
        context = {
            "topic": "测试主题",
            "content": "低质量内容",
            "quality_score": 0.5
        }
        
        # 应该触发改进流程
        should_improve = workflow._should_improve_quality(context)
        assert should_improve is True
```

## 📦 打包和分发

### 创建插件包

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="deepresearch-custom-plugin",
    version="1.0.0",
    description="DeepResearch 自定义插件",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "deepresearch>=2.0.0",
    ],
    entry_points={
        "deepresearch.plugins": [
            "custom_plugin = plugins.custom_plugin:CustomPlugin",
        ],
        "deepresearch.tools": [
            "text_analyzer = tools.custom_analyzer:TextAnalyzer",
            "data_visualizer = tools.custom_analyzer:DataVisualizer",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)
```

### 插件配置

```yaml
# plugin_config.yml
plugin:
  name: "custom_research_plugin"
  version: "1.0.0"
  description: "自定义研究插件"
  
  dependencies:
    - "matplotlib>=3.5.0"
    - "pandas>=1.3.0"
  
  hooks:
    - "before_research"
    - "after_outline_generation"
    - "before_content_generation"
    - "after_research"
  
  tools:
    - "text_analyzer"
    - "data_visualizer"
  
  configuration:
    enable_advanced_analysis: true
    visualization_format: "png"
    quality_threshold: 0.8
```

## 🔧 调试和性能优化

### 调试工具

```python
# debug/profiler.py
import cProfile
import pstats
import functools
from typing import Callable

def profile_function(func: Callable) -> Callable:
    """函数性能分析装饰器"""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profiler.disable()
            
            # 保存分析结果
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            stats.print_stats(20)  # 显示前20个最耗时的函数
    
    return wrapper

# 使用示例
@profile_function
def expensive_function():
    """耗时函数"""
    import time
    time.sleep(1)
    return "完成"
```

### 内存监控

```python
# debug/memory_monitor.py
import psutil
import tracemalloc
from typing import Dict, Any

class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self):
        self.start_memory = None
        self.peak_memory = 0
    
    def start(self):
        """开始监控"""
        tracemalloc.start()
        self.start_memory = psutil.Process().memory_info().rss
    
    def get_current_usage(self) -> Dict[str, Any]:
        """获取当前内存使用"""
        current_memory = psutil.Process().memory_info().rss
        
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            
            return {
                "current_rss": current_memory,
                "start_rss": self.start_memory,
                "memory_increase": current_memory - self.start_memory,
                "traced_current": current,
                "traced_peak": peak
            }
        
        return {
            "current_rss": current_memory,
            "start_rss": self.start_memory,
            "memory_increase": current_memory - self.start_memory
        }
    
    def stop(self) -> Dict[str, Any]:
        """停止监控并返回统计"""
        usage = self.get_current_usage()
        
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        
        return usage

# 使用示例
monitor = MemoryMonitor()
monitor.start()

# 执行代码...

usage = monitor.stop()
print(f"内存使用增加: {usage['memory_increase'] / 1024 / 1024:.2f} MB")
```

## 📚 文档生成

### API 文档

```python
# docs/generate_docs.py
import inspect
import json
from pathlib import Path
from typing import Dict, Any, List

def generate_api_docs(module_path: str, output_dir: str):
    """生成 API 文档"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 扫描模块
    modules = _scan_modules(module_path)
    
    for module_name, module in modules.items():
        doc_data = _extract_module_docs(module)
        
        # 生成 Markdown 文档
        markdown_content = _generate_markdown(module_name, doc_data)
        
        doc_file = output_path / f"{module_name}.md"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    print(f"API 文档已生成到: {output_dir}")

def _extract_module_docs(module) -> Dict[str, Any]:
    """提取模块文档"""
    
    classes = []
    functions = []
    
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj):
            classes.append(_extract_class_docs(obj))
        elif inspect.isfunction(obj):
            functions.append(_extract_function_docs(obj))
    
    return {
        "module_doc": inspect.getdoc(module),
        "classes": classes,
        "functions": functions
    }

def _extract_class_docs(cls) -> Dict[str, Any]:
    """提取类文档"""
    
    methods = []
    for name, method in inspect.getmembers(cls, inspect.ismethod):
        if not name.startswith('_'):
            methods.append(_extract_function_docs(method))
    
    return {
        "name": cls.__name__,
        "doc": inspect.getdoc(cls),
        "methods": methods
    }

def _extract_function_docs(func) -> Dict[str, Any]:
    """提取函数文档"""
    
    signature = inspect.signature(func)
    
    return {
        "name": func.__name__,
        "doc": inspect.getdoc(func),
        "signature": str(signature),
        "parameters": [
            {
                "name": param.name,
                "type": str(param.annotation) if param.annotation != param.empty else "Any",
                "default": str(param.default) if param.default != param.empty else None
            }
            for param in signature.parameters.values()
        ]
    }
```

---

**通过这些开发指南，您可以轻松扩展 DeepResearch 的功能！** 🛠️✨ 