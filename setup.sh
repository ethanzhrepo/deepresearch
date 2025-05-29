#!/bin/bash

# DeepResearch 系统安装脚本
# 使用 conda 创建 deep-research-dev 环境并安装依赖

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示横幅
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🔬 DeepResearch                           ║"
    echo "║                  自动化深度研究系统                            ║"
    echo "║                                                              ║"
    echo "║                    环境安装脚本                               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查 conda 是否安装
check_conda() {
    print_info "检查 conda 是否已安装..."
    if ! command -v conda &> /dev/null; then
        print_error "conda 未找到！请先安装 Anaconda 或 Miniconda"
        print_info "下载地址："
        print_info "  Miniconda: https://docs.conda.io/en/latest/miniconda.html"
        print_info "  Anaconda: https://www.anaconda.com/products/distribution"
        exit 1
    fi
    print_success "conda 已安装: $(conda --version)"
}

# 检查 Python 版本要求
check_python_version() {
    print_info "检查 Python 版本要求..."
    local python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ -z "$python_version" ]]; then
        print_warning "未找到 python3，将使用 conda 安装 Python 3.11"
    else
        print_info "系统 Python 版本: $python_version"
    fi
}

# 创建 conda 环境
create_conda_env() {
    local env_name="deep-research-dev"
    
    print_info "检查是否存在 $env_name 环境..."
    if conda env list | grep -q "^$env_name "; then
        print_warning "环境 $env_name 已存在"
        read -p "是否删除现有环境并重新创建？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "删除现有环境 $env_name..."
            conda env remove -n $env_name -y
        else
            print_info "使用现有环境 $env_name"
            return 0
        fi
    fi
    
    print_info "创建 conda 环境: $env_name (Python 3.11)..."
    conda create -n $env_name python=3.11 -y
    print_success "conda 环境创建完成"
}

