# Translator based on speech_recognition
# 简介(2023.1.25)
      这是一个基于speech_recognition和腾讯翻译的实时翻译软件。
# 原理
      工作原理为先使用soundcard实时不断地录制扬声器音频，再利用speech_recognition对每段语音进行识别，最后通过腾讯机器翻译。
# 功能
      程序可以选择将英语,德语,日语三种源语言翻译成中文。
# 使用
### 需要安装
      pip install soundcard
      pip install SpeechRecognition
      pip install tencentcloud-sdk-python-common
### 需要开通
      腾讯云-机器翻译api（https://console.cloud.tencent.com/tmt）
### 使用方式
      填写获得的ID和KEY，选择对应的语言和服务器
      
      
