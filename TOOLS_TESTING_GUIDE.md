# 🔬 DeepResearch 工具测试指南

本指南帮助您验证 DeepResearch 系统的所有工具和功能是否正常工作。

## 🚀 快速验证

一键测试所有核心功能：

```bash
# 运行完整的功能测试
python test_fixes.py

# 检查配置状态
./run.sh config-check

# 运行演示
./run.sh demo
```

## 🔍 详细工具测试

### 1. 搜索引擎测试

#### 测试所有搜索引擎
```python
# 创建搜索引擎测试脚本
cat > test_search_engines.py << 'EOF'
#!/usr/bin/env python3
"""测试所有搜索引擎功能"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.search_engines import SearchEngineManager

def test_all_search_engines():
    """测试所有可用的搜索引擎"""
    print("🔍 测试搜索引擎...")
    
    manager = SearchEngineManager()
    
    # 显示可用的搜索引擎
    available_engines = manager.get_available_engines()
    print(f"可用搜索引擎: {available_engines}")
    
    test_query = "DeepSeek LLM"
    
    for engine in available_engines:
        print(f"\n🔍 测试 {engine} 搜索引擎:")
        try:
            results = manager.search(test_query, engine=engine, max_results=3)
            if results:
                print(f"  ✅ 成功获取 {len(results)} 个结果")
                for i, result in enumerate(results[:2], 1):
                    print(f"  {i}. {result.title[:60]}... 来源: {result.source}")
                    print(f"     URL: {result.url}")
            else:
                print(f"  ⚠️ 没有获取到结果")
        except Exception as e:
            print(f"  ❌ 搜索失败: {e}")
    
    # 测试引用来源修复
    print(f"\n🎯 验证引用来源修复:")
    print("确保显示的是域名而不是搜索引擎名称")

if __name__ == "__main__":
    test_all_search_engines()
EOF

# 运行搜索引擎测试
python test_search_engines.py
```

#### 测试特定搜索引擎

**Tavily 搜索测试**:
```python
from tools.search_engines import TavilySearch

# 测试 Tavily 搜索
tavily = TavilySearch()
results = tavily.search("人工智能发展趋势", max_results=5)
print(f"Tavily 搜索结果: {len(results)} 个")
for result in results[:2]:
    print(f"标题: {result.title}")
    print(f"来源: {result.source}")  # 应该显示域名，不是 "tavily"
```

**ArXiv 搜索测试**:
```python
from tools.search_engines import ArxivSearch

# 测试 ArXiv 搜索
arxiv = ArxivSearch()
results = arxiv.search("machine learning", max_results=3)
print(f"ArXiv 搜索结果: {len(results)} 个")
for result in results:
    print(f"论文: {result.title}")
    print(f"来源: {result.source}")  # 应该显示 "arxiv.org"
```

**DuckDuckGo 搜索测试**:
```python
from tools.search_engines import DuckDuckGoSearch

# 测试 DuckDuckGo 搜索
ddg = DuckDuckGoSearch()
results = ddg.search("量子计算", max_results=5)
print(f"DuckDuckGo 搜索结果: {len(results)} 个")
for result in results:
    print(f"标题: {result.title}")
    print(f"来源: {result.source}")  # 应该显示实际域名
```

### 2. Browser-Use 工具测试

#### 基础功能测试
```python
# 创建 Browser-Use 测试脚本
cat > test_browser_use.py << 'EOF'
#!/usr/bin/env python3
"""测试 Browser-Use 工具功能"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.browser_use_tool import BrowserUseTool

async def test_browser_use():
    """测试 Browser-Use 工具"""
    print("🌐 测试 Browser-Use 工具...")
    
    try:
        # 初始化工具
        browser_tool = BrowserUseTool()
        print("✅ Browser-Use 工具初始化成功")
        
        # 测试搜索和提取功能
        print("\n🔍 测试搜索和提取功能:")
        result = browser_tool.execute(
            action="search_and_extract",
            query="人工智能最新发展",
            search_engine="google",
            timeout=30
        )
        
        if result.get('success'):
            print("✅ 搜索和提取功能正常")
            extracted_data = result.get('extracted_data', {})
            print(f"提取的数据项: {len(extracted_data)}")
        else:
            print(f"❌ 搜索和提取功能失败: {result.get('error')}")
        
        # 测试网页导航和提取
        print("\n🌐 测试网页导航和提取:")
        result = browser_tool.execute(
            action="navigate_and_extract",
            url="https://example.com",
            extraction_task="提取页面标题和主要内容",
            timeout=20
        )
        
        if result.get('success'):
            print("✅ 网页导航和提取功能正常")
        else:
            print(f"❌ 网页导航失败: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Browser-Use 工具测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_browser_use())
EOF

# 运行 Browser-Use 测试
python test_browser_use.py
```

