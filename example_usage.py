# -*- coding: utf-8 -*-
"""
屏幕录制工具使用示例
快速演示如何使用ScreenRecorder类
"""

from screen_recorder import ScreenRecorder

def quick_demo():
    """
    快速演示功能
    """
    # 创建录制器实例
    recorder = ScreenRecorder(output_dir="recordings")
    
    print("=== 快速演示 ===")
    print("即将开始录制5分钟屏幕视频...")
    input("按回车键开始录制: ")
    
    # 录制5分钟视频
    video_path = recorder.record_screen(duration_minutes=5, fps=15)  # 降低帧率以减少文件大小
    
    # 提取第3分钟的截图
    print("\n正在提取第3分钟的截图...")
    screenshot_path = recorder.extract_frame_at_minute(video_path, minute=3)
    
    print(f"\n完成！")
    print(f"视频文件: {video_path}")
    print(f"截图文件: {screenshot_path}")

def extract_from_existing():
    """
    从现有视频提取截图
    """
    recorder = ScreenRecorder()
    
    # 获取最新录制的视频
    latest_video = recorder.get_latest_recording()
    
    if latest_video:
        print(f"找到最新录制: {latest_video}")
        
        # 提取多个时间点的截图
        for minute in [1, 2, 3, 4, 5]:
            try:
                screenshot_path = recorder.extract_frame_at_minute(latest_video, minute)
                print(f"第{minute}分钟截图: {screenshot_path}")
            except Exception as e:
                print(f"提取第{minute}分钟截图失败: {e}")
    else:
        print("没有找到录制文件")

if __name__ == "__main__":
    print("选择功能:")
    print("1. 快速演示（录制+截图）")
    print("2. 从现有视频提取所有分钟截图")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        quick_demo()
    elif choice == "2":
        extract_from_existing()
    else:
        print("无效选择")