"""
LangGraph-based research workflow for DeepResearch system.
Implements the main research automation pipeline using state graphs.
"""

import asyncio
from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass

from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from config import config
from utils.logger import LoggerMixin
from utils.json_utils import ResearchOutline, extract_outline_from_text, create_sample_outline
from utils.markdown_export import ResearchContent
from utils.user_interaction import get_user_interaction
from llm.base import LLMWrapper
from llm.openai import OpenAIWrapper
from llm.claude import ClaudeWrapper
from llm.gemini import GeminiWrapper
from llm.ollama import OllamaWrapper
from llm.deepseek import DeepSeekWrapper
from tools.search_engines import SearchEngineManager
from tools.tool_registry import ToolRegistry


class ResearchState(TypedDict):
    """State for research workflow."""
    topic: str
    outline: Optional[ResearchOutline]
    content_map: Dict[str, ResearchContent]
    current_section: int
    current_subsection: int
    search_results: List[Dict[str, Any]]
    error_message: Optional[str]
    completed: bool
    user_approved: bool
    user_feedback: Optional[str]
    interactive_mode: bool


@dataclass
class WorkflowConfig:
    """Configuration for research workflow."""
    llm_provider: str = "openai"
    max_sections: int = 5
    max_subsections_per_section: int = 3
    language: str = "zh-CN"
    enable_search: bool = True
    enable_tools: bool = True
    interactive_mode: bool = True


