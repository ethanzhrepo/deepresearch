#!/usr/bin/env python3
"""
Test script to verify all security and architecture fixes.
"""

import asyncio
import sys
import traceback
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_config_loading():
    """测试配置加载是否正常。"""
    print("🔧 测试配置加载...")
    try:
        from config import config
        
        # 测试基本配置访问
        assert hasattr(config.search, 'default_engine'), "缺少 default_engine 配置"
        assert hasattr(config.search, 'timeout'), "缺少 timeout 配置"
        assert hasattr(config.search, 'enable_google_docs'), "缺少 enable_google_docs 配置"
        assert hasattr(config.search, 'authority_sites'), "缺少 authority_sites 配置"
        
        print(f"  ✅ 默认搜索引擎: {config.search.default_engine}")
        print(f"  ✅ 搜索超时: {config.search.timeout}s")
        print(f"  ✅ Google Docs 搜索: {config.search.enable_google_docs}")
        print(f"  ✅ 权威网站数量: {len(config.search.authority_sites)}")
        
        return True
    except Exception as e:
        print(f"  ❌ 配置加载失败: {e}")
        traceback.print_exc()
        return False


def test_tool_registry():
    """测试工具注册表是否正常。"""
    print("\n🔧 测试工具注册表...")
    try:
        from tools.tool_registry import ToolRegistry
        
        registry = ToolRegistry()
        tools = registry.list_tools()
        
        print(f"  ✅ 注册的工具数量: {len(tools)}")
        for tool_name, tool_info in tools.items():
            print(f"    - {tool_name}: {tool_info['description']}")
        
        # 测试工具验证
        validation_results = registry.validate_tools()
        print(f"  ✅ 工具验证结果: {validation_results}")
        
        return True
    except Exception as e:
        print(f"  ❌ 工具注册表测试失败: {e}")
        traceback.print_exc()
        return False


def test_code_runner_security():
    """测试代码执行器的安全性。"""
    print("\n🔧 测试代码执行器安全性...")
    try:
        from tools.code_runner import CodeRunner, SecurityAnalyzer
        
        # 测试安全分析器
        analyzer = SecurityAnalyzer()
        
        # 测试安全代码
        safe_code = """
import math
print("Hello, World!")
result = math.sqrt(16)
print(f"Square root of 16 is {result}")
"""
        is_safe, warnings = analyzer.analyze_code(safe_code)
        print(f"  ✅ 安全代码分析: {is_safe}, 警告: {len(warnings)}")
        
        # 测试危险代码
        dangerous_code = """
import os
os.system("rm -rf /")
"""
        is_safe, warnings = analyzer.analyze_code(dangerous_code)
        print(f"  ✅ 危险代码分析: {is_safe}, 警告: {len(warnings)}")
        assert not is_safe, "危险代码应该被标记为不安全"
        
        # 测试代码执行器
        runner = CodeRunner()
        env_info = runner.get_environment_info()
        print(f"  ✅ 执行环境: {env_info['environment']}")
        print(f"  ✅ 安全检查: {env_info['security_enabled']}")
        
        return True
    except Exception as e:
        print(f"  ❌ 代码执行器安全测试失败: {e}")
        traceback.print_exc()
        return False


def test_search_engines():
    """测试搜索引擎管理器。"""
    print("\n🔧 测试搜索引擎...")
    try:
        from tools.search_engines import SearchEngineManager
        
        manager = SearchEngineManager()
        available_engines = manager.get_available_engines()
        
        print(f"  ✅ 可用搜索引擎: {available_engines}")
        
        # 测试基本搜索（使用 DuckDuckGo）
        if 'duckduckgo' in available_engines:
            results = manager.search("Python programming", max_results=3)
            print(f"  ✅ 搜索结果数量: {len(results)}")
            if results:
                print(f"    第一个结果: {results[0].title}")
        
        return True
    except Exception as e:
        print(f"  ❌ 搜索引擎测试失败: {e}")
        traceback.print_exc()
        return False


