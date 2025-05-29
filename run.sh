#!/bin/bash

# DeepResearch 启动脚本
# 自动激活conda环境并运行程序
# 支持传统研究和Studio可视化研究

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示帮助信息
show_help() {
    echo "🔬 DeepResearch - 自动化深度研究系统"
    echo "========================================"
    echo ""
    echo "使用方法:"
    echo "  ./run.sh [命令] [选项]"
    echo ""
    echo "📚 传统研究命令:"
    echo "  interactive <主题>      启动交互式研究"
    echo "  auto <主题>            启动自动化研究"
    echo "  demo                   运行演示"
    echo ""
    echo "🎨 Studio 可视化研究命令:"
    echo "  studio-demo            运行 Studio 演示研究"
    echo "  studio-research <主题>  启动 Studio 研究"
    echo "  studio-check           检查 Studio 环境"
    echo "  studio-setup           设置 Studio 环境"
    echo "  studio-info            显示 Studio 使用指南"
    echo ""
    echo "🔧 系统命令:"
    echo "  config-check           检查系统配置"
    echo "  config-show            显示当前配置"
    echo "  config-edit            编辑配置文件"
    echo "  version                显示版本信息"
    echo ""
    echo "📋 Studio 参数:"
    echo "  --provider PROVIDER    指定 LLM 提供商 (openai|claude|gemini|deepseek|ollama)"
    echo "  --depth DEPTH          指定研究深度 (basic|intermediate|advanced)"
    echo "  --language LANG        指定语言 (默认: zh-CN)"
    echo ""
    echo "示例:"
    echo "  ./run.sh interactive \"人工智能发展趋势\""
    echo "  ./run.sh auto \"区块链技术应用\""
    echo "  ./run.sh studio-demo"
    echo "  ./run.sh studio-research \"AI发展\" --provider deepseek --depth advanced"
    echo "  ./run.sh config-check"
    echo ""
    echo "🎯 LangGraph Studio 集成:"
    echo "  1. 运行 'studio-setup' 设置环境"
    echo "  2. 运行 'studio-demo' 测试工作流"
    echo "  3. 在 LangGraph Studio 中打开项目目录"
    echo "  4. 选择 'studio_research_workflow' 图进行可视化调试"
}

