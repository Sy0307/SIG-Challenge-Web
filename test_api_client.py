#!/usr/bin/env python3
"""
SigMOS API客户端测试脚本
"""

import requests
import json
import sys
import os

def test_health_check(base_url):
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def test_service_info(base_url):
    """测试服务信息接口"""
    print("\n📋 测试服务信息接口...")
    try:
        response = requests.get(f"{base_url}/info")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 服务信息获取失败: {e}")
        return False

def test_file_upload(base_url, file_path):
    """测试文件上传评估接口"""
    print(f"\n🎵 测试文件上传评估: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{base_url}/evaluate", files=files)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        if result.get('success', False):
            print("✅ 评估成功!")
            print(f"文件信息: {json.dumps(result['file_info'], indent=2, ensure_ascii=False)}")
            print(f"MOS评分: {json.dumps(result['mos_scores'], indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 评估失败: {result.get('error', '未知错误')}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ 文件上传失败: {e}")
        return False

def test_file_path(base_url, file_path):
    """测试文件路径评估接口"""
    print(f"\n📁 测试文件路径评估: {file_path}")
    
    try:
        data = {"file_path": file_path}
        response = requests.post(f"{base_url}/evaluate_path", json=data)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        if result.get('success', False):
            print("✅ 评估成功!")
            print(f"文件信息: {json.dumps(result['file_info'], indent=2, ensure_ascii=False)}")
            print(f"MOS评分: {json.dumps(result['mos_scores'], indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 评估失败: {result.get('error', '未知错误')}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ 路径评估失败: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 test_api_client.py <服务器地址> [音频文件路径]")
        print("  例如: python3 test_api_client.py http://localhost:5000 audio.wav")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    audio_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"🚀 测试SigMOS API服务: {base_url}")
    print("=" * 60)
    
    # 测试健康检查
    if not test_health_check(base_url):
        print("❌ 服务不可用，退出测试")
        sys.exit(1)
    
    # 测试服务信息
    test_service_info(base_url)
    
    # 如果提供了音频文件，进行测试
    if audio_file:
        # 测试文件上传
        test_file_upload(base_url, audio_file)
        
        # 测试文件路径（需要服务器能访问到该路径）
        abs_path = os.path.abspath(audio_file)
        test_file_path(base_url, abs_path)
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main()