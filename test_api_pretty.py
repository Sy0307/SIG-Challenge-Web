#!/usr/bin/env python3
"""
SigMOS API美化测试脚本 - 解决中文显示和排序问题
"""

import requests
import json
import sys
import os
from collections import OrderedDict

def pretty_print_json(data, indent=2):
    """美化打印JSON，确保中文正确显示和顺序保持"""
    return json.dumps(data, indent=indent, ensure_ascii=False, separators=(',', ': '))

def test_health_check(base_url):
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {pretty_print_json(response.json())}")
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
        print(f"响应: {pretty_print_json(response.json())}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 服务信息获取失败: {e}")
        return False

def print_mos_scores(mos_scores):
    """按照指定顺序打印MOS评分"""
    print("  MOS评分结果:")
    score_order = [
        ("整体质量_MOS_OVRL", "整体质量 (MOS_OVRL)"),
        ("信号质量_MOS_SIG", "信号质量 (MOS_SIG)"),
        ("噪声程度_MOS_NOISE", "噪声程度 (MOS_NOISE)"),
        ("响度_MOS_LOUD", "响度 (MOS_LOUD)"),
        ("着色度_MOS_COL", "着色度 (MOS_COL)"),
        ("不连续性_MOS_DISC", "不连续性 (MOS_DISC)"),
        ("混响_MOS_REVERB", "混响 (MOS_REVERB)")
    ]
    
    for key, display_name in score_order:
        if key in mos_scores:
            print(f"    * {display_name:20}: {mos_scores[key]:.3f}")

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
            print(f"  文件信息:")
            file_info = result['file_info']
            print(f"    - 文件名: {file_info['filename']}")
            print(f"    - 文件大小: {file_info['file_size_samples']} 采样点")
            print(f"    - 采样率: {file_info['sample_rate']} Hz")
            print(f"    - 时长: {file_info['duration_seconds']} 秒")
            if file_info.get('converted_to_mono', False):
                print(f"    - 转换为单声道: 是")
            
            print_mos_scores(result['mos_scores'])
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
            print(f"  文件信息:")
            file_info = result['file_info']
            print(f"    - 文件名: {file_info['filename']}")
            print(f"    - 文件大小: {file_info['file_size_samples']} 采样点")
            print(f"    - 采样率: {file_info['sample_rate']} Hz")
            print(f"    - 时长: {file_info['duration_seconds']} 秒")
            
            print_mos_scores(result['mos_scores'])
        else:
            print(f"❌ 评估失败: {result.get('error', '未知错误')}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ 路径评估失败: {e}")
        return False

def batch_test_files(base_url, directory):
    """批量测试目录下的音频文件"""
    print(f"\n🎶 批量测试目录: {directory}")
    
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        return
    
    # 获取所有音频文件
    audio_extensions = ['.wav', '.mp3', '.flac', '.m4a']
    audio_files = []
    
    for file in os.listdir(directory):
        if any(file.lower().endswith(ext) for ext in audio_extensions):
            audio_files.append(os.path.join(directory, file))
    
    if not audio_files:
        print(f"❌ 目录中没有找到音频文件")
        return
    
    audio_files.sort()  # 排序文件列表
    
    print(f"找到 {len(audio_files)} 个音频文件")
    print("=" * 80)
    
    results = []
    for i, file_path in enumerate(audio_files, 1):
        filename = os.path.basename(file_path)
        print(f"\n[{i}/{len(audio_files)}] 测试文件: {filename}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{base_url}/evaluate", files=files)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    mos_scores = result['mos_scores']
                    overall_score = mos_scores.get('整体质量_MOS_OVRL', 0)
                    results.append((filename, overall_score, mos_scores))
                    print(f"  ✅ 整体质量: {overall_score:.3f}")
                else:
                    print(f"  ❌ 评估失败: {result.get('error', '未知错误')}")
            else:
                print(f"  ❌ 请求失败，状态码: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
        
        print("-" * 40)
    
    # 显示汇总结果
    if results:
        print(f"\n📊 批量测试汇总 (按整体质量排序):")
        print("=" * 80)
        results.sort(key=lambda x: x[1], reverse=True)  # 按整体质量降序排序
        
        for i, (filename, overall_score, mos_scores) in enumerate(results, 1):
            print(f"{i:2d}. {filename:<30} 整体质量: {overall_score:.3f}")

def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 test_api_pretty.py <服务器地址> [音频文件路径或目录]")
        print("  例如:")
        print("    python3 test_api_pretty.py http://localhost:5000 audio.wav")
        print("    python3 test_api_pretty.py http://localhost:5000 MOQ_test_example/")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    target_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"🚀 测试SigMOS API服务: {base_url}")
    print("=" * 60)
    
    # 测试健康检查
    if not test_health_check(base_url):
        print("❌ 服务不可用，退出测试")
        sys.exit(1)
    
    # 测试服务信息
    test_service_info(base_url)
    
    # 如果提供了路径，进行测试
    if target_path:
        if os.path.isfile(target_path):
            # 单个文件测试
            test_file_upload(base_url, target_path)
            abs_path = os.path.abspath(target_path)
            test_file_path(base_url, abs_path)
        elif os.path.isdir(target_path):
            # 目录批量测试
            batch_test_files(base_url, target_path)
        else:
            print(f"❌ 路径不存在: {target_path}")
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main()