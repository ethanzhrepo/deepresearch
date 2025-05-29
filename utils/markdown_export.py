"""
Markdown export utilities for DeepResearch system.
Handles generation of structured research reports in Markdown format.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .json_utils import ResearchOutline, Section, SubSection
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class ResearchContent:
    """Container for research content with metadata."""
    section_title: str
    subsection_title: Optional[str] = None
    content: str = ""
    sources: List[str] = None
    keywords: List[str] = None
    generated_at: datetime = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.keywords is None:
            self.keywords = []
        if self.generated_at is None:
            self.generated_at = datetime.now()


class MarkdownExporter:
    """
    Handles export of research content to structured Markdown format.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the Markdown exporter.
        
        Args:
            output_dir: Directory to save exported files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(self.__class__.__name__)
    
    def export_outline(self, outline: ResearchOutline, filename: Optional[str] = None) -> str:
        """
        Export research outline to Markdown format.
        
        Args:
            outline: Research outline to export
            filename: Optional custom filename
        
        Returns:
            Path to exported file
        """
        if not filename:
            safe_title = self._sanitize_filename(outline.title)
            filename = f"{safe_title}_outline.md"
        
        filepath = self.output_dir / filename
        
        content = self._generate_outline_markdown(outline)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"Exported outline to: {filepath}")
        return str(filepath)
    
    def export_full_report(
        self,
        outline: ResearchOutline,
        content_map: Dict[str, ResearchContent],
        filename: Optional[str] = None
    ) -> str:
        """
        Export complete research report with content.
        
        Args:
            outline: Research outline structure
            content_map: Mapping of section/subsection to content
            filename: Optional custom filename
        
        Returns:
            Path to exported file
        """
        if not filename:
            safe_title = self._sanitize_filename(outline.title)
            filename = f"{safe_title}_report.md"
        
        filepath = self.output_dir / filename
        
        content = self._generate_full_report_markdown(outline, content_map)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"Exported full report to: {filepath}")
        return str(filepath)
    
    def _generate_outline_markdown(self, outline: ResearchOutline) -> str:
        """Generate Markdown content for outline only."""
        lines = []
        
        # Title and metadata
        lines.append(f"# {outline.title}")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**语言**: {outline.language}")
        lines.append(f"**预估总字数**: {outline.estimated_total_length:,}")
        lines.append("")
        
        # Abstract
        if outline.abstract:
            lines.append("## 摘要")
            lines.append("")
            lines.append(outline.abstract)
            lines.append("")
        
        # Keywords
        if outline.keywords:
            lines.append("## 关键词")
            lines.append("")
            lines.append(", ".join(f"`{kw}`" for kw in outline.keywords))
            lines.append("")
        
        # Table of Contents
        lines.append("## 目录")
        lines.append("")
        for i, section in enumerate(outline.sections, 1):
            lines.append(f"{i}. [{section.title}](#{self._to_anchor(section.title)})")
            for j, subsection in enumerate(section.subsections, 1):
                lines.append(f"   {i}.{j}. [{subsection.title}](#{self._to_anchor(subsection.title)})")
        lines.append("")
        
        # Sections outline
        lines.append("## 详细提纲")
        lines.append("")
        
        for i, section in enumerate(outline.sections, 1):
            lines.append(f"### {i}. {section.title}")
            lines.append("")
            
            if section.description:
                lines.append(f"**描述**: {section.description}")
                lines.append("")
            
            if section.keywords:
                lines.append(f"**关键词**: {', '.join(f'`{kw}`' for kw in section.keywords)}")
                lines.append("")
            
            lines.append(f"**预估字数**: {section.estimated_length:,}")
            lines.append("")
            
            if section.subsections:
                lines.append("**子章节**:")
                lines.append("")
                for j, subsection in enumerate(section.subsections, 1):
                    lines.append(f"#### {i}.{j}. {subsection.title}")
                    if subsection.description:
                        lines.append(f"- {subsection.description}")
                    if subsection.keywords:
                        lines.append(f"- 关键词: {', '.join(f'`{kw}`' for kw in subsection.keywords)}")
                    lines.append(f"- 预估字数: {subsection.estimated_length:,}")
                    lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_full_report_markdown(
        self,
        outline: ResearchOutline,
        content_map: Dict[str, ResearchContent]
    ) -> str:
        """Generate complete Markdown report with content."""
        lines = []
        
        # Title and metadata
        lines.append(f"# {outline.title}")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**语言**: {outline.language}")
        lines.append("")
        
        # Abstract
        if outline.abstract:
            lines.append("## 摘要")
            lines.append("")
            lines.append(outline.abstract)
            lines.append("")
        
        # Keywords
        if outline.keywords:
            lines.append("## 关键词")
            lines.append("")
            lines.append(", ".join(f"`{kw}`" for kw in outline.keywords))
            lines.append("")
        
        # Table of Contents
        lines.append("## 目录")
        lines.append("")
        for i, section in enumerate(outline.sections, 1):
            lines.append(f"{i}. [{section.title}](#{self._to_anchor(section.title)})")
            for j, subsection in enumerate(section.subsections, 1):
                lines.append(f"   {i}.{j}. [{subsection.title}](#{self._to_anchor(subsection.title)})")
        lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Content sections
        for i, section in enumerate(outline.sections, 1):
            lines.append(f"## {i}. {section.title}")
            lines.append("")
            
            # Section-level content
            section_key = f"section_{i}"
            if section_key in content_map:
                content = content_map[section_key]
                lines.append(content.content)
                lines.append("")
                
                if content.sources:
                    lines.append("### 参考资料")
                    lines.append("")
                    for source in content.sources:
                        lines.append(f"- {source}")
                    lines.append("")
            
            # Subsections
            for j, subsection in enumerate(section.subsections, 1):
                lines.append(f"### {i}.{j}. {subsection.title}")
                lines.append("")
                
                subsection_key = f"section_{i}_subsection_{j}"
                if subsection_key in content_map:
                    content = content_map[subsection_key]
                    lines.append(content.content)
                    lines.append("")
                    
                    if content.sources:
                        lines.append("#### 参考资料")
                        lines.append("")
                        for source in content.sources:
                            lines.append(f"- {source}")
                        lines.append("")
                else:
                    lines.append("*[内容待补充]*")
                    lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # Footer
        lines.append("## 生成信息")
        lines.append("")
        lines.append(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- **系统**: DeepResearch 自动化研究系统")
        lines.append(f"- **版本**: 1.0.0")
        lines.append("")
        
        return "\n".join(lines)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove extra spaces and limit length
        filename = '_'.join(filename.split())
        return filename[:100]  # Limit to 100 characters
    
    def _to_anchor(self, text: str) -> str:
        """Convert text to markdown anchor format."""
        # Convert to lowercase and replace spaces with hyphens
        anchor = text.lower().replace(' ', '-')
        # Remove special characters
        anchor = ''.join(c for c in anchor if c.isalnum() or c in '-_')
        return anchor
    
    def create_content_template(self, outline: ResearchOutline) -> Dict[str, ResearchContent]:
        """
        Create empty content template based on outline structure.
        
        Args:
            outline: Research outline
        
        Returns:
            Dictionary with empty content placeholders
        """
        content_map = {}
        
        for i, section in enumerate(outline.sections, 1):
            # Section-level content
            section_key = f"section_{i}"
            content_map[section_key] = ResearchContent(
                section_title=section.title,
                content="*[内容待生成]*",
                keywords=section.keywords
            )
            
            # Subsection content
            for j, subsection in enumerate(section.subsections, 1):
                subsection_key = f"section_{i}_subsection_{j}"
                content_map[subsection_key] = ResearchContent(
                    section_title=section.title,
                    subsection_title=subsection.title,
                    content="*[内容待生成]*",
                    keywords=subsection.keywords
                )
        
        return content_map
    
    def update_content(
        self,
        content_map: Dict[str, ResearchContent],
        key: str,
        content: str,
        sources: List[str] = None
    ) -> None:
        """
        Update content in the content map.
        
        Args:
            content_map: Content mapping dictionary
            key: Content key to update
            content: New content
            sources: Optional list of sources
        """
        if key in content_map:
            content_map[key].content = content
            if sources:
                content_map[key].sources.extend(sources)
            content_map[key].generated_at = datetime.now()
            self.logger.debug(f"Updated content for key: {key}")
        else:
            self.logger.warning(f"Content key not found: {key}")
    
    def get_progress_summary(self, content_map: Dict[str, ResearchContent]) -> Dict[str, Any]:
        """
        Get progress summary of content generation.
        
        Args:
            content_map: Content mapping dictionary
        
        Returns:
            Progress summary statistics
        """
        total_items = len(content_map)
        completed_items = sum(
            1 for content in content_map.values()
            if content.content and content.content != "*[内容待生成]*"
        )
        
        return {
            "total_items": total_items,
            "completed_items": completed_items,
            "completion_rate": completed_items / total_items if total_items > 0 else 0,
            "remaining_items": total_items - completed_items
        } 