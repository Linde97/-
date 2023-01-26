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



def speech_to_text(translate_config:tuple[str,str,str,str],information_queue:mp.Queue):#利用speech_recognition识别语音，识别后立刻调用翻译
    recognizer = sr.Recognizer()
    mic=sr.Microphone()
    while True:
        if information_queue.qsize()>0 and information_queue.get()=="quit":
            return
        with mic as source:
            audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio, language=translate_config[0])  # 还可以选择不同的数据源，从而用来识别不同的语言
                print(text)
                history = open('record/' + f"history.txt", "a",encoding='utf-8')
                history.write(text + '\n')
                history.close()
                translations(translate_config,text)    #若有新的原文产生，则利用腾讯翻译 
            except Exception as err:
                if type(err).__dict__['__module__']=="speech_recognition":  #由于噪声过大，谷歌识别异常,UnknownValueError
                    translation = open('record/' + f"translation2.txt", "a")
                    translation.write("噪声过大" + '\n')
                    translation.close()
                else:
                    print("翻译系统错误:"+err)
def translations(translate_config:tuple[str,str,str,str],text:str):#用于将翻译文本保存，翻译后逐行保存在translation2.txt中
    try:
        text=translate(text,translate_config)#开始翻译
        if text:
            print(text+"\n")
            translation = open('record/' + f"translation2.txt", "a")
            translation.write(text + '\n')
            translation.close()
    except Exception as err:
        translation = open('record/' + f"translation2.txt", "a")
        translation.write("翻译时出错" + '\n')
        translation.close()
        print("翻译时出错: "+err)
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

class Win():#字幕窗口
    def __init__(self,information_queue:mp.Queue):
        self.backFlag=False    
        self.root = tk.Tk()
        self.root.title("字幕")
        self.root.geometry('1600x50+100+0')
        self.root.attributes("-alpha",0.5)
        self.TText=tk.Text(self.root,font=('Arial',15),width=137,height=10)
        self.line_length=73#每行显示的中文数量
        def button1_click():                 #返回按钮点击事件
            information_queue.put("quit")
            self.backFlag=True
            self.root.destroy()
        self.button1 = tk.Button(self.root, text='返回', width=5,height=2, command=button1_click)
        self.TText.grid(row=1,column=0,rowspan=10,columnspan=10)
        self.button1.grid(row=1,column=10, sticky=N)
        self.update()
        

    def update(self): #更新字幕，每秒更新一次
        self.TText.delete(1.0,'end')
        f = open('record/' + f"translation2.txt", "r") #读取文件
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
def win_run(information_queue:mp.Queue):#运行字幕窗口
    backFlag=False
    try:
        win=Win(information_queue)
        win.root.mainloop()
        backFlag=win.backFlag
        del win
    except Exception as err:
        tk.messagebox.showerror(title='字幕窗口错误',
		    message=err)
        print("字幕窗口错误: "+err)
    if backFlag:
        run_log()
    else:
        sys.exit()
def run_log():      #运行登录窗口
    log=Log_WIN()
    log.root.mainloop()
    config=log.config
    del log
    if config!={} and config["next_step"]:        #只有通过确定按钮才能继续
        run_main(config["id"],config["key"],config["text_language_num"],config["region_num"])
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

    history = open('record/' + f"history.txt", "w+")#记录原文
    history.close()
    translation = open('record/' + f"translation2.txt", "w+")#记录译文
    translation.close()
    translate_config=(text_language,SecretId,SecretKey,region)
    information_queue:mp.Queue=mp.Queue()
    stt_proc: mp.Process = mp.Process(target=speech_to_text,
                                      args=(translate_config,information_queue))
    stt_proc.daemon=True
    stt_proc.start()
    try:
        win_run(information_queue)
    except Exception as err:
        stt_proc.terminate()
        tk.messagebox.showerror(title='主程序错误',
		            message=err)
        print("主程序错误: "+err)

if __name__ == "__main__":
    mp.freeze_support()
    if not os.path.exists('record'):
        os.makedirs('record') #创建目录
    run_log()




