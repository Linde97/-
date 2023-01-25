import speech_recognition as sr
import os,sys
import tkinter as tk
from tkinter import *
from tkinter import messagebox
import multiprocessing as mp
import soundcard as sc
import soundfile as sf
import sounddevice as sd
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tmt.v20180321 import tmt_client, models


def speech_to_text(capture_sec: float,#先存储扬声器播放内容，再将内容通过谷歌语音识别，最后利用腾讯翻译 
                   sample_rate: int,
                   translate_config:tuple[str,str,str,str]):#translate_config=(text_language,SecretId,SecretKey,region)
    line_change=[]          #定义一个数组，每一次停顿则存储一个“0”，每次说话就清空数组并存储一个“1”，若说话后停顿一段时间，则换行，否则不换行
    while True:
        try:
            capture_audio_output(capture_sec,sample_rate)     #存储扬声器播放内容         
            audioRecognition(line_change,translate_config[0])        #将内容通过谷歌语音识别
            if line_change==["1"]:
                translations(translate_config)    #若有新的原文产生，则利用腾讯翻译 
        except:
            print("翻译系统错误")  
def capture_audio_output(capture_sec: float,#file name.#将扬声器的内容录入output.wav，语音长度为capture_sec秒
                         sample_rate: int):
    output_file_name = "output.wav"
    num_frame: int = int(sample_rate * capture_sec)
    with sc.get_microphone(id=str(sc.default_speaker().name),include_loopback=True).recorder(samplerate=sample_rate) as mic:#将录入设备设为默认扬声器
        data = mic.record(numframes=num_frame)
        sf.write(file='record/' +output_file_name,data=data[:, 0],samplerate=sample_rate)
def audioRecognition(line_change,language:str):#利用speech_recognition识别语音，由于按固定时间记录扬声器内容无法准确断句，因此大量原文将被保存在同一行
    recognizer = sr.Recognizer()
    adu=sr.AudioFile('record/' +"output.wav")
    with adu as source:
        audio = recognizer.listen(source)
        if len(line_change)>10 and "1" in line_change:  #若说话后停顿一段时间，则换行，否则不换行
                line_change=[]
                history = open('record/' + f"history.txt", "a")
                history.write(" "+'\n')
                history.close()
        try:
            text = recognizer.recognize_google(audio, language=language)  # 还可以选择不同的数据源，从而用来识别不同的语言
            line_change.clear()          #每次说话就清空数组并存储一个“1”   
            line_change.append("1")
            print(text+" ")
            history = open('record/' + f"history.txt", "a")
            history.write(text + ' ')
            history.close()
        except:
            if len(line_change)<50:         
                line_change.append("0")                    
def translations(translate_config:tuple[str,str,str,str]):#用于将翻译文本保存，每次先读取原文100长度的内容，翻译后逐行保存在translation1.txt中
    f = open('record/' + f"history.txt", "r") #读取文件
    line_length=100#每行选取文本的最大长度
    try:
        last_line = f.readlines()[-1] #读文件最后一行
    except IndexError:
        last_line = ''
    if len(last_line)<=line_length:#此判断用于分割文本，避免翻译内容过长
        last_line
    else:
        last_line=sentence_split(last_line,line_length)
    try:
        text=translate(last_line,translate_config)#开始翻译
        if text:
            print(text)
            translation = open('record/' + f"translation1.txt", "a")
            translation.write(text + '\n')
            translation.close()
    except Exception as err:
        translation = open('record/' + f"translation1.txt", "a")
        translation.write("翻译时出错" + '\n')
        translation.close()
        print("翻译时出错")
        print(err)
def translate(text:str,translate_config:tuple[str,str,str,str]):#翻译
    #translate_config=(text_language,SecretId,SecretKey,region)
    try:
        # 实例化一个认证对象，入参需要传入腾讯云账户 SecretId 和 SecretKey，此处还需注意密钥对的保密
        # 代码泄露可能会导致 SecretId 和 SecretKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议采用更安全的方式来使用密钥，请参见：https://cloud.tencent.com/document/product/1278/85305
        # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
        cred = credential.Credential(translate_config[1], translate_config[2])
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = "tmt.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = tmt_client.TmtClient(cred, translate_config[3], clientProfile)#服务器地区选择

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.TextTranslateRequest()
        params = {
            "Target": "zh",
            "ProjectId": 0
        }
        params["SourceText"]=text
        params["Source"]=translate_config[0]
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个TextTranslateResponse的实例，与请求对象对应
        resp = client.TextTranslate(req)
        # 输出json格式的字符串回包
        resp_dict=eval(resp.to_json_string())
        translation=resp_dict["TargetText"]
        return translation
    except TencentCloudSDKException as err:
        print(err)
        if err.get_code()=="AuthFailure.SecretIdNotFound"or"AuthFailure.SignatureFailure"or"InvalidCredential":
            tk.messagebox.showerror(title=err.get_code(),
		    message=err.get_message()+"请退出后重试。")
            sys.exit()       