class ResearchWorkflow(LoggerMixin):
    """
    Main research workflow using LangGraph.
    Orchestrates the entire research process from outline to final report.
    """
    
    def __init__(
        self,
        llm_provider: Optional[str] = None,
        max_sections: int = 5,
        language: str = "zh-CN",
        interactive_mode: bool = True
    ):
        """
        Initialize research workflow.
        
        Args:
            llm_provider: LLM provider to use
            max_sections: Maximum number of sections
            language: Research language
            interactive_mode: Enable user interaction
        """
        self.config = WorkflowConfig(
            llm_provider=llm_provider or config.llm.default_provider,
            max_sections=max_sections,
            language=language,
            interactive_mode=interactive_mode
        )
        
        # Initialize components
        self.llm = self._initialize_llm()
        self.search_manager = SearchEngineManager()
        self.tool_registry = ToolRegistry()
        self.user_interaction = get_user_interaction()
        
        # Build workflow graph
        self.graph = self._build_graph()
    
    def _initialize_llm(self) -> LLMWrapper:
        """Initialize LLM wrapper based on provider."""
        provider = self.config.llm_provider
        llm_config = config.get_llm_config(provider)
        
        if provider == "openai":
            return OpenAIWrapper(llm_config)
        elif provider == "claude":
            return ClaudeWrapper(llm_config)
        elif provider == "gemini":
            return GeminiWrapper(llm_config)
        elif provider == "ollama":
            return OllamaWrapper(llm_config)
        elif provider == "deepseek":
            return DeepSeekWrapper(llm_config)
        else:
            self.log_warning(f"Unknown provider {provider}, falling back to OpenAI")
            return OpenAIWrapper(config.get_llm_config("openai"))
    
    def _build_graph(self) -> StateGraph:
        """Build the research workflow graph."""
        workflow = StateGraph(ResearchState)
        
        # Add nodes
        workflow.add_node("generate_outline", self._generate_outline_node)
        workflow.add_node("user_confirm_outline", self._user_confirm_outline_node)
        workflow.add_node("improve_outline", self._improve_outline_node)
        workflow.add_node("validate_outline", self._validate_outline_node)
        workflow.add_node("search_content", self._search_content_node)
        workflow.add_node("generate_content", self._generate_content_node)
        workflow.add_node("finalize_report", self._finalize_report_node)
        
        # Add edges
        workflow.set_entry_point("generate_outline")
        workflow.add_edge("generate_outline", "user_confirm_outline")
        
        # Conditional edges for user confirmation
        workflow.add_conditional_edges(
            "user_confirm_outline",
            self._should_improve_outline,
            {
                "improve": "improve_outline",
                "regenerate": "generate_outline",
                "proceed": "validate_outline"
            }
        )
        
        workflow.add_edge("improve_outline", "user_confirm_outline")
        workflow.add_edge("validate_outline", "search_content")
        workflow.add_edge("search_content", "generate_content")
        workflow.add_edge("generate_content", "finalize_report")
        workflow.add_edge("finalize_report", END)
        
        return workflow.compile()
    
    async def _generate_outline_node(self, state: ResearchState) -> ResearchState:
        """Generate research outline."""
        self.log_info(f"Generating outline for topic: {state['topic']}")
        
        system_prompt = f"""
        你是一个专业的研究助手。请为给定的研究主题生成一个详细的研究提纲。
        
        要求:
        1. 提纲应该包含 {self.config.max_sections} 个主要章节
        2. 每个章节应该有 2-3 个子章节
        3. 提供每个章节的简要描述和关键词
        4. 估算每个部分的字数
        5. 使用 {self.config.language} 语言
        
        请以JSON格式返回提纲，格式如下:
        {{
            "title": "研究标题",
            "abstract": "研究摘要",
            "sections": [
                {{
                    "title": "章节标题",
                    "description": "章节描述",
                    "keywords": ["关键词1", "关键词2"],
                    "estimated_length": 1000,
                    "subsections": [
                        {{
                            "title": "子章节标题",
                            "description": "子章节描述",
                            "keywords": ["关键词"],
                            "estimated_length": 500
                        }}
                    ]
                }}
            ],
            "keywords": ["总体关键词"],
            "estimated_total_length": 5000,
            "language": "{self.config.language}"
        }}
        """
        
        user_prompt = f"请为以下研究主题生成详细的研究提纲：{state['topic']}"
        
        try:
            response = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4000,
                temperature=0.7
            )
            
            if response.is_success:
                outline = extract_outline_from_text(response.content)
                if outline:
                    state["outline"] = outline
                    state["user_approved"] = False
                    state["user_feedback"] = None
                    self.log_info("Successfully generated outline")
                else:
                    self.log_error("Failed to parse outline from response")
                    state["error_message"] = "Failed to parse outline"
            else:
                self.log_error(f"LLM request failed: {response.error}")
                state["error_message"] = response.error
                
        except Exception as e:
            self.log_error(f"Error generating outline: {e}")
            state["error_message"] = str(e)
        
        return state
    
    async def _user_confirm_outline_node(self, state: ResearchState) -> ResearchState:
        """Get user confirmation for the outline."""
        if not self.config.interactive_mode:
            # Skip user interaction in non-interactive mode
            state["user_approved"] = True
            return state
        
        if not state.get("outline"):
            self.log_warning("No outline to confirm")
            state["user_approved"] = False
            return state
        
        try:
            # Get user confirmation
            approved, feedback = self.user_interaction.get_outline_confirmation(state["outline"])
            
            state["user_approved"] = approved
            state["user_feedback"] = feedback
            
            if approved:
                self.log_info("User approved the outline")
            else:
                self.log_info(f"User requested outline changes: {feedback}")
                
        except Exception as e:
            self.log_error(f"Error during user confirmation: {e}")
            # Default to approval if interaction fails
            state["user_approved"] = True
            state["user_feedback"] = None
        
        return state
    
    async def _improve_outline_node(self, state: ResearchState) -> ResearchState:
        """Improve outline based on user feedback."""
        if not state.get("outline") or not state.get("user_feedback"):
            return state
        
        self.log_info("Improving outline based on user feedback")
        
        # Get modification choice from user
        try:
            choice = self.user_interaction.get_modification_choice("提纲")
            
            if choice == "自动改进":
                # Use LLM to improve outline based on feedback
                improved_outline = await self._llm_improve_outline(
                    state["outline"], 
                    state["user_feedback"]
                )
                if improved_outline:
                    state["outline"] = improved_outline
                    self.log_info("Outline improved using LLM")
                
            elif choice == "手动编辑":
                # Allow user to manually edit outline
                modified_outline = self.user_interaction.get_manual_outline_edit(state["outline"])
                if modified_outline:
                    state["outline"] = modified_outline
                    self.log_info("Outline manually edited by user")
                
            elif choice == "重新生成":
                # Clear outline to trigger regeneration
                state["outline"] = None
                state["error_message"] = "User requested regeneration"
                self.log_info("User requested outline regeneration")
                
            elif choice == "继续执行":
                # Proceed with current outline
                state["user_approved"] = True
                self.log_info("User chose to proceed with current outline")
            
            # Reset feedback for next iteration
            state["user_feedback"] = None
            
        except Exception as e:
            self.log_error(f"Error during outline improvement: {e}")
            # Default to proceeding with current outline
            state["user_approved"] = True
        
        return state
    
    async def _llm_improve_outline(self, outline: ResearchOutline, feedback: str) -> Optional[ResearchOutline]:
        """Use LLM to improve outline based on feedback."""
        system_prompt = """
        你是一个研究提纲优化专家。请根据用户反馈改进现有的研究提纲。
        
        改进要求:
        1. 保持原有结构的合理部分
        2. 根据反馈调整章节安排
        3. 优化章节标题和描述
        4. 确保逻辑流畅性
        5. 保持JSON格式输出
        """
        
        user_prompt = f"""
        当前提纲:
        {outline.dict()}
        
        用户反馈:
        {feedback}
        
        请根据反馈改进提纲，返回完整的JSON格式提纲。
        """
        
        try:
            response = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4000,
                temperature=0.5
            )
            
            if response.is_success:
                improved_outline = extract_outline_from_text(response.content)
                if improved_outline:
                    self.log_info("Successfully improved outline using LLM")
                    return improved_outline
            
        except Exception as e:
            self.log_error(f"Failed to improve outline using LLM: {e}")
        
        return None
    
    def _should_improve_outline(self, state: ResearchState) -> str:
        """Decide whether to improve, regenerate, or proceed with outline."""
        if not state.get("outline"):
            return "regenerate"
        
        if not state.get("user_approved"):
            if state.get("user_feedback"):
                return "improve"
            else:
                return "regenerate"
        
        return "proceed"
    
    async def _validate_outline_node(self, state: ResearchState) -> ResearchState:
        """Validate generated outline."""
        if state.get("outline"):
            outline = state["outline"]
            
            # Basic validation
            if len(outline.sections) > self.config.max_sections:
                self.log_warning(f"Outline has too many sections ({len(outline.sections)}), truncating")
                outline.sections = outline.sections[:self.config.max_sections]
            
            # Validate each section has subsections
            for section in outline.sections:
                if not section.subsections:
                    self.log_warning(f"Section '{section.title}' has no subsections, adding default")
                    section.subsections = [
                        type(section.subsections[0] if section.subsections else None)(
                            title="概述",
                            description="本节的概述内容",
                            keywords=section.keywords[:2] if section.keywords else []
                        )
                    ]
            
            state["outline"] = outline
            self.log_info("Outline validation completed")
        
        return state

    async def _search_content_node(self, state: ResearchState) -> ResearchState:
        """Search for content related to outline sections."""
        if not state.get("outline") or not self.config.enable_search:
            return state
        
        outline = state["outline"]
        search_results = []
        
        self.log_info("Searching for content related to outline sections")
        
        try:
            for i, section in enumerate(outline.sections):
                # Create search query for this section
                search_query = f"{state['topic']} {section.title}"
                if section.keywords:
                    search_query += " " + " ".join(section.keywords[:2])
                
                # Perform search
                results = self.search_manager.search(search_query, max_results=5)
                
                search_results.append({
                    "section_index": i,
                    "section_title": section.title,
                    "query": search_query,
                    "results": results
                })
                
                # Add delay between searches to avoid rate limiting
                await asyncio.sleep(2)
            
            state["search_results"] = search_results
            self.log_info(f"Completed search for {len(search_results)} sections")
            
        except Exception as e:
            self.log_error(f"Error during content search: {e}")
            state["search_results"] = []
        
        return state
    
    async def _generate_content_node(self, state: ResearchState) -> ResearchState:
        """Generate content for each section and subsection."""
        if not state.get("outline"):
            return state
        
        outline = state["outline"]
        content_map = {}
        search_results = state.get("search_results", [])
        
        self.log_info("Generating content for outline sections")
        
        for i, section in enumerate(outline.sections):
            # Find relevant search results for this section
            section_search = next(
                (sr for sr in search_results if sr["section_index"] == i),
                None
            )
            
            # Extract sources from search results
            sources = []
            if section_search and section_search.get("results"):
                for result in section_search["results"]:
                    if hasattr(result, 'title') and hasattr(result, 'url') and result.url:
                        sources.append(f"{result.title} - {result.url}")
                    elif isinstance(result, dict) and result.get("url"):
                        title = result.get("title", "Unknown")
                        sources.append(f"{title} - {result['url']}")
            
            # Generate section-level content
            section_content = await self._generate_section_content(
                section, state["topic"], section_search
            )
            
            section_key = f"section_{i+1}"
            content_map[section_key] = ResearchContent(
                section_title=section.title,
                content=section_content,
                sources=sources,
                keywords=section.keywords
            )
            
            # Generate subsection content
            for j, subsection in enumerate(section.subsections):
                subsection_content = await self._generate_subsection_content(
                    subsection, section, state["topic"], section_search
                )
                
                subsection_key = f"section_{i+1}_subsection_{j+1}"
                content_map[subsection_key] = ResearchContent(
                    section_title=section.title,
                    subsection_title=subsection.title,
                    content=subsection_content,
                    sources=sources,
                    keywords=subsection.keywords
                )
        
        state["content_map"] = content_map
        self.log_info(f"Generated content for {len(content_map)} sections/subsections")
        
        return state
    
    async def _generate_section_content(
        self,
        section,
        topic: str,
        search_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate content for a specific section."""
        
        # Prepare search context
        search_context = ""
        if search_results and search_results.get("results"):
            search_context = "\n参考资料:\n"
            for result in search_results["results"][:3]:
                if hasattr(result, 'title') and hasattr(result, 'snippet'):
                    search_context += f"- {result.title}: {result.snippet}\n"
                elif isinstance(result, dict):
                    title = result.get('title', 'No title')
                    snippet = result.get('snippet', 'No description')
                    search_context += f"- {title}: {snippet}\n"
        
        system_prompt = f"""
        你是一个专业的研究写作助手。请为给定的研究章节生成详细的内容。
        
        要求:
        1. 内容应该专业、准确、有深度
        2. 字数约 800-1200 字
        3. 使用 {self.config.language} 语言
        4. 结构清晰，逻辑严密
        5. 如果有参考资料，请合理引用
        """
        
        user_prompt = f"""
        研究主题: {topic}
        章节标题: {section.title}
        章节描述: {section.description}
        关键词: {', '.join(section.keywords) if section.keywords else '无'}
        
        请生成这个章节的详细内容。
        
        {search_context}
        """
        
        try:
            response = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            if response.is_success:
                return response.content
            else:
                self.log_error(f"Failed to generate section content: {response.error}")
                return f"生成章节内容时出错: {response.error}"
                
        except Exception as e:
            self.log_error(f"Error generating section content: {e}")
            return f"生成章节内容时出现异常: {str(e)}"

    async def _generate_subsection_content(
        self,
        subsection,
        section,
        topic: str,
        search_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate content for a specific subsection."""
        
        # Prepare search context
        search_context = ""
        if search_results and search_results.get("results"):
            search_context = "\n参考资料:\n"
            for result in search_results["results"][:2]:
                if hasattr(result, 'title') and hasattr(result, 'snippet'):
                    search_context += f"- {result.title}: {result.snippet}\n"
                elif isinstance(result, dict):
                    title = result.get('title', 'No title')
                    snippet = result.get('snippet', 'No description')
                    search_context += f"- {title}: {snippet}\n"
        
        system_prompt = f"""
        你是一个专业的研究写作助手。请为给定的研究子章节生成详细的内容。
        
        要求:
        1. 内容应该专业、准确、有深度
        2. 字数约 400-600 字
        3. 使用 {self.config.language} 语言
        4. 结构清晰，逻辑严密
        5. 与主章节内容保持一致性
        """
        
        user_prompt = f"""
        研究主题: {topic}
        主章节: {section.title}
        子章节标题: {subsection.title}
        子章节描述: {subsection.description}
        关键词: {', '.join(subsection.keywords) if subsection.keywords else '无'}
        
        请生成这个子章节的详细内容。
        
        {search_context}
        """
        
        try:
            response = self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=1000,
                temperature=0.7
            )
            
            if response.is_success:
                return response.content
            else:
                self.log_error(f"Failed to generate subsection content: {response.error}")
                return f"生成子章节内容时出错: {response.error}"
                
        except Exception as e:
            self.log_error(f"Error generating subsection content: {e}")
            return f"生成子章节内容时出现异常: {str(e)}"
    
    async def _finalize_report_node(self, state: ResearchState) -> ResearchState:
        """Finalize the research report."""
        state["completed"] = True
        self.log_info("Research workflow completed successfully")
        
        if self.config.interactive_mode:
            self.user_interaction.display_success("研究工作流程已完成！")
        
        return state
    
    async def generate_outline(self, topic: str) -> Optional[ResearchOutline]:
        """
        Generate research outline for given topic.
        
        Args:
            topic: Research topic
        
        Returns:
            Generated outline or None if failed
        """
        initial_state = ResearchState(
            topic=topic,
            outline=None,
            content_map={},
            current_section=0,
            current_subsection=0,
            search_results=[],
            error_message=None,
            completed=False,
            user_approved=False,
            user_feedback=None,
            interactive_mode=self.config.interactive_mode
        )
        
        try:
            # Run only outline generation part
            state = await self._generate_outline_node(initial_state)
            
            if self.config.interactive_mode:
                state = await self._user_confirm_outline_node(state)
                
                # Handle user feedback loop
                max_iterations = 3
                iteration = 0
                while not state.get("user_approved") and iteration < max_iterations:
                    if state.get("user_feedback"):
                        state = await self._improve_outline_node(state)
                        state = await self._user_confirm_outline_node(state)
                    else:
                        # Regenerate if no feedback
                        state = await self._generate_outline_node(state)
                        state = await self._user_confirm_outline_node(state)
                    iteration += 1
                
                if iteration >= max_iterations and not state.get("user_approved"):
                    self.log_warning("Maximum iterations reached, proceeding with current outline")
                    state["user_approved"] = True
            
            state = await self._validate_outline_node(state)
            
            return state.get("outline")
            
        except Exception as e:
            self.log_error(f"Failed to generate outline: {e}")
            return None
    
    async def generate_content(self, outline: ResearchOutline) -> Dict[str, ResearchContent]:
        """
        Generate content for given outline.
        
        Args:
            outline: Research outline
        
        Returns:
            Content mapping dictionary
        """
        initial_state = ResearchState(
            topic=outline.title,
            outline=outline,
            content_map={},
            current_section=0,
            current_subsection=0,
            search_results=[],
            error_message=None,
            completed=False,
            user_approved=True,
            user_feedback=None,
            interactive_mode=self.config.interactive_mode
        )
        
        try:
            # Run content generation workflow
            state = await self._search_content_node(initial_state)
            state = await self._generate_content_node(state)
            state = await self._finalize_report_node(state)
            
            return state.get("content_map", {})
            
        except Exception as e:
            self.log_error(f"Failed to generate content: {e}")
            return {}
    
    async def run_full_workflow(self, topic: str) -> tuple[Optional[ResearchOutline], Dict[str, ResearchContent]]:
        """
        Run the complete research workflow.
        
        Args:
            topic: Research topic
        
        Returns:
            Tuple of (outline, content_map)
        """
        initial_state = ResearchState(
            topic=topic,
            outline=None,
            content_map={},
            current_section=0,
            current_subsection=0,
            search_results=[],
            error_message=None,
            completed=False,
            user_approved=False,
            user_feedback=None,
            interactive_mode=self.config.interactive_mode
        )
        
        try:
            # Run the complete workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return final_state.get("outline"), final_state.get("content_map", {})
            
        except Exception as e:
            self.log_error(f"Workflow execution failed: {e}")
            return None, {} 