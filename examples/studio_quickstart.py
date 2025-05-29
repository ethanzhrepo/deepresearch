"""
LangGraph Studio 快速开始示例
演示如何在 Studio 中可视化和调试 DeepResearch 工作流
"""

import asyncio
from typing import Dict, Any, Optional, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 简化的状态定义
class SimpleResearchState(TypedDict):
    """简化的研究状态，适用于 Studio 演示"""
    topic: str
    stage: Literal["init", "search", "analyze", "complete"]
    findings: str
    debug_info: Dict[str, Any]

class StudioQuickstartWorkflow:
    """Studio 快速开始工作流演示"""
    
    def __init__(self):
        self.memory = MemorySaver()
        self.graph = self._build_demo_graph()
    
    def _build_demo_graph(self) -> StateGraph:
        """构建演示工作流图"""
        
        workflow = StateGraph(SimpleResearchState)
        
        # 添加演示节点
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("search_topic", self._search_topic_node)
        workflow.add_node("analyze_results", self._analyze_results_node)
        workflow.add_node("generate_summary", self._generate_summary_node)
        
        # 添加边
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "search_topic")
        workflow.add_edge("search_topic", "analyze_results")
        workflow.add_edge("analyze_results", "generate_summary")
        workflow.add_edge("generate_summary", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _initialize_node(self, state: SimpleResearchState) -> SimpleResearchState:
        """初始化节点 - 在 Studio 中可视化"""
        print(f"[Studio Demo] 🚀 初始化研究: {state['topic']}")
        
        return {
            **state,
            "stage": "init",
            "findings": "",
            "debug_info": {
                "node": "initialize",
                "timestamp": asyncio.get_event_loop().time(),
                "status": "完成初始化"
            }
        }
    
    async def _search_topic_node(self, state: SimpleResearchState) -> SimpleResearchState:
        """搜索节点 - 模拟搜索过程"""
        print(f"[Studio Demo] 🔍 搜索主题: {state['topic']}")
        
        # 模拟搜索延迟
        await asyncio.sleep(1)
        
        # 模拟搜索结果
        mock_findings = f"关于 '{state['topic']}' 的搜索结果:\n1. 相关研究A\n2. 重要发现B\n3. 最新进展C"
        
        return {
            **state,
            "stage": "search",
            "findings": mock_findings,
            "debug_info": {
                **state.get("debug_info", {}),
                "node": "search_topic",
                "search_results_count": 3,
                "search_duration": 1.0
            }
        }
    
    async def _analyze_results_node(self, state: SimpleResearchState) -> SimpleResearchState:
        """分析节点 - 可以在 Studio 中设置断点"""
        print(f"[Studio Demo] 📊 分析结果...")
        
        # 在 Studio 中可以在这里暂停调试
        if state.get("debug_mode"):
            print("[Studio Breakpoint] 分析节点暂停 - 检查搜索结果")
        
        await asyncio.sleep(0.5)
        
        analysis = f"分析 '{state['topic']}' 的研究结果:\n- 趋势分析\n- 关键发现\n- 建议方向"
        
        return {
            **state,
            "stage": "analyze", 
            "findings": state["findings"] + "\n\n" + analysis,
            "debug_info": {
                **state.get("debug_info", {}),
                "node": "analyze_results",
                "analysis_type": "trend_analysis"
            }
        }
    
    async def _generate_summary_node(self, state: SimpleResearchState) -> SimpleResearchState:
        """生成总结节点 - 完成研究"""
        print(f"[Studio Demo] 📝 生成研究总结")
        
        summary = f"研究总结 - {state['topic']}:\n{state['findings']}\n\n结论: 研究完成"
        
        return {
            **state,
            "stage": "complete",
            "findings": summary,
            "debug_info": {
                **state.get("debug_info", {}),
                "node": "generate_summary",
                "final_status": "研究完成"
            }
        }

# Studio 演示函数
async def run_studio_demo():
    """运行 Studio 演示"""
    
    workflow = StudioQuickstartWorkflow()
    
    # 初始状态
    initial_state = {
        "topic": "人工智能发展趋势",
        "stage": "init",
        "findings": "",
        "debug_info": {}
    }
    
    # 配置
    config = {"configurable": {"thread_id": "studio-demo-001"}}
    
    print("🎨 LangGraph Studio 演示开始...")
    print("💡 在 Studio 中可以可视化此工作流的执行过程")
    
    # 执行工作流
    result = await workflow.graph.ainvoke(initial_state, config=config)
    
    print("\n✅ 演示完成!")
    print(f"📊 最终状态: {result['stage']}")
    print(f"📝 研究结果: {result['findings'][:100]}...")
    
    return result

# 主函数
if __name__ == "__main__":
    print("🎨 LangGraph Studio 快速开始演示")
    print("📖 请参考 docs/langgraph-studio-customization.md 获取完整指南")
    print("-" * 60)
    
    # 运行演示
    asyncio.run(run_studio_demo()) 