#### 高级功能测试
```python
# 测试表单填写功能
async def test_form_filling():
    browser_tool = BrowserUseTool()
    
    result = browser_tool.execute(
        action="fill_form",
        url="https://httpbin.org/forms/post",
        form_data={
            "name": "Test User",
            "email": "test@example.com",
            "message": "This is a test message"
        },
        submit=False  # 不实际提交
    )
    
    print(f"表单填写结果: {result}")

# 测试自定义任务
async def test_custom_task():
    browser_tool = BrowserUseTool()
    
    result = browser_tool.execute(
        action="custom_task",
        task_description="访问GitHub主页，提取主要导航菜单的链接",
        url="https://github.com",
        max_steps=10
    )
    
    print(f"自定义任务结果: {result}")
```

### 3. LLM 集成测试

#### 测试所有 LLM 提供商
```python
# 创建 LLM 测试脚本
cat > test_llms.py << 'EOF'
#!/usr/bin/env python3
"""测试所有 LLM 提供商"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from llm.openai import OpenAIWrapper
from llm.claude import ClaudeWrapper
from llm.gemini import GeminiWrapper
from llm.deepseek import DeepSeekWrapper
from llm.ollama import OllamaWrapper

def test_llm_provider(provider_name, wrapper_class):
    """测试单个 LLM 提供商"""
    print(f"\n🤖 测试 {provider_name}:")
    
    try:
        llm_config = config.get_llm_config(provider_name)
        if not llm_config.get('api_key') and provider_name != 'ollama':
            print(f"  ⚠️ 没有配置 API 密钥，跳过测试")
            return False
        
        llm = wrapper_class(llm_config)
        
        # 测试简单生成
        response = llm.generate(
            prompt="请用一句话介绍人工智能",
            max_tokens=100
        )
        
        if response.is_success:
            print(f"  ✅ 生成成功: {response.content[:50]}...")
            return True
        else:
            print(f"  ❌ 生成失败: {response.error}")
            return False
            
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_all_llms():
    """测试所有 LLM 提供商"""
    print("🤖 测试 LLM 提供商...")
    
    providers = [
        ("openai", OpenAIWrapper),
        ("claude", ClaudeWrapper),
        ("gemini", GeminiWrapper),
        ("deepseek", DeepSeekWrapper),
        ("ollama", OllamaWrapper),
    ]
    
    results = {}
    for provider_name, wrapper_class in providers:
        results[provider_name] = test_llm_provider(provider_name, wrapper_class)
    
    # 显示测试结果
    print(f"\n📊 LLM 测试结果:")
    for provider, success in results.items():
        status = "✅ 正常" if success else "❌ 失败"
        print(f"  {provider}: {status}")
    
    working_providers = [p for p, s in results.items() if s]
    print(f"\n🎯 可用的 LLM 提供商: {working_providers}")

if __name__ == "__main__":
    test_all_llms()
EOF

# 运行 LLM 测试
python test_llms.py
```

#### 测试 DeepSeek 集成
```python
# 专门测试 DeepSeek LLM
from llm.deepseek import DeepSeekWrapper
from config import config

def test_deepseek():
    llm_config = config.get_llm_config("deepseek")
    deepseek = DeepSeekWrapper(llm_config)
    
    response = deepseek.generate(
        prompt="请介绍 DeepSeek 模型的特点",
        max_tokens=200,
        temperature=0.7
    )
    
    print(f"DeepSeek 响应: {response.content}")
    print(f"Token 使用: {response.token_usage}")
```

