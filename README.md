# Translator based on speech_recognition
# (2023.1.26) v1.0.1
# 原理
      stereoReverb版本利用立体声混响代替soundcard录制声音，大幅提高语句完整性，进而提高翻译准确度。同时若声音持续不断，则长时间无法得到翻译。
# 功能
      新增了返回按钮。可以随时返回登录界面更改语言和其他配置信息。
# 使用
### 需要安装
      pip install soundcard
      pip install SpeechRecognition
      pip install tencentcloud-sdk-python-common
### 使用方式
      1.将立体声混音设为默认音频输入设备
      2.填写获得的ID和KEY，选择对应的语言和服务器

      
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


