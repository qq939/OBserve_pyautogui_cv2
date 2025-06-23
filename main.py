#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时屏幕录制与VideoChat模型集成
将实时屏幕录制的帧数据传入videochat模型进行多模态推理
"""

import cv2
import pyautogui
import numpy as np
import time
import os
from datetime import datetime
from typing import List, Optional
import threading
import queue
from collections import deque

# VideoChat相关导入（根据README.md中的示例）
try:
    from videochat import VideoChatModel, VideoProcessor
except ImportError:
    print("警告: videochat库未安装，将使用模拟模式")
    VideoChatModel = None
    VideoProcessor = None

class RealTimeScreenAnalyzer:
    """
    实时屏幕分析器
    结合屏幕录制和VideoChat模型进行实时分析
    """
    
    def __init__(self, 
                 max_frames: int = 100,
                 fps: int = 10,
                 analysis_interval: int = 30,
                 output_dir: str = "recordings"):
        """
        初始化实时屏幕分析器
        
        Args:
            max_frames (int): 最大帧数缓存
            fps (int): 录制帧率
            analysis_interval (int): 分析间隔（秒）
            output_dir (str): 输出目录
        """
        self.max_frames = max_frames
        self.fps = fps
        self.analysis_interval = analysis_interval
        self.output_dir = output_dir
        
        # 屏幕信息
        self.screen_size = pyautogui.size()
        
        # 帧缓存队列
        self.frame_buffer = deque(maxlen=max_frames)
        self.frame_queue = queue.Queue()
        
        # 控制标志
        self.is_recording = False
        self.is_analyzing = False
        
        # 线程
        self.capture_thread = None
        self.analysis_thread = None
        
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 初始化VideoChat模型
        self.model = None
        self.processor = None
        self._init_videochat_model()
    
    def _init_videochat_model(self):
        """
        初始化VideoChat模型
        """
        if VideoChatModel and VideoProcessor:
            try:
                print("正在初始化VideoChat模型...")
                self.model = VideoChatModel.from_pretrained("videochat-base")
                self.processor = VideoProcessor()
                print("VideoChat模型初始化成功")
            except Exception as e:
                print(f"VideoChat模型初始化失败: {e}")
                print("将使用模拟模式")
                self.model = None
                self.processor = None
        else:
            print("VideoChat库未安装，使用模拟模式")
    
    def _capture_frames(self):
        """
        屏幕帧捕获线程
        """
        print(f"开始屏幕捕获，分辨率: {self.screen_size}，帧率: {self.fps}")
        
        frame_interval = 1.0 / self.fps
        last_capture_time = time.time()
        
        while self.is_recording:
            current_time = time.time()
            
            # 控制帧率
            if current_time - last_capture_time >= frame_interval:
                try:
                    # 截取屏幕
                    screenshot = pyautogui.screenshot()
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # 添加时间戳
                    timestamp = datetime.now()
                    frame_data = {
                        'frame': frame,
                        'timestamp': timestamp,
                        'frame_id': len(self.frame_buffer)
                    }
                    
                    # 添加到缓存
                    self.frame_buffer.append(frame_data)
                    
                    # 添加到分析队列
                    if not self.frame_queue.full():
                        self.frame_queue.put(frame_data)
                    
                    last_capture_time = current_time
                    
                except Exception as e:
                    print(f"屏幕捕获错误: {e}")
            
            time.sleep(0.001)  # 短暂休眠避免CPU占用过高
    
    def _analyze_frames(self):
        """
        帧分析线程
        """
        print("开始帧分析线程")
        last_analysis_time = time.time()
        
        while self.is_analyzing:
            current_time = time.time()
            
            # 检查是否到了分析时间
            if current_time - last_analysis_time >= self.analysis_interval:
                if len(self.frame_buffer) > 0:
                    self._perform_analysis()
                    last_analysis_time = current_time
            
            time.sleep(1)  # 每秒检查一次
    
    def _perform_analysis(self):
        """
        执行VideoChat分析
        """
        try:
            # 获取最近的帧
            recent_frames = list(self.frame_buffer)[-min(30, len(self.frame_buffer)):]
            
            if not recent_frames:
                return
            
            print(f"\n=== 开始分析 {len(recent_frames)} 帧 ===")
            print(f"时间范围: {recent_frames[0]['timestamp'].strftime('%H:%M:%S')} - {recent_frames[-1]['timestamp'].strftime('%H:%M:%S')}")
            
            # 提取帧数据
            video_frames = [frame_data['frame'] for frame_data in recent_frames]
            
            if self.model and self.processor:
                # 使用真实的VideoChat模型
                self._analyze_with_videochat(video_frames)
            else:
                # 使用模拟分析
                self._simulate_analysis(video_frames)
                
        except Exception as e:
            print(f"分析过程出错: {e}")
    
    def _analyze_with_videochat(self, video_frames: List[np.ndarray]):
        """
        使用VideoChat模型进行分析
        
        Args:
            video_frames: 视频帧列表
        """
        try:
            # 预处理视频帧
            processed_frames = self.processor.load_video_from_frames(
                video_frames, 
                max_frames=self.max_frames
            )
            
            # 准备问题列表
            questions = [
                "屏幕上正在发生什么？",
                "用户在进行什么操作？",
                "有什么值得注意的变化吗？",
                "这个界面的主要内容是什么？"
            ]
            
            # 对每个问题进行分析
            for question in questions:
                print(f"\n问题: {question}")
                
                response = self.model.generate_response(
                    video=processed_frames,
                    question=question,
                    max_length=512,
                    temperature=0.7
                )
                
                print(f"回答: {response}")
                
                # 保存分析结果
                self._save_analysis_result(question, response)
                
        except Exception as e:
            print(f"VideoChat分析失败: {e}")
            self._simulate_analysis(video_frames)
    
    def _simulate_analysis(self, video_frames: List[np.ndarray]):
        """
        模拟分析（当VideoChat不可用时）
        
        Args:
            video_frames: 视频帧列表
        """
        print("使用模拟分析模式")
        
        # 简单的图像分析
        if video_frames:
            first_frame = video_frames[0]
            last_frame = video_frames[-1]
            
            # 计算帧差异
            diff = cv2.absdiff(first_frame, last_frame)
            diff_score = np.mean(diff)
            
            # 计算平均亮度
            avg_brightness = np.mean(cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY))
            
            # 检测边缘
            gray = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            print(f"帧变化程度: {diff_score:.2f}")
            print(f"平均亮度: {avg_brightness:.2f}")
            print(f"边缘密度: {edge_density:.4f}")
            
            # 简单的活动检测
            if diff_score > 10:
                activity = "检测到屏幕活动"
            else:
                activity = "屏幕相对静止"
            
            print(f"活动状态: {activity}")
            
            # 保存分析结果
            analysis_result = f"帧变化: {diff_score:.2f}, 亮度: {avg_brightness:.2f}, 边缘密度: {edge_density:.4f}, 状态: {activity}"
            self._save_analysis_result("模拟分析", analysis_result)
    
    def _save_analysis_result(self, question: str, response: str):
        """
        保存分析结果到文件
        
        Args:
            question: 问题
            response: 回答
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(self.output_dir, f"analysis_{timestamp}.txt")
        
        with open(result_file, "a", encoding="utf-8") as f:
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"问题: {question}\n")
            f.write(f"回答: {response}\n")
            f.write("-" * 50 + "\n")
    
    def start_analysis(self):
        """
        开始实时分析
        """
        if self.is_recording:
            print("分析已在进行中")
            return
        
        print("开始实时屏幕分析...")
        print(f"分析间隔: {self.analysis_interval}秒")
        print("按 Ctrl+C 停止分析")
        
        # 设置标志
        self.is_recording = True
        self.is_analyzing = True
        
        # 启动线程
        self.capture_thread = threading.Thread(target=self._capture_frames)
        self.analysis_thread = threading.Thread(target=self._analyze_frames)
        
        self.capture_thread.start()
        self.analysis_thread.start()
        
        try:
            # 主线程等待
            while self.is_recording:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n用户中断分析")
            self.stop_analysis()
    
    def stop_analysis(self):
        """
        停止实时分析
        """
        print("正在停止分析...")
        
        # 设置停止标志
        self.is_recording = False
        self.is_analyzing = False
        
        # 等待线程结束
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)
        
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=5)
        
        print("分析已停止")
    
    def interactive_query(self, question: str) -> str:
        """
        交互式查询当前屏幕内容
        
        Args:
            question: 用户问题
            
        Returns:
            str: 分析结果
        """
        if len(self.frame_buffer) == 0:
            return "没有可用的屏幕帧数据"
        
        # 获取最近的帧
        recent_frames = list(self.frame_buffer)[-min(10, len(self.frame_buffer)):]
        video_frames = [frame_data['frame'] for frame_data in recent_frames]
        
        if self.model and self.processor:
            try:
                processed_frames = self.processor.load_video_from_frames(
                    video_frames, 
                    max_frames=10
                )
                
                response = self.model.generate_response(
                    video=processed_frames,
                    question=question,
                    max_length=512,
                    temperature=0.7
                )
                
                return response
                
            except Exception as e:
                return f"分析失败: {e}"
        else:
            return "VideoChat模型不可用，无法进行交互式查询"

