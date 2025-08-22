#!/usr/bin/env python3
"""
SigMOS音频质量评估API服务
提供HTTP接口进行音频文件质量评估
"""

import os
import sys
import tempfile
import uuid
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import soundfile as sf
import numpy as np
from datetime import datetime
import traceback

# 添加sigmos模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'ICASSP2024', 'sigmos'))

from sigmos import SigMOS, Version

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['JSON_AS_ASCII'] = False  # 确保中文不被转义

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 全局变量存储模型实例
sigmos_estimator = None
model_dir = None

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_sigmos_model():
    """初始化SigMOS模型"""
    global sigmos_estimator, model_dir
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, "ICASSP2024", "sigmos")
        
        # 检查模型文件是否存在
        model_file = os.path.join(model_dir, "model-sigmos_1697718653_41d092e8-epo-200.onnx")
        if not os.path.exists(model_file):
            raise FileNotFoundError(f"模型文件不存在: {model_file}")
        
        sigmos_estimator = SigMOS(model_dir=model_dir, model_version=Version.V1)
        print(f"✅ SigMOS模型初始化成功: {model_file}")
        return True
        
    except Exception as e:
        print(f"❌ SigMOS模型初始化失败: {e}")
        return False

def evaluate_audio_file(audio_file_path):
    """评估音频文件并返回结果"""
    global sigmos_estimator
    
    try:
        # 检查文件是否存在
        if not os.path.exists(audio_file_path):
            return {"error": f"音频文件不存在: {audio_file_path}"}
        
        # 读取音频文件
        audio_data, sample_rate = sf.read(audio_file_path)
        
        # 获取文件信息
        file_info = {
            "filename": os.path.basename(audio_file_path),
            "file_size_samples": len(audio_data),
            "sample_rate": int(sample_rate),
            "duration_seconds": round(len(audio_data) / sample_rate, 2)
        }
        
        # 如果是立体声，取单声道
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]
            file_info["converted_to_mono"] = True
        else:
            file_info["converted_to_mono"] = False
        
        # 使用SigMOS进行评估
        result = sigmos_estimator.run(audio_data, sr=sample_rate)
        
        # 构建返回结果 - 使用OrderedDict保持顺序
        from collections import OrderedDict
        
        # 按照期望的顺序构建MOS评分
        mos_scores = OrderedDict([
            ("整体质量_MOS_OVRL", round(result['MOS_OVRL'], 3)),
            ("信号质量_MOS_SIG", round(result['MOS_SIG'], 3)),
            ("噪声程度_MOS_NOISE", round(result['MOS_NOISE'], 3)),
            ("响度_MOS_LOUD", round(result['MOS_LOUD'], 3)),
            ("着色度_MOS_COL", round(result['MOS_COL'], 3)),
            ("不连续性_MOS_DISC", round(result['MOS_DISC'], 3)),
            ("混响_MOS_REVERB", round(result['MOS_REVERB'], 3))
        ])
        
        raw_scores = OrderedDict([
            ("MOS_OVRL", float(result['MOS_OVRL'])),
            ("MOS_SIG", float(result['MOS_SIG'])),
            ("MOS_NOISE", float(result['MOS_NOISE'])),
            ("MOS_LOUD", float(result['MOS_LOUD'])),
            ("MOS_COL", float(result['MOS_COL'])),
            ("MOS_DISC", float(result['MOS_DISC'])),
            ("MOS_REVERB", float(result['MOS_REVERB']))
        ])
        
        evaluation_result = OrderedDict([
            ("success", True),
            ("timestamp", datetime.now().isoformat()),
            ("file_info", file_info),
            ("mos_scores", mos_scores),
            ("raw_scores", raw_scores)
        ])
        
        return evaluation_result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.route('/', methods=['GET'])
