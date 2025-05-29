#!/usr/bin/env python3
"""
DeepResearch - 自动化深度研究系统
主程序入口点，提供命令行接口和核心功能调度。
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
import time

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from config import config
from utils.logger import get_logger
from utils.markdown_export import MarkdownExporter
from utils.user_interaction import get_user_interaction
from workflow.graph import ResearchWorkflow

# Initialize components
console = Console()
logger = get_logger("main")
app = typer.Typer(
    name="deepresearch",
    help="🔬 DeepResearch - 自动化深度研究系统",
    add_completion=False
)


def display_banner():
    """Display application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🔬 DeepResearch                           ║
    ║                  自动化深度研究系统                            ║
    ║                                                              ║
    ║  支持多模型LLM • 智能搜索 • 工具调用 • 结构化报告              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


def check_system_status() -> bool:
    """
    Check system configuration and API keys.
    
    Returns:
        bool: True if system is ready, False otherwise
    """
    try:
        # Check API keys
        api_status = config.validate_api_keys()
        
        # Check if at least one LLM provider is available
        llm_available = any([
            api_status.get("openai", False),
            api_status.get("claude", False),
            api_status.get("gemini", False)
        ])
        
        if not llm_available:
            console.print("⚠️  警告: 没有可用的LLM提供商", style="bold yellow")
            console.print("请配置至少一个LLM API密钥 (OpenAI, Claude, 或 Gemini)")
            return False
        
        # Check output directory
        output_dir = Path(config.system.output_dir)
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                console.print(f"📁 创建输出目录: {output_dir}")
            except Exception as e:
                console.print(f"❌ 无法创建输出目录: {e}", style="bold red")
                return False
        
        return True
        
    except Exception as e:
        console.print(f"❌ 系统检查失败: {e}", style="bold red")
        return False


