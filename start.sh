#!/bin/bash
set -e

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$PROJECT_ROOT"

FRONTEND_PORT=${FRONTEND_PORT:-8080}
BACKEND_PORT=${BACKEND_PORT:-8000}

show_help() {
    echo "=== LexPrime 一键启动脚本 ==="
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help, -h          显示帮助信息"
    echo "  --dev               开发模式启动 (前端+后端, 后端带热重载)"
    echo "  --prod              生产模式启动 (前端+后端)"
    echo "  --frontend          只启动前端"
    echo "  --backend           只启动后端"
    echo "  --docker            使用 docker-compose 启动全部服务"
    echo "  --docker-only-db    只启动数据库服务 (PostgreSQL, Elasticsearch, Neo4j)"
    echo ""
    echo "环境变量:"
    echo "  FRONTEND_PORT       前端端口 (默认: 8080)"
    echo "  BACKEND_PORT        后端端口 (默认: 8000)"
    echo "  APP_ENV             环境模式 (development/production)"
    echo ""
    echo "示例:"
    echo "  $0 --dev            # 开发模式"
    echo "  $0 --prod           # 生产模式"
    echo "  $0 --docker         # Docker 模式"
}

start_frontend() {
    echo "=== 启动前端 (端口: $FRONTEND_PORT) ==="
    cd "$PROJECT_ROOT"
    PORT=$FRONTEND_PORT bash scripts/start-frontend.sh &
    FRONTEND_PID=$!
    echo "前端已启动 (PID: $FRONTEND_PID)"
}

start_backend_dev() {
    echo "=== 启动后端开发模式 (端口: $BACKEND_PORT) ==="
    cd "$PROJECT_ROOT/backend/cases-crawler"
    API_PORT=$BACKEND_PORT bash start-dev.sh &
    BACKEND_PID=$!
    echo "后端已启动 (PID: $BACKEND_PID)"
}

start_backend_prod() {
    echo "=== 启动后端生产模式 (端口: $BACKEND_PORT) ==="
    cd "$PROJECT_ROOT/backend/cases-crawler"
    API_PORT=$BACKEND_PORT APP_ENV=production bash start.sh &
    BACKEND_PID=$!
    echo "后端已启动 (PID: $BACKEND_PID)"
}

start_docker() {
    echo "=== 使用 docker-compose 启动服务 ==="
    cd "$PROJECT_ROOT/backend/cases-crawler"
    docker-compose up -d
    echo "Docker 服务已启动"
    echo "API: http://localhost:$BACKEND_PORT"
    echo "PostgreSQL: localhost:5432"
    echo "Elasticsearch: http://localhost:9200"
    echo "Neo4j: http://localhost:7474"
}

start_docker_db_only() {
    echo "=== 只启动数据库服务 ==="
    cd "$PROJECT_ROOT/backend/cases-crawler"
    docker-compose up -d postgres elasticsearch neo4j
    echo "数据库服务已启动"
    echo "PostgreSQL: localhost:5432"
    echo "Elasticsearch: http://localhost:9200"
    echo "Neo4j: http://localhost:7474"
}

cleanup() {
    echo ""
    echo "=== 正在停止服务 ==="
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
        echo "前端已停止"
    fi
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
        echo "后端已停止"
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    --help|-h)
        show_help
        exit 0
        ;;
    --dev)
        export APP_ENV=development
        start_frontend
        start_backend_dev
        echo ""
        echo "=== 开发模式启动完成 ==="
        echo "前端: http://localhost:$FRONTEND_PORT"
        echo "后端: http://localhost:$BACKEND_PORT"
        echo "按 Ctrl+C 停止服务"
        wait
        ;;
    --prod)
        export APP_ENV=production
        start_frontend
        start_backend_prod
        echo ""
        echo "=== 生产模式启动完成 ==="
        echo "前端: http://localhost:$FRONTEND_PORT"
        echo "后端: http://localhost:$BACKEND_PORT"
        echo "按 Ctrl+C 停止服务"
        wait
        ;;
    --frontend)
        start_frontend
        echo ""
        echo "=== 前端启动完成 ==="
        echo "前端: http://localhost:$FRONTEND_PORT"
        echo "按 Ctrl+C 停止服务"
        wait
        ;;
    --backend)
        if [ "$APP_ENV" = "production" ]; then
            start_backend_prod
        else
            start_backend_dev
        fi
        echo ""
        echo "=== 后端启动完成 ==="
        echo "后端: http://localhost:$BACKEND_PORT"
        echo "按 Ctrl+C 停止服务"
        wait
        ;;
    --docker)
        start_docker
        ;;
    --docker-only-db)
        start_docker_db_only
        ;;
    *)
        echo "错误: 未知选项 $1"
        show_help
        exit 1
        ;;
esac