# 查找并激活conda环境
activate_conda() {
    if [[ -f "/opt/homebrew/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "/opt/homebrew/anaconda3/etc/profile.d/conda.sh"
    elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    elif [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
    else
        # 尝试从PATH中找到conda
        local conda_base=$(conda info --base 2>/dev/null || echo "")
        if [[ -n "$conda_base" && -f "$conda_base/etc/profile.d/conda.sh" ]]; then
            source "$conda_base/etc/profile.d/conda.sh"
        else
            print_error "无法找到conda安装路径"
            echo "请手动激活环境: conda activate deep-research-dev"
            exit 1
        fi
    fi
    
    # 激活环境
    conda activate deep-research-dev || {
        print_error "无法激活 deep-research-dev 环境"
        echo "请先运行安装脚本: ./setup.sh"
        exit 1
    }
}

# 检查Studio环境
check_studio_environment() {
    print_info "检查 Studio 环境配置..."
    
    # 检查关键文件
    local required_files=("langgraph.json" "workflow/studio_workflow.py" ".env")
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_success "$file"
        else
            missing_files+=("$file")
            print_error "缺少文件: $file"
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        print_error "环境检查失败"
        return 1
    fi
    
    # 检查关键Python包
    print_info "检查 Python 依赖包..."
    local packages=("langgraph" "langchain" "langchain_openai" "langchain_anthropic")
    local missing_packages=()
    
    for package in "${packages[@]}"; do
        if python3 -c "import ${package//-/_}" 2>/dev/null; then
            print_success "✓ $package"
        else
            missing_packages+=("$package")
            print_error "✗ $package"
        fi
    done
    
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        print_warning "缺少以下依赖包: ${missing_packages[*]}"
        print_info "运行 './run.sh studio-setup' 进行安装"
        return 1
    fi
    
    # 检查LangSmith配置
    if [[ -f ".env" ]]; then
        source .env 2>/dev/null || true
        if [[ -n "$LANGCHAIN_API_KEY" && "$LANGCHAIN_API_KEY" != "your_langsmith_api_key_here" ]]; then
            print_success "LangSmith API 密钥已配置"
        else
            print_warning "LangSmith API 密钥未配置"
            print_info "请在 .env 文件中设置 LANGCHAIN_API_KEY"
        fi
    fi
    
    print_success "Studio 环境检查完成"
    return 0
}

# 设置Studio环境
setup_studio_environment() {
    print_info "设置 LangGraph Studio 环境..."
    
    # 安装Studio相关依赖
    print_info "安装 LangGraph Studio 依赖..."
    pip install "langgraph[studio]" langsmith
    
    # 检查.env文件
    if [[ ! -f ".env" ]]; then
        print_info "创建 .env 文件模板..."
        cat > .env << 'EOF'
# LLM API 密钥
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 搜索引擎 API 密钥
TAVILY_API_KEY=your_tavily_api_key_here
BRAVE_API_KEY=your_brave_api_key_here

# LangSmith 配置 (Studio 必需)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=DeepResearch-Studio

# 其他配置
DEFAULT_LLM_PROVIDER=deepseek
EOF
        print_success "已创建 .env 文件模板，请填入您的 API 密钥"
    fi
    
    print_success "Studio 环境设置完成"
    print_info "请在 .env 文件中配置 LangSmith API 密钥"
    print_info "获取密钥: https://smith.langchain.com/"
}

# 显示Studio使用指南
show_studio_info() {
    print_info "LangGraph Studio 使用指南"
    echo ""
    echo "1. 下载 LangGraph Studio:"
    echo "   访问: https://github.com/langchain-ai/langgraph-studio/releases"
    echo "   下载适用于 macOS 的 .dmg 文件并安装"
    echo ""
    echo "2. 配置 LangSmith:"
    echo "   访问: https://smith.langchain.com/"
    echo "   创建账户并获取 API 密钥"
    echo "   在 .env 文件中设置 LANGCHAIN_API_KEY"
    echo ""
    echo "3. 在 Studio 中打开项目:"
    echo "   启动 LangGraph Studio"
    echo "   点击 'Open Directory'"
    echo "   选择当前项目目录: $(pwd)"
    echo ""
    echo "4. 选择工作流:"
    echo "   在左侧面板选择 'studio_research_workflow'"
    echo "   这是专门为 Studio 优化的研究工作流"
    echo ""
    echo "5. 可视化调试:"
    echo "   设置断点暂停执行"
    echo "   检查节点状态和数据流"
    echo "   手动修改状态值"
    echo "   查看详细的执行日志"
    echo ""
    print_success "开始您的可视化研究之旅！🚀"
}

# 运行Studio演示
run_studio_demo() {
    local provider="deepseek"
    local depth="intermediate"
    local topic="人工智能发展趋势"
    
    print_info "运行 Studio 演示研究..."
    print_info "主题: $topic"
    print_info "深度: $depth"
    print_info "提供商: $provider"
    
    # 运行Studio研究
    python studio.py --run "$topic" --provider "$provider" --depth "$depth"
    
    if [[ $? -eq 0 ]]; then
        print_success "Studio 演示完成"
        print_info "现在可以在 LangGraph Studio 中打开项目目录进行可视化调试"
    else
        print_error "Studio 演示失败"
        return 1
    fi
}

# 运行Studio研究
run_studio_research() {
    local topic="$1"
    local provider="deepseek"
    local depth="intermediate"
    local language="zh-CN"
    
    # 解析参数
    shift
    while [[ $# -gt 0 ]]; do
        case $1 in
            --provider)
                provider="$2"
                shift 2
                ;;
            --depth)
                depth="$2"
                shift 2
                ;;
            --language)
                language="$2"
                shift 2
                ;;
            *)
                print_warning "未知参数: $1"
                shift
                ;;
        esac
    done
    
    if [[ -z "$topic" ]]; then
        print_error "请指定研究主题"
        echo "用法: ./run.sh studio-research \"研究主题\" [--provider PROVIDER] [--depth DEPTH]"
        return 1
    fi
    
    print_info "启动 Studio 研究..."
    print_info "主题: $topic"
    print_info "提供商: $provider"
    print_info "深度: $depth"
    print_info "语言: $language"
    
    # 运行Studio研究
    python studio.py --run "$topic" --provider "$provider" --depth "$depth" --language "$language"
}

# 主函数
main() {
    printf "${GREEN}🔬 启动 DeepResearch 系统...${NC}\n"
    
    # 激活conda环境
    activate_conda
    
    # 如果没有参数，显示帮助
    if [[ $# -eq 0 ]]; then
        show_help
        return 0
    fi
    
    # 解析命令
    local command="$1"
    shift
    
    case "$command" in
        # 传统研究命令
        interactive|auto|demo)
            python main.py "$command" "$@"
            ;;
        
        # Studio命令
        studio-demo)
            if check_studio_environment; then
                run_studio_demo "$@"
            else
                print_error "Studio 环境检查失败"
                print_info "请运行 './run.sh studio-setup' 进行设置"
                return 1
            fi
            ;;
        
        studio-research)
            if check_studio_environment; then
                run_studio_research "$@"
            else
                print_error "Studio 环境检查失败"
                print_info "请运行 './run.sh studio-setup' 进行设置"
                return 1
            fi
            ;;
        
        studio-check)
            check_studio_environment
            ;;
        
        studio-setup)
            setup_studio_environment
            ;;
        
        studio-info)
            show_studio_info
            ;;
        
        # 系统命令
        config-check)
            python main.py config-check
            ;;
        
        config-show)
            python main.py config-show
            ;;
        
        config-edit)
            python main.py config-edit
            ;;
        
        version)
            python main.py version
            ;;
        
        # 帮助
        help|--help|-h)
            show_help
            ;;
        
        # 默认传递给main.py
        *)
            python main.py "$command" "$@"
            ;;
    esac
}

# 运行主函数
main "$@" 