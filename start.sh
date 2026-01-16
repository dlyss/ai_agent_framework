#!/bin/bash

# AI Agent 全栈项目启动脚本
# 功能：启动前后端服务并检查是否正常启动

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/ai_agent_framework"
FRONTEND_DIR="$SCRIPT_DIR/ai_agent_web"

# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=3000

# pip镜像源（国内加速）
PIP_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
PIP_TRUSTED_HOST="pypi.tuna.tsinghua.edu.cn"

# npm镜像源（国内加速）
NPM_REGISTRY="https://registry.npmmirror.com"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 等待服务启动
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    log_info "等待 $name 启动..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            log_success "$name 已启动"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    log_error "$name 启动超时"
    return 1
}

# 停止已有服务
stop_existing_services() {
    log_info "检查并停止已有服务..."
    
    if check_port $BACKEND_PORT; then
        log_warning "端口 $BACKEND_PORT 被占用，尝试停止..."
        kill $(lsof -t -i:$BACKEND_PORT) 2>/dev/null || true
        sleep 2
    fi

    if check_port $FRONTEND_PORT; then
        log_warning "端口 $FRONTEND_PORT 被占用，尝试停止..."
        kill $(lsof -t -i:$FRONTEND_PORT) 2>/dev/null || true
        sleep 2
    fi
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    
    cd "$BACKEND_DIR"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 检查依赖
    if [ ! -f "venv/.installed" ]; then
        log_info "安装Python依赖（使用清华镜像源）..."
        pip install -r requirements.txt -i "$PIP_INDEX_URL" --trusted-host "$PIP_TRUSTED_HOST" -q
        touch venv/.installed
    fi
    
    # 检查环境变量
    if [ ! -f ".env" ]; then
        log_warning ".env 文件不存在，复制示例文件..."
        cp .env.example .env
        log_warning "请编辑 .env 文件配置必要的环境变量"
    fi
    
    # 启动服务（后台运行）
    nohup uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > backend.log 2>&1 &
    echo $! > backend.pid
    
    log_info "后端服务 PID: $(cat backend.pid)"
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    
    cd "$FRONTEND_DIR"
    
    # 检查node_modules
    if [ ! -d "node_modules" ]; then
        log_info "安装npm依赖（使用淘宝镜像源）..."
        npm install --registry "$NPM_REGISTRY"
    fi
    
    # 检查环境变量
    if [ ! -f ".env.local" ]; then
        log_warning ".env.local 文件不存在，复制示例文件..."
        cp .env.example .env.local
    fi
    
    # 启动服务（后台运行）
    nohup npm run dev > frontend.log 2>&1 &
    echo $! > frontend.pid
    
    log_info "前端服务 PID: $(cat frontend.pid)"
}

# 检查服务状态
check_services() {
    echo ""
    log_info "========== 服务状态检查 =========="
    
    local all_ok=true
    
    # 检查后端
    if wait_for_service "http://localhost:$BACKEND_PORT/health" "后端服务"; then
        echo -e "  后端API: ${GREEN}http://localhost:$BACKEND_PORT${NC}"
        echo -e "  API文档: ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
    else
        all_ok=false
    fi
    
    # 检查前端
    if wait_for_service "http://localhost:$FRONTEND_PORT" "前端服务"; then
        echo -e "  前端页面: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
    else
        all_ok=false
    fi
    
    echo ""
    if [ "$all_ok" = true ]; then
        log_success "========== 所有服务启动成功 =========="
        echo ""
        echo -e "  ${YELLOW}默认账号: admin / 111111${NC}"
        echo ""
    else
        log_error "========== 部分服务启动失败 =========="
        echo "请检查日志文件:"
        echo "  后端日志: $BACKEND_DIR/backend.log"
        echo "  前端日志: $FRONTEND_DIR/frontend.log"
        return 1
    fi
}

# 停止所有服务
stop_services() {
    log_info "停止所有服务..."
    
    if [ -f "$BACKEND_DIR/backend.pid" ]; then
        kill $(cat "$BACKEND_DIR/backend.pid") 2>/dev/null || true
        rm "$BACKEND_DIR/backend.pid"
        log_success "后端服务已停止"
    fi
    
    if [ -f "$FRONTEND_DIR/frontend.pid" ]; then
        kill $(cat "$FRONTEND_DIR/frontend.pid") 2>/dev/null || true
        rm "$FRONTEND_DIR/frontend.pid"
        log_success "前端服务已停止"
    fi
    
    # 确保端口释放
    stop_existing_services
}

# 显示帮助
show_help() {
    echo "AI Agent 全栈项目启动脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动所有服务（默认）"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  status    检查服务状态"
    echo "  backend   仅启动后端"
    echo "  frontend  仅启动前端"
    echo "  help      显示帮助"
}

# 主函数
main() {
    local command=${1:-start}
    
    case $command in
        start)
            echo ""
            log_info "========== AI Agent 全栈项目启动 =========="
            echo ""
            stop_existing_services
            start_backend
            start_frontend
            check_services
            ;;
        stop)
            stop_services
            log_success "所有服务已停止"
            ;;
        restart)
            stop_services
            sleep 2
            main start
            ;;
        status)
            check_services
            ;;
        backend)
            stop_existing_services
            start_backend
            wait_for_service "http://localhost:$BACKEND_PORT/health" "后端服务"
            ;;
        frontend)
            start_frontend
            wait_for_service "http://localhost:$FRONTEND_PORT" "前端服务"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
