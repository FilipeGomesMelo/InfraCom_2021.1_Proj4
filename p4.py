from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
import tkinter.font as font
import threading
import os
from datetime import datetime
import socket

class GUI:
    def __init__(self, width, height, name, target) -> None:
        self.miniature_pics = []

        self.name = name
        self.separation_character = "$#"
        self.send_lock = threading.Lock()
        self.recv_lock = threading.Lock()
        self.window = Tk()
        self.window.title("waiting...")

        self.canva = Canvas(self.window, width=width, height=height)
        self.canva.grid(columnspan=6)
        
        self.target_ip = target

        self.createWidgets()

        self.status = ''
        self.conn = None
        self.addr = None
        self.connector = None
        self.connect()
    
    def createWidgets(self):
        fonte = font.Font(family='Century Gothic', size=8, weight='bold')
        anexo = PhotoImage(file=r"anexo2.png")
        miniatura_anexo = anexo.subsample(52)
        self.txt_area = Text(self.canva, border=1)
        self.txt_field = Entry(self.canva, width=50, border=1, bg='#FFF275')
        self.send_button = Button(self.canva, text='Send', padx=30, command=self.send, bg='#0077B6', fg='white', font=fonte)
        self.update_button = Button(self.canva, text='Update', padx=30, command=self.update, bg='#0077B6', fg='white', font=fonte)
        self.clear_button = Button(self.canva, text='Clear', padx=30, command=self.clear_chat, bg='#0077B6', fg='white', font=fonte)
        self.upload_button = Button(self.canva, text='Upload',padx=20, image=miniatura_anexo, compound=RIGHT, command=self.get_file, bg='#0077B6', fg='white', font=fonte)
        self.upload_button.miniatura_anexo = miniatura_anexo
        

        self.window.bind('<Return>', self.send)
        # self.window.bind('<Shift_R>', self.update)
        self.txt_area.bind('<Configure>', self.reset_tabstop)
        self.window.bind('<Shift_R>', self.get_file)
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
    
    def send(self, event=None):
        msg = self.txt_field.get()
        if msg.replace(' ', '') == '':
            return
        msg = msg.replace("\\n","\n").replace(self.separation_character, "")
        msg = f"{self.separation_character}\n{self.name}: {msg}\n{datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}\n"
        self.connector.sendall(bytes(msg, 'utf-8')) 
        msg = msg.replace('\n', '\n\t')
        self.txt_area.insert(END, msg[len(self.separation_character):])
        self.txt_field.delete(0, END)

    def reset_tabstop(self, event):
        event.widget.configure(tabs=(event.width-8, "right"))

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
                print('>>'+msg)
                if msg[0] == "!":
                    t = threading.Thread(target = lambda: self.recv_file(msg))
                    t.start()
                else:
                    msg = msg.replace("\\n","\n")
                    self.txt_area.insert(END, msg)
            print("Todas mensagens foram carregadas")

    def clear_chat(self, event=None):
        self.txt_area.delete(1.0, END)

    def get_file(self, event=None):
        file_path = filedialog.askopenfilename()
        if file_path == '':
            return
        try:
            self.miniature_pics
            pic = Image.open(file_path)
            miniature_pic = pic.resize((150, (150*pic.height)//pic.width), Image.ANTIALIAS)
            my_img = ImageTk.PhotoImage(miniature_pic)
            self.miniature_pics.append(my_img)
            self.txt_area.insert(END,'\n\t')
            self.txt_area.image_create(END, image=self.miniature_pics[-1])
            self.txt_area.insert(END,'\n')
        except:
            pass
        t = threading.Thread(target = lambda: self.send_file(file_path))
        t.start()
            
    def send_file(self, file_path):
        self.send_lock.acquire()
        size_bytes = os.path.getsize(file_path)
        print(size_bytes)
        name = file_path.split('/')[-1].replace(';','')
        header = self.separation_character+'!'+name+';'+str(size_bytes)
        print(header)
        self.connector.sendall(bytes(header, 'utf-8'))

        file = open(file_path, 'rb')
        l = file.read(1024)
        while l:
            self.connector_f.sendall(l)
            l = file.read(1024)
        file.close()
        print(f"fineshed sending {name}")
        self.send_lock.release()

    def recv_file(self, header):
        self.recv_lock.acquire()
        name, size_bytes = header[1:].split(';')
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
        file.close()
        self.recv_lock.release()

    def start(self):
        self.window.mainloop()

if __name__ == '__main__':
    nome = input("Qual o seu nome? ")
    interface = GUI(600, 800, nome, 'localhost').start()
    print("Goodbye")