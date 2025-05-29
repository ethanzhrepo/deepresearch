"""
专为 LangGraph Studio 设计的研究工作流
提供完整的可视化调试和状态管理功能
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, TypedDict, Literal, Annotated
from dataclasses import dataclass

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

from config import config
from utils.logger import LoggerMixin
from utils.json_utils import ResearchOutline, extract_outline_from_text
from utils.markdown_export import ResearchContent
from llm.base import LLMWrapper
from llm.openai import OpenAIWrapper
from llm.claude import ClaudeWrapper
from llm.gemini import GeminiWrapper
from llm.ollama import OllamaWrapper
from llm.deepseek import DeepSeekWrapper
from tools.search_engines import SearchEngineManager


# Studio 优化的状态定义
class StudioResearchState(TypedDict):
    """LangGraph Studio 优化的研究状态"""
    # 基础信息
    topic: str
    research_depth: Literal["basic", "intermediate", "advanced"]
    language: str
    llm_provider: str
    
    # 大纲相关
    outline: Optional[Dict[str, Any]]
    outline_approved: bool
    outline_feedback: Optional[str]
    
    # 内容生成
    current_section: int
    current_subsection: int
    content_map: Dict[str, Any]
    
    # 搜索和工具
    search_results: List[Dict[str, Any]]
    search_engines_used: List[str]
    
    # 流程控制
    stage: Literal["init", "outline", "outline_review", "search", "content", "review", "complete", "error"]
    error_message: Optional[str]
    debug_info: Dict[str, Any]
    
    # Studio 特有功能
    user_interventions: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    execution_log: List[str]
    
    # 消息历史（Studio 需要）
    messages: Annotated[List[Dict[str, Any]], add_messages]


class StudioResearchWorkflow(LoggerMixin):
    """专为 LangGraph Studio 设计的研究工作流"""
    
    def __init__(self):
        """初始化 Studio 工作流"""
        self.memory = MemorySaver()
        self.search_manager = SearchEngineManager()
        self.graph = self._build_studio_graph()
    
    def _build_studio_graph(self) -> StateGraph:
        """构建适用于 LangGraph Studio 的研究图"""
        
        workflow = StateGraph(StudioResearchState)
        
        # 添加所有节点
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("generate_outline", self._generate_outline_node)
        workflow.add_node("review_outline", self._review_outline_node)
        workflow.add_node("search_information", self._search_information_node)
        workflow.add_node("generate_content", self._generate_content_node)
        workflow.add_node("review_content", self._review_content_node)
        workflow.add_node("finalize_report", self._finalize_report_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # 设置入口点
        workflow.set_entry_point("initialize")
        
        # 添加边和条件边
        workflow.add_edge("initialize", "generate_outline")
        
        # 大纲生成后的条件分支
        workflow.add_conditional_edges(
            "generate_outline",
            self._should_review_outline,
            {
                "review": "review_outline",
                "approve": "search_information",
                "error": "handle_error"
            }
        )
        
        # 大纲审核后的条件分支
        workflow.add_conditional_edges(
            "review_outline", 
            self._outline_review_decision,
            {
                "regenerate": "generate_outline",
                "approve": "search_information",
                "error": "handle_error"
            }
        )
        
        # 内容生成流程
        workflow.add_edge("search_information", "generate_content")
        workflow.add_edge("generate_content", "review_content")
        
        # 内容审核后的条件分支
        workflow.add_conditional_edges(
            "review_content",
            self._content_review_decision,
            {
                "revise": "generate_content", 
                "finalize": "finalize_report",
                "error": "handle_error"
            }
        )
        
        # 结束节点
        workflow.add_edge("finalize_report", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _initialize_llm(self, provider: str) -> LLMWrapper:
        """初始化 LLM"""
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
            self.log_warning(f"Unknown provider {provider}, falling back to DeepSeek")
            return DeepSeekWrapper(config.get_llm_config("deepseek"))
    
    async def _initialize_node(self, state: StudioResearchState) -> StudioResearchState:
        """初始化研究流程 - Studio 可视化"""
        start_time = time.time()
        
        # 记录初始化日志
        log_entry = f"[{time.strftime('%H:%M:%S')}] 🚀 初始化研究: {state.get('topic', 'Unknown')}"
        execution_log = state.get("execution_log", [])
        execution_log.append(log_entry)
        
        print(f"[Studio Init] {log_entry}")
        
        # 初始化性能指标
        performance_metrics = {
            "start_time": start_time,
            "node_execution_times": {},
            "total_api_calls": 0,
            "total_search_queries": 0
        }
        
        # 初始化调试信息
        debug_info = {
            "initialized": True,
            "timestamp": start_time,
            "config": {
                "research_depth": state.get("research_depth", "intermediate"),
                "language": state.get("language", "zh-CN"),
                "llm_provider": state.get("llm_provider", "deepseek")
            },
            "available_search_engines": self.search_manager.get_available_engines()
        }
        
        return {
            **state,
            "stage": "init",
            "current_section": 0,
            "current_subsection": 0,
            "content_map": {},
            "search_results": [],
            "search_engines_used": [],
            "user_interventions": [],
            "performance_metrics": performance_metrics,
            "execution_log": execution_log,
            "debug_info": debug_info,
            "messages": state.get("messages", [])
        }
    
    async def _generate_outline_node(self, state: StudioResearchState) -> StudioResearchState:
        """生成研究大纲 - Studio 可视化"""
        start_time = time.time()
        
        # 记录日志
        log_entry = f"[{time.strftime('%H:%M:%S')}] 📋 生成研究大纲..."
        execution_log = state.get("execution_log", [])
        execution_log.append(log_entry)
        
        print(f"[Studio Outline] {log_entry}")
        
        try:
            # 初始化 LLM
            llm = self._initialize_llm(state.get("llm_provider", "deepseek"))
            
            # 构建大纲生成提示
            depth = state.get("research_depth", "intermediate")
            section_count = {"basic": 3, "intermediate": 5, "advanced": 8}[depth]
            
            system_prompt = f"""
            你是一个专业的研究助手。请为给定的研究主题生成一个详细的研究提纲。
            
            研究深度: {depth}
            要求章节数: {section_count}
            语言: {state.get('language', 'zh-CN')}
            
            请以JSON格式返回提纲，包含标题、摘要、章节列表等。
            """
            
            user_prompt = f"请为以下研究主题生成详细的研究提纲：{state['topic']}"
            
            # 调用 LLM
            response = llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4000,
                temperature=0.7
            )
            
            execution_time = time.time() - start_time
            
            if response.is_success:
                # 解析大纲
                outline = extract_outline_from_text(response.content)
                
                if outline:
                    # 转换为字典格式以支持 Studio
                    outline_dict = {
                        "title": outline.title,
                        "abstract": outline.abstract,
                        "sections": [
                            {
                                "title": section.title,
                                "description": section.description,
                                "keywords": section.keywords,
                                "estimated_length": section.estimated_length,
                                "subsections": [
                                    {
                                        "title": sub.title,
                                        "description": sub.description,
                                        "keywords": sub.keywords,
                                        "estimated_length": sub.estimated_length
                                    }
                                    for sub in section.subsections
                                ]
                            }
                            for section in outline.sections
                        ],
                        "keywords": outline.keywords,
                        "estimated_total_length": outline.estimated_total_length,
                        "language": outline.language
                    }
                    
                    # 更新状态
                    state["outline"] = outline_dict
                    state["stage"] = "outline"
                    state["outline_approved"] = False
                    
                    # 更新性能指标
                    metrics = state.get("performance_metrics", {})
                    metrics["node_execution_times"]["generate_outline"] = execution_time
                    metrics["total_api_calls"] = metrics.get("total_api_calls", 0) + 1
                    state["performance_metrics"] = metrics
                    
                    # 更新调试信息
                    debug_info = state.get("debug_info", {})
                    debug_info["outline_generated"] = True
                    debug_info["outline_sections_count"] = len(outline.sections)
                    debug_info["last_llm_call"] = {
                        "model": state.get("llm_provider"),
                        "tokens": response.token_usage,
                        "execution_time": execution_time
                    }
                    state["debug_info"] = debug_info
                    
                    execution_log.append(f"[{time.strftime('%H:%M:%S')}] ✅ 大纲生成成功 ({len(outline.sections)} 个章节)")
                else:
                    raise ValueError("Failed to parse outline from response")
            else:
                raise Exception(f"LLM request failed: {response.error}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            state["error_message"] = error_msg
            state["stage"] = "error"
            
            execution_log.append(f"[{time.strftime('%H:%M:%S')}] ❌ 大纲生成失败: {error_msg}")
            
            self.log_error(f"Outline generation failed: {e}")
        
        state["execution_log"] = execution_log
        return state
    
    def _should_review_outline(self, state: StudioResearchState) -> str:
        """决定是否需要审核大纲"""
        if state.get("error_message"):
            return "error"
        elif state.get("outline"):
            # 在 Studio 中，可以设置自动审核或人工审核
            research_depth = state.get("research_depth", "intermediate")
            if research_depth == "advanced":
                return "review"  # 高级研究需要审核
            else:
                return "approve"  # 基础和中级研究自动批准
        else:
            return "error"
    
    async def _review_outline_node(self, state: StudioResearchState) -> StudioResearchState:
        """审核研究大纲 - Studio 交互点"""
        log_entry = f"[{time.strftime('%H:%M:%S')}] 🔍 审核研究大纲..."
        execution_log = state.get("execution_log", [])
        execution_log.append(log_entry)
        
        print(f"[Studio Review] {log_entry}")
        
        # 在 Studio 中，这里可以暂停等待用户输入
        # 暂时设为自动批准，用户可以在 Studio 中手动干预
        
        # 模拟审核过程
        await asyncio.sleep(1)
        
        # 记录用户干预
        intervention = {
            "timestamp": time.time(),
            "node": "review_outline",
            "action": "auto_approve",
            "reason": "Studio auto-review mode"
        }
        
        interventions = state.get("user_interventions", [])
        interventions.append(intervention)
        
        state["user_interventions"] = interventions
        state["outline_approved"] = True
        state["stage"] = "outline_review"
        
        execution_log.append(f"[{time.strftime('%H:%M:%S')}] ✅ 大纲审核通过")
        state["execution_log"] = execution_log
        
        return state
    
    def _outline_review_decision(self, state: StudioResearchState) -> str:
        """大纲审核决策"""
        if state.get("error_message"):
            return "error"
        elif state.get("outline_approved"):
            return "approve"
        else:
            return "regenerate"
    
    async def _search_information_node(self, state: StudioResearchState) -> StudioResearchState:
        """搜索信息 - Studio 可视化搜索过程"""
        start_time = time.time()
        
        log_entry = f"[{time.strftime('%H:%M:%S')}] 🔍 搜索相关信息..."
        execution_log = state.get("execution_log", [])
        execution_log.append(log_entry)
        
        print(f"[Studio Search] {log_entry}")
        
        try:
            outline = state.get("outline", {})
            topic = state.get("topic", "")
            
            # 从大纲中提取搜索关键词
            search_keywords = []
            if outline:
                search_keywords.extend(outline.get("keywords", []))
                for section in outline.get("sections", []):
                    search_keywords.extend(section.get("keywords", []))
            
            # 如果没有关键词，使用主题
            if not search_keywords:
                search_keywords = [topic]
            
            # 使用多个搜索引擎
            available_engines = self.search_manager.get_available_engines()
            search_engines_used = []
            all_search_results = []
            
            # 限制搜索引擎数量以避免过长等待
            engines_to_use = available_engines[:3]  # 使用前3个可用引擎
            
            for engine in engines_to_use:
                try:
                    # 搜索前几个关键词
                    for keyword in search_keywords[:2]:  # 限制关键词数量
                        results = self.search_manager.search(
                            query=keyword,
                            engine=engine,
                            max_results=3
                        )
                        
                        if results:
                            search_engines_used.append(engine)
                            for result in results:
                                all_search_results.append({
                                    "engine": engine,
                                    "keyword": keyword,
                                    "title": result.title,
                                    "url": result.url,
                                    "snippet": result.snippet,
                                    "source": result.source
                                })
                            
                        await asyncio.sleep(0.5)  # 避免过快请求
                        
                except Exception as e:
                    self.log_warning(f"Search failed for {engine}: {e}")
                    continue
            
            execution_time = time.time() - start_time
            
            # 更新状态
            state["search_results"] = all_search_results
            state["search_engines_used"] = list(set(search_engines_used))
            state["stage"] = "search"
            
            # 更新性能指标
            metrics = state.get("performance_metrics", {})
            metrics["node_execution_times"]["search_information"] = execution_time
            metrics["total_search_queries"] = metrics.get("total_search_queries", 0) + len(search_keywords) * len(engines_to_use)
            state["performance_metrics"] = metrics
            
            # 更新调试信息
            debug_info = state.get("debug_info", {})
            debug_info["search_completed"] = True
            debug_info["search_stats"] = {
                "total_results": len(all_search_results),
                "engines_used": search_engines_used,
                "keywords_searched": search_keywords[:2]
            }
            state["debug_info"] = debug_info
            
            execution_log.append(f"[{time.strftime('%H:%M:%S')}] ✅ 搜索完成 ({len(all_search_results)} 个结果)")
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            state["error_message"] = error_msg
            state["stage"] = "error"
            
            execution_log.append(f"[{time.strftime('%H:%M:%S')}] ❌ 搜索失败: {error_msg}")
            
            self.log_error(f"Search failed: {e}")
        
        state["execution_log"] = execution_log
        return state
    
    async def _generate_content_node(self, state: StudioResearchState) -> StudioResearchState:
        """生成内容 - Studio 可视化内容生成"""
        start_time = time.time()
        
        log_entry = f"[{time.strftime('%H:%M:%S')}] ✍️ 生成研究内容..."
        execution_log = state.get("execution_log", [])
        execution_log.append(log_entry)
        
        print(f"[Studio Content] {log_entry}")
        
        try:
            # 初始化 LLM
            llm = self._initialize_llm(state.get("llm_provider", "deepseek"))
            
            outline = state.get("outline", {})
            search_results = state.get("search_results", [])
            
            # 生成内容映射
            content_map = {}
            
            # 为每个章节生成内容
            for i, section in enumerate(outline.get("sections", [])):
                section_key = f"section_{i+1}"
                
                # 构建内容生成提示
                search_context = ""
                if search_results:
                    # 选择相关的搜索结果
                    relevant_results = [r for r in search_results if any(
                        keyword.lower() in r.get("title", "").lower() or 
                        keyword.lower() in r.get("snippet", "").lower()
                        for keyword in section.get("keywords", [])
                    )][:5]  # 最多5个相关结果
                    
                    if relevant_results:
                        search_context = "\n\n参考资料:\n"
                        for result in relevant_results:
                            search_context += f"- {result.get('title', '')} ({result.get('source', '')})\n"
                            search_context += f"  {result.get('snippet', '')[:200]}...\n"
                
                content_prompt = f"""
                请为以下章节生成详细内容：
                
                章节标题: {section.get('title', '')}
                章节描述: {section.get('description', '')}
                关键词: {', '.join(section.get('keywords', []))}
                目标长度: {section.get('estimated_length', 800)} 字
                
                {search_context}
                
                要求:
                1. 内容应该专业、准确、有深度
                2. 使用 {state.get('language', 'zh-CN')} 语言
                3. 包含适当的引用和参考
                4. 结构清晰，逻辑连贯
                """
                
                response = llm.generate(
                    prompt=content_prompt,
                    max_tokens=2000,
                    temperature=0.7
                )
                
                if response.is_success:
                    # 提取引用来源
                    sources = []
                    if search_results:
                        relevant_results = [r for r in search_results if any(
                            keyword.lower() in r.get("title", "").lower() or 
                            keyword.lower() in r.get("snippet", "").lower()
                            for keyword in section.get("keywords", [])
                        )][:3]  # 最多3个来源
                        
                        sources = [f"{r.get('title', '')} - {r.get('source', '')}" for r in relevant_results]
                    
                    content_map[section_key] = {
                        "title": section.get("title", ""),
                        "content": response.content,
                        "sources": sources,
                        "keywords": section.get("keywords", [])
                    }
                    
                    execution_log.append(f"[{time.strftime('%H:%M:%S')}] ✅ 章节 {i+1} 内容生成完成")
                else:
                    self.log_warning(f"Failed to generate content for section {i+1}")
                
                # 添加进度延迟，让 Studio 可以看到进度
                await asyncio.sleep(0.5)
            
            execution_time = time.time() - start_time
            
            # 更新状态
            state["content_map"] = content_map
            state["stage"] = "content"
            
            # 更新性能指标
            metrics = state.get("performance_metrics", {})
            metrics["node_execution_times"]["generate_content"] = execution_time
            metrics["total_api_calls"] = metrics.get("total_api_calls", 0) + len(outline.get("sections", []))
            state["performance_metrics"] = metrics
            
            # 更新调试信息
            debug_info = state.get("debug_info", {})
            debug_info["content_generated"] = True
            debug_info["content_stats"] = {
                "sections_generated": len(content_map),
                "total_content_length": sum(len(c.get("content", "")) for c in content_map.values())
            }
            state["debug_info"] = debug_info
            
            execution_log.append(f"[{time.strftime('%H:%M:%S')}] ✅ 所有内容生成完成")
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            state["error_message"] = error_msg
            state["stage"] = "error"
            
            execution_log.append(f"[{time.strftime('%H:%M:%S')}] ❌ 内容生成失败: {error_msg}")
            
            self.log_error(f"Content generation failed: {e}")
        
        state["execution_log"] = execution_log
        return state
    
    async def _review_content_node(self, state: StudioResearchState) -> StudioResearchState:
        """审核内容 - Studio 可视化审核"""
        log_entry = f"[{time.strftime('%H:%M:%S')}] 🔍 审核生成内容..."
        execution_log = state.get("execution_log", [])
        execution_log.append(log_entry)
        
        print(f"[Studio Content Review] {log_entry}")
        
        # 简单的内容质量检查
        content_map = state.get("content_map", {})
        
        quality_score = 0
        total_sections = len(content_map)
        
        if total_sections > 0:
            for section_key, content in content_map.items():
                content_text = content.get("content", "")
                
                # 检查内容长度
                if len(content_text) > 200:
                    quality_score += 1
                
                # 检查是否有引用来源
                if content.get("sources"):
                    quality_score += 1
            
            quality_ratio = quality_score / (total_sections * 2)  # 每个章节最多2分
        else:
            quality_ratio = 0
        
        # 记录审核结果
        intervention = {
            "timestamp": time.time(),
            "node": "review_content",
            "action": "quality_check",
            "quality_score": quality_ratio,
            "details": f"Generated {total_sections} sections with {quality_score}/{total_sections*2} quality points"
        }
        
        interventions = state.get("user_interventions", [])
        interventions.append(intervention)
        
        state["user_interventions"] = interventions
        state["stage"] = "review"
        
        execution_log.append(f"[{time.strftime('%H:%M:%S')}] ✅ 内容审核完成 (质量分数: {quality_ratio:.2f})")
        state["execution_log"] = execution_log
        
        return state
    
    def _content_review_decision(self, state: StudioResearchState) -> str:
        """内容审核决策"""
        if state.get("error_message"):
            return "error"
        
        # 检查内容质量
        interventions = state.get("user_interventions", [])
        latest_review = None
        
        for intervention in reversed(interventions):
            if intervention.get("node") == "review_content":
                latest_review = intervention
                break
        
        if latest_review:
            quality_score = latest_review.get("quality_score", 0)
            if quality_score >= 0.7:  # 质量分数阈值
                return "finalize"
            else:
                return "revise"
        else:
            return "finalize"  # 默认完成
    
    async def _finalize_report_node(self, state: StudioResearchState) -> StudioResearchState:
        """完成报告 - Studio 可视化最终步骤"""
        log_entry = f"[{time.strftime('%H:%M:%S')}] 📄 完成研究报告..."
        execution_log = state.get("execution_log", [])
        execution_log.append(log_entry)
        
        print(f"[Studio Finalize] {log_entry}")
        
        # 计算总执行时间
        start_time = state.get("performance_metrics", {}).get("start_time", time.time())
        total_time = time.time() - start_time
        
        # 更新最终状态
        state["stage"] = "complete"
        
        # 更新性能指标
        metrics = state.get("performance_metrics", {})
        metrics["total_execution_time"] = total_time
        metrics["completion_timestamp"] = time.time()
        state["performance_metrics"] = metrics
        
        # 最终调试信息
        debug_info = state.get("debug_info", {})
        debug_info["workflow_completed"] = True
        debug_info["final_stats"] = {
            "total_execution_time": total_time,
            "sections_count": len(state.get("content_map", {})),
            "search_results_count": len(state.get("search_results", [])),
            "interventions_count": len(state.get("user_interventions", []))
        }
        state["debug_info"] = debug_info
        
        execution_log.append(f"[{time.strftime('%H:%M:%S')}] 🎉 研究报告完成! (总耗时: {total_time:.2f}s)")
        state["execution_log"] = execution_log
        
        return state
    
    async def _handle_error_node(self, state: StudioResearchState) -> StudioResearchState:
        """处理错误 - Studio 错误可视化"""
        error_msg = state.get("error_message", "Unknown error")
        
        log_entry = f"[{time.strftime('%H:%M:%S')}] ❌ 处理错误: {error_msg}"
        execution_log = state.get("execution_log", [])
        execution_log.append(log_entry)
        
        print(f"[Studio Error] {log_entry}")
        
        # 记录错误干预
        intervention = {
            "timestamp": time.time(),
            "node": "handle_error",
            "action": "error_handling",
            "error_message": error_msg
        }
        
        interventions = state.get("user_interventions", [])
        interventions.append(intervention)
        
        state["user_interventions"] = interventions
        state["stage"] = "error"
        state["execution_log"] = execution_log
        
        return state


# Studio 工作流的工厂函数
def create_studio_workflow() -> StudioResearchWorkflow:
    """创建 Studio 工作流实例"""
    return StudioResearchWorkflow()


# 直接导出图实例给 Studio 使用
studio_workflow = create_studio_workflow()
graph = studio_workflow.graph

# 为 Studio 提供的便捷函数
async def run_studio_research(
    topic: str,
    research_depth: str = "intermediate",
    language: str = "zh-CN",
    llm_provider: str = "deepseek",
    thread_id: str = None
) -> Dict[str, Any]:
    """
    运行 Studio 研究工作流
    
    Args:
        topic: 研究主题
        research_depth: 研究深度 (basic/intermediate/advanced)
        language: 语言
        llm_provider: LLM 提供商
        thread_id: 线程ID (Studio 会话管理)
    
    Returns:
        研究结果状态
    """
    
    # 初始状态
    initial_state = {
        "topic": topic,
        "research_depth": research_depth,
        "language": language,
        "llm_provider": llm_provider,
        "outline": None,
        "outline_approved": False,
        "outline_feedback": None,
        "current_section": 0,
        "current_subsection": 0,
        "content_map": {},
        "search_results": [],
        "search_engines_used": [],
        "stage": "init",
        "error_message": None,
        "debug_info": {},
        "user_interventions": [],
        "performance_metrics": {},
        "execution_log": [],
        "messages": []
    }
    
    # 配置
    config = {
        "configurable": {
            "thread_id": thread_id or f"studio-research-{int(time.time())}"
        }
    }
    
    # 运行工作流
    try:
        result = await graph.ainvoke(initial_state, config=config)
        return result
    except Exception as e:
        print(f"Studio workflow error: {e}")
        return {
            **initial_state,
            "stage": "error",
            "error_message": str(e)
        }


if __name__ == "__main__":
    """Studio 本地测试"""
    import asyncio
    
    async def test_studio_workflow():
        result = await run_studio_research(
            topic="人工智能在医疗领域的应用",
            research_depth="intermediate",
            language="zh-CN",
            llm_provider="deepseek"
        )
        
        print("\n🎨 Studio 工作流测试结果:")
        print(f"阶段: {result.get('stage')}")
        print(f"主题: {result.get('topic')}")
        
        if result.get('outline'):
            print(f"大纲: {result['outline'].get('title')}")
        
        if result.get('content_map'):
            print(f"内容章节: {len(result['content_map'])}")
        
        if result.get('execution_log'):
            print("\n执行日志:")
            for log in result['execution_log'][-5:]:  # 显示最后5条日志
                print(f"  {log}")
    
    asyncio.run(test_studio_workflow()) 