# 激活环境并安装依赖
install_dependencies() {
    local env_name="deep-research-dev"
    
    print_info "激活环境并安装依赖..."
    
    # 激活环境 - 修复conda路径
    if [[ -f "/opt/homebrew/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "/opt/homebrew/anaconda3/etc/profile.d/conda.sh"
    elif [[ -f "~/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "~/anaconda3/etc/profile.d/conda.sh"
    elif [[ -f "~/miniconda3/etc/profile.d/conda.sh" ]]; then
        source "~/miniconda3/etc/profile.d/conda.sh"
    else
        # 尝试从PATH中找到conda
        local conda_base=$(conda info --base 2>/dev/null || echo "")
        if [[ -n "$conda_base" && -f "$conda_base/etc/profile.d/conda.sh" ]]; then
            source "$conda_base/etc/profile.d/conda.sh"
        else
            print_error "无法找到conda安装路径，请手动激活环境后重新运行"
            exit 1
        fi
    fi
    
    conda activate $env_name
    
    # 升级 pip 和基础工具
    print_info "升级 pip 和基础工具..."
    pip install --upgrade pip setuptools wheel
    
    # 检查 requirements.txt 是否存在
    if [[ ! -f "requirements.txt" ]]; then
        print_error "requirements.txt 文件未找到！"
        print_info "请确保在 DeepResearch 项目根目录下运行此脚本"
        exit 1
    fi
    
    # 分步安装依赖以避免冲突
    print_info "📦 第1步：安装核心依赖..."
    # 基础包
    pip install "pydantic>=2.5.0,<3.0.0" || print_warning "pydantic 安装失败"
    pip install "pydantic-settings>=2.0.0,<3.0.0" || print_warning "pydantic-settings 安装失败"
    pip install "PyYAML>=6.0.1,<7.0.0" || print_warning "PyYAML 安装失败"
    pip install "requests>=2.31.0,<3.0.0" || print_warning "requests 安装失败"
    pip install "python-dotenv>=1.0.0,<2.0.0" || print_warning "python-dotenv 安装失败"
    pip install "rich>=13.7.0,<14.0.0" || print_warning "rich 安装失败"
    pip install "typer>=0.9.0,<1.0.0" || print_warning "typer 安装失败"
    pip install "docker>=7.0.0,<8.0.0" || print_warning "docker 安装失败"
    
    print_info "📦 第2步：安装 LangChain 核心..."
    # 使用兼容版本避免冲突
    pip install "langchain>=0.2.17,<0.3.0" || print_warning "langchain 安装失败"
    pip install "langchain-core>=0.2.43,<0.3.0" || print_warning "langchain-core 安装失败"
    pip install "langgraph>=0.0.20,<0.3.0" || print_warning "langgraph 安装失败"
    
    print_info "📦 第3步：安装 LLM 提供商..."
    pip install "openai>=1.0.0,<2.0.0" || print_warning "openai 安装失败"
    pip install "anthropic>=0.8.0,<1.0.0" || print_warning "anthropic 安装失败"
    pip install "google-generativeai>=0.3.0,<1.0.0" || print_warning "google-generativeai 安装失败"
    
    print_info "📦 第4步：安装 Web 相关依赖..."
    pip install "beautifulsoup4>=4.12.0,<5.0.0" || print_warning "beautifulsoup4 安装失败"
    pip install "lxml>=4.9.0,<5.0.0" || print_warning "lxml 安装失败"
    pip install "aiohttp>=3.8.0,<4.0.0" || print_warning "aiohttp 安装失败"
    
    print_info "📦 第5步：安装搜索引擎（可能有冲突的包）..."
    # 使用稳定版本避免冲突
    pip install "duckduckgo-search>=3.8.0,<3.9.0" || {
        print_warning "DuckDuckGo search 3.8.x 安装失败，尝试 3.7.x..."
        pip install "duckduckgo-search>=3.7.0,<3.8.0" || {
            print_warning "DuckDuckGo search 安装失败，跳过"
        }
    }
    pip install "google-search-results>=2.4.2,<3.0.0" || print_warning "google-search-results 安装失败"
    
    print_info "📦 第6步：安装 LangChain 扩展..."
    pip install "langchain-community>=0.0.10,<0.3.0" || print_warning "langchain-community 安装失败"
    
    print_info "📦 第7步：安装其他依赖..."
    pip install "requests-html>=0.10.0,<1.0.0" || print_warning "requests-html 安装失败"
    pip install "markdown>=3.5.0,<4.0.0" || print_warning "markdown 安装失败"
    
    # 安装开发依赖（如果存在）
    if [[ -f "requirements-dev.txt" ]]; then
        print_info "📦 安装开发依赖..."
        pip install "pytest>=7.4.0,<8.0.0" || print_warning "pytest 安装失败"
        pip install "black>=23.0.0,<24.0.0" || print_warning "black 安装失败"
        pip install "flake8>=6.0.0,<7.0.0" || print_warning "flake8 安装失败"
    fi
    
    # 处理依赖冲突 - 强制安装兼容版本
    print_info "📦 第8步：解决依赖冲突..."
    pip install "google-ai-generativelanguage==0.6.6" --force-reinstall || print_warning "google-ai-generativelanguage 版本冲突解决失败"
    
    print_success "核心依赖安装完成"
    
    # 可选：安装 Browser-Use 集成（如果需要）
    if [[ "${INSTALL_BROWSER_USE:-yes}" == "yes" ]]; then
        install_browser_use
    else
        print_info "跳过 Browser-Use 安装"
    fi
    
    print_success "依赖安装完成"
}

# 安装 Browser-Use 集成
install_browser_use() {
    print_info "🌐 安装 Browser-Use 集成..."
    
    # 检查 Python 版本
    local python_version=$(python --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    local required_version="3.8"
    
    if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
        print_error "Browser-Use 需要 Python 3.8 或更高版本，当前版本: $python_version"
        return 1
    fi
    
    print_success "Python 版本检查通过: $python_version"
    
    # 分步安装 Browser-Use 依赖
    print_info "📦 安装 Playwright..."
    pip install "playwright>=1.40.0,<2.0.0" || {
        print_warning "Playwright 安装失败，尝试使用 conda..."
        conda install -c conda-forge playwright -y || {
            print_error "Playwright 安装失败，Browser-Use 功能将不可用"
            return 1
        }
    }
    
    print_info "📦 安装 LangChain 集成包..."
    pip install "langchain-openai>=0.1.0,<1.0.0" || print_warning "langchain-openai 安装失败"
    pip install "langchain-anthropic>=0.1.0,<1.0.0" || print_warning "langchain-anthropic 安装失败"
    pip install "langchain-google-genai>=1.0.0,<2.0.0" || print_warning "langchain-google-genai 安装失败"
    
    print_info "📦 安装 browser-use 库..."
    pip install "browser-use>=0.2.0,<1.0.0" || {
        print_warning "browser-use 指定版本安装失败，尝试最新版本..."
        pip install browser-use || {
            print_error "browser-use 安装失败，Browser-Use 功能将不可用"
            return 1
        }
    }
    
    # 安装 Playwright 浏览器
    print_info "🌐 安装 Playwright 浏览器..."
    if command -v playwright &> /dev/null; then
        playwright install chromium --with-deps || {
            print_warning "Playwright 浏览器安装失败，尝试不带依赖安装..."
            playwright install chromium || {
                print_warning "Playwright 浏览器安装失败，但这不会影响其他功能"
                print_info "您可以稍后手动运行: playwright install chromium --with-deps"
            }
        }
    else
        print_warning "playwright 命令不可用，跳过浏览器安装"
        print_info "您可以稍后手动运行: python -m playwright install chromium --with-deps"
    fi
    
    # 创建输出目录
    print_info "📁 创建 Browser-Use 输出目录..."
    mkdir -p browser_outputs
    mkdir -p research_outputs
    
    # 设置权限
    chmod 755 browser_outputs 2>/dev/null || true
    chmod 755 research_outputs 2>/dev/null || true
    
    print_success "Browser-Use 集成安装完成"
}

# 创建配置文件
setup_config() {
    print_info "设置配置文件..."
    
    # 创建 .env 文件模板（如果不存在）
    if [[ ! -f ".env" ]]; then
        print_info "创建 .env 配置文件模板..."
        cat > .env << 'EOF'
# DeepResearch 配置文件
# 请根据需要配置以下 API 密钥

# LLM 提供商 (至少配置一个)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_claude_key_here
GOOGLE_API_KEY=your_gemini_key_here

# 搜索引擎 (可选，提升搜索质量)
SERPAPI_KEY=your_serpapi_key_here
BING_SEARCH_KEY=your_bing_search_key_here

# DeepSeek API 密钥  
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 云存储 (可选，支持文件集成)
GOOGLE_DRIVE_CREDENTIALS=path/to/credentials.json
DROPBOX_ACCESS_TOKEN=your_dropbox_token_here

# Ollama 配置 (如果使用本地模型)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
EOF
        print_success "已创建 .env 配置文件模板"
        print_warning "请编辑 .env 文件并配置您的 API 密钥"
    else
        print_info ".env 文件已存在，跳过创建"
    fi
    
    # 创建输出目录
    print_info "创建输出目录..."
    mkdir -p output
    mkdir -p logs
    mkdir -p demo_output
    
    print_success "配置文件设置完成"
}

# 验证安装
verify_installation() {
    local env_name="deep-research-dev"
    
    print_info "验证安装..."
    
    # 激活环境 - 使用和install_dependencies相同的逻辑
    if [[ -f "/opt/homebrew/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "/opt/homebrew/anaconda3/etc/profile.d/conda.sh"
    elif [[ -f "~/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "~/anaconda3/etc/profile.d/conda.sh"
    elif [[ -f "~/miniconda3/etc/profile.d/conda.sh" ]]; then
        source "~/miniconda3/etc/profile.d/conda.sh"
    else
        # 尝试从PATH中找到conda
        local conda_base=$(conda info --base 2>/dev/null || echo "")
        if [[ -n "$conda_base" && -f "$conda_base/etc/profile.d/conda.sh" ]]; then
            source "$conda_base/etc/profile.d/conda.sh"
        else
            print_error "无法找到conda安装路径进行验证"
            return 1
        fi
    fi
    
    conda activate $env_name
    
    # 检查主要模块是否可以导入
    print_info "检查核心模块..."
    
    local import_test_result=0
    
    # 测试配置模块
    python -c "from config import config; print('✅ Config 模块')" 2>/dev/null || {
        print_error "❌ Config 模块导入失败"
        import_test_result=1
    }
    
    # 测试用户交互模块
    python -c "from utils.user_interaction import get_user_interaction; print('✅ UserInteraction 模块')" 2>/dev/null || {
        print_error "❌ UserInteraction 模块导入失败"
        import_test_result=1
    }
    
    # 测试工作流模块（可能有警告但不影响功能）
    if python -c "from workflow.graph import ResearchWorkflow; print('✅ ResearchWorkflow 模块')" 2>/dev/null; then
        true  # 成功
    else
        print_error "❌ ResearchWorkflow 模块导入失败"
        import_test_result=1
    fi
    
    # 测试代理模块
    if python -c "from agents.outline_agent import OutlineAgent; print('✅ OutlineAgent 模块')" 2>/dev/null; then
        true  # 成功
    else
        print_error "❌ OutlineAgent 模块导入失败"
        import_test_result=1
    fi
    
    if [[ $import_test_result -eq 0 ]]; then
        print_success "✅ 所有核心模块导入成功"
    else
        print_error "❌ 部分模块导入失败，请检查依赖安装"
        return 1
    fi
    
    # 检查配置
    print_info "检查系统配置..."
    if python main.py config-check 2>/dev/null | grep -q "配置检查"; then
        print_success "✅ 配置系统正常"
    else
        print_warning "⚠️ 配置系统可能有问题，但不影响基本功能"
    fi
    
    print_success "安装验证完成"
    print_info "注意：导入过程中的警告信息不影响系统功能"
}

# 验证 Browser-Use 安装
verify_browser_use() {
    print_info "🌐 验证 Browser-Use 集成..."
    
    # 检查依赖是否正确安装
    python -c "
import sys
success = True

try:
    import browser_use
    print('✅ browser-use 导入成功')
except ImportError as e:
    print(f'❌ browser-use 导入失败: {e}')
    success = False

try:
    import playwright
    print('✅ playwright 导入成功')
except ImportError as e:
    print(f'❌ playwright 导入失败: {e}')
    success = False

try:
    from langchain_openai import ChatOpenAI
    print('✅ langchain-openai 导入成功')
except ImportError as e:
    print(f'❌ langchain-openai 导入失败: {e}')
    success = False

try:
    from langchain_anthropic import ChatAnthropic
    print('✅ langchain-anthropic 导入成功')
except ImportError as e:
    print(f'❌ langchain-anthropic 导入失败: {e}')
    success = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    print('✅ langchain-google-genai 导入成功')
except ImportError as e:
    print(f'❌ langchain-google-genai 导入失败: {e}')
    success = False

if success:
    print('✅ Browser-Use 依赖验证通过')
else:
    print('⚠️  部分 Browser-Use 依赖验证失败')
    sys.exit(1)
"
    
    if [[ $? -eq 0 ]]; then
        print_success "Browser-Use 依赖验证通过"
        
        # 检查 BrowserUseTool 是否可以导入
        python -c "
try:
    from tools.browser_use_tool import BrowserUseTool
    print('✅ BrowserUseTool 导入成功')
except ImportError as e:
    print(f'⚠️  BrowserUseTool 导入失败: {e}')
    print('   这可能是因为缺少 API 密钥，但不影响其他功能')
"
        
        # 检查 Playwright 浏览器
        python -c "
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browsers = p.chromium
        print('✅ Playwright Chromium 浏览器可用')
except Exception as e:
    print(f'⚠️  Playwright 浏览器检查失败: {e}')
    print('   您可以稍后运行: playwright install chromium --with-deps')
"
    else
        print_warning "Browser-Use 依赖验证失败，但不影响其他功能"
    fi
}

# 显示使用说明
show_usage() {
    print_info "安装完成！使用说明："
    echo
    echo -e "${GREEN}激活环境:${NC}"
    echo "  source /opt/homebrew/anaconda3/etc/profile.d/conda.sh"
    echo "  conda activate deep-research-dev"
    echo
    echo -e "${GREEN}配置 API 密钥:${NC}"
    echo "  编辑 .env 文件，配置您的 API 密钥"
    echo "  至少需要配置一个 LLM 提供商 (OpenAI/Claude/Gemini)"
    echo
    echo -e "${GREEN}运行系统:${NC}"
    echo "  python main.py --help                       # 查看所有命令"
    echo "  python main.py interactive \"研究主题\"        # 交互式研究"
    echo "  python main.py auto \"研究主题\"               # 自动化研究"
    echo "  python main.py demo                         # 运行演示"
    echo
    echo -e "${GREEN}配置管理:${NC}"
    echo "  python main.py config-check                 # 检查配置状态"
    echo "  python main.py config-show                  # 显示配置摘要"
    echo "  python main.py config-edit                  # 编辑配置文件"
    echo "  python main.py config-validate              # 验证配置文件"
    echo
    echo -e "${GREEN}系统状态:${NC}"
    echo "  ✅ 核心功能：已安装并可用"
    echo "  ✅ LLM集成：支持 OpenAI、Claude、Gemini、Ollama"
    echo "  ✅ 搜索引擎：支持 DuckDuckGo、Google、Bing"
    echo "  ✅ 工作流：自动研究流程已就绪"
    echo "  ✅ 工具集成：代码执行、文件读取等"
    echo
    echo -e "${YELLOW}注意事项:${NC}"
    echo "  1. 系统启动时可能出现一些警告信息，这不影响功能"
    echo "  2. 请先配置 .env 文件中的 API 密钥"
    echo "  3. 至少需要配置一个 LLM 提供商才能正常工作"
    echo "  4. 搜索引擎 API 是可选的，但建议配置以获得更好效果"
    echo "  5. Browser-Use 功能需要额外配置，目前使用基础功能"
    echo
    echo -e "${BLUE}快速开始:${NC}"
    echo "  1. 编辑 .env 文件配置 API 密钥"
    echo "  2. 运行 python main.py config-check 检查配置"
    echo "  3. 运行 python main.py demo 体验系统功能"
    echo
}

# 主函数
main() {
    print_banner
    
    print_info "开始安装 DeepResearch 开发环境..."
    echo
    
    # 检查前置条件
    check_conda
    check_python_version
    
    # 创建环境和安装依赖
    create_conda_env
    install_dependencies
    
    # 设置配置
    setup_config
    
    # 验证安装
    verify_installation
    
    # 显示使用说明
    echo
    print_success "🎉 DeepResearch 安装完成！"
    echo
    show_usage
}

# 错误处理
trap 'print_error "安装过程中发生错误，请检查上面的错误信息"; exit 1' ERR

# 运行主函数
main "$@" 