async def run_research_workflow(
    topic: str,
    provider: Optional[str] = None,
    output_dir: Optional[str] = None,
    max_sections: int = 5,
    language: str = "zh-CN",
    debug: bool = False,
    streaming: bool = True,
    interactive: bool = True
) -> bool:
    """
    Run the research workflow with given parameters.
    
    Args:
        topic: Research topic
        provider: LLM provider to use
        output_dir: Output directory
        max_sections: Maximum number of sections
        language: Research language
        debug: Enable debug mode
        streaming: Enable streaming output
        interactive: Enable interactive mode
    
    Returns:
        bool: True if successful, False otherwise
    """
    if debug:
        config.development.debug_mode = True
        config.system.logging.level = "DEBUG"
    
    if not streaming:
        config.system.enable_streaming = False
    
    # Set output directory
    if output_dir:
        config.system.output_dir = output_dir
    
    # Create output directory
    output_path = Path(config.system.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    console.print(f"\n🎯 开始研究主题: [bold cyan]{topic}[/bold cyan]")
    console.print(f"📁 输出目录: {output_path.absolute()}")
    
    if provider:
        console.print(f"🤖 使用LLM: {provider}")
    
    if interactive:
        console.print("🤝 交互模式: 启用")
        # Get user preferences if in interactive mode
        user_interaction = get_user_interaction()
        preferences = user_interaction.get_research_preferences()
        
        # Apply preferences
        if preferences.get("research_depth") == "basic":
            max_sections = min(max_sections, 3)
        elif preferences.get("research_depth") == "comprehensive":
            max_sections = max(max_sections, 6)
        
        console.print(f"📊 研究深度: {preferences.get('research_depth', 'standard')}")
        console.print(f"📚 章节数量: {max_sections}")
    else:
        console.print("🤖 自动模式: 无用户交互")
    
    try:
        # Initialize workflow
        workflow = ResearchWorkflow(
            llm_provider=provider,
            max_sections=max_sections,
            language=language,
            interactive_mode=interactive
        )
        
        # Run research workflow
        if interactive:
            # Interactive mode - show detailed progress
            console.print("\n" + "="*60)
            console.print("🚀 开始交互式研究流程", style="bold green")
            console.print("="*60)
            
            # Step 1: Generate and confirm outline
            console.print("\n📋 第一步: 生成研究提纲")
            outline = await workflow.generate_outline(topic)
            
            if not outline:
                console.print("❌ 提纲生成失败", style="bold red")
                return False
            
            # Export outline
            exporter = MarkdownExporter(config.system.output_dir)
            outline_file = exporter.export_outline(outline)
            console.print(f"📄 提纲已保存: {outline_file}")
            
            # Step 2: Generate content
            console.print("\n📝 第二步: 生成研究内容")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("正在生成内容...", total=None)
                content_map = await workflow.generate_content(outline)
                progress.update(task, completed=True, description="✅ 内容生成完成")
            
            # Step 3: Export final report
            console.print("\n📊 第三步: 导出最终报告")
            report_file = exporter.export_full_report(outline, content_map)
            
        else:
            # Non-interactive mode - use progress bars
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Step 1: Generate outline
                task1 = progress.add_task("🗂️  生成研究提纲...", total=None)
                outline = await workflow.generate_outline(topic)
                progress.update(task1, completed=True, description="✅ 研究提纲已生成")
                
                if not outline:
                    console.print("❌ 提纲生成失败", style="bold red")
                    return False
                
                # Export outline
                exporter = MarkdownExporter(config.system.output_dir)
                outline_file = exporter.export_outline(outline)
                console.print(f"📄 提纲已保存: {outline_file}")
                
                # Step 2: Generate content
                task2 = progress.add_task("📝 生成研究内容...", total=None)
                content_map = await workflow.generate_content(outline)
                progress.update(task2, completed=True, description="✅ 研究内容已生成")
                
                # Step 3: Export final report
                task3 = progress.add_task("📊 导出最终报告...", total=None)
                report_file = exporter.export_full_report(outline, content_map)
                progress.update(task3, completed=True, description="✅ 最终报告已导出")
        
        # Display results
        console.print("\n🎉 研究完成!", style="bold green")
        console.print(f"📄 最终报告: [link]{report_file}[/link]")
        
        # Show progress summary
        progress_summary = exporter.get_progress_summary(content_map)
        console.print(f"📊 完成度: {progress_summary['completion_rate']:.1%}")
        console.print(f"📝 生成内容: {progress_summary['completed_items']}/{progress_summary['total_items']} 个部分")
        
        return True
        
    except KeyboardInterrupt:
        console.print("\n⏹️  用户中断操作", style="bold yellow")
        return False
    except Exception as e:
        logger.error(f"Research failed: {e}", exc_info=True)
        console.print(f"\n❌ 研究失败: {str(e)}", style="bold red")
        return False


@app.command()
def research(
    topic: str = typer.Argument(..., help="研究主题"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="指定LLM提供商 (openai/claude/gemini/ollama/deepseek)"),
    output_dir: Optional[str] = typer.Option(None, "--output", "-o", help="输出目录"),
    max_sections: int = typer.Option(5, "--max-sections", help="最大章节数"),
    language: str = typer.Option("zh-CN", "--language", "-l", help="研究语言"),
    debug: bool = typer.Option(False, "--debug", help="启用调试模式"),
    streaming: bool = typer.Option(True, "--streaming/--no-streaming", help="启用流式输出"),
    interactive: bool = typer.Option(True, "--interactive/--auto", help="启用交互模式")
):
    """
    🔬 开始深度研究任务
    
    示例:
        deepresearch research "人工智能的发展趋势"
        deepresearch research "区块链技术" --provider claude --output ./reports
        deepresearch research "量子计算" --auto  # 自动模式，无用户交互
    """
    display_banner()
    
    # Check system status
    if not check_system_status():
        console.print("\n❌ 系统配置不完整，无法继续", style="bold red")
        raise typer.Exit(1)
    
    # Run research workflow
    success = asyncio.run(run_research_workflow(
        topic=topic,
        provider=provider,
        output_dir=output_dir,
        max_sections=max_sections,
        language=language,
        debug=debug,
        streaming=streaming,
        interactive=interactive
    ))
    
    if not success:
        raise typer.Exit(1)


@app.command()
def interactive(
    topic: str = typer.Argument(..., help="研究主题")
):
    """
    🤝 启动完全交互式研究模式
    
    这个模式会在每个关键步骤询问用户意见，提供最大的控制权。
    """
    display_banner()
    
    # Check system status
    if not check_system_status():
        console.print("\n❌ 系统配置不完整，无法继续", style="bold red")
        raise typer.Exit(1)
    
    console.print("🤝 完全交互式研究模式", style="bold blue")
    console.print("系统将在每个关键步骤征求您的意见\n")
    
    # Run with full interactivity
    success = asyncio.run(run_research_workflow(
        topic=topic,
        provider=None,  # Let user choose
        output_dir=None,  # Use default
        max_sections=5,  # Will be adjusted based on user preference
        language="zh-CN",
        debug=False,
        streaming=True,
        interactive=True
    ))
    
    if not success:
        raise typer.Exit(1)


@app.command()
def auto(
    topic: str = typer.Argument(..., help="研究主题"),
    provider: Optional[str] = typer.Option("openai", "--provider", "-p", help="指定LLM提供商"),
    max_sections: int = typer.Option(4, "--max-sections", help="最大章节数")
):
    """
    🤖 启动自动研究模式
    
    这个模式会自动完成整个研究流程，无需用户交互。
    """
    display_banner()
    
    # Check system status
    if not check_system_status():
        console.print("\n❌ 系统配置不完整，无法继续", style="bold red")
        raise typer.Exit(1)
    
    console.print("🤖 自动研究模式", style="bold blue")
    console.print("系统将自动完成整个研究流程\n")
    
    # Run without interactivity
    success = asyncio.run(run_research_workflow(
        topic=topic,
        provider=provider,
        output_dir=None,
        max_sections=max_sections,
        language="zh-CN",
        debug=False,
        streaming=True,
        interactive=False
    ))
    
    if not success:
        raise typer.Exit(1)


@app.command()
def config_check():
    """
    🔧 检查配置文件和API密钥
    """
    console.print("🔧 配置检查", style="bold blue")
    
    # Check configuration
    api_status = config.validate_api_keys()
    
    console.print("\n📋 当前配置:")
    console.print(f"  默认LLM提供商: {config.llm.default_provider}")
    console.print(f"  默认搜索引擎: {config.search.default_engine}")
    console.print(f"  输出目录: {config.system.output_dir}")
    console.print(f"  日志级别: {config.system.logging.level}")
    console.print(f"  调试模式: {config.development.debug_mode}")
    
    console.print("\n🔑 API密钥状态:")
    for service, available in api_status.items():
        status = "✅" if available else "❌"
        console.print(f"  {service}: {status}")
    
    # Recommendations
    console.print("\n💡 建议:")
    if not api_status.get("openai") and not api_status.get("claude"):
        console.print("  - 配置至少一个主流LLM提供商 (OpenAI 或 Claude)")
    
    if not api_status.get("serpapi") and not api_status.get("bing"):
        console.print("  - 配置搜索API以获得更好的搜索结果 (SerpAPI 或 Bing)")
    
    if not api_status.get("google_drive") and not api_status.get("dropbox"):
        console.print("  - 配置云存储服务以支持文件集成功能")


@app.command()
def config_show():
    """
    📋 显示当前配置摘要
    """
    console.print("📋 配置摘要", style="bold blue")
    
    summary = config.get_config_summary()
    
    # Create configuration table
    table = Table(title="系统配置")
    table.add_column("配置项", style="cyan")
    table.add_column("当前值", style="green")
    
    table.add_row("LLM提供商", summary["llm_provider"])
    table.add_row("搜索引擎", summary["search_engine"])
    table.add_row("输出目录", summary["output_dir"])
    table.add_row("调试模式", "启用" if summary["debug_mode"] else "禁用")
    
    console.print(table)
    
    # Show tools status
    console.print("\n🔧 工具状态:")
    for tool, enabled in summary["tools_enabled"].items():
        status = "✅ 启用" if enabled else "❌ 禁用"
        console.print(f"  {tool}: {status}")
    
    # Show API keys status
    console.print("\n🔑 API密钥:")
    for service, available in summary["api_keys_available"].items():
        status = "✅ 已配置" if available else "❌ 未配置"
        console.print(f"  {service}: {status}")


@app.command()
def config_edit():
    """
    ✏️  编辑配置文件
    """
    console.print("✏️  配置编辑", style="bold blue")
    
    config_path = Path("config.yml")
    
    if not config_path.exists():
        console.print("❌ 配置文件不存在，请先运行系统生成默认配置", style="bold red")
        return
    
    # Try to open with default editor
    import os
    import subprocess
    
    try:
        if os.name == 'nt':  # Windows
            os.startfile(str(config_path))
        elif os.name == 'posix':  # macOS and Linux
            subprocess.call(['open', str(config_path)])
        else:
            console.print(f"请手动编辑配置文件: {config_path.absolute()}")
    except Exception as e:
        console.print(f"无法自动打开编辑器: {e}")
        console.print(f"请手动编辑配置文件: {config_path.absolute()}")


@app.command()
def config_reset(
    confirm: bool = typer.Option(False, "--confirm", help="确认重置配置")
):
    """
    🔄 重置配置文件到默认值
    """
    console.print("🔄 重置配置", style="bold blue")
    
    if not confirm:
        console.print("⚠️  这将重置所有配置到默认值，所有自定义配置将丢失！")
        console.print("如果确认要重置，请使用: python main.py config-reset --confirm")
        return
    
    try:
        import shutil
        from pathlib import Path
        
        config_path = Path("config.yml")
        
        # Backup existing config
        if config_path.exists():
            backup_path = Path(f"config.yml.backup.{int(time.time())}")
            shutil.copy2(config_path, backup_path)
            console.print(f"📁 已备份现有配置到: {backup_path}")
        
        # Remove existing config to trigger default creation
        if config_path.exists():
            config_path.unlink()
        
        # Reload config (will create default)
        config.reload_config()
        
        console.print("✅ 配置已重置到默认值")
        
    except Exception as e:
        console.print(f"❌ 配置重置失败: {str(e)}", style="bold red")


@app.command()
def config_validate():
    """
    ✅ 验证配置文件
    """
    console.print("✅ 配置验证", style="bold blue")
    
    try:
        # Test configuration loading
        from pathlib import Path
        import yaml
        
        config_path = Path("config.yml")
        
        if not config_path.exists():
            console.print("❌ 配置文件不存在", style="bold red")
            return
        
        # Test YAML parsing
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        console.print("✅ YAML 格式正确")
        
        # Test configuration loading
        config.reload_config()
        console.print("✅ 配置加载成功")
        
        # Validate API keys
        api_status = config.validate_api_keys()
        available_apis = sum(api_status.values())
        total_apis = len(api_status)
        
        console.print(f"🔑 API 密钥: {available_apis}/{total_apis} 已配置")
        
        # Check required sections
        required_sections = ['llm', 'search', 'system', 'tools']
        missing_sections = [s for s in required_sections if s not in config_data]
        
        if missing_sections:
            console.print(f"⚠️  缺少配置节: {', '.join(missing_sections)}", style="bold yellow")
        else:
            console.print("✅ 所有必需配置节都存在")
        
        console.print("✅ 配置验证完成")
        
    except Exception as e:
        console.print(f"❌ 配置验证失败: {str(e)}", style="bold red")


@app.command()
def demo(
    provider: Optional[str] = typer.Option("openai", "--provider", "-p", help="LLM提供商")
):
    """
    🚀 运行演示示例
    """
    display_banner()
    
    # Check system status first
    if not check_system_status():
        console.print("\n❌ 系统配置不完整，无法继续", style="bold red")
        raise typer.Exit(1)
    
    demo_topics = [
        "人工智能在医疗领域的应用",
        "可持续能源发展趋势",
        "区块链技术的商业应用",
        "量子计算的发展前景"
    ]
    
    console.print("🚀 演示模式", style="bold blue")
    console.print("选择一个演示主题:")
    
    for i, topic in enumerate(demo_topics, 1):
        console.print(f"  {i}. {topic}")
    
    choice = typer.prompt("请选择 (1-4)", type=int)
    
    if 1 <= choice <= len(demo_topics):
        selected_topic = demo_topics[choice - 1]
        console.print(f"\n🎯 开始演示研究: {selected_topic}")
        
        # Ask for mode
        mode_choice = typer.prompt("选择模式 (1=交互式, 2=自动)", type=int, default=1)
        interactive_mode = mode_choice == 1
        
        # Run research workflow with selected topic
        success = asyncio.run(run_research_workflow(
            topic=selected_topic,
            provider=provider,
            output_dir=None,  # Use default output directory
            max_sections=3,   # Smaller for demo
            language="zh-CN",
            debug=False,
            streaming=True,
            interactive=interactive_mode
        ))
        
        if not success:
            raise typer.Exit(1)
    else:
        console.print("❌ 无效选择", style="bold red")
        raise typer.Exit(1)


@app.command()
def version():
    """
    📦 显示版本信息
    """
    console.print("📦 版本信息", style="bold blue")
    console.print("DeepResearch v1.0.0")
    console.print("自动化深度研究系统")
    console.print("\n🔗 项目地址: https://github.com/your-repo/deepresearch")
    console.print("📧 联系方式: your-email@example.com")


if __name__ == "__main__":
    app() 