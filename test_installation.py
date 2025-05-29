#!/usr/bin/env python3
"""
DeepResearch 安装测试脚本
用于验证系统是否正确安装和配置
"""

import sys
import os
from pathlib import Path

def test_imports():
    """测试核心模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试核心模块
        from utils.user_interaction import get_user_interaction
        print("  ✅ UserInteraction 模块")
        
        from workflow.graph import ResearchWorkflow
        print("  ✅ ResearchWorkflow 模块")
        
        from agents.outline_agent import OutlineAgent, OutlineConfig
        print("  ✅ OutlineAgent 模块")
        
        from config import config
        print("  ✅ Config 模块")
        
        from utils.json_utils import ResearchOutline
        print("  ✅ JSON Utils 模块")
        
        from utils.markdown_export import MarkdownExporter
        print("  ✅ Markdown Export 模块")
        
        print("✅ 所有核心模块导入成功")
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_environment():
    """测试环境配置"""
    print("\n🔍 测试环境配置...")
    
    # 检查 Python 版本
    python_version = sys.version_info
    print(f"  🐍 Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major == 3 and python_version.minor >= 8:
        print("  ✅ Python 版本符合要求")
    else:
        print("  ❌ Python 版本过低，需要 3.8+")
        return False
    
    # 检查必要目录
    directories = ['output', 'logs', 'demo_output']
    for directory in directories:
        if Path(directory).exists():
            print(f"  ✅ 目录存在: {directory}")
        else:
            print(f"  ⚠️  目录不存在: {directory}，将创建")
            Path(directory).mkdir(exist_ok=True)
    
    return True

def test_config():
    """测试配置文件"""
    print("\n🔍 测试配置...")
    
    try:
        from config import config
        
        # 检查 .env 文件
        if Path('.env').exists():
            print("  ✅ .env 文件存在")
        else:
            print("  ⚠️  .env 文件不存在，请配置 API 密钥")
        
        # 检查 API 密钥
        api_status = config.validate_api_keys()
        available_apis = sum(api_status.values())
        
        print(f"  📊 可用 API: {available_apis}/{len(api_status)}")
        
        for service, available in api_status.items():
            status = "✅" if available else "❌"
            print(f"    {status} {service}")
        
        if available_apis > 0:
            print("  ✅ 至少有一个 LLM API 可用")
            return True
        else:
            print("  ⚠️  没有可用的 LLM API，请配置 API 密钥")
            return False
            
    except Exception as e:
        print(f"  ❌ 配置测试失败: {e}")
        return False

def test_interactive_components():
    """测试交互组件"""
    print("\n🔍 测试交互组件...")
    
    try:
        from utils.user_interaction import get_user_interaction
        ui = get_user_interaction()
        print("  ✅ UserInteraction 实例创建成功")
        
        # 测试工作流初始化
        from workflow.graph import ResearchWorkflow
        workflow = ResearchWorkflow(interactive_mode=True)
        print("  ✅ 交互式 ResearchWorkflow 初始化成功")
        
        # 测试 Agent 初始化
        from agents.outline_agent import OutlineAgent, OutlineConfig
        config = OutlineConfig(interactive_mode=True)
        agent = OutlineAgent(config=config)
        print("  ✅ 交互式 OutlineAgent 初始化成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 交互组件测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 DeepResearch 安装测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("环境配置", test_environment),
        ("配置文件", test_config),
        ("交互组件", test_interactive_components)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统安装正确")
        print("\n💡 下一步:")
        print("  1. 配置 .env 文件中的 API 密钥")
        print("  2. 运行 ./run.sh demo 体验系统")
        print("  3. 运行 ./run.sh interactive \"您的研究主题\" 开始研究")
        return True
    else:
        print("❌ 部分测试失败，请检查安装")
        print("\n🔧 建议:")
        print("  1. 重新运行 ./setup.sh")
        print("  2. 确保 conda 环境已激活: conda activate deep-research-dev")
        print("  3. 手动安装依赖: pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 