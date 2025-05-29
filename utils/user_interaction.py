"""
User interaction utilities for DeepResearch system.
Provides functions for user confirmation, feedback collection, and interactive modifications.
"""

import json
from typing import Dict, Any, Optional, List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.syntax import Syntax

from utils.json_utils import ResearchOutline, Section, SubSection
from utils.logger import LoggerMixin


class UserInteraction(LoggerMixin):
    """
    Handles user interaction for research workflow.
    Provides confirmation, feedback collection, and modification capabilities.
    """
    
    def __init__(self):
        """Initialize user interaction handler."""
        self.console = Console()
    
    def display_outline(self, outline: ResearchOutline) -> None:
        """
        Display research outline in a formatted way.
        
        Args:
            outline: Research outline to display
        """
        # Create main panel
        title_panel = Panel(
            f"[bold blue]{outline.title}[/bold blue]",
            title="📋 研究提纲",
            border_style="blue"
        )
        self.console.print(title_panel)
        
        # Display abstract if available
        if outline.abstract:
            abstract_panel = Panel(
                outline.abstract,
                title="📝 摘要",
                border_style="green"
            )
            self.console.print(abstract_panel)
        
        # Display sections
        for i, section in enumerate(outline.sections, 1):
            section_content = f"[bold]{section.title}[/bold]\n"
            if section.description:
                section_content += f"{section.description}\n"
            
            # Add subsections
            if section.subsections:
                section_content += "\n子章节:\n"
                for j, subsection in enumerate(section.subsections, 1):
                    section_content += f"  {i}.{j} {subsection.title}\n"
                    if subsection.description:
                        section_content += f"      {subsection.description}\n"
            
            # Add keywords
            if section.keywords:
                section_content += f"\n关键词: {', '.join(section.keywords)}"
            
            section_panel = Panel(
                section_content,
                title=f"📖 第{i}章",
                border_style="cyan"
            )
            self.console.print(section_panel)
        
        # Display summary
        summary_content = f"""
总章节数: {len(outline.sections)}
预估总字数: {outline.estimated_total_length:,}
研究语言: {outline.language}
        """
        
        if outline.keywords:
            summary_content += f"总体关键词: {', '.join(outline.keywords)}"
        
        summary_panel = Panel(
            summary_content.strip(),
            title="📊 提纲摘要",
            border_style="yellow"
        )
        self.console.print(summary_panel)
    
    def get_outline_confirmation(self, outline: ResearchOutline) -> Tuple[bool, Optional[str]]:
        """
        Get user confirmation for research outline.
        
        Args:
            outline: Research outline to confirm
        
        Returns:
            Tuple of (approved, feedback)
        """
        self.console.print("\n" + "="*60)
        self.console.print("📋 请确认研究提纲", style="bold blue")
        self.console.print("="*60)
        
        # Display the outline
        self.display_outline(outline)
        
        # Get user confirmation
        self.console.print("\n请选择您的操作:", style="bold yellow")
        self.console.print("1. ✅ 确认提纲，继续研究")
        self.console.print("2. 📝 提供修改意见")
        self.console.print("3. 🔄 重新生成提纲")
        
        while True:
            choice = Prompt.ask("请输入选择 (1-3)", choices=["1", "2", "3"], default="1")
            
            if choice == "1":
                return True, None
            elif choice == "2":
                feedback = Prompt.ask("请描述您希望如何修改提纲")
                if feedback.strip():
                    return False, feedback
                else:
                    self.console.print("❌ 请提供具体的修改意见", style="bold red")
                    continue
            elif choice == "3":
                return False, None
    
    def get_modification_choice(self, item_type: str = "提纲") -> str:
        """
        Get user choice for modification method.
        
        Args:
            item_type: Type of item being modified
        
        Returns:
            User's choice
        """
        self.console.print(f"\n🔧 如何修改{item_type}?", style="bold blue")
        self.console.print("1. 🤖 自动改进 - 让AI根据您的反馈自动优化")
        self.console.print("2. ✏️ 手动编辑 - 直接编辑内容")
        self.console.print("3. 🔁 重新生成 - 完全重新生成")
        self.console.print("4. ⏭️ 继续执行 - 使用当前版本继续")
        
        choice_map = {
            "1": "自动改进",
            "2": "手动编辑", 
            "3": "重新生成",
            "4": "继续执行"
        }
        
        choice = Prompt.ask("请选择修改方式 (1-4)", choices=["1", "2", "3", "4"], default="1")
        return choice_map[choice]
    
    def get_manual_outline_edit(self, outline: ResearchOutline) -> Optional[ResearchOutline]:
        """
        Allow user to manually edit outline.
        
        Args:
            outline: Current outline
        
        Returns:
            Modified outline or None if cancelled
        """
        self.console.print("\n✏️ 手动编辑模式", style="bold blue")
        self.console.print("您可以修改以下内容:")
        
        # Convert outline to editable format
        outline_dict = outline.dict()
        
        # Edit title
        new_title = Prompt.ask("研究标题", default=outline.title)
        if new_title != outline.title:
            outline_dict["title"] = new_title
        
        # Edit abstract
        if outline.abstract:
            new_abstract = Prompt.ask("研究摘要", default=outline.abstract)
            if new_abstract != outline.abstract:
                outline_dict["abstract"] = new_abstract
        
        # Edit sections (simplified)
        self.console.print("\n📖 章节编辑 (输入空白跳过):")
        for i, section in enumerate(outline.sections):
            new_section_title = Prompt.ask(f"第{i+1}章标题", default=section.title)
            if new_section_title != section.title:
                outline_dict["sections"][i]["title"] = new_section_title
            
            if section.description:
                new_description = Prompt.ask(f"第{i+1}章描述", default=section.description)
                if new_description != section.description:
                    outline_dict["sections"][i]["description"] = new_description
        
        try:
            # Create new outline from modified data
            modified_outline = ResearchOutline(**outline_dict)
            self.console.print("✅ 提纲修改完成", style="bold green")
            return modified_outline
        except Exception as e:
            self.console.print(f"❌ 提纲修改失败: {e}", style="bold red")
            return None
    
    def get_research_preferences(self) -> Dict[str, Any]:
        """
        Get user research preferences.
        
        Returns:
            Dictionary of user preferences
        """
        self.console.print("\n🎯 研究偏好设置", style="bold blue")
        self.console.print("请设置您的研究偏好:")
        
        preferences = {}
        
        # Research depth
        self.console.print("\n📊 研究深度:")
        self.console.print("1. 基础 - 快速概览，3-4个章节")
        self.console.print("2. 标准 - 平衡深度，4-6个章节") 
        self.console.print("3. 深入 - 全面分析，6-8个章节")
        
        depth_choice = Prompt.ask("选择研究深度 (1-3)", choices=["1", "2", "3"], default="2")
        depth_map = {"1": "basic", "2": "standard", "3": "comprehensive"}
        preferences["research_depth"] = depth_map[depth_choice]
        
        # Output format preference
        self.console.print("\n📄 输出格式偏好:")
        self.console.print("1. 学术风格 - 正式、引用丰富")
        self.console.print("2. 商业风格 - 实用、重点突出")
        self.console.print("3. 通俗风格 - 易懂、生动有趣")
        
        style_choice = Prompt.ask("选择输出风格 (1-3)", choices=["1", "2", "3"], default="2")
        style_map = {"1": "academic", "2": "business", "3": "popular"}
        preferences["output_style"] = style_map[style_choice]
        
        # Include search results
        include_search = Confirm.ask("是否包含搜索结果和引用?", default=True)
        preferences["include_search"] = include_search
        
        # Language preference
        language = Prompt.ask("研究语言", default="zh-CN", choices=["zh-CN", "en-US"])
        preferences["language"] = language
        
        self.console.print("\n✅ 偏好设置完成!", style="bold green")
        return preferences
    
    def show_progress_update(self, message: str, status: str = "info") -> None:
        """
        Show progress update to user.
        
        Args:
            message: Progress message
            status: Status type (info, success, warning, error)
        """
        style_map = {
            "info": "blue",
            "success": "green", 
            "warning": "yellow",
            "error": "red"
        }
        
        icon_map = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️", 
            "error": "❌"
        }
        
        style = style_map.get(status, "blue")
        icon = icon_map.get(status, "ℹ️")
        
        self.console.print(f"{icon} {message}", style=f"bold {style}")
    
    def display_success(self, message: str) -> None:
        """Display success message."""
        success_panel = Panel(
            f"[bold green]{message}[/bold green]",
            title="🎉 成功",
            border_style="green"
        )
        self.console.print(success_panel)
    
    def display_error(self, message: str) -> None:
        """Display error message."""
        error_panel = Panel(
            f"[bold red]{message}[/bold red]",
            title="❌ 错误",
            border_style="red"
        )
        self.console.print(error_panel)
    
    def display_warning(self, message: str) -> None:
        """Display warning message."""
        warning_panel = Panel(
            f"[bold yellow]{message}[/bold yellow]",
            title="⚠️ 警告",
            border_style="yellow"
        )
        self.console.print(warning_panel)


# Global instance
_user_interaction = None


def get_user_interaction() -> UserInteraction:
    """
    Get global user interaction instance.
    
    Returns:
        UserInteraction instance
    """
    global _user_interaction
    if _user_interaction is None:
        _user_interaction = UserInteraction()
    return _user_interaction 