### 4. 其他工具测试

#### 代码执行工具测试
```python
from tools.code_runner import CodeTool

def test_code_execution():
    """测试代码执行工具"""
    print("💻 测试代码执行工具...")
    
    code_tool = CodeTool()
    
    # 测试 Python 代码执行
    test_code = """
import pandas as pd
import numpy as np

# 创建测试数据
data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
df = pd.DataFrame(data)
print(f"数据形状: {df.shape}")
print(df.head())
    """
    
    result = code_tool.execute(test_code)
    print(f"代码执行结果: {result}")
```

#### 文件处理工具测试
```python
from tools.file_reader import FileTool

def test_file_operations():
    """测试文件操作工具"""
    print("📁 测试文件操作工具...")
    
    file_tool = FileTool()
    
    # 测试文件读取
    test_content = "这是一个测试文件内容\n包含多行文本\n用于测试文件读取功能"
    
    # 写入测试文件
    file_tool.write_file("test_file.txt", test_content)
    
    # 读取测试文件
    content = file_tool.read_file("test_file.txt")
    print(f"文件内容: {content}")
    
    # 清理测试文件
    import os
    if os.path.exists("test_file.txt"):
        os.remove("test_file.txt")
        print("✅ 测试文件已清理")
```

## 🧪 完整研究流程测试

### 端到端测试
```python
# 创建完整流程测试脚本
cat > test_full_workflow.py << 'EOF'
#!/usr/bin/env python3
"""测试完整研究工作流"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow.graph import ResearchWorkflow

async def test_research_workflow():
    """测试完整研究工作流"""
    print("🔬 测试完整研究工作流...")
    
    # 创建研究工作流
    workflow = ResearchWorkflow(
        llm_provider="deepseek",  # 使用 DeepSeek
        max_sections=3,          # 限制章节数量
        interactive_mode=False   # 非交互模式
    )
    
    test_topic = "人工智能在教育领域的应用"
    
    print(f"📝 研究主题: {test_topic}")
    
    try:
        # 运行完整工作流
        outline, content_map = await workflow.run_full_workflow(test_topic)
        
        if outline and content_map:
            print("✅ 研究工作流完成")
            print(f"📋 生成大纲: {outline.title}")
            print(f"📊 章节数量: {len(outline.sections)}")
            print(f"📝 内容部分: {len(content_map)}")
            
            # 检查引用来源
            total_sources = 0
            for section_key, content in content_map.items():
                sources = content.sources
                total_sources += len(sources)
                print(f"  {section_key}: {len(sources)} 个引用来源")
                
                # 显示前几个引用来源
                for source in sources[:2]:
                    print(f"    - {source}")
            
            print(f"📚 总引用来源: {total_sources} 个")
            
            # 验证引用来源格式
            print(f"\n🎯 验证引用来源格式:")
            if total_sources > 0:
                print("✅ 引用来源已包含在内容中")
            else:
                print("⚠️ 没有找到引用来源")
                
            return True
        else:
            print("❌ 研究工作流失败")
            return False
            
    except Exception as e:
        print(f"❌ 研究工作流异常: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_research_workflow())
    if success:
        print("\n🎉 完整研究流程测试通过！")
    else:
        print("\n⚠️ 研究流程测试失败，请检查配置")
EOF

# 运行完整流程测试
python test_full_workflow.py
```

### 交互式测试
```bash
# 运行交互式研究测试
./run.sh interactive "机器学习算法比较" --provider deepseek

# 测试自动化模式
./run.sh auto "区块链技术发展" --provider claude --max-sections 4
```

## 🎨 LangGraph Studio 测试

### 安装和配置测试
```bash
# 1. 验证 LangGraph Studio 配置文件
cat langgraph.json

# 2. 检查依赖项
pip list | grep -E "(langgraph|langchain)"

# 3. 验证环境变量
echo $LANGCHAIN_TRACING_V2
echo $LANGCHAIN_API_KEY
```

