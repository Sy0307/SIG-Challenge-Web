#!/usr/bin/env python3
"""
使用SigMOS评估器测试单个音频文件质量
"""

import os
import sys
import argparse
import soundfile as sf
import numpy as np

# 添加sigmos模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'ICASSP2024', 'sigmos'))

from sigmos import SigMOS, Version

def test_audio_file(audio_file_path, model_dir):
    """
    测试单个音频文件并输出MOS评分
    
    Args:
        audio_file_path: 音频文件路径
        model_dir: SigMOS模型文件目录
    """
    
    print("正在初始化SigMOS评估器...")
    try:
        sigmos_estimator = SigMOS(model_dir=model_dir, model_version=Version.V1)
        print("SigMOS评估器初始化成功！")
    except Exception as e:
        print(f"初始化SigMOS评估器失败: {e}")
        return None
    
    # 检查文件是否存在
    if not os.path.exists(audio_file_path):
        print(f"错误: 音频文件不存在: {audio_file_path}")
        return None
    
    # 检查文件扩展名
    if not audio_file_path.lower().endswith(('.wav', '.mp3', '.flac', '.m4a')):
        print(f"警告: 文件可能不是音频文件: {audio_file_path}")
    
    filename = os.path.basename(audio_file_path)
    print(f"\n正在处理: {filename}")
    print("-" * 80)
    
    try:
        # 读取音频文件
        audio_data, sample_rate = sf.read(audio_file_path)
        print(f"  - 文件大小: {len(audio_data)} 采样点")
        print(f"  - 采样率: {sample_rate} Hz")
        print(f"  - 时长: {len(audio_data)/sample_rate:.2f} 秒")
        
        # 如果是立体声，取单声道
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]
            print("  - 转换为单声道")
        
        # 使用SigMOS进行评估
        print("  - 正在进行MOS评估...")
        result = sigmos_estimator.run(audio_data, sr=sample_rate)
        
        # 输出结果
        print("  - MOS评分结果:")
        print(f"    * 整体质量 (MOS_OVRL):  {result['MOS_OVRL']:.3f}")
        print(f"    * 信号质量 (MOS_SIG):   {result['MOS_SIG']:.3f}")
        print(f"    * 噪声程度 (MOS_NOISE): {result['MOS_NOISE']:.3f}")
        print(f"    * 响度 (MOS_LOUD):      {result['MOS_LOUD']:.3f}")
        print(f"    * 着色度 (MOS_COL):     {result['MOS_COL']:.3f}")
        print(f"    * 不连续性 (MOS_DISC):  {result['MOS_DISC']:.3f}")
        print(f"    * 混响 (MOS_REVERB):    {result['MOS_REVERB']:.3f}")
        
        return result
        
    except Exception as e:
        print(f"  - 处理文件时出错: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="使用SigMOS评估器测试单个音频文件质量",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 测试单个文件
  python3 test_single_file.py audio.wav
  
  # 指定自定义模型目录
  python3 test_single_file.py audio.wav -m /path/to/sigmos/model
        """
    )
    
    parser.add_argument('file', type=str, 
                       help='要测试的音频文件路径')
    parser.add_argument('-m', '--model-dir', type=str,
                       help='SigMOS模型文件目录路径 (默认: ICASSP2024/sigmos)')
    
    args = parser.parse_args()
    
    # 设置模型目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if args.model_dir:
        model_dir = os.path.abspath(args.model_dir)
    else:
        model_dir = os.path.join(current_dir, "ICASSP2024", "sigmos")
    
    print("=== SigMOS 音频质量评估 ===")
    print(f"模型目录: {model_dir}")
    
    # 检查模型目录是否存在
    if not os.path.exists(model_dir):
        print(f"错误: 模型目录不存在: {model_dir}")
        return
    
    # 检查模型文件是否存在
    model_file = os.path.join(model_dir, "model-sigmos_1697718653_41d092e8-epo-200.onnx")
    if not os.path.exists(model_file):
        print(f"错误: 模型文件不存在: {model_file}")
        return
    
    print(f"模型文件: {model_file}")
    
    # 测试音频文件
    audio_file_path = os.path.abspath(args.file)
    print(f"音频文件: {audio_file_path}")
    
    result = test_audio_file(audio_file_path, model_dir)
    
    if result:
        print("\n=== 测试完成 ===")
    else:
        print("\n=== 测试失败 ===")

if __name__ == "__main__":
    main()