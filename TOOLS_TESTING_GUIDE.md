# DeepResearch 工具测试指南

这个文档提供了所有工具和 Browser-Use 功能的详细测试命令和配置示例。

## 📋 目录

1. [快速验证所有工具](#快速验证所有工具)
2. [搜索引擎测试](#搜索引擎测试)
3. [Browser-Use 工具测试](#browser-use-工具测试)
4. [其他工具测试](#其他工具测试)
5. [完整研究流程测试](#完整研究流程测试)
6. [故障排除](#故障排除)

---

## 🚀 快速验证所有工具

### 1. 检查配置和 API 密钥
```bash
# 检查系统配置
python main.py config-check

# 预期输出：显示所有 API 密钥状态和工具配置
```

### 2. 验证所有工具注册
```bash
# 测试工具注册
python -c "
from tools.tool_registry import ToolRegistry
registry = ToolRegistry()
print('已注册的工具:')
for name, tool in registry.tools.items():
    print(f'  - {name}: {tool.__class__.__name__}')
print(f'\\n总计: {len(registry.tools)} 个工具')
"
```

### 3. 快速搜索引擎测试
```bash
# 测试搜索引擎管理器
python -c "
from tools.search_engines import SearchEngineManager
manager = SearchEngineManager()
print('可用搜索引擎:', list(manager.engines.keys()))
results = manager.search('人工智能', max_results=2)
print(f'搜索结果: {len(results)} 条')
for i, result in enumerate(results[:2], 1):
    print(f'{i}. {result.title[:50]}... (来源: {result.source})')
"
```

---

## 🔍 搜索引擎测试

### Tavily Search (AI 优化搜索)
```bash
# 基础 Tavily 搜索测试
python -c "
from tools.search_engines import TavilySearch
import os

config = {
    'api_key': os.getenv('TAVILY_API_KEY'),
    'timeout': 30,
    'max_results': 5,
    'include_answer': True,
    'include_raw_content': False
}

if config['api_key']:
    tavily = TavilySearch(config)
    print('🔍 测试 Tavily 搜索...')
    results = tavily.search('机器学习最新进展', max_results=3)
    print(f'找到 {len(results)} 个结果:')
    for i, result in enumerate(results, 1):
        print(f'{i}. {result.title}')
        print(f'   来源: {result.source}')
        print(f'   URL: {result.url}')
        print(f'   摘要: {result.snippet[:100]}...')
        print()
else:
    print('❌ TAVILY_API_KEY 未配置')
"
```

### DuckDuckGo Search (免费搜索)
```bash
# DuckDuckGo 搜索测试
python -c "
from tools.search_engines import DuckDuckGoSearch

config = {
    'timeout': 30,
    'max_results': 5,
    'region': 'cn-zh',
    'safe_search': 'moderate'
}

try:
    ddg = DuckDuckGoSearch(config)
    print('🔍 测试 DuckDuckGo 搜索...')
    results = ddg.search('Python 编程教程', max_results=3)
    print(f'找到 {len(results)} 个结果:')
    for i, result in enumerate(results, 1):
        print(f'{i}. {result.title[:60]}...')
        print(f'   URL: {result.url}')
        print()
except Exception as e:
    print(f'❌ DuckDuckGo 搜索失败: {e}')
"
```

### ArXiv 学术搜索
```bash
# ArXiv 学术论文搜索测试
python -c "
from tools.search_engines import ArxivSearch

config = {
    'timeout': 30,
    'max_results': 5,
    'sort_by': 'relevance',
    'sort_order': 'descending'
}

try:
    arxiv = ArxivSearch(config)
    print('🔍 测试 ArXiv 学术搜索...')
    results = arxiv.search('machine learning', max_results=3)
    print(f'找到 {len(results)} 个学术论文:')
    for i, result in enumerate(results, 1):
        print(f'{i}. {result.title}')
        print(f'   ArXiv ID: {result.metadata.get(\"arxiv_id\", \"N/A\")}')
        print(f'   作者: {result.metadata.get(\"authors\", [])}')
        print(f'   分类: {result.metadata.get(\"categories\", [])}')
        print(f'   发布时间: {result.metadata.get(\"published\", \"N/A\")}')
        print()
except Exception as e:
    print(f'❌ ArXiv 搜索失败: {e}')
"
```

### 多引擎对比搜索
```bash
# 对比多个搜索引擎的结果
python -c "
from tools.search_engines import SearchEngineManager

manager = SearchEngineManager()
query = '区块链技术应用'

print(f'🔍 搜索查询: {query}')
print('=' * 50)

results = manager.search_multiple_engines(
    query=query,
    engines=['tavily', 'duckduckgo', 'arxiv'],
    max_results_per_engine=2
)

for engine, engine_results in results.items():
    print(f'\n📊 {engine.upper()} 搜索结果 ({len(engine_results)} 条):')
    for i, result in enumerate(engine_results, 1):
        print(f'  {i}. {result.title[:60]}...')
        print(f'     来源: {result.source}')
"
```

---

## 🌐 Browser-Use 工具测试

### 基础 Browser-Use 功能测试
```bash
# 测试 Browser-Use 工具初始化
python -c "
from tools.browser_use_tool import BrowserUseTool
from config import config

print('🌐 测试 Browser-Use 工具初始化...')

try:
    browser_tool = BrowserUseTool()
    print('✅ Browser-Use 工具初始化成功')
    print(f'LLM 提供商: {browser_tool.llm_provider}')
    print(f'LLM 模型: {browser_tool.llm_model}')
    print(f'浏览器配置: {browser_tool.browser_config}')
    print(f'启用功能: {list(browser_tool.features.keys())}')
except Exception as e:
    print(f'❌ Browser-Use 工具初始化失败: {e}')
"
```

### Browser-Use 搜索和提取测试
```bash
# 创建 Browser-Use 搜索测试脚本
cat > test_browser_use_search.py << 'EOF'
#!/usr/bin/env python3
"""Browser-Use 搜索和提取功能测试"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.browser_use_tool import BrowserUseTool

async def test_browser_search():
    """测试浏览器搜索和数据提取"""
    try:
        browser_tool = BrowserUseTool()
        
        # 测试搜索和提取功能
        print("🔍 测试浏览器搜索和提取...")
        
        task_config = {
            "search_query": "Python 最新版本特性",
            "target_websites": ["python.org", "docs.python.org"],
            "extract_elements": ["h1", "h2", "p"],
            "max_pages": 2,
            "timeout": 60
        }
        
        # 使用 search_and_extract 功能
        result = await browser_tool.search_and_extract(task_config)
        
        if result["success"]:
            print("✅ 搜索和提取成功")
            print(f"📊 提取的数据条目: {len(result.get('extracted_data', []))}")
            print(f"🌐 访问的页面: {len(result.get('visited_pages', []))}")
            
            # 显示部分提取的数据
            for i, data in enumerate(result.get('extracted_data', [])[:3], 1):
                print(f"\n📄 数据条目 {i}:")
                print(f"   标题: {data.get('title', 'N/A')[:50]}...")
                print(f"   URL: {data.get('url', 'N/A')}")
                print(f"   内容: {data.get('content', 'N/A')[:100]}...")
        else:
            print(f"❌ 搜索和提取失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"💥 测试出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_browser_search())
EOF

# 运行 Browser-Use 搜索测试
python test_browser_use_search.py
```

### Browser-Use 表单填写测试
```bash
# 创建表单填写测试脚本
cat > test_browser_form.py << 'EOF'
#!/usr/bin/env python3
"""Browser-Use 表单填写功能测试"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.browser_use_tool import BrowserUseTool

async def test_browser_form():
    """测试浏览器表单填写功能"""
    try:
        browser_tool = BrowserUseTool()
        
        print("📝 测试浏览器表单填写...")
        
        # 表单填写配置（以 Google 搜索为例）
        form_config = {
            "url": "https://www.google.com",
            "form_data": {
                "q": "人工智能研究进展"  # Google 搜索框
            },
            "submit_button_selector": "input[type='submit']",
            "wait_for_results": True,
            "extract_results": True
        }
        
        result = await browser_tool.fill_form(form_config)
        
        if result["success"]:
            print("✅ 表单填写成功")
            print(f"🌐 最终页面 URL: {result.get('final_url', 'N/A')}")
            print(f"📊 提取的结果数量: {len(result.get('form_results', []))}")
        else:
            print(f"❌ 表单填写失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"💥 测试出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_browser_form())
EOF

# 运行表单填写测试
python test_browser_form.py
```

### Browser-Use 自定义任务测试
```bash
# 创建自定义任务测试脚本
cat > test_browser_custom.py << 'EOF'
#!/usr/bin/env python3
"""Browser-Use 自定义任务功能测试"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.browser_use_tool import BrowserUseTool

async def test_custom_task():
    """测试自定义浏览器任务"""
    try:
        browser_tool = BrowserUseTool()
        
        print("🎯 测试自定义浏览器任务...")
        
        # 自定义任务：访问 GitHub 并提取 Python 项目信息
        custom_task = {
            "task_description": "访问 GitHub 搜索 Python 机器学习项目，提取前3个项目的名称、描述和星数",
            "steps": [
                {"action": "navigate", "url": "https://github.com"},
                {"action": "search", "query": "python machine learning", "search_type": "repositories"},
                {"action": "extract", "selector": ".repo-list-item", "limit": 3},
                {"action": "get_details", "fields": ["name", "description", "stars"]}
            ],
            "timeout": 120,
            "save_screenshots": True
        }
        
        result = await browser_tool.execute_custom_task(custom_task)
        
        if result["success"]:
            print("✅ 自定义任务执行成功")
            print(f"📊 执行的步骤数: {len(result.get('executed_steps', []))}")
            print(f"🖼️ 截图保存位置: {result.get('screenshots_path', 'N/A')}")
            
            # 显示提取的项目信息
            extracted_data = result.get('extracted_data', [])
            print(f"\n🐍 找到 {len(extracted_data)} 个 Python 项目:")
            for i, project in enumerate(extracted_data[:3], 1):
                print(f"  {i}. {project.get('name', 'N/A')}")
                print(f"     描述: {project.get('description', 'N/A')[:80]}...")
                print(f"     ⭐ Stars: {project.get('stars', 'N/A')}")
        else:
            print(f"❌ 自定义任务执行失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"💥 测试出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_custom_task())
EOF

# 运行自定义任务测试
python test_browser_custom.py
```

---

## 🔧 其他工具测试

### 代码执行工具测试
```bash
# 测试代码执行工具
python -c "
from tools.tool_registry import CodeTool

code_tool = CodeTool()
print('💻 测试代码执行工具...')

# 测试 Python 代码执行
python_code = '''
import pandas as pd
import numpy as np

# 创建示例数据
data = {
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'score': [95, 87, 92]
}

df = pd.DataFrame(data)
print("数据框信息:")
print(df.info())
print("\n数据预览:")
print(df.head())
print(f"\n平均分数: {df['score'].mean():.2f}")
'''

try:
    result = code_tool._run(python_code)
    print('✅ 代码执行成功:')
    print(result)
except Exception as e:
    print(f'❌ 代码执行失败: {e}')
"
```

### 文件处理工具测试
```bash
# 测试文件处理工具
python -c "
from tools.tool_registry import FileTool
import tempfile
import os

file_tool = FileTool()
print('📁 测试文件处理工具...')

# 创建临时文件
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write('这是一个测试文件\n包含多行文本\n用于测试文件读取功能')
    temp_file = f.name

try:
    # 测试文件读取
    result = file_tool._run(f'read:{temp_file}')
    print('✅ 文件读取成功:')
    print(result[:200] + '...' if len(result) > 200 else result)
finally:
    # 清理临时文件
    os.unlink(temp_file)
"
```

---

## 🧪 完整研究流程测试

### 简单研究流程测试
```bash
# 快速研究流程测试（非交互模式）
python main.py research "人工智能在教育领域的应用" \
    --provider deepseek \
    --max-sections 2 \
    --language zh-CN \
    --output-dir output \
    --no-interactive
```

### 完整研究流程测试
```bash
# 完整研究流程测试（交互模式）
python main.py research "区块链技术的发展趋势" \
    --provider deepseek \
    --max-sections 4 \
    --language zh-CN \
    --enable-browser-use
```

### 使用特定搜索引擎的研究
```bash
# 使用 Tavily 搜索引擎进行研究
python -c "
import asyncio
from workflow.graph import ResearchWorkflow
from tools.search_engines import SearchEngineManager

async def test_research_with_tavily():
    workflow = ResearchWorkflow(
        llm_provider='deepseek',
        max_sections=2,
        interactive_mode=False
    )
    
    # 强制使用 Tavily 搜索
    original_search = workflow.search_manager.search
    def force_tavily_search(query, **kwargs):
        return workflow.search_manager.search(query, engine='tavily', **kwargs)
    workflow.search_manager.search = force_tavily_search
    
    print('🔍 使用 Tavily 搜索引擎进行研究...')
    outline, content_map = await workflow.run_full_workflow('量子计算基础原理')
    
    if outline and content_map:
        print(f'✅ 研究完成，生成 {len(content_map)} 个内容部分')
        
        # 检查引用来源
        sources_count = sum(1 for content in content_map.values() if content.sources)
        print(f'📚 包含引用来源的部分: {sources_count}/{len(content_map)}')
    else:
        print('❌ 研究失败')

asyncio.run(test_research_with_tavily())
"
```

---

## 🚨 故障排除

### 常见问题诊断
```bash
# 创建诊断脚本
cat > diagnose_tools.py << 'EOF'
#!/usr/bin/env python3
"""工具诊断脚本"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def diagnose_environment():
    """诊断环境配置"""
    print("🔍 诊断系统环境...")
    
    # 检查 Python 版本
    print(f"Python 版本: {sys.version}")
    
    # 检查关键依赖包
    required_packages = [
        'requests', 'pydantic', 'langchain', 'langgraph', 
        'duckduckgo_search', 'feedparser', 'browser_use'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: 已安装")
        except ImportError:
            print(f"❌ {package}: 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 需要安装的包: {', '.join(missing_packages)}")
        print(f"安装命令: pip install {' '.join(missing_packages)}")
    
    return len(missing_packages) == 0

def diagnose_api_keys():
    """诊断 API 密钥配置"""
    print("\n🔑 诊断 API 密钥...")
    
    api_keys = {
        'TAVILY_API_KEY': 'Tavily 搜索',
        'BRAVE_SEARCH_API_KEY': 'Brave 搜索',
        'SERPAPI_KEY': 'Google 搜索',
        'BING_SEARCH_KEY': 'Bing 搜索',
        'OPENAI_API_KEY': 'OpenAI',
        'ANTHROPIC_API_KEY': 'Claude',
        'GOOGLE_API_KEY': 'Gemini',
        'DEEPSEEK_API_KEY': 'DeepSeek'
    }
    
    configured_keys = 0
    for key, name in api_keys.items():
        if os.getenv(key):
            print(f"✅ {name}: 已配置")
            configured_keys += 1
        else:
            print(f"❌ {name}: 未配置")
    
    print(f"\n📊 已配置 {configured_keys}/{len(api_keys)} 个 API 密钥")
    return configured_keys > 0

def diagnose_search_engines():
    """诊断搜索引擎"""
    print("\n🔍 诊断搜索引擎...")
    
    try:
        from tools.search_engines import SearchEngineManager
        manager = SearchEngineManager()
        
        available_engines = manager.get_available_engines()
        print(f"可用搜索引擎: {', '.join(available_engines)}")
        
        if available_engines:
            # 测试第一个可用的搜索引擎
            test_engine = available_engines[0]
            print(f"测试 {test_engine} 搜索...")
            results = manager.search("test", engine=test_engine, max_results=1)
            if results:
                print(f"✅ {test_engine} 搜索正常")
                return True
            else:
                print(f"❌ {test_engine} 搜索无结果")
                return False
        else:
            print("❌ 没有可用的搜索引擎")
            return False
            
    except Exception as e:
        print(f"❌ 搜索引擎诊断失败: {e}")
        return False

def diagnose_browser_use():
    """诊断 Browser-Use 工具"""
    print("\n🌐 诊断 Browser-Use 工具...")
    
    try:
        from tools.browser_use_tool import BrowserUseTool
        browser_tool = BrowserUseTool()
        print("✅ Browser-Use 工具初始化成功")
        return True
    except Exception as e:
        print(f"❌ Browser-Use 工具初始化失败: {e}")
        return False

if __name__ == "__main__":
    print("🏥 DeepResearch 工具诊断")
    print("=" * 50)
    
    checks = [
        diagnose_environment(),
        diagnose_api_keys(),
        diagnose_search_engines(),
        diagnose_browser_use()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n📊 诊断结果: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("🎉 所有工具正常，可以开始使用！")
    else:
        print("⚠️ 部分工具存在问题，请检查上述错误信息")
EOF

# 运行诊断
python diagnose_tools.py
```

### 调试模式测试
```bash
# 启用详细日志进行调试
export DEBUG=1
python main.py research "测试主题" --provider deepseek --debug
```

### 修复引用来源问题测试
```bash
# 运行引用来源修复测试
python test_sources_fix.py
```

---

## 📝 测试检查清单

使用此检查清单确保所有功能正常：

- [ ] **环境配置**: Python 依赖包已安装
- [ ] **API 密钥**: 至少配置一个 LLM 和一个搜索引擎的 API 密钥
- [ ] **搜索引擎**: 
  - [ ] Tavily 搜索正常
  - [ ] DuckDuckGo 搜索正常
  - [ ] ArXiv 搜索正常
- [ ] **Browser-Use 工具**:
  - [ ] 工具初始化成功
  - [ ] 搜索和提取功能正常
  - [ ] 表单填写功能正常
  - [ ] 自定义任务执行正常
- [ ] **其他工具**:
  - [ ] 代码执行工具正常
  - [ ] 文件处理工具正常
- [ ] **完整流程**:
  - [ ] 研究提纲生成正常
  - [ ] 内容生成包含引用来源
  - [ ] 最终报告导出成功
- [ ] **引用来源**: 报告中正确显示参考资料

---

## 🎯 性能基准测试

```bash
# 创建性能测试脚本
cat > benchmark_tools.py << 'EOF'
#!/usr/bin/env python3
"""工具性能基准测试"""

import asyncio
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.search_engines import SearchEngineManager
from workflow.graph import ResearchWorkflow

async def benchmark_search_engines():
    """搜索引擎性能基准测试"""
    print("⏱️ 搜索引擎性能测试...")
    
    manager = SearchEngineManager()
    queries = ["人工智能", "区块链技术", "量子计算"]
    
    for engine in manager.get_available_engines():
        print(f"\n🔍 测试 {engine}:")
        total_time = 0
        total_results = 0
        
        for query in queries:
            start_time = time.time()
            results = manager.search(query, engine=engine, max_results=5)
            end_time = time.time()
            
            query_time = end_time - start_time
            total_time += query_time
            total_results += len(results)
            
            print(f"  查询 '{query}': {len(results)} 结果, {query_time:.2f}s")
        
        avg_time = total_time / len(queries)
        avg_results = total_results / len(queries)
        print(f"  平均: {avg_results:.1f} 结果/查询, {avg_time:.2f}s/查询")

async def benchmark_research_workflow():
    """研究流程性能基准测试"""
    print("\n⏱️ 研究流程性能测试...")
    
    workflow = ResearchWorkflow(
        llm_provider="deepseek",
        max_sections=2,
        interactive_mode=False
    )
    
    test_topics = ["机器学习基础", "网络安全概述"]
    
    for topic in test_topics:
        print(f"\n📝 测试主题: {topic}")
        
        start_time = time.time()
        outline, content_map = await workflow.run_full_workflow(topic)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        if outline and content_map:
            print(f"  ✅ 完成时间: {total_time:.2f}s")
            print(f"  📊 生成章节: {len(outline.sections)}")
            print(f"  📝 内容部分: {len(content_map)}")
            
            # 统计引用来源
            sources_count = sum(len(content.sources) for content in content_map.values())
            print(f"  📚 引用来源: {sources_count} 个")
        else:
            print(f"  ❌ 失败，耗时: {total_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(benchmark_search_engines())
    asyncio.run(benchmark_research_workflow())
EOF

# 运行性能测试
python benchmark_tools.py
```

---

## 📞 获取帮助

如果遇到问题，请：

1. **查看日志文件**: `deepresearch.log`
2. **运行诊断脚本**: `python diagnose_tools.py`
3. **检查配置文件**: `config.yml` 和 `.env`
4. **验证 API 密钥**: `python main.py config-check`
5. **查看详细错误**: 使用 `--debug` 参数

---

## 🎉 恭喜！

如果所有测试都通过，您的 DeepResearch 系统已经完全配置好，可以开始进行高质量的自动化研究了！

记得定期更新依赖包并检查 API 密钥的有效性。 