### Studio 工作流测试
```python
# 运行 Studio 快速开始演示
python examples/studio_quickstart.py

# 测试 Studio 集成
cat > test_studio_integration.py << 'EOF'
#!/usr/bin/env python3
"""测试 LangGraph Studio 集成"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from examples.studio_quickstart import StudioQuickstartWorkflow

async def test_studio_workflow():
    """测试 Studio 工作流"""
    print("🎨 测试 LangGraph Studio 工作流...")
    
    try:
        # 创建演示工作流
        workflow = StudioQuickstartWorkflow()
        
        # 初始状态
        initial_state = {
            "topic": "LangGraph Studio 测试",
            "stage": "init",
            "findings": "",
            "debug_info": {}
        }
        
        # 配置
        config = {"configurable": {"thread_id": "studio-test-001"}}
        
        print("⚡ 执行 Studio 演示工作流...")
        
        # 执行工作流
        result = await workflow.graph.ainvoke(initial_state, config=config)
        
        if result and result.get("stage") == "complete":
            print("✅ Studio 工作流测试成功")
            print(f"📊 最终状态: {result['stage']}")
            print(f"🔍 调试信息: {result.get('debug_info', {})}")
            return True
        else:
            print("❌ Studio 工作流测试失败")
            return False
            
    except Exception as e:
        print(f"❌ Studio 工作流测试异常: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_studio_workflow())
    if success:
        print("\n🎉 LangGraph Studio 集成测试通过！")
        print("💡 现在可以在 LangGraph Studio 中打开项目目录进行可视化调试")
    else:
        print("\n⚠️ Studio 集成测试失败")
EOF

# 运行 Studio 集成测试
python test_studio_integration.py
```

### Studio 可视化验证
```bash
# 创建 Studio 验证指南
cat > verify_studio.md << 'EOF'
# LangGraph Studio 可视化验证

## 步骤 1: 打开 LangGraph Studio
1. 启动 LangGraph Studio 应用
2. 登录 LangSmith 账户
3. 选择 "Open Directory"
4. 选择 DeepResearch 项目目录

## 步骤 2: 验证工作流可视化
- [ ] 图形界面显示工作流节点
- [ ] 节点之间的连接正确显示
- [ ] 可以看到以下节点:
  - [ ] initialize
  - [ ] search_topic  
  - [ ] analyze_results
  - [ ] generate_summary

## 步骤 3: 测试交互功能
- [ ] 在输入框中输入测试主题
- [ ] 点击运行按钮启动工作流
- [ ] 观察节点执行状态变化
- [ ] 查看实时状态更新

## 步骤 4: 调试功能验证
- [ ] 设置断点并暂停执行
- [ ] 检查状态面板中的数据
- [ ] 手动修改状态值
- [ ] 继续执行验证修改效果

## 步骤 5: 监控面板验证
- [ ] 查看执行日志
- [ ] 检查性能指标
- [ ] 验证错误处理
EOF

echo "📖 Studio 验证指南已创建: verify_studio.md"
```

## 🚨 故障排除和诊断