def main():
    """
    主函数
    """
    print("=== 实时屏幕分析工具 ===")
    print("1. 开始实时分析")
    print("2. 交互式查询模式")
    print("3. 退出")
    
    choice = input("请选择功能 (1/2/3): ").strip()
    
    if choice == "1":
        # 实时分析模式
        analyzer = RealTimeScreenAnalyzer(
            max_frames=50,
            fps=5,  # 降低帧率以减少资源消耗
            analysis_interval=30  # 每30秒分析一次
        )
        
        analyzer.start_analysis()
        
    elif choice == "2":
        # 交互式查询模式
        analyzer = RealTimeScreenAnalyzer(
            max_frames=30,
            fps=2,  # 更低的帧率
            analysis_interval=60  # 不进行自动分析
        )
        
        # 启动捕获但不启动自动分析
        analyzer.is_recording = True
        analyzer.capture_thread = threading.Thread(target=analyzer._capture_frames)
        analyzer.capture_thread.start()
        
        print("交互式查询模式已启动")
        print("等待几秒钟收集屏幕数据...")
        time.sleep(5)
        
        try:
            while True:
                question = input("\n请输入您的问题 (输入 'quit' 退出): ").strip()
                
                if question.lower() == 'quit':
                    break
                
                if question:
                    print("正在分析...")
                    response = analyzer.interactive_query(question)
                    print(f"回答: {response}")
                
        except KeyboardInterrupt:
            print("\n用户中断")
        
        finally:
            analyzer.stop_analysis()
    
    elif choice == "3":
        print("再见！")
    
    else:
        print("无效选择")

if __name__ == "__main__":
    main()