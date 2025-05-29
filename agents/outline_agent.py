"""
Outline generation agent for DeepResearch system.
Specialized agent for creating detailed research outlines.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from utils.json_utils import ResearchOutline, extract_outline_from_text
from utils.user_interaction import get_user_interaction
from tools.search_engines import SearchEngineManager
from .base_agent import BaseAgent


@dataclass
class OutlineConfig:
    """Configuration for outline generation."""
    max_sections: int = 5
    max_subsections_per_section: int = 3
    language: str = "zh-CN"
    include_keywords: bool = True
    include_estimates: bool = True
    research_depth: str = "comprehensive"  # basic, standard, comprehensive
    interactive_mode: bool = True


class OutlineAgent(BaseAgent):
    """
    Specialized agent for generating research outlines.
    Uses LLM and search engines to create comprehensive research structures.
    """
    
    def __init__(self, llm_provider: Optional[str] = None, config: OutlineConfig = None):
        """
        Initialize outline agent.
        
        Args:
            llm_provider: LLM provider to use (overrides config)
            config: Configuration for outline generation
        """
        self.config = config or OutlineConfig()
        
        # 调用父类初始化（会自动选择和初始化 LLM）
        super().__init__(llm_provider=llm_provider)
        
        # Initialize user interaction if in interactive mode
        if self.config.interactive_mode:
            self.user_interaction = get_user_interaction()
        else:
            self.user_interaction = None
        
    def _initialize_components(self):
        """初始化 OutlineAgent 特定的组件。"""
        # 调用父类初始化（获取服务容器）
        super()._initialize_components()
        
        # 优先使用服务容器，回退到直接创建
        if self.service_container and self.service_container.has("search_manager"):
            self.search_manager = self.service_container.get("search_manager")
            self.log_debug("Using search manager from service container")
        else:
            from tools.search_engines import SearchEngineManager
            self.search_manager = SearchEngineManager()
            self.log_debug("Created new search manager instance")
    
    async def generate_outline(self, topic: str, context: Optional[str] = None) -> Optional[ResearchOutline]:
        """
        Generate comprehensive research outline for given topic.
        
        Args:
            topic: Research topic
            context: Optional additional context
        
        Returns:
            Generated research outline or None if failed
        """
        self.log_info(f"Generating outline for topic: {topic}")
        
        try:
            # Step 1: Gather background information
            background_info = await self._gather_background_info(topic)
            
            # Step 2: Generate initial outline
            outline = await self._generate_initial_outline(topic, background_info, context)
            
            if not outline:
                self.log_error("Failed to generate initial outline")
                return None
            
            # Step 3: User interaction if enabled
            if self.config.interactive_mode and self.user_interaction:
                outline = await self._handle_user_interaction(outline, topic)
            
            # Step 4: Final validation
            refined_outline = await self._refine_outline(outline, topic)
            
            self.log_info(f"Successfully generated outline with {len(refined_outline.sections)} sections")
            return refined_outline
            
        except Exception as e:
            self.log_error(f"Outline generation failed: {e}")
            return None
    
    async def _handle_user_interaction(self, outline: ResearchOutline, topic: str) -> ResearchOutline:
        """
        Handle user interaction for outline confirmation and improvement.
        
        Args:
            outline: Initial outline
            topic: Research topic
        
        Returns:
            Final outline after user interaction
        """
        max_iterations = 3
        iteration = 0
        current_outline = outline
        
        while iteration < max_iterations:
            # Get user confirmation
            approved, feedback = self.user_interaction.get_outline_confirmation(current_outline)
            
            if approved:
                self.log_info("User approved the outline")
                break
            
            if not feedback:
                self.log_info("User rejected outline without feedback, regenerating")
                # Regenerate outline
                background_info = await self._gather_background_info(topic)
                new_outline = await self._generate_initial_outline(topic, background_info)
                if new_outline:
                    current_outline = new_outline
                iteration += 1
                continue
            
            # Get modification choice
            choice = self.user_interaction.get_modification_choice("提纲")
            
            if choice == "自动改进":
                # Use LLM to improve outline
                improved_outline = await self.suggest_improvements(current_outline, feedback)
                if improved_outline:
                    current_outline = improved_outline
                    self.log_info("Outline improved using LLM")
                
            elif choice == "手动编辑":
                # Allow manual editing
                modified_outline = self.user_interaction.get_manual_outline_edit(current_outline)
                if modified_outline:
                    current_outline = modified_outline
                    self.log_info("Outline manually edited by user")
                
            elif choice == "重新生成":
                # Regenerate outline
                background_info = await self._gather_background_info(topic)
                new_outline = await self._generate_initial_outline(topic, background_info)
                if new_outline:
                    current_outline = new_outline
                    self.log_info("Outline regenerated")
                
            elif choice == "继续执行":
                # Proceed with current outline
                self.log_info("User chose to proceed with current outline")
                break
            
            iteration += 1
        
        if iteration >= max_iterations:
            self.log_warning("Maximum iterations reached, proceeding with current outline")
            if self.user_interaction:
                self.user_interaction.show_progress_update(
                    "已达到最大修改次数，将使用当前提纲继续", 
                    "warning"
                )
        
        return current_outline
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行大纲生成任务。
        
        Args:
            task_data: 包含 topic 和可选 context 的任务数据
        
        Returns:
            任务执行结果
        """
        try:
            topic = task_data.get("topic", "")
            context = task_data.get("context")
            
            if not topic:
                return {
                    "success": False,
                    "error": "Missing required field: topic"
                }
            
            outline = await self.generate_outline(topic, context)
            
            if outline:
                return {
                    "success": True,
                    "data": {
                        "outline": outline,
                        "sections_count": len(outline.sections),
                        "estimated_length": outline.estimated_total_length
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate outline"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_capabilities(self) -> list:
        """获取 OutlineAgent 的能力列表。"""
        return [
            "outline_generation",
            "research_planning", 
            "topic_analysis",
            "structure_design",
            "keyword_extraction"
        ]
    
    async def _gather_background_info(self, topic: str) -> Dict[str, Any]:
        """Gather background information for the topic."""
        background_info = {
            "search_results": [],
            "key_concepts": [],
            "related_topics": []
        }
        
        try:
            # Perform initial search to gather context
            search_results = self.search_manager.search(topic, max_results=5)
            background_info["search_results"] = search_results
            
            # Extract key concepts from search results
            if search_results:
                concepts = set()
                for result in search_results:
                    if hasattr(result, 'title'):
                        # Simple keyword extraction from titles
                        words = result.title.split()
                        concepts.update([w for w in words if len(w) > 3])
                
                background_info["key_concepts"] = list(concepts)[:10]
            
            self.log_debug(f"Gathered background info: {len(search_results)} search results")
            
        except Exception as e:
            self.log_error(f"Failed to gather background info: {e}")
        
        return background_info
    
    async def _generate_initial_outline(
        self, 
        topic: str, 
        background_info: Dict[str, Any],
        context: Optional[str] = None
    ) -> Optional[ResearchOutline]:
        """Generate initial research outline."""
        
        # Prepare background context
        background_context = ""
        if background_info.get("search_results"):
            background_context += "\n参考信息:\n"
            for result in background_info["search_results"]:
                if hasattr(result, 'title') and hasattr(result, 'snippet'):
                    background_context += f"- {result.title}: {result.snippet}\n"
                elif isinstance(result, dict):
                    title = result.get('title', 'No title')
                    snippet = result.get('snippet', 'No description')
                    background_context += f"- {title}: {snippet}\n"
        
        if background_info.get("key_concepts"):
            background_context += f"\n关键概念: {', '.join(background_info['key_concepts'])}\n"
        
        if background_info.get("related_topics"):
            background_context += f"相关主题: {', '.join(background_info['related_topics'])}\n"
        
        # Generate outline based on research depth
        depth_instructions = self._get_depth_instructions()
        
        system_prompt = f"""
        你是一个专业的研究规划专家。请为给定的研究主题生成一个详细、结构化的研究提纲。
        
        研究深度要求: {depth_instructions}
        
        提纲要求:
        1. 包含 {self.config.max_sections} 个主要章节
        2. 每个章节包含 {self.config.max_subsections_per_section} 个子章节
        3. 每个章节和子章节都要有清晰的描述和关键词
        4. 估算每个部分的字数（总计约5000-8000字）
        5. 使用 {self.config.language} 语言
        6. 确保逻辑结构清晰，层次分明
        
        请以JSON格式返回提纲，格式如下:
        {{
            "title": "研究标题",
            "abstract": "研究摘要（100-200字）",
            "sections": [
                {{
                    "title": "章节标题",
                    "description": "章节描述（50-100字）",
                    "keywords": ["关键词1", "关键词2", "关键词3"],
                    "estimated_length": 1500,
                    "subsections": [
                        {{
                            "title": "子章节标题",
                            "description": "子章节描述（30-50字）",
                            "keywords": ["关键词1", "关键词2"],
                            "estimated_length": 500
                        }}
                    ]
                }}
            ],
            "keywords": ["总体关键词1", "总体关键词2", "总体关键词3"],
            "estimated_total_length": 6000,
            "language": "{self.config.language}"
        }}
        """
        
        user_prompt = f"""
        研究主题: {topic}
        
        {f"额外背景: {context}" if context else ""}
        
        {background_context}
        
        请生成详细的研究提纲。
        """
        
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
                    self.log_info("Successfully generated initial outline")
                    return outline
                else:
                    self.log_error("Failed to parse outline from LLM response")
            else:
                self.log_error(f"LLM request failed: {response.error}")
                
        except Exception as e:
            self.log_error(f"Error generating initial outline: {e}")
        
        return None
    
    async def _refine_outline(self, outline: ResearchOutline, topic: str) -> ResearchOutline:
        """Refine and validate the outline."""
        # Basic validation and refinement
        if len(outline.sections) > self.config.max_sections:
            self.log_warning(f"Outline has too many sections, truncating to {self.config.max_sections}")
            outline.sections = outline.sections[:self.config.max_sections]
        
        # Ensure each section has subsections
        for section in outline.sections:
            if not section.subsections:
                self.log_warning(f"Section '{section.title}' has no subsections, adding default")
                from utils.json_utils import SubSection
                section.subsections = [
                    SubSection(
                        title="概述",
                        description="本节的概述内容",
                        keywords=section.keywords[:2] if section.keywords else []
                    )
                ]
        
        return outline
    
    def _get_depth_instructions(self) -> str:
        """Get instructions based on research depth setting."""
        depth_map = {
            "basic": "基础研究 - 提供主题的基本概述和核心要点",
            "standard": "标准研究 - 包含详细分析和多角度探讨", 
            "comprehensive": "深度研究 - 全面深入分析，包含历史背景、现状、趋势、案例等"
        }
        return depth_map.get(self.config.research_depth, depth_map["standard"])
    
    async def suggest_improvements(self, outline: ResearchOutline, feedback: str) -> Optional[ResearchOutline]:
        """
        Suggest improvements to existing outline based on feedback.
        
        Args:
            outline: Current outline
            feedback: Feedback or improvement suggestions
        
        Returns:
            Improved outline or None if failed
        """
        self.log_info("Generating outline improvements based on feedback")
        
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
                    self.log_info("Successfully generated improved outline")
                    return improved_outline
            
        except Exception as e:
            self.log_error(f"Failed to improve outline: {e}")
        
        return None 