### 自动诊断脚本
```python
# 创建综合诊断脚本
cat > diagnose_tools.py << 'EOF'
#!/usr/bin/env python3
"""DeepResearch 工具诊断脚本"""

import sys
import os
import importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def diagnose_environment():
    """诊断环境配置"""
    print("🔧 诊断环境配置...")
    
    try:
        # 检查 Python 版本
        python_version = sys.version_info
        print(f"Python 版本: {python_version.major}.{python_version.minor}")
        
        if python_version.major >= 3 and python_version.minor >= 11:
            print("✅ Python 版本满足要求")
        else:
            print("⚠️ Python 版本建议 3.11+")
        
        # 检查关键依赖包
        required_packages = [
            'langchain', 'langgraph', 'openai', 'anthropic', 
            'google-generativeai', 'tavily-python', 'duckduckgo-search',
            'browser-use', 'playwright'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                importlib.import_module(package.replace('-', '_'))
                print(f"✅ {package} 已安装")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} 未安装")
        
        if not missing_packages:
            print("✅ 所有依赖包已安装")
            return True
        else:
            print(f"⚠️ 缺少依赖包: {missing_packages}")
            return False
            
    except Exception as e:
        print(f"❌ 环境诊断失败: {e}")
        return False

def diagnose_api_keys():
    """诊断 API 密钥配置"""
    print("\n🔑 诊断 API 密钥配置...")
    
    try:
        from config import config
        
        api_keys = {
            'OPENAI_API_KEY': config.llm.openai.api_key,
            'ANTHROPIC_API_KEY': config.llm.claude.api_key,
            'GOOGLE_API_KEY': config.llm.gemini.api_key,
            'DEEPSEEK_API_KEY': config.llm.deepseek.api_key,
            'TAVILY_API_KEY': config.search.tavily.api_key,
        }
        
        configured_keys = 0
        for key_name, key_value in api_keys.items():
            if key_value and key_value.strip():
                print(f"✅ {key_name} 已配置")
                configured_keys += 1
            else:
                print(f"⚠️ {key_name} 未配置")
        
        if configured_keys >= 2:  # 至少需要一个 LLM 和一个搜索 API
            print(f"✅ API 密钥配置充足 ({configured_keys} 个)")
            return True
        else:
            print(f"⚠️ 建议配置更多 API 密钥 (当前: {configured_keys} 个)")
            return False
            
    except Exception as e:
        print(f"❌ API 密钥诊断失败: {e}")
        return False

def diagnose_search_engines():
    """诊断搜索引擎"""
    print("\n🔍 诊断搜索引擎...")
    
    try:
        from tools.search_engines import SearchEngineManager
        
        manager = SearchEngineManager()
        available_engines = manager.get_available_engines()
        
        print(f"可用搜索引擎: {available_engines}")
        
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

def diagnose_studio_integration():
    """诊断 LangGraph Studio 集成"""
    print("\n🎨 诊断 LangGraph Studio 集成...")
    
    try:
        # 检查 langgraph.json 配置文件
        if os.path.exists("langgraph.json"):
            print("✅ langgraph.json 配置文件存在")
        else:
            print("❌ langgraph.json 配置文件不存在")
            return False
        
        # 检查 LangSmith 环境变量
        langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
        if langchain_api_key:
            print("✅ LANGCHAIN_API_KEY 已配置")
        else:
            print("⚠️ LANGCHAIN_API_KEY 未配置")
        
        # 检查 Studio 示例文件
        if os.path.exists("examples/studio_quickstart.py"):
            print("✅ Studio 快速开始示例存在")
        else:
            print("❌ Studio 快速开始示例不存在")
            return False
        
        print("✅ LangGraph Studio 集成配置正常")
        return True
        
    except Exception as e:
        print(f"❌ Studio 集成诊断失败: {e}")
        return False

if __name__ == "__main__":
    print("🏥 DeepResearch 工具诊断")
    print("=" * 50)
    
    checks = [
        diagnose_environment(),
        diagnose_api_keys(),
        diagnose_search_engines(),
        diagnose_browser_use(),
        diagnose_studio_integration()
    ]
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n📊 诊断结果: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("🎉 所有工具正常，可以开始使用！")
        print("💡 现在可以在 LangGraph Studio 中可视化调试工作流")
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
- [ ] **LangGraph Studio**:
  - [ ] 配置文件正确创建
  - [ ] LangSmith 连接正常
  - [ ] 工作流可视化显示
  - [ ] 交互式调试功能
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
6. **Studio 相关问题**: 查看 `docs/langgraph-studio-customization.md`

---

## 🎉 恭喜！

如果所有测试都通过，您的 DeepResearch 系统已经完全配置好，包括：

✅ **核心功能**: 搜索、LLM、工具集成  
✅ **高级功能**: Browser-Use 智能浏览器自动化  
✅ **可视化调试**: LangGraph Studio 集成  
✅ **引用来源**: 正确显示实际域名  

现在您可以：
- 进行高质量的自动化研究
- 在 LangGraph Studio 中可视化调试工作流
- 创建自定义研究模板和工作流

记得定期更新依赖包并检查 API 密钥的有效性。🚀 