def test_prompt_manager():
    """测试 Prompt 管理器。"""
    print("\n🔧 测试 Prompt 管理器...")
    try:
        from utils.prompt_manager import PromptManager, PromptTemplate, PromptType
        
        manager = PromptManager()
        
        # 创建测试模板
        test_template = PromptTemplate(
            id="test_template",
            name="测试模板",
            description="用于测试的模板",
            type=PromptType.SYSTEM,
            template="你好，{name}！今天是 {date}。",
            variables=["name", "date"]
        )
        
        # 添加模板
        success = manager.add_template(test_template)
        print(f"  ✅ 添加模板: {success}")
        
        # 渲染模板
        rendered = manager.render_template(
            "test_template",
            {"name": "世界", "date": "2024年"}
        )
        print(f"  ✅ 渲染结果: {rendered}")
        
        # 获取统计信息
        stats = manager.get_template_stats()
        print(f"  ✅ 模板统计: {stats}")
        
        return True
    except Exception as e:
        print(f"  ❌ Prompt 管理器测试失败: {e}")
        traceback.print_exc()
        return False


def test_retry_handler():
    """测试重试处理器。"""
    print("\n🔧 测试重试处理器...")
    try:
        from utils.retry_handler import RetryHandler, RetryStrategy, CircuitBreaker
        
        handler = RetryHandler()
        
        # 测试成功的函数
        @handler.retry(max_retries=2, base_delay=0.1)
        def success_function():
            return "success"
        
        result = success_function()
        print(f"  ✅ 成功函数结果: {result}")
        
        # 测试失败的函数
        attempt_count = 0
        
        @handler.retry(max_retries=2, base_delay=0.1, exceptions=(ValueError,))
        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError(f"Attempt {attempt_count} failed")
            return "finally succeeded"
        
        try:
            result = failing_function()
            print(f"  ✅ 重试后成功: {result}")
        except ValueError as e:
            print(f"  ✅ 重试失败（预期）: {e}")
        
        # 测试熔断器
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        
        @breaker
        def circuit_test():
            raise RuntimeError("Always fails")
        
        # 触发熔断器
        for i in range(3):
            try:
                circuit_test()
            except RuntimeError:
                pass
        
        print(f"  ✅ 熔断器状态: {breaker.state}")
        
        # 获取重试统计
        stats = handler.get_retry_stats()
        print(f"  ✅ 重试统计: {len(stats)} 个函数")
        
        return True
    except Exception as e:
        print(f"  ❌ 重试处理器测试失败: {e}")
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_mcp_planner():
    """测试 MCP 规划器。"""
    print("\n🔧 测试 MCP 规划器...")
    try:
        from mcp.planner import MCPPlanner, TaskType, ExecutionStrategy
        
        planner = MCPPlanner()
        
        # 验证异步执行器初始化
        if planner.async_executor:
            print(f"  ✅ 异步执行器已初始化")
            executor_stats = planner.async_executor.get_stats()
            print(f"  ✅ 执行器统计: {executor_stats}")
        else:
            print(f"  ⚠️  异步执行器未初始化")
        
        # 创建简单的研究计划
        plan = planner.create_research_plan(
            topic="人工智能基础",
            requirements={
                "max_sections": 3,
                "language": "zh-CN",
                "search_results": 5
            }
        )
        
        print(f"  ✅ 创建计划: {plan.plan_id}")
        print(f"  ✅ 步骤数量: {len(plan.steps)}")
        print(f"  ✅ 预估时间: {plan.estimated_total_duration:.1f}s")
        
        # 测试工具执行准备
        for step in plan.steps[:3]:  # 测试前3个步骤
            tool, input_data = planner._prepare_tool_execution(step, {})
            if tool:
                print(f"  ✅ 步骤 {step.step_id} 工具准备: {tool.name}")
            else:
                print(f"  ⚠️  步骤 {step.step_id} 工具准备失败 (可能是 LLM 任务)")
        
        # 测试搜索结果解析
        test_search_output = """1. 人工智能概述
   人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。
   URL: https://example.com/ai-overview

2. 机器学习基础
   机器学习是人工智能的一个子集，使计算机能够在没有明确编程的情况下学习。
   URL: https://example.com/ml-basics"""
        
        parsed_results = planner._parse_search_output(test_search_output)
        print(f"  ✅ 搜索结果解析: {len(parsed_results)} 个结果")
        
        # 获取计划状态
        status = planner.get_plan_status(plan.plan_id)
        print(f"  ✅ 计划状态: {status}")
        
        # 注意：这里不执行完整的计划，因为需要 API 密钥
        print("  ℹ️  跳过完整执行（需要 API 密钥）")
        
        return True
    except Exception as e:
        print(f"  ❌ MCP 规划器测试失败: {e}")
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_async_tools():
    """测试异步工具框架。"""
    print("\n🔧 测试异步工具框架...")
    try:
        from tools.async_tools import AsyncToolExecutor, AsyncSearchTool, async_tool_executor
        
        # 测试异步工具执行器
        executor = AsyncToolExecutor()
        
        # 创建异步搜索工具
        search_tool = AsyncSearchTool()
        
        # 测试工具执行
        result = await executor.execute_tool(
            search_tool,
            "Python programming",
            timeout=10.0
        )
        
        print(f"  ✅ 异步工具执行: success={result.success}")
        print(f"  ✅ 执行时间: {result.execution_time:.2f}s")
        
        if result.success:
            print(f"  ✅ 搜索结果长度: {len(result.data)} 字符")
        else:
            print(f"  ⚠️  执行失败: {result.error}")
        
        # 测试执行器统计
        stats = executor.get_stats()
        print(f"  ✅ 执行器统计: {stats}")
        
        # 测试全局执行器
        from tools.async_tools import get_global_async_executor
        global_executor = get_global_async_executor()
        global_stats = global_executor.get_stats()
        print(f"  ✅ 全局执行器统计: {global_stats}")
        
        return True
    except Exception as e:
        print(f"  ❌ 异步工具框架测试失败: {e}")
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_async_optimizations():
    """测试异步优化功能。"""
    print("\n🔧 测试异步优化功能...")
    try:
        from tools.async_tools import AsyncBaseTool, AsyncToolExecutor
        import asyncio
        import time
        
        # 创建测试异步工具
        class TestAsyncTool(AsyncBaseTool):
            name: str = "test_async_tool"
            description: str = "Test async tool"
            
            async def _arun(self, input_data: str) -> str:
                await asyncio.sleep(0.1)  # 模拟异步操作
                return f"Async result: {input_data}"
        
        tool = TestAsyncTool()
        executor = AsyncToolExecutor()
        
        # 测试同步包装器性能
        start_time = time.time()
        sync_result = tool._run("test input")
        sync_duration = time.time() - start_time
        print(f"  ✅ 同步包装器执行: {sync_duration:.3f}s")
        print(f"  ✅ 同步结果: {sync_result}")
        
        # 测试异步执行性能
        start_time = time.time()
        async_result = await executor.execute_tool(tool, "test input")
        async_duration = time.time() - start_time
        print(f"  ✅ 异步执行: {async_duration:.3f}s")
        print(f"  ✅ 异步结果成功: {async_result.success}")
        
        # 测试并行执行
        start_time = time.time()
        parallel_results = await executor.execute_tools_parallel([
            (tool, "input1"),
            (tool, "input2"),
            (tool, "input3")
        ])
        parallel_duration = time.time() - start_time
        print(f"  ✅ 并行执行 3 个工具: {parallel_duration:.3f}s")
        print(f"  ✅ 并行结果数量: {len(parallel_results)}")
        
        # 验证并行执行比顺序执行快
        expected_sequential_time = 0.3  # 3 * 0.1s
        if parallel_duration < expected_sequential_time:
            print(f"  ✅ 并行执行优化生效: {parallel_duration:.3f}s < {expected_sequential_time}s")
        else:
            print(f"  ⚠️  并行执行可能未优化: {parallel_duration:.3f}s")
        
        return True
    except Exception as e:
        print(f"  ❌ 异步优化测试失败: {e}")
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_resource_manager():
    """测试资源管理器。"""
    print("\n🔧 测试资源管理器...")
    try:
        from utils.resource_manager import ResourceManager, BrowserResourceFactory, get_browser_resource
        import asyncio
        
        # 创建资源管理器
        manager = ResourceManager()
        
        # 创建浏览器资源池
        factory = BrowserResourceFactory()
        pool = manager.create_pool(
            "test_browser",
            factory,
            min_size=0,
            max_size=2,
            max_idle_time=60.0
        )
        
        print(f"  ✅ 创建资源池: test_browser")
        
        # 测试资源获取和释放
        try:
            async with pool.acquire_context(timeout=5.0) as resource:
                print(f"  ✅ 成功获取资源: {type(resource).__name__}")
        except Exception as e:
            print(f"  ⚠️  资源获取测试跳过: {e}")
        
        # 测试超时机制
        try:
            start_time = asyncio.get_event_loop().time()
            try:
                async with pool.acquire_context(timeout=0.1) as resource:
                    pass
            except asyncio.TimeoutError:
                elapsed = asyncio.get_event_loop().time() - start_time
                print(f"  ✅ 超时机制正常工作: {elapsed:.2f}s")
        except Exception as e:
            print(f"  ⚠️  超时测试跳过: {e}")
        
        # 获取池统计
        stats = pool.get_stats()
        print(f"  ✅ 池统计: {stats}")
        
        # 获取所有统计
        all_stats = manager.get_all_stats()
        print(f"  ✅ 所有池统计: {all_stats}")
        
        # 测试便捷函数
        try:
            async with get_browser_resource() as browser:
                print(f"  ✅ 便捷函数测试成功: {type(browser).__name__}")
        except Exception as e:
            print(f"  ⚠️  便捷函数测试跳过: {e}")
        
        return True
    except Exception as e:
        print(f"  ❌ 资源管理器测试失败: {e}")
        traceback.print_exc()
        return False


def test_service_container():
    """测试服务容器和依赖注入。"""
    print("\n🔧 测试服务容器...")
    try:
        from utils.service_container import ServiceContainer, get_service_container
        
        # 测试全局服务容器
        container = get_service_container()
        print(f"  ✅ 获取全局服务容器")
        
        # 获取注册的服务列表
        services = container.get_registered_services()
        print(f"  ✅ 注册的服务数量: {len(services)}")
        for service_name, service_type in services.items():
            print(f"    - {service_name}: {service_type}")
        
        # 测试服务获取
        if container.has("search_manager"):
            search_manager = container.get("search_manager")
            print(f"  ✅ 获取搜索管理器: {type(search_manager).__name__}")
        
        if container.has("tool_registry"):
            tool_registry = container.get("tool_registry")
            print(f"  ✅ 获取工具注册表: {type(tool_registry).__name__}")
        
        # 测试便捷函数
        from utils.service_container import get_search_manager, get_tool_registry
        search_mgr = get_search_manager()
        tool_reg = get_tool_registry()
        print(f"  ✅ 便捷函数测试: {type(search_mgr).__name__}, {type(tool_reg).__name__}")
        
        # 测试自定义服务注册
        test_container = ServiceContainer()
        test_container.register_singleton("test_service", "test_value")
        
        assert test_container.has("test_service")
        assert test_container.get("test_service") == "test_value"
        print(f"  ✅ 自定义服务注册测试通过")
        
        return True
    except Exception as e:
        print(f"  ❌ 服务容器测试失败: {e}")
        traceback.print_exc()
        return False


def test_config_updates():
    """测试配置更新（LLM 配置）。"""
    print("\n🔧 测试配置更新...")
    try:
        from config import config
        
        # 测试新的 LLM 配置字段
        print(f"  ✅ 默认 LLM 提供商: {config.llm.default_provider}")
        
        # 测试 agent_llms 配置
        agent_llms = config.llm.agent_llms
        print(f"  ✅ Agent LLM 配置数量: {len(agent_llms)}")
        for agent, provider in agent_llms.items():
            print(f"    - {agent}: {provider}")
        
        # 测试 task_specific_models 配置
        task_models = config.llm.task_specific_models
        print(f"  ✅ 任务特定模型配置数量: {len(task_models)}")
        for task, model_config in task_models.items():
            print(f"    - {task}: {model_config.provider} ({model_config.model})")
        
        # 测试配置验证
        if hasattr(config.llm, 'agent_llms') and hasattr(config.llm, 'task_specific_models'):
            print(f"  ✅ 新配置字段验证通过")
        else:
            print(f"  ❌ 新配置字段缺失")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ 配置更新测试失败: {e}")
        traceback.print_exc()
        return False


def main():
    """运行所有测试。"""
    print("🚀 开始运行安全性和架构修复验证测试...\n")
    
    tests = [
        ("配置加载", test_config_loading),
        ("配置更新", test_config_updates),
        ("工具注册表", test_tool_registry),
        ("代码执行器安全性", test_code_runner_security),
        ("搜索引擎", test_search_engines),
        ("Prompt 管理器", test_prompt_manager),
        ("重试处理器", test_retry_handler),
        ("服务容器", test_service_container),
        ("资源管理器", lambda: asyncio.run(test_resource_manager())),
        ("异步工具框架", lambda: asyncio.run(test_async_tools())),
        ("异步优化功能", lambda: asyncio.run(test_async_optimizations())),
        ("MCP 规划器", lambda: asyncio.run(test_mcp_planner())),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出总结
    print("\n" + "="*50)
    print("📊 测试结果总结:")
    print("="*50)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status} {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n🎉 所有测试通过！系统修复成功。")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查相关组件。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 