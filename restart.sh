#!/bin/bash


export LANG=zh_TW.UTF-8

# 配置
BACKEND_PORT=8100
FRONTEND_PORT=3000
BACKEND_DIR="/data1/ASR/backend"
FRONTEND_DIR="/data1/ASR/frontend"

echo "🚀 啟動奇美食品分析系統"
echo "========================"

# 檢查並釋放端口函數
check_and_kill_port() {
    local port=$1
    local name=$2
    
    echo -n "檢查 $name 端口 $port ... "
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "占用中，正在釋放"
        lsof -Pi :$port -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
        sleep 1
    else
        echo "可用"
    fi
}

# 檢查端口
check_and_kill_port $BACKEND_PORT "後端"
check_and_kill_port $FRONTEND_PORT "前端"

echo ""

# 啟動後端
echo "🔧 啟動後端服務..."
cd "$BACKEND_DIR"
if [ -f "asr/bin/activate" ]; then
    source asr/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

nohup python run_server.py > backend.log 2>&1 &
echo "後端啟動中... (PID: $!)"

# 等待後端啟動
echo -n "等待後端就緒"
for i in {1..15}; do
    if curl -s http://localhost:$BACKEND_PORT/health >/dev/null 2>&1; then
        echo " ✅"
        break
    fi
    echo -n "."
    sleep 1
done

# 啟動前端
echo "🎨 啟動前端服務..."
cd "$FRONTEND_DIR"
nohup npm run dev > frontend.log 2>&1 &
echo "前端啟動中... (PID: $!)"

# 等待前端啟動
echo -n "等待前端就緒"
for i in {1..20}; do
    if curl -s http://192.168.50.123:$FRONTEND_PORT >/dev/null 2>&1; then
        echo " ✅"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "🎉 啟動完成！"
echo "========================"
echo "前端: http://192.168.50.123:$FRONTEND_PORT"
echo "後端: http://localhost:$BACKEND_PORT"
echo "API文檔: http://localhost:$BACKEND_PORT/docs"
echo ""
echo "登入帳號: admin@chimei.com"
echo "登入密碼: admin123"
echo ""
echo "查看日誌:"
echo "  後端: tail -f $BACKEND_DIR/backend.log"
echo "  前端: tail -f $FRONTEND_DIR/frontend.log"