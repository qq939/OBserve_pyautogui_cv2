# 导入必要的库和模块
import base64  # 用于Base64编码/解码
from threading import Lock, Thread  # 用于多线程处理和线程同步

import cv2  # OpenCV库，用于图像处理和计算机视觉
import openai  # OpenAI API客户端
from cv2 import VideoCapture, imencode  # 视频捕获和图像编码功能
from dotenv import load_dotenv  # 用于从.env文件加载环境变量
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder  # LangChain提示模板
from langchain.schema.messages import SystemMessage  # LangChain系统消息类型
from langchain_community.chat_message_histories import ChatMessageHistory  # 聊天历史记录管理
from langchain_core.output_parsers import StrOutputParser  # 字符串输出解析器
from langchain_core.runnables.history import RunnableWithMessageHistory  # 带历史记录的可运行对象
from langchain_openai import ChatOpenAI  # LangChain的OpenAI聊天模型接口
from pyaudio import PyAudio, paInt16  # 音频处理库
from speech_recognition import Microphone, Recognizer, UnknownValueError  # 语音识别功能

# 加载环境变量（从.env文件）
load_dotenv()


class WebcamStream:
    """网络摄像头流处理类
    
    该类实现了对网络摄像头的多线程访问，允许在不阻塞主线程的情况下
    持续捕获和处理视频帧。
    """
    def __init__(self):
        """初始化WebcamStream对象
        
        创建视频捕获对象，初始化第一帧，并设置线程控制变量。
        """
        self.stream = VideoCapture(index=0)  # 初始化摄像头，index=0表示默认摄像头
        _, self.frame = self.stream.read()  # 读取第一帧
        self.running = False  # 线程运行状态标志
        self.lock = Lock()  # 创建线程锁，用于同步对帧数据的访问

    def start(self):
        """启动摄像头流处理线程
        
        如果线程已经在运行，则直接返回当前对象。
        否则，创建并启动新线程来持续捕获视频帧。
        
        Returns:
            WebcamStream: 返回自身实例，支持链式调用
        """
        if self.running:
            return self

        self.running = True

        self.thread = Thread(target=self.update, args=())  # 创建更新线程
        self.thread.start()  # 启动线程
        return self

    def update(self):
        """持续更新视频帧的线程函数
        
        在线程中持续读取摄像头的新帧，并使用线程锁安全地更新当前帧。
        """
        while self.running:
            _, frame = self.stream.read()  # 读取新帧

            self.lock.acquire()  # 获取线程锁
            self.frame = frame  # 更新当前帧
            self.lock.release()  # 释放线程锁

    def read(self, encode=False):
        """读取当前视频帧
        
        线程安全地获取当前帧的副本，可选择是否将其编码为Base64字符串。
        
        Args:
            encode (bool, optional): 是否将帧编码为Base64字符串。默认为False。
        
        Returns:
            numpy.ndarray 或 bytes: 如果encode=False，返回帧的numpy数组；
                                    如果encode=True，返回Base64编码的字节串。
        """
        self.lock.acquire()  # 获取线程锁
        frame = self.frame.copy()  # 复制当前帧以避免数据竞争
        self.lock.release()  # 释放线程锁

        if encode:
            _, buffer = imencode(".jpeg", frame)  # 将帧编码为JPEG格式
            return base64.b64encode(buffer)  # 返回Base64编码的字节串

        return frame

    def stop(self):
        """停止摄像头流处理线程
        
        设置运行标志为False并等待线程结束。
        """
        self.running = False  # 设置运行标志为False
        if self.thread.is_alive():
            self.thread.join()  # 等待线程结束

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """上下文管理器退出方法
        
        在使用with语句时，确保释放摄像头资源。
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 异常回溯
        """
        self.stream.release()  # 释放摄像头资源


