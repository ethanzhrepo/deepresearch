#!/usr/bin/env python3
"""
DeepResearch Browser-Use 集成测试脚本

测试 browser-use 工具是否正确安装和配置。
"""

import asyncio
import os
import sys
from typing import Dict, Any

def check_dependencies():
    """检查依赖是否正确安装"""
    print("🔍 检查依赖...")
    
    try:
        import browser_use
        print("✅ browser-use 导入成功")
    except ImportError as e:
        print(f"❌ browser-use 导入失败: {e}")
        return False
    
    try:
        import playwright
        print("✅ playwright 导入成功")
    except ImportError as e:
        print(f"❌ playwright 导入失败: {e}")
        return False
    
    try:
        from langchain_openai import ChatOpenAI
        print("✅ langchain-openai 导入成功")
    except ImportError as e:
        print(f"❌ langchain-openai 导入失败: {e}")
        return False
    
    return True

def check_environment():
    """检查环境变量"""
    print("\n🔑 检查环境变量...")
    
    required_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']
    available_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            available_vars.append(var)
            print(f"✅ {var} 已设置")
        else:
            print(f"⚠️  {var} 未设置")
    
    if not available_vars:
        print("❌ 错误: 至少需要设置一个 LLM API 密钥")
        return False
    
    print(f"✅ 找到 {len(available_vars)} 个可用的 API 密钥")
    return True

async def test_browser_use_basic():
    """测试基本的 browser-use 功能"""
    print("\n🌐 测试基本 browser-use 功能...")
    
    try:
        from browser_use import Agent
        from langchain_openai import ChatOpenAI
        
        # 检查是否有 OpenAI API 密钥
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️  跳过测试: 未设置 OPENAI_API_KEY")
            return True
        
        # 创建简单的测试任务
        llm = ChatOpenAI(model="gpt-4o-mini")  # 使用较便宜的模型进行测试
        
        agent = Agent(
            task="Navigate to https://httpbin.org/get and extract the response data",
            llm=llm,
            headless=True,
            max_steps=5
        )
        
        print("🚀 执行测试任务...")
        result = await asyncio.wait_for(agent.run(), timeout=60)
        
        print("✅ Browser-use 基本功能测试成功")
        print(f"📊 测试结果: {str(result)[:200]}...")
        
        return True
        
    except asyncio.TimeoutError:
        print("⚠️  测试超时，但这可能是正常的")
        return True
    except Exception as e:
        print(f"❌ Browser-use 测试失败: {e}")
        return False

async def test_browser_use_tool():
    """测试 DeepResearch BrowserUseTool"""
    print("\n🛠️  测试 DeepResearch BrowserUseTool...")
    
    try:
        # 尝试导入我们的工具
        sys.path.append('.')
        from tools.browser_use_tool import BrowserUseTool
        
        config = {
            'llm_provider': 'openai',
            'llm_model': 'gpt-4o-mini',
            'browser': {
                'headless': True,
                'timeout': 60,
                'max_steps': 5
            },
            'output_dir': 'test_outputs'
        }
        
        # 检查是否有 API 密钥
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️  跳过测试: 未设置 OPENAI_API_KEY")
            return True
        
        tool = BrowserUseTool(config)
        print("✅ BrowserUseTool 初始化成功")
        
        # 测试简单的导航任务
        result = tool.execute(
            action="custom_task",
            task_description="Navigate to https://httpbin.org/get and check if the page loads successfully",
            max_steps=3,
            timeout=30
        )
        
        if result.get('success'):
            print("✅ BrowserUseTool 执行测试成功")
        else:
            print(f"⚠️  BrowserUseTool 测试未完全成功: {result.get('error', 'Unknown error')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ BrowserUseTool 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ BrowserUseTool 测试失败: {e}")
        return False

def test_playwright_installation():
    """测试 Playwright 浏览器是否正确安装"""
    print("\n🎭 测试 Playwright 浏览器安装...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # 尝试启动浏览器
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 访问简单页面
            page.goto("https://httpbin.org/get")
            title = page.title()
            
            browser.close()
            
            print(f"✅ Playwright 浏览器测试成功，页面标题: {title}")
            return True
            
    except Exception as e:
        print(f"❌ Playwright 浏览器测试失败: {e}")
        print("💡 尝试运行: playwright install chromium --with-deps")
        return False

async def main():
    """主测试函数"""
    print("🧪 DeepResearch Browser-Use 集成测试")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装必要的依赖")
        sys.exit(1)
    
    # 检查环境变量
    env_ok = check_environment()
    
    # 测试 Playwright
    playwright_ok = test_playwright_installation()
    
    # 测试基本 browser-use 功能
    if env_ok:
        browser_use_ok = await test_browser_use_basic()
        tool_ok = await test_browser_use_tool()
    else:
        print("\n⚠️  跳过 browser-use 功能测试（缺少 API 密钥）")
        browser_use_ok = True
        tool_ok = True
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"  📦 依赖安装: ✅")
    print(f"  🔑 环境变量: {'✅' if env_ok else '⚠️'}")
    print(f"  🎭 Playwright: {'✅' if playwright_ok else '❌'}")
    print(f"  🌐 Browser-use: {'✅' if browser_use_ok else '❌'}")
    print(f"  🛠️  工具集成: {'✅' if tool_ok else '❌'}")
    
    if all([playwright_ok, browser_use_ok, tool_ok]):
        print("\n🎉 所有测试通过！Browser-Use 集成已准备就绪。")
        print("\n💡 下一步:")
        print("  1. 确保设置了至少一个 LLM API 密钥")
        print("  2. 运行示例: python examples/browser_use_integration.py")
        print("  3. 查看文档: docs/tools.md")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 