def sentence_split(last_line:str,line_length:int):#用于分割语音识别出的原文，避免翻译文本太长
    temp_f=last_line[len(last_line)-line_length-1:]
    if last_line[len(last_line)-line_length-2]==" ":
        return temp_f
    else:
        temp_f=temp_f.split(" ",1)[1]
        return temp_f


class Win():#字幕窗口
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("字幕")
        self.root.geometry('1600x50+100+0')
        self.root.attributes("-alpha",0.5)
        self.TText=tk.Text(self.root,font=('Arial',30),width=70,height=10)
        self.line_length=37#每行显示的中文数量
        self.TText.grid(row=1,column=0,rowspan=10,columnspan=10)
        self.update()
        

    def update(self): #更新字幕，每秒更新一次
        self.TText.delete(1.0,'end')
        f = open('record/' + f"translation1.txt", "r") #读取文件
        try:
            last_line = f.readlines()[-1] #读文件最后一行
        except IndexError:
            last_line = ''
        if last_line=='':#未开始时显示此消息
            self.TText.insert(1.0,"等待翻译")
        else:
            if len(last_line)>self.line_length:#此判断用于分割文本，显示内容过多
                last_line=last_line[len(last_line)-self.line_length:]
            self.TText.insert(1.0,last_line)
        self.root.after(1000, self.update)
class Log_WIN():#登录窗口
    def __init__(self):
        self.config={}
        self.root = tk.Tk()
        self.root.title("登录")
        self.root.geometry('500x300')
        self.root.attributes("-alpha",0.85)
        self.Label1=Label(self.root, text="请输入腾讯云翻译的api ID和密钥：", 
                                    font=('Arial', 15))                          
        self.Label_SecretId = Label(self.root, text="ID", 
                                    font=('Arial', 12))
        self.Label_SecretKey = Label(self.root, text="密钥", 
                                    font=('Arial', 12)) 
        self.SecretId=StringVar()
        self.SecretKey=StringVar()                        
        self.Enrty_SecretId=Entry(self.root,width=50,textvariable=self.SecretId)
        self.Enrty_SecretKey=Entry(self.root,width=50,textvariable=self.SecretKey)
        self.GIRLS = [("英语",0),("日语",1),("德语",2)]
        self.language=tk.IntVar()
        for girl, num in self.GIRLS:
            b = tk.Radiobutton(self.root, text=girl, variable=self.language, value=num)
            b.place(relx=0.1*num, rely =0.39, anchor=NW)

        self.Label2=Label(self.root, text="腾讯翻译服务器选择：", 
                                    font=('Arial', 12))  
        self.GIRLS_region = [("欧洲",0),("上海",1),("北京",2)]
        self.region=tk.IntVar()
        for girl, num in self.GIRLS_region:
            b = tk.Radiobutton(self.root, text=girl, variable=self.region, value=num)
            b.place(relx=0.1*num+0.35, rely =0.52, anchor=NW)
        def button1_click():                 #确定按钮点击事件
            self.config["next_step"]=False
            self.config["key"]=self.Enrty_SecretKey.get()
            self.config["id"]=self.Enrty_SecretId.get()
            self.config["text_language_num"]=self.language.get()
            self.config["region_num"]=self.region.get()
            if self.check(self.config["key"],self.config["id"]):
                self.config["next_step"]=True
                self.root.destroy()
                
        self.button1 = tk.Button(self.root, text='确定', width=15,
              height=2, command=button1_click)
        def button2_click():                 #保存按钮点击事件
            config = open('record/' + f"config.txt", "w+")#记录配置
            config.write("SecretId:" + ' '+self.SecretId.get()+"\n")
            config.write("SecretKey:" + ' '+self.SecretKey.get()+"\n")
            config.write("text_language_num:" + ' '+str(self.language.get())+"\n")
            config.write("region_num:" + ' '+str(self.region.get())+"\n")
            config.close()
        self.button2 = tk.Button(self.root, text='保存', width=15,
              height=2, command=button2_click)
        self.Label1.place(relx=0, rely =0, anchor=NW)   
        self.Label_SecretKey.place(relx=0, rely =0.26, anchor=NW)
        self.Label_SecretId.place(relx=0, rely =0.13, anchor=NW)
        self.Enrty_SecretId.place(relx=0.2, rely =0.13, anchor=NW)
        self.Enrty_SecretKey.place(relx=0.2, rely =0.26, anchor=NW)
        self.Label2.place(relx=0, rely =0.52, anchor=NW) 
        self.button1.place(relx=0.8, rely =0.8, anchor=SE)
        self.button2.place(relx=0.2, rely =0.8, anchor=SW)
        self.load()
        
    def check(self,key,id):     #检查输入长度
        if len(id)!=36:
            tk.messagebox.showerror(title='ID长度错误',
		message='ID长度错误,请重新输入')
            return False
        elif len(key)!=32:
            tk.messagebox.showerror(title='密钥长度错误',
		message='密钥长度错误,请重新输入')
            return False
        return True
    def load(self):             #自动加载保存数据
        try:
            f = open('record/' + f"config.txt", 'r')
            for config in f.readlines():
                if config.split(" ",1)[0]=="SecretId:":
                    self.SecretId.set(config.split(" ",1)[1].strip())
                elif config.split(" ",1)[0]=="SecretKey:":
                    self.SecretKey.set(config.split(" ",1)[1].strip())
                elif config.split(" ",1)[0]=="text_language_num:":
                    self.language.set(int(config.split(" ",1)[1].strip()))
                elif config.split(" ",1)[0]=="SecretKey:":
                    self.region.set(int(config.split(" ",1)[1].strip()))
        except Exception as e:
            print(e)
            return
        finally:
            try:
                f.close()
            except:
                return
