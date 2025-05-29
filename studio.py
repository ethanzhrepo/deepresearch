#!/usr/bin/env python3
"""
DeepResearch LangGraph Studio Python API
提供 Studio 工作流的 Python 调用接口
"""

import asyncio
import argparse
import sys
import os
import json
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow.studio_workflow import run_studio_research
from utils.logger import LoggerMixin


class StudioAPI(LoggerMixin):
    """Studio API 接口"""
    
    def __init__(self):
        """初始化 API"""
        pass
    
    def show_banner(self):
        """显示横幅"""
        print("""
🎨 DeepResearch LangGraph Studio
================================
AI驱动的可视化研究工作流系统

版本: 1.0.0
Studio 图: studio_research_workflow
        """)
    
    async def run_research(
        self, 
        topic: str, 
        provider: str = "deepseek",
        depth: str = "intermediate",
        language: str = "zh-CN"
    ) -> Dict[str, Any]:
        """运行研究工作流"""
        
        print(f"🚀 启动 Studio 研究工作流...")
        print(f"📝 主题: {topic}")
        print(f"🤖 LLM: {provider}")
        print(f"📊 深度: {depth}")
        print(f"🌍 语言: {language}")
        print("-" * 50)
        
        try:
            result = await run_studio_research(
                topic=topic,
                research_depth=depth,
                language=language,
                llm_provider=provider
            )
            
            self._display_results(result)
            return result
            
        except Exception as e:
            print(f"❌ 研究失败: {e}")
            self.log_error(f"Research failed: {e}")
            return {"stage": "error", "error_message": str(e)}
    
    def _display_results(self, result: Dict[str, Any]):
        """显示研究结果"""
        print("\n" + "="*50)
        print("📊 研究结果")
        print("="*50)
        
        stage = result.get("stage", "unknown")
        print(f"阶段: {stage}")
        
        if stage == "complete":
            print("🎉 研究成功完成!")
            
            # 大纲信息
            outline = result.get("outline")
            if outline:
                print(f"\n📋 大纲: {outline.get('title', 'N/A')}")
                sections = outline.get("sections", [])
                print(f"📄 章节数: {len(sections)}")
                
                for i, section in enumerate(sections, 1):
                    print(f"  {i}. {section.get('title', 'N/A')}")
            
            # 内容信息
            content_map = result.get("content_map", {})
            if content_map:
                print(f"\n✍️  生成内容: {len(content_map)} 个章节")
                total_length = sum(
                    len(content.get("content", "")) 
                    for content in content_map.values()
                )
                print(f"📝 总字数: {total_length:,} 字")
            
            # 搜索信息
            search_results = result.get("search_results", [])
            if search_results:
                print(f"\n🔍 搜索结果: {len(search_results)} 个")
                engines_used = set(r.get("engine") for r in search_results)
                print(f"🔧 使用引擎: {', '.join(engines_used)}")
            
            # 性能指标
            performance = result.get("performance_metrics", {})
            if performance:
                total_time = performance.get("total_execution_time", 0)
                api_calls = performance.get("total_api_calls", 0)
                print(f"\n⚡ 性能:")
                print(f"  ⏱️  总耗时: {total_time:.2f}s")
                print(f"  🔄 API调用: {api_calls} 次")
        
        elif stage == "error":
            print("❌ 研究失败")
            error_msg = result.get("error_message", "Unknown error")
            print(f"错误: {error_msg}")
        
        else:
            print(f"⚠️  研究未完成 (当前阶段: {stage})")
        
        # 执行日志
        execution_log = result.get("execution_log", [])
        if execution_log:
            print(f"\n📝 执行日志 (最近 5 条):")
            for log_entry in execution_log[-5:]:
                print(f"  {log_entry}")
        
        print("\n" + "="*50)
    
    def show_studio_info(self):
        """显示 Studio 信息和使用指南"""
        print("""
🎨 LangGraph Studio 使用指南
==========================

快速启动:
  ./run.sh studio-demo                    # 运行演示
  ./run.sh studio-research "主题"          # 启动研究
  ./run.sh studio-setup                   # 设置环境

安装 LangGraph Studio:
  1. 访问: https://github.com/langchain-ai/langgraph-studio/releases
  2. 下载 macOS 版本并安装

配置步骤:
  1. 运行: ./run.sh studio-setup
  2. 在 .env 文件中设置 LANGCHAIN_API_KEY
  3. 启动 LangGraph Studio 应用
  4. 打开项目目录并选择 'studio_research_workflow'

工作流节点说明:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 initialize          - 初始化研究参数
📋 generate_outline     - 生成研究大纲  
🔍 review_outline       - 审核大纲质量
🔍 search_information   - 搜索相关信息
✍️  generate_content     - 生成研究内容
📝 review_content       - 审核内容质量
📄 finalize_report      - 完成最终报告
❌ handle_error         - 处理异常情况

开始您的可视化研究之旅! 🚀
        """)
    
    def export_config(self, output_file: str = "studio_config.json"):
        """导出 Studio 配置"""
        config_data = {
            "project": "DeepResearch",
            "version": "1.0.0",
            "studio_workflow": "studio_research_workflow",
            "description": "AI驱动的自动化深度研究系统",
            "features": [
                "可视化工作流调试",
                "实时状态监控",
                "交互式断点调试",
                "性能指标分析",
                "多LLM提供商支持",
                "多搜索引擎集成"
            ],
            "supported_llm_providers": [
                "openai", "claude", "gemini", "deepseek", "ollama"
            ],
            "supported_search_engines": [
                "tavily", "duckduckgo", "arxiv", "brave", "google", "bing"
            ],
            "workflow_nodes": [
                "initialize", "generate_outline", "review_outline",
                "search_information", "generate_content", "review_content",
                "finalize_report", "handle_error"
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Studio 配置已导出到: {output_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="DeepResearch Studio Python API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python studio.py --info                        # 显示使用指南
  python studio.py --run "AI发展趋势"             # 运行研究
  python studio.py --run "量子计算" --provider deepseek --depth advanced

推荐使用 run.sh 统一入口:
  ./run.sh studio-demo                          # 运行演示
  ./run.sh studio-research "主题" --provider deepseek
        """
    )
    
    # 主要操作参数
    parser.add_argument(
        "--run", 
        type=str, 
        metavar="TOPIC",
        help="运行研究工作流，指定研究主题"
    )
    
    parser.add_argument(
        "--provider", 
        type=str, 
        default="deepseek",
        choices=["openai", "claude", "gemini", "deepseek", "ollama"],
        help="LLM 提供商 (默认: deepseek)"
    )
    
    parser.add_argument(
        "--depth", 
        type=str, 
        default="intermediate",
        choices=["basic", "intermediate", "advanced"],
        help="研究深度 (默认: intermediate)"
    )
    
    parser.add_argument(
        "--language", 
        type=str, 
        default="zh-CN",
        help="研究语言 (默认: zh-CN)"
    )
    
    # 信息和配置参数
    parser.add_argument(
        "--info", 
        action="store_true",
        help="显示 LangGraph Studio 使用指南"
    )
    
    parser.add_argument(
        "--export-config", 
        type=str, 
        nargs="?",
        const="studio_config.json",
        metavar="FILE",
        help="导出 Studio 配置到文件"
    )
    
    args = parser.parse_args()
    
    # 创建 API 实例
    studio_api = StudioAPI()
    studio_api.show_banner()
    
    # 处理参数
    if args.info:
        studio_api.show_studio_info()
        return
    
    if args.export_config:
        studio_api.export_config(args.export_config)
        return
    
    if args.run:
        # 运行研究
        try:
            result = asyncio.run(studio_api.run_research(
                topic=args.run,
                provider=args.provider,
                depth=args.depth,
                language=args.language
            ))
            
            if result.get("stage") == "complete":
                print("\n🎯 下一步:")
                print("1. 在 LangGraph Studio 中打开项目目录")
                print("2. 选择 'studio_research_workflow' 图")
                print("3. 重新运行以观察可视化调试过程")
                sys.exit(0)
            else:
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n👋 用户中断操作")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 运行失败: {e}")
            sys.exit(1)
    
    # 默认显示帮助
    parser.print_help()


if __name__ == "__main__":
    main() 