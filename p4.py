from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import tkinter.font as font
import threading
import os
from datetime import datetime
import socket
import time
from pygame import mixer
import videoPlayer
import multiprocessing

class GUI:
    def __init__(self, width, height, name, target) -> None:
        self.miniature_pics = []

        self.name = name
        self.separation_character = "$#"
        self.send_lock = threading.Lock()
        self.recv_lock = threading.Lock()
        self.window = Tk()
        self.window.title("waiting...")
        self.pics = []

        self.canva = Canvas(self.window, width=width, height=height)
        self.canva.grid(columnspan=6)
        
        self.target_ip = target

        self.createWidgets()
        t = threading.Thread(target = self.check_updates, daemon=True)
        t.start()

        mixer.init()
        self.audio_channel = mixer.Channel(0)
        self.playing_audio = False

        self.media_dict = dict()
        self.media_path_dict = dict()

        self.status = ''
        self.conn = None
        self.addr = None
        self.connector = None
        self.connect()
    
    def createWidgets(self):
        fonte = font.Font(family='Century Gothic', size=8, weight='bold')
        anexo = PhotoImage(file=r"anexo2.png")
        miniatura_anexo = anexo.subsample(52)
        self.txt_area = Text(self.canva, border=1, width=90, height=35)
        self.txt_field = Entry(self.canva, width=50, border=1, bg='#FFF275')
        self.send_button = Button(self.canva, text='Send', padx=30, command=self.send, bg='#0077B6', fg='white', font=fonte)
        self.update_button = Button(self.canva, text='Update', padx=30, command=self.update, bg='#0077B6', fg='white', font=fonte)
        self.clear_button = Button(self.canva, text='Clear', padx=30, command=self.clear_chat, bg='#0077B6', fg='white', font=fonte)
        self.upload_button = Button(self.canva, text='Upload',padx=20, image=miniatura_anexo, compound=RIGHT, command=self.get_file, bg='#0077B6', fg='white', font=fonte)
        self.upload_button.miniatura_anexo = miniatura_anexo
        

        self.window.bind('<Return>', self.send)
        # self.window.bind('<Shift_R>', self.update)
        self.txt_area.bind('<Configure>', self.reset_tabstop)
        # self.window.bind('<Shift_R>', self.get_file)
        self.window.bind('<F1>', self.pause_audio)
        self.window.bind('<F2>', self.stop_audio)
        self.txt_area.config(background='#7CC8CB')

        self.txt_area.grid(column=0, row=0, columnspan=6)
        self.txt_field.grid(column=0, row=1, columnspan=2)
        self.send_button.grid(column=2, row=1)
        self.update_button.grid(column=3, row=1)
        self.clear_button.grid(column=5, row=1)
        self.upload_button.grid(column=4, row=1)

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.target_ip, 28886))
            self.s_f = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s_f.connect((self.target_ip, 28887))
            self.status = f'{self.name} - client'
            self.connector = self.s
            self.connector_f = self.s_f
        except ConnectionRefusedError:
            self.status = f'{self.name} - Server'
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind(('localhost', 28886))
            self.s.listen(1)
            self.s_f = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s_f.bind(('localhost', 28887))
            self.s_f.listen(1)
            self.conn, self.addr = self.s.accept()
            self.conn_f, self.addr_f = self.s_f.accept()
            self.connector = self.conn
            self.connector_f = self.conn_f
        finally:
            self.window.title(self.status)

    def write_log(self, msg):
        log_name = f"chat_log_{self.name}.txt"

        # Escreve a mensagem no log
        with open(log_name,"a",encoding="utf-8") as log:
            log.write(msg)
    
    def send(self, event=None):
        msg = self.txt_field.get()
        if msg.replace(' ', '') == '':
            return
        
        if msg[:5] == "!play":
            try:
                type_index = msg[6:].rindex(".")
            except ValueError: 
                print("404 - File Not Found")
                self.txt_field.delete(0, END)
                return

            file_format = msg[6:][type_index+1:]
            if file_format in ["wav","mp3","ogg"] and msg[6:] in self.media_dict:
                # Play the sound in the file. Ex: !play me.wav
                print(f"Tocando {msg[6:]}")
                file = self.media_dict[msg[6:]]
                self.play_audio(file)
            else:
                try:
                    # Se o arquivo não for um arquivo de áudio, tentamos abrir ele com os, só funciona se estiver no diretório que está rodando
                    # o cliente
                    print(f"Abrindo {msg[6:]}")

                    # Se o arquivo tiver sido enviado pelo usuário, o acessa por seu diretório.
                    # Senão, o acessa pela pasta da aplicação
                    if file_format in ['mp4']:
                        p = multiprocessing.Process(target= videoPlayer.play_video, args=(msg[6:],))
                        p.start()
                    elif msg[6:] in self.media_path_dict:
                        os.startfile(msg[6:])
                    else:
                        os.startfile(os.getcwd()+'\\'+msg[6:])
                except:
                    # Se não conseguir, printa que arquivo não foi achado
                    print("404 - File Not Found")
            self.txt_field.delete(0, END)
            return
        
        msg = msg.replace("\\n","\n").replace(self.separation_character, "")
        msg = f"{self.separation_character}\n{self.name}: {msg}\n{datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}\n"
        self.connector.sendall(bytes(msg, 'utf-8')) 
        msg = msg.replace('\n', '\n\t')
        self.txt_area.insert(END, msg[len(self.separation_character):])
        self.txt_field.delete(0, END)

        self.write_log("\n" + msg[4:]) # Remove alguns chars desncessários

    def reset_tabstop(self, event):
        event.widget.configure(tabs=(event.width-8, "right"))

    # thread pra checar que chama a checagem de novas mensagens em um timer
    def check_updates(self):
        while True:
            time.sleep(0.5)
            self.update()
            
    def update(self, event=None):
        aux = []
        try:
            while True:
                self.connector.settimeout(0.001)
                msg = self.connector.recv(1024)
                if not msg:
                    return
                msg = msg.decode('utf-8')
                aux.append(msg) 
        except:
            mensagens = ''.join(aux).split(self.separation_character)[1:]
            for msg in mensagens:
                if msg[0] == "!":
                    self.recv_file(msg)
                else:
                    msg = msg.replace("\\n","\n")
                    self.txt_area.insert(END, msg)
                    self.write_log(msg)

    def clear_chat(self, event=None):
        self.txt_area.delete(1.0, END)

    def play_audio(self,audio):
        # If there is an audio playing, stop it
        try:
            self.audio_channel.stop()
    
            # Play the audio
            self.audio_channel.play(audio)
            self.playing_audio = True
        except KeyError:
            print("Audio nao encontado")

    def pause_audio(self, event=None):
        # If there is not playing, return
        if not self.audio_channel.get_busy():
            return

        if self.playing_audio: 
            self.audio_channel.pause()
        else:
            self.audio_channel.unpause()
        
        self.playing_audio = not self.playing_audio

    def stop_audio(self, event=None):
        # If there is not playing, return
        if not self.audio_channel.get_busy():
            return

        self.audio_channel.stop()

    def get_file(self, event=None):
        file_path = filedialog.askopenfilename()

        if file_path == '':
                return
        type_index = file_path.rindex(".")
        file_format = file_path[type_index+1:]
        self.txt_area.insert(END, f'\n\t{self.name}:\n\t')
        if file_format in ["wav","mp3","ogg"]:
            audio = mixer.Sound(file_path)
            self.media_dict[file_path] = audio
            
            self.txt_area.insert(END, f"#Audio: {file_path.split('/')[-1]}")
        elif file_format in ["mp4"]:
            self.txt_area.insert(END, f"#Video: {file_path.split('/')[-1]}")
        else:
            try:
                pic = Image.open(file_path)
                miniature_pic = pic.resize((325, (325*pic.height)//pic.width), Image.ANTIALIAS)
                my_img = ImageTk.PhotoImage(miniature_pic)
                self.miniature_pics.append(my_img)
                
                self.txt_area.image_create(END, image=self.miniature_pics[-1])
                
            except:
                self.txt_area.insert(END, f"#File: {file_path.split('/')[-1]}")

        self.txt_area.insert(END, f"\n\t{datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}\n")
        t = threading.Thread(target = lambda: self.send_file(file_path))
        t.start()
            
    def send_file(self, file_path):
        self.send_lock.acquire()
        print(f"Começando a enviar {file_path.split('/')[-1]}")
        size_bytes = os.path.getsize(file_path)
        name = file_path.split('/')[-1].replace(';','')
        header = (self.separation_character+'!'+name+';'+str(size_bytes)+';'+
                  self.name+';'+datetime.now().strftime('%d/%m/%Y, %H:%M:%S'))
        self.connector.sendall(bytes(header, 'utf-8'))

        file = open(file_path, 'rb')
        l = file.read(1024)
        while l:
            self.connector_f.sendall(l)
            l = file.read(1024)
        file.close()
        
        type_index = file_path.rindex(".")
        file_format = file_path[type_index+1:]

        if file_format in ["wav","mp3","ogg"]:
            audio = mixer.Sound(file_path)
            self.media_dict[name] = audio
        else:
            self.media_path_dict[name] = file_path

        print(f"Terminamos colocar {file_path.split('/')[-1]} no buffer")
        self.send_lock.release()
        

    def recv_file(self, header):
        name, size_bytes, sender, time = header[1:].split(';')
        print(f"starting dowload of {name}")
        size_bytes = int(size_bytes)
        file = open(name, 'wb')
        l = self.connector_f.recv(1024)
        size_bytes -= 1024
        while size_bytes > 0:
                file.write(l)
                l = self.connector_f.recv(min(1024, size_bytes))
                size_bytes -= 1024
        file.write(l)
        print(f"File {name} downloaded")
        file_path = file.name
        #file_formmat = file_path[-3:]
        file.close()

        type_index = file_path.rindex(".")
        file_format = file_path[type_index+1:]
        self.txt_area.insert(END, f'\n{sender}:\n')
        if file_format in ["wav","mp3","ogg"]:
            audio = mixer.Sound(file_path)
            self.media_dict[file_path] = audio
            
            self.txt_area.insert(END, f'#Audio: {name}')

        elif file_format in ["mp4"]:
            self.txt_area.insert(END, f'#Video: {name}')
        else:
            try:
                pic = Image.open(file_path)
                miniature_pic = pic.resize((325, (325*pic.height)//pic.width), Image.ANTIALIAS)
                my_img = ImageTk.PhotoImage(miniature_pic)
                self.miniature_pics.append(my_img)
                
                self.txt_area.image_create(END, image=self.miniature_pics[-1])
                
            except:
                self.txt_area.insert(END, f'#File: {name}')

        self.txt_area.insert(END, f"\n{time}\n")

    def start(self):
        self.window.mainloop()

if __name__ == '__main__':
    nome = input("Qual o seu nome? ")
    interface = GUI(600, 800, nome, 'localhost').start()
    print("Goodbye")
