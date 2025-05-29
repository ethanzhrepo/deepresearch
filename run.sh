#!/bin/bash

# DeepResearch 启动脚本
# 自动激活conda环境并运行程序

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

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
            printf "${RED}错误: 无法找到conda安装路径${NC}\n"
            echo "请手动激活环境: conda activate deep-research-dev"
            exit 1
        fi
    fi
    
    # 激活环境
    conda activate deep-research-dev || {
        printf "${RED}错误: 无法激活 deep-research-dev 环境${NC}\n"
        echo "请先运行安装脚本: ./setup.sh"
        exit 1
    }
}

# 主函数
main() {
    printf "${GREEN}🔬 启动 DeepResearch 系统...${NC}\n"
    
    # 激活conda环境
    activate_conda
    
    # 如果没有参数，显示帮助
    if [[ $# -eq 0 ]]; then
        printf "${YELLOW}运行帮助命令...${NC}\n"
        python main.py --help
    else
        # 传递所有参数给main.py
        python main.py "$@"
    fi
}

# 运行主函数
main "$@" 