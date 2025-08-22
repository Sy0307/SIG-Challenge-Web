#!/bin/bash

# SigMOS API服务启动脚本

echo "🚀 启动SigMOS音频质量评估API服务..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python3"
    exit 1
fi

# 检查依赖包
echo "📦 检查依赖包..."
python3 -c "import flask, soundfile, numpy, scipy, librosa, onnxruntime" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 缺少依赖包，正在安装..."
    pip3 install flask soundfile numpy scipy librosa onnxruntime
fi

# 检查模型文件
MODEL_FILE="ICASSP2024/sigmos/model-sigmos_1697718653_41d092e8-epo-200.onnx"
if [ ! -f "$MODEL_FILE" ]; then
    echo "❌ 模型文件不存在: $MODEL_FILE"
    echo "请确保SigMOS模型文件在正确位置"
    exit 1
fi

# 创建上传目录
mkdir -p uploads

# 启动服务
echo "🌐 启动API服务..."
python3 sigmos_api.py