def win_run():#运行字幕窗口
    try:
        win=Win()
        win.root.mainloop()
    except Exception as err:
        tk.messagebox.showerror(title='字幕窗口错误',
		    message=err)
        print("字幕窗口错误")
        print(err)
    sys.exit()
def run_log():      #运行登录窗口
    log=Log_WIN()
    log.root.mainloop()
    config=log.config
    del log
    return config
def run_main(id:str,key:str,text_language_num:int,region_num:int):        #准备运行翻译程序和字幕窗口
    SecretId=id
    SecretKey=key       
    #0表示英语，谷歌代码：en 腾讯代码：en
    #1表示日语，谷歌代码：ja 腾讯代码：ja
    #2表示德语，谷歌代码：de 腾讯代码：de
    #3表示汉语，谷歌代码：zh 腾讯代码：zh
    if text_language_num==0:
        text_language="en"
    elif text_language_num==1:
        text_language="ja"
    elif text_language_num==2:
        text_language="de"
    elif text_language_num==3:
        text_language="zh"
    #腾讯翻译服务器 1：法兰克福 2：上海 3：北京
    if region_num==0:
        region="eu-frankfurt"
    elif region_num==1:
        region="ap-shanghai"
    elif region_num==2:
        region="ap-beijing"

    CAPTURE_SEC: int = 4
    history = open('record/' + f"history.txt", "w+")#记录原文
    history.close()
    translation = open('record/' + f"translation1.txt", "w+")#记录译文
    translation.close()
    translate_config=(text_language,SecretId,SecretKey,region)
    sample_rate: int = int(sd.query_devices(kind="output")["default_samplerate"])
    stt_proc: mp.Process = mp.Process(target=speech_to_text,
                                      args=(CAPTURE_SEC,sample_rate,translate_config))
    stt_proc.daemon=True
    stt_proc.start()
    try:
        win_run()
    except Exception as err:
        stt_proc.terminate()
        tk.messagebox.showerror(title='主程序错误',
		            message=err)
        print(err)

if __name__ == "__main__":
    mp.freeze_support()
    config={}
    if not os.path.exists('record'):
        os.makedirs('record') #创建目录
    config=run_log()
    if config!={} and config["next_step"]:        #只有通过确定按钮才能继续
        run_main(config["id"],config["key"],config["text_language_num"],config["region_num"])



