# -*- coding: utf-8 -*-
"""
屏幕录制和截图提取工具
使用pyautogui和opencv-python实现屏幕录制功能
支持录制5分钟视频并提取指定分钟的截图
"""

import cv2
import pyautogui
import numpy as np
import time
import os
from datetime import datetime
from PIL import Image

class ScreenRecorder:
    def __init__(self, output_dir="recordings"):
        """
        初始化屏幕录制器
        
        Args:
            output_dir (str): 输出目录
        """
        self.output_dir = output_dir
        self.screen_size = pyautogui.size()
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def record_screen(self, duration_minutes=5, fps=20):
        """
        录制屏幕视频
        
        Args:
            duration_minutes (int): 录制时长（分钟）
            fps (int): 帧率
            
        Returns:
            str: 视频文件路径
        """
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"screen_recording_{timestamp}.avi"
        video_path = os.path.join(self.output_dir, video_filename)
        
        # 创建视频写入器
        out = cv2.VideoWriter(video_path, self.fourcc, fps, self.screen_size)
        
        print(f"开始录制屏幕，时长: {duration_minutes}分钟")
        print(f"屏幕分辨率: {self.screen_size}")
        print(f"输出文件: {video_path}")
        print("按 Ctrl+C 可提前停止录制")
        
        start_time = time.time()
        duration_seconds = duration_minutes * 60
        frame_count = 0
        
        try:
            while True:
                # 检查是否超时
                elapsed_time = time.time() - start_time
                if elapsed_time >= duration_seconds:
                    break
                
                # 截取屏幕
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # 写入视频
                out.write(frame)
                frame_count += 1
                
                # 显示进度
                if frame_count % (fps * 10) == 0:  # 每10秒显示一次进度
                    progress = (elapsed_time / duration_seconds) * 100
                    print(f"录制进度: {progress:.1f}% ({elapsed_time:.0f}s/{duration_seconds}s)")
                
                # 控制帧率
                time.sleep(1/fps)
                
        except KeyboardInterrupt:
            print("\n用户中断录制")
        
        finally:
            out.release()
            cv2.destroyAllWindows()
            
        print(f"录制完成！视频已保存到: {video_path}")
        print(f"总帧数: {frame_count}")
        return video_path
    
    def extract_frame_at_minute(self, video_path, minute, output_filename=None):
        """
        从视频中提取指定分钟的截图
        
        Args:
            video_path (str): 视频文件路径
            minute (int): 要提取的分钟数（1-5）
            output_filename (str): 输出图片文件名（可选）
            
        Returns:
            str: 截图文件路径
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_seconds = total_frames / fps
        
        print(f"视频信息: FPS={fps:.2f}, 总帧数={total_frames}, 时长={duration_seconds:.2f}秒")
        
        # 计算目标帧位置（指定分钟的中间时刻）
        target_second = (minute - 1) * 60 + 30  # 每分钟的第30秒
        target_frame = int(target_second * fps)
        
        if target_frame >= total_frames:
            raise ValueError(f"指定的分钟数超出视频长度。视频总长度: {duration_seconds/60:.2f}分钟")
        
        # 跳转到目标帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
        # 读取帧
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise ValueError(f"无法读取第{minute}分钟的帧")
        
        # 生成输出文件名
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"screenshot_minute_{minute}_{timestamp}.png"
        
        screenshot_path = os.path.join(self.output_dir, output_filename)
        
        # 保存截图
        cv2.imwrite(screenshot_path, frame)
        
        print(f"截图已保存到: {screenshot_path}")
        print(f"截图位置: 第{minute}分钟第30秒 (帧号: {target_frame})")
        
        return screenshot_path
    
    def get_latest_recording(self):
        """
        获取最新的录制文件
        
        Returns:
            str: 最新录制文件路径，如果没有则返回None
        """
        if not os.path.exists(self.output_dir):
            return None
        
        video_files = [f for f in os.listdir(self.output_dir) if f.endswith('.avi')]
        if not video_files:
            return None
        
        # 按修改时间排序，返回最新的
        video_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.output_dir, x)), reverse=True)
        return os.path.join(self.output_dir, video_files[0])

def main():
    """
    主函数 - 演示用法
    """
    recorder = ScreenRecorder()
    
    print("=== 屏幕录制和截图工具 ===")
    print("1. 录制5分钟屏幕视频")
    print("2. 从视频提取指定分钟的截图")
    print("3. 录制并提取截图（完整流程）")
    
    choice = input("请选择功能 (1/2/3): ").strip()
    
    if choice == "1":
        # 录制视频
        video_path = recorder.record_screen(duration_minutes=5)
        print(f"\n录制完成: {video_path}")
        
    elif choice == "2":
        # 从现有视频提取截图
        latest_video = recorder.get_latest_recording()
        if latest_video:
            print(f"找到最新录制: {latest_video}")
            video_path = latest_video
        else:
            video_path = input("请输入视频文件路径: ").strip()
        
        try:
            minute = int(input("请输入要提取的分钟数 (1-5): "))
            if 1 <= minute <= 5:
                screenshot_path = recorder.extract_frame_at_minute(video_path, minute)
                print(f"\n截图完成: {screenshot_path}")
            else:
                print("分钟数必须在1-5之间")
        except ValueError:
            print("请输入有效的数字")
            
    elif choice == "3":
        # 完整流程
        print("\n开始录制...")
        video_path = recorder.record_screen(duration_minutes=5)
        
        print("\n录制完成，现在提取截图...")
        try:
            minute = int(input("请输入要提取的分钟数 (1-5): "))
            if 1 <= minute <= 5:
                screenshot_path = recorder.extract_frame_at_minute(video_path, minute)
                print(f"\n截图完成: {screenshot_path}")
            else:
                print("分钟数必须在1-5之间")
        except ValueError:
            print("请输入有效的数字")
    
    else:
        print("无效选择")

if __name__ == "__main__":
    main()