def index():
    """API首页"""
    return jsonify({
        "service": "SigMOS音频质量评估API",
        "version": "1.0",
        "endpoints": {
            "POST /evaluate": "上传音频文件进行评估",
            "POST /evaluate_url": "通过URL评估音频文件",
            "GET /health": "健康检查",
            "GET /info": "服务信息"
        },
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_CONTENT_LENGTH // (1024 * 1024)
    })

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    global sigmos_estimator
    
    if sigmos_estimator is None:
        return jsonify({
            "status": "unhealthy",
            "message": "SigMOS模型未初始化"
        }), 503
    
    return jsonify({
        "status": "healthy",
        "message": "服务运行正常",
        "model_loaded": True
    })

@app.route('/info', methods=['GET'])
def service_info():
    """服务信息接口"""
    global model_dir
    
    return jsonify({
        "service": "SigMOS音频质量评估API",
        "model_version": "V1 (15.10.2023)",
        "model_directory": model_dir,
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_CONTENT_LENGTH // (1024 * 1024),
        "mos_dimensions": [
            "整体质量 (MOS_OVRL)",
            "信号质量 (MOS_SIG)", 
            "噪声程度 (MOS_NOISE)",
            "响度 (MOS_LOUD)",
            "着色度 (MOS_COL)",
            "不连续性 (MOS_DISC)",
            "混响 (MOS_REVERB)"
        ]
    })

@app.route('/evaluate', methods=['POST'])
def evaluate_uploaded_file():
    """评估上传的音频文件"""
    
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({
            "success": False,
            "error": "没有上传文件"
        }), 400
    
    file = request.files['file']
    
    # 检查文件名
    if file.filename == '':
        return jsonify({
            "success": False,
            "error": "没有选择文件"
        }), 400
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": f"不支持的文件格式，支持的格式: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400
    
    try:
        # 保存上传的文件
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # 评估音频文件
        result = evaluate_audio_file(file_path)
        
        # 删除临时文件
        try:
            os.remove(file_path)
        except:
            pass
        
        if result.get("success", False):
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"处理文件时出错: {str(e)}"
        }), 500

@app.route('/evaluate_path', methods=['POST'])
def evaluate_file_path():
    """评估指定路径的音频文件"""
    
    data = request.get_json()
    if not data or 'file_path' not in data:
        return jsonify({
            "success": False,
            "error": "请提供file_path参数"
        }), 400
    
    file_path = data['file_path']
    
    # 安全检查：确保文件路径在允许的范围内
    if not os.path.exists(file_path):
        return jsonify({
            "success": False,
            "error": f"文件不存在: {file_path}"
        }), 404
    
    # 评估音频文件
    result = evaluate_audio_file(file_path)
    
    if result.get("success", False):
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.errorhandler(413)
def too_large(e):
    """文件太大错误处理"""
    return jsonify({
        "success": False,
        "error": f"文件太大，最大允许 {MAX_CONTENT_LENGTH // (1024 * 1024)} MB"
    }), 413

@app.errorhandler(500)
def internal_error(e):
    """内部服务器错误处理"""
    return jsonify({
        "success": False,
        "error": "内部服务器错误"
    }), 500

if __name__ == '__main__':
    print("🚀 启动SigMOS音频质量评估API服务...")
    
    # 初始化模型
    if not init_sigmos_model():
        print("❌ 模型初始化失败，服务无法启动")
        sys.exit(1)
    
    print("📡 服务启动配置:")
    print(f"   - 端口: 5000")
    print(f"   - 支持格式: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"   - 最大文件大小: {MAX_CONTENT_LENGTH // (1024 * 1024)} MB")
    print(f"   - 上传目录: {UPLOAD_FOLDER}")
    print()
    print("🌐 API接口:")
    print("   - GET  /          - 服务首页")
    print("   - GET  /health    - 健康检查")
    print("   - GET  /info      - 服务信息")
    print("   - POST /evaluate  - 上传文件评估")
    print("   - POST /evaluate_path - 路径文件评估")
    print()
    
    # 启动Flask应用
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=5000,
        debug=False,
        threaded=True
    )