class Assistant:
    """AI助手类
    
    该类封装了一个能够处理图像和文本输入的AI助手，使用LangChain和OpenAI API
    来生成回答并通过文本转语音(TTS)输出。
    """
    def __init__(self, model):
        """初始化Assistant对象
        
        Args:
            model: LangChain兼容的语言模型对象(如ChatOpenAI或ChatGoogleGenerativeAI)
        """
        self.chain = self._create_inference_chain(model)  # 创建推理链

    def answer(self, prompt, image):
        """处理用户提问并生成回答
        
        接收用户的文本提示和图像，使用AI模型生成回答，
        并通过文本转语音(TTS)朗读回答。
        
        Args:
            prompt (str): 用户的文本提示/问题
            image (bytes): Base64编码的图像数据
        """
        if not prompt:  # 如果提示为空，则直接返回
            return

        print("Prompt:", prompt)  # 打印用户提示

        # 调用推理链处理提示和图像
        response = self.chain.invoke(
            {"prompt": prompt, "image_base64": image.decode()},  # 输入数据
            config={"configurable": {"session_id": "unused"}},  # 配置会话ID
        ).strip()  # 去除首尾空白字符

        print("Response:", response)  # 打印AI回答

        if response:  # 如果有回答，则通过TTS朗读
            self._tts(response)

    def _tts(self, response):
        """文本转语音功能
        
        使用OpenAI的TTS API将文本转换为语音并播放。
        
        Args:
            response (str): 要转换为语音的文本
        """
        # 初始化音频播放器
        player = PyAudio().open(format=paInt16, channels=1, rate=24000, output=True)

        # 使用OpenAI的TTS API创建语音流
        with openai.audio.speech.with_streaming_response.create(
            model="tts-1",  # 使用TTS-1模型
            voice="alloy",  # 使用alloy语音
            response_format="pcm",  # PCM格式输出
            input=response,  # 输入文本
        ) as stream:
            # 逐块读取并播放音频数据
            for chunk in stream.iter_bytes(chunk_size=1024):
                player.write(chunk)

    def _create_inference_chain(self, model):
        """创建推理链
        
        构建一个LangChain推理链，用于处理多模态输入(文本和图像)并生成回答。
        
        Args:
            model: LangChain兼容的语言模型对象
            
        Returns:
            RunnableWithMessageHistory: 带有聊天历史记录功能的推理链
        """
        # 系统提示，定义AI助手的行为和风格
        SYSTEM_PROMPT = """
        You are a witty assistant that will use the chat history and the image 
        provided by the user to answer its questions. Your job is to answer 
        questions.

        Use few words on your answers. Go straight to the point. Do not use any
        emoticons or emojis. 

        Be friendly and helpful. Show some personality.
        """

        # 创建聊天提示模板，包含系统消息、聊天历史和用户输入(文本和图像)
        prompt_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=SYSTEM_PROMPT),  # 系统提示
                MessagesPlaceholder(variable_name="chat_history"),  # 聊天历史占位符
                (
                    "human",  # 人类消息
                    [
                        {"type": "text", "text": "{prompt}"},  # 文本输入
                        {
                            "type": "image_url",  # 图像输入
                            "image_url": "data:image/jpeg;base64,{image_base64}",  # Base64编码的图像
                        },
                    ],
                ),
            ]
        )

        # 构建推理链：提示模板 -> 模型 -> 字符串输出解析器
        chain = prompt_template | model | StrOutputParser()

        # 创建聊天历史记录对象
        chat_message_history = ChatMessageHistory()
        
        # 返回带有聊天历史记录功能的推理链
        return RunnableWithMessageHistory(
            chain,  # 基础推理链
            lambda _: chat_message_history,  # 聊天历史记录获取函数
            input_messages_key="prompt",  # 输入消息键
            history_messages_key="chat_history",  # 历史消息键
        )


# 初始化并启动网络摄像头流
webcam_stream = WebcamStream().start()

# 选择AI模型
# 可以使用Google的Gemini模型
# model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")

# 或者使用OpenAI的GPT-4o模型
model = ChatOpenAI(model="gpt-4o")  # 初始化OpenAI的GPT-4o模型

# 创建Assistant实例
assistant = Assistant(model)


def audio_callback(recognizer, audio):
    """语音识别回调函数
    
    当检测到音频输入时被调用，将语音转换为文本，
    然后将文本和当前摄像头图像发送给AI助手处理。
    
    Args:
        recognizer: 语音识别器实例
        audio: 捕获的音频数据
    """
    try:
        # 使用OpenAI的Whisper模型进行语音识别
        prompt = recognizer.recognize_whisper(audio, model="base", language="english")
        # 将识别的文本和当前摄像头图像发送给AI助手
        assistant.answer(prompt, webcam_stream.read(encode=True))

    except UnknownValueError:
        # 处理语音识别错误
        print("There was an error processing the audio.")


# 初始化语音识别组件
recognizer = Recognizer()  # 创建语音识别器
microphone = Microphone()  # 创建麦克风对象
with microphone as source:
    # 调整麦克风以适应环境噪音
    recognizer.adjust_for_ambient_noise(source)

# 在后台启动语音监听
stop_listening = recognizer.listen_in_background(microphone, audio_callback)

# 主循环：显示摄像头画面并检测退出按键
while True:
    # 显示摄像头画面
    cv2.imshow("webcam", webcam_stream.read())
    # 检测按键 - ESC(27)或'q'键退出
    if cv2.waitKey(1) in [27, ord("q")]:
        break

# 清理资源
webcam_stream.stop()  # 停止摄像头流
cv2.destroyAllWindows()  # 关闭所有OpenCV窗口
stop_listening(wait_for_stop=False)  # 停止语音监听（不等待完全停止）