#!/usr/bin/env python3
"""
Interactive Research Demo
演示 DeepResearch 系统的交互式研究功能
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel

from config import config
from workflow.graph import ResearchWorkflow
from agents.outline_agent import OutlineAgent, OutlineConfig
from utils.user_interaction import get_user_interaction
from utils.markdown_export import MarkdownExporter


console = Console()


def display_demo_banner():
    """Display demo banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                🤝 交互式研究演示                              ║
    ║                                                              ║
    ║  本演示展示 DeepResearch 系统的用户交互功能：                 ║
    ║  • 提纲生成后的用户确认                                       ║
    ║  • 基于用户反馈的自动改进                                     ║
    ║  • 手动编辑和重新生成选项                                     ║
    ║  • 完整的交互式研究流程                                       ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


async def demo_outline_agent_interaction():
    """演示 OutlineAgent 的交互功能。"""
    console.print("\n🎯 演示1: OutlineAgent 交互式提纲生成", style="bold green")
    console.print("="*60)
    
    # 配置交互式 OutlineAgent
    outline_config = OutlineConfig(
        max_sections=4,
        research_depth="standard",
        interactive_mode=True
    )
    
    # 创建 OutlineAgent
    outline_agent = OutlineAgent(config=outline_config)
    
    # 演示主题
    topic = "人工智能在教育领域的应用与挑战"
    console.print(f"📚 研究主题: {topic}")
    
    try:
        # 生成交互式提纲
        outline = await outline_agent.generate_outline(topic)
        
        if outline:
            console.print("\n✅ 提纲生成完成！", style="bold green")
            
            # 导出提纲
            exporter = MarkdownExporter("demo_output")
            outline_file = exporter.export_outline(outline)
            console.print(f"📄 提纲已保存到: {outline_file}")
            
            return outline
        else:
            console.print("\n❌ 提纲生成失败", style="bold red")
            return None
            
    except Exception as e:
        console.print(f"\n❌ 演示过程中出错: {e}", style="bold red")
        return None


async def demo_workflow_interaction():
    """演示 ResearchWorkflow 的交互功能。"""
    console.print("\n🎯 演示2: ResearchWorkflow 完整交互流程", style="bold green")
    console.print("="*60)
    
    # 创建交互式工作流
    workflow = ResearchWorkflow(
        llm_provider="openai",
        max_sections=3,
        language="zh-CN",
        interactive_mode=True
    )
    
    # 演示主题
    topic = "区块链技术在供应链管理中的应用"
    console.print(f"📚 研究主题: {topic}")
    
    try:
        # 运行完整的交互式工作流
        outline, content_map = await workflow.run_full_workflow(topic)
        
        if outline and content_map:
            console.print("\n✅ 完整研究流程完成！", style="bold green")
            
            # 导出最终报告
            exporter = MarkdownExporter("demo_output")
            report_file = exporter.export_full_report(outline, content_map)
            console.print(f"📊 最终报告已保存到: {report_file}")
            
            # 显示统计信息
            progress_summary = exporter.get_progress_summary(content_map)
            console.print(f"📈 完成度: {progress_summary['completion_rate']:.1%}")
            console.print(f"📝 生成内容: {progress_summary['completed_items']}/{progress_summary['total_items']} 个部分")
            
            return True
        else:
            console.print("\n❌ 研究流程失败", style="bold red")
            return False
            
    except Exception as e:
        console.print(f"\n❌ 演示过程中出错: {e}", style="bold red")
        return False


async def demo_user_preferences():
    """演示用户偏好设置功能。"""
    console.print("\n🎯 演示3: 用户偏好设置", style="bold green")
    console.print("="*60)
    
    user_interaction = get_user_interaction()
    
    try:
        # 获取用户偏好
        preferences = user_interaction.get_research_preferences()
        
        console.print("\n✅ 用户偏好设置完成！", style="bold green")
        console.print("您的偏好设置:")
        for key, value in preferences.items():
            console.print(f"  • {key}: {value}")
        
        return preferences
        
    except Exception as e:
        console.print(f"\n❌ 偏好设置过程中出错: {e}", style="bold red")
        return {}


def demo_non_interactive_comparison():
    """演示非交互模式对比。"""
    console.print("\n🎯 演示4: 非交互模式对比", style="bold green")
    console.print("="*60)
    
    console.print("非交互模式特点:")
    console.print("  • 🤖 完全自动化，无需用户干预")
    console.print("  • ⚡ 执行速度更快")
    console.print("  • 📊 适合批量处理和自动化场景")
    console.print("  • 🔧 使用默认配置和策略")
    
    console.print("\n交互模式特点:")
    console.print("  • 🤝 用户可以在关键节点提供反馈")
    console.print("  • 🎯 结果更符合用户期望")
    console.print("  • 🔧 支持实时调整和优化")
    console.print("  • 📚 适合重要研究和定制化需求")
    
    console.print("\n💡 建议:")
    console.print("  • 重要研究使用交互模式")
    console.print("  • 批量处理使用非交互模式")
    console.print("  • 可以通过 --auto 参数切换到非交互模式")


async def main():
    """主演示函数。"""
    display_demo_banner()
    
    # 检查系统配置
    console.print("\n🔍 检查系统配置...", style="bold yellow")
    api_status = config.validate_api_keys()
    
    if not any([api_status.get("openai"), api_status.get("claude"), api_status.get("gemini")]):
        console.print("❌ 没有可用的LLM提供商，请配置API密钥", style="bold red")
        console.print("请设置以下环境变量之一:")
        console.print("  • OPENAI_API_KEY")
        console.print("  • ANTHROPIC_API_KEY") 
        console.print("  • GOOGLE_API_KEY")
        return
    
    console.print("✅ 系统配置检查通过", style="bold green")
    
    # 创建输出目录
    Path("demo_output").mkdir(exist_ok=True)
    
    # 演示选择菜单
    console.print("\n📋 请选择演示内容:", style="bold blue")
    console.print("  1. OutlineAgent 交互式提纲生成")
    console.print("  2. ResearchWorkflow 完整交互流程")
    console.print("  3. 用户偏好设置演示")
    console.print("  4. 交互模式 vs 非交互模式对比")
    console.print("  5. 运行所有演示")
    
    try:
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == "1":
            await demo_outline_agent_interaction()
        elif choice == "2":
            await demo_workflow_interaction()
        elif choice == "3":
            await demo_user_preferences()
        elif choice == "4":
            demo_non_interactive_comparison()
        elif choice == "5":
            # 运行所有演示
            console.print("\n🚀 运行所有演示...", style="bold blue")
            
            await demo_user_preferences()
            await demo_outline_agent_interaction()
            await demo_workflow_interaction()
            demo_non_interactive_comparison()
            
        else:
            console.print("❌ 无效选择", style="bold red")
            return
        
        console.print("\n🎉 演示完成！", style="bold green")
        console.print("📁 输出文件保存在 demo_output/ 目录中")
        
    except KeyboardInterrupt:
        console.print("\n⏹️  演示被用户中断", style="bold yellow")
    except Exception as e:
        console.print(f"\n❌ 演示过程中出错: {e}", style="bold red")


if __name__ == "__main__":
    asyncio.run(main()) 