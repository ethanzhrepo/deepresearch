"""
Content writing agent for DeepResearch system.
Specialized agent for generating high-quality research content.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from utils.logger import LoggerMixin
from utils.markdown_export import ResearchContent
from llm.base import LLMWrapper
from tools.search_engines import SearchResult
from agents.task_splitter import ResearchTask, TaskType


@dataclass
class WritingStyle:
    """Configuration for writing style."""
    tone: str = "academic"  # academic, professional, casual
    language: str = "zh-CN"
    citation_style: str = "inline"  # inline, footnote, endnote
    include_examples: bool = True
    include_statistics: bool = True
    target_audience: str = "general"  # general, expert, beginner


@dataclass
class ContentWriterConfig:
    """Configuration for content writer."""
    writing_style: WritingStyle
    max_content_length: int = 2000
    min_content_length: int = 300
    include_sources: bool = True
    fact_check: bool = True
    use_templates: bool = True


class ContentWriter(LoggerMixin):
    """
    Specialized agent for writing research content.
    Generates high-quality, well-structured content based on tasks and research data.
    """
    
    def __init__(self, llm_wrapper: LLMWrapper, config: ContentWriterConfig = None):
        """
        Initialize content writer.
        
        Args:
            llm_wrapper: LLM wrapper for content generation
            config: Configuration for content writing
        """
        self.llm = llm_wrapper
        self.config = config or ContentWriterConfig(
            writing_style=WritingStyle()
        )
    
    async def write_content_for_task(
        self, 
        task: ResearchTask,
        research_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> ResearchContent:
        """
        Write content for a specific research task.
        
        Args:
            task: Research task to write content for
            research_data: Research data including search results, analysis, etc.
            context: Optional additional context
        
        Returns:
            Generated research content
        """
        self.log_info(f"Writing content for task: {task.title}")
        
        try:
            # Select appropriate writing strategy based on task type
            if task.task_type == TaskType.SEARCH:
                content = await self._write_search_based_content(task, research_data, context)
            elif task.task_type == TaskType.ANALYSIS:
                content = await self._write_analysis_content(task, research_data, context)
            elif task.task_type == TaskType.SYNTHESIS:
                content = await self._write_synthesis_content(task, research_data, context)
            elif task.task_type == TaskType.COMPARISON:
                content = await self._write_comparison_content(task, research_data, context)
            elif task.task_type == TaskType.CASE_STUDY:
                content = await self._write_case_study_content(task, research_data, context)
            else:
                content = await self._write_general_content(task, research_data, context)
            
            # Extract sources from research data
            sources = self._extract_sources(research_data)
            
            research_content = ResearchContent(
                section_title=task.section_id,
                subsection_title=task.subsection_id,
                content=content,
                sources=sources,
                keywords=task.keywords,
                generated_at=datetime.now()
            )
            
            self.log_info(f"Successfully generated {len(content)} characters of content")
            return research_content
            
        except Exception as e:
            self.log_error(f"Content writing failed for task {task.id}: {e}")
            return ResearchContent(
                section_title=task.section_id,
                subsection_title=task.subsection_id,
                content=f"*[内容生成失败: {str(e)}]*",
                sources=[],
                keywords=task.keywords,
                generated_at=datetime.now()
            )
    
    async def _write_search_based_content(
        self, 
        task: ResearchTask, 
        research_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """Write content based on search results."""
        
        search_results = research_data.get("search_results", [])
        
        # Prepare search context
        search_context = ""
        if search_results:
            search_context = "\n参考资料:\n"
            for i, result in enumerate(search_results[:5], 1):
                if isinstance(result, SearchResult):
                    search_context += f"{i}. {result.title}\n   {result.snippet}\n   来源: {result.url}\n\n"
                elif isinstance(result, dict):
                    search_context += f"{i}. {result.get('title', '')}\n   {result.get('snippet', '')}\n   来源: {result.get('url', '')}\n\n"
        
        system_prompt = f"""
        你是一个专业的研究内容写作专家。请根据任务要求和搜索结果生成高质量的研究内容。
        
        写作要求:
        - 语调: {self.config.writing_style.tone}
        - 语言: {self.config.writing_style.language}
        - 目标读者: {self.config.writing_style.target_audience}
        - 字数范围: {self.config.min_content_length}-{self.config.max_content_length}字
        - 包含实例: {self.config.writing_style.include_examples}
        - 包含统计数据: {self.config.writing_style.include_statistics}
        
        内容要求:
        1. 结构清晰，逻辑严密
        2. 基于提供的搜索结果
        3. 准确引用信息来源
        4. 避免重复和冗余
        5. 保持客观中立的立场
        """
        
        user_prompt = f"""
        任务信息:
        - 标题: {task.title}
        - 描述: {task.description}
        - 关键词: {', '.join(task.keywords)}
        - 期望输出: {task.expected_output}
        
        {f"额外背景: {context}" if context else ""}
        
        {search_context}
        
        请基于以上信息生成专业的研究内容。
        """
        
        response = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=2500,
            temperature=0.6
        )
        
        if response.is_success:
            return response.content
        else:
            self.log_error(f"Content generation failed: {response.error}")
            return f"*[内容生成失败: {response.error}]*"
    
    async def _write_analysis_content(
        self, 
        task: ResearchTask, 
        research_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """Write analytical content."""
        
        analysis_data = research_data.get("analysis_results", {})
        raw_data = research_data.get("raw_data", [])
        
        system_prompt = f"""
        你是一个数据分析和研究专家。请根据提供的数据和分析结果生成深入的分析内容。
        
        分析要求:
        1. 深入解读数据含义
        2. 识别关键趋势和模式
        3. 提供洞察和结论
        4. 使用图表描述（文字形式）
        5. 保持分析的客观性
        
        写作风格: {self.config.writing_style.tone}
        字数要求: {self.config.min_content_length}-{self.config.max_content_length}字
        """
        
        user_prompt = f"""
        分析任务: {task.title}
        任务描述: {task.description}
        
        分析数据:
        {analysis_data}
        
        原始数据:
        {raw_data}
        
        {f"背景信息: {context}" if context else ""}
        
        请生成深入的分析内容。
        """
        
        response = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=2500,
            temperature=0.5
        )
        
        return response.content if response.is_success else f"*[分析内容生成失败]*"
    
    async def _write_synthesis_content(
        self, 
        task: ResearchTask, 
        research_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """Write synthesis content combining multiple sources."""
        
        multiple_sources = research_data.get("multiple_sources", [])
        section_contents = research_data.get("section_contents", {})
        
        system_prompt = f"""
        你是一个内容综合专家。请将多个来源的信息综合成连贯、完整的内容。
        
        综合要求:
        1. 整合不同来源的信息
        2. 消除重复和矛盾
        3. 建立逻辑连接
        4. 保持内容的完整性
        5. 突出关键观点
        
        写作风格: {self.config.writing_style.tone}
        目标字数: {self.config.max_content_length}字
        """
        
        sources_text = ""
        if multiple_sources:
            sources_text = "\n待综合的内容:\n"
            for i, source in enumerate(multiple_sources, 1):
                sources_text += f"\n来源{i}:\n{source}\n"
        
        if section_contents:
            sources_text += "\n章节内容:\n"
            for section_id, content in section_contents.items():
                sources_text += f"\n{section_id}:\n{content}\n"
        
        user_prompt = f"""
        综合任务: {task.title}
        任务描述: {task.description}
        
        {sources_text}
        
        {f"额外背景: {context}" if context else ""}
        
        请将以上内容综合成连贯的研究报告。
        """
        
        response = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=3000,
            temperature=0.4
        )
        
        return response.content if response.is_success else f"*[综合内容生成失败]*"
    
    async def _write_comparison_content(
        self, 
        task: ResearchTask, 
        research_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """Write comparative analysis content."""
        
        comparison_items = research_data.get("comparison_items", [])
        criteria = research_data.get("comparison_criteria", [])
        
        system_prompt = f"""
        你是一个比较分析专家。请根据提供的比较对象和标准生成详细的比较分析。
        
        比较分析要求:
        1. 明确比较维度
        2. 客观评估各项指标
        3. 突出差异和相似点
        4. 提供结论和建议
        5. 使用表格或结构化格式
        
        写作风格: {self.config.writing_style.tone}
        """
        
        comparison_text = ""
        if comparison_items:
            comparison_text += f"\n比较对象: {', '.join(comparison_items)}\n"
        if criteria:
            comparison_text += f"比较标准: {', '.join(criteria)}\n"
        
        user_prompt = f"""
        比较任务: {task.title}
        任务描述: {task.description}
        
        {comparison_text}
        
        {f"背景信息: {context}" if context else ""}
        
        请生成详细的比较分析内容。
        """
        
        response = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=2500,
            temperature=0.5
        )
        
        return response.content if response.is_success else f"*[比较分析生成失败]*"
    
    async def _write_case_study_content(
        self, 
        task: ResearchTask, 
        research_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """Write case study content."""
        
        case_data = research_data.get("case_data", {})
        case_analysis = research_data.get("case_analysis", "")
        
        system_prompt = f"""
        你是一个案例研究专家。请根据案例数据生成详细的案例分析内容。
        
        案例研究要求:
        1. 清晰描述案例背景
        2. 分析关键因素
        3. 识别成功/失败原因
        4. 提取经验教训
        5. 总结可借鉴的要点
        
        写作风格: {self.config.writing_style.tone}
        包含实例: {self.config.writing_style.include_examples}
        """
        
        user_prompt = f"""
        案例研究任务: {task.title}
        任务描述: {task.description}
        
        案例数据:
        {case_data}
        
        案例分析:
        {case_analysis}
        
        {f"背景信息: {context}" if context else ""}
        
        请生成详细的案例研究内容。
        """
        
        response = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=2500,
            temperature=0.6
        )
        
        return response.content if response.is_success else f"*[案例研究生成失败]*"
    
    async def _write_general_content(
        self, 
        task: ResearchTask, 
        research_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """Write general content for unspecified task types."""
        
        system_prompt = f"""
        你是一个专业的内容写作专家。请根据任务要求生成高质量的研究内容。
        
        写作要求:
        - 语调: {self.config.writing_style.tone}
        - 语言: {self.config.writing_style.language}
        - 字数: {self.config.min_content_length}-{self.config.max_content_length}字
        - 结构清晰，内容准确
        """
        
        research_context = ""
        if research_data:
            research_context = f"\n研究数据:\n{research_data}\n"
        
        user_prompt = f"""
        任务: {task.title}
        描述: {task.description}
        关键词: {', '.join(task.keywords)}
        期望输出: {task.expected_output}
        
        {research_context}
        
        {f"额外背景: {context}" if context else ""}
        
        请生成相应的研究内容。
        """
        
        response = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=2500,
            temperature=0.7
        )
        
        return response.content if response.is_success else f"*[内容生成失败]*"
    
    def _extract_sources(self, research_data: Dict[str, Any]) -> List[str]:
        """Extract source URLs from research data."""
        sources = []
        
        # Extract from search results
        search_results = research_data.get("search_results", [])
        for result in search_results:
            if isinstance(result, SearchResult):
                sources.append(f"{result.title} - {result.url}")
            elif isinstance(result, dict) and result.get("url"):
                title = result.get("title", "Unknown")
                sources.append(f"{title} - {result['url']}")
        
        # Extract from other data sources
        if "sources" in research_data:
            sources.extend(research_data["sources"])
        
        return list(set(sources))  # Remove duplicates
    
    async def improve_content(
        self, 
        content: str, 
        feedback: str,
        task: ResearchTask
    ) -> str:
        """
        Improve existing content based on feedback.
        
        Args:
            content: Current content
            feedback: Improvement feedback
            task: Original task
        
        Returns:
            Improved content
        """
        self.log_info(f"Improving content for task: {task.title}")
        
        system_prompt = f"""
        你是一个内容编辑专家。请根据反馈意见改进现有内容。
        
        改进要求:
        1. 保持原有内容的核心信息
        2. 根据反馈调整结构和表达
        3. 提高内容质量和可读性
        4. 保持写作风格一致性
        5. 确保事实准确性
        
        写作风格: {self.config.writing_style.tone}
        """
        
        user_prompt = f"""
        原始任务: {task.title}
        
        当前内容:
        {content}
        
        改进反馈:
        {feedback}
        
        请根据反馈改进内容。
        """
        
        response = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=3000,
            temperature=0.5
        )
        
        if response.is_success:
            self.log_info("Content improvement completed")
            return response.content
        else:
            self.log_error(f"Content improvement failed: {response.error}")
            return content  # Return original content if improvement fails
    
    def validate_content_quality(self, content: str, task: ResearchTask) -> Dict[str, Any]:
        """
        Validate content quality against task requirements.
        
        Args:
            content: Generated content
            task: Original task
        
        Returns:
            Quality assessment results
        """
        assessment = {
            "length_check": False,
            "keyword_coverage": 0.0,
            "structure_score": 0.0,
            "overall_score": 0.0,
            "suggestions": []
        }
        
        # Length check
        content_length = len(content)
        if self.config.min_content_length <= content_length <= self.config.max_content_length:
            assessment["length_check"] = True
        else:
            if content_length < self.config.min_content_length:
                assessment["suggestions"].append("内容长度不足，需要补充更多信息")
            else:
                assessment["suggestions"].append("内容过长，需要精简")
        
        # Keyword coverage
        content_lower = content.lower()
        covered_keywords = sum(1 for kw in task.keywords if kw.lower() in content_lower)
        assessment["keyword_coverage"] = covered_keywords / len(task.keywords) if task.keywords else 1.0
        
        if assessment["keyword_coverage"] < 0.5:
            assessment["suggestions"].append("关键词覆盖不足，需要包含更多相关术语")
        
        # Structure assessment (simple heuristic)
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 3:
            assessment["structure_score"] = 0.8
        elif len(paragraphs) >= 2:
            assessment["structure_score"] = 0.6
        else:
            assessment["structure_score"] = 0.4
            assessment["suggestions"].append("内容结构需要改进，建议分段组织")
        
        # Overall score
        assessment["overall_score"] = (
            (1.0 if assessment["length_check"] else 0.5) * 0.3 +
            assessment["keyword_coverage"] * 0.3 +
            assessment["structure_score"] * 0.4
        )
        
        return assessment 