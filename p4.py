from tkinter import *
from tkinter import filedialog
import os
from datetime import datetime
import threading
import socket

"""Nota: O sistema de mandar e receber arquivos ainda não funciona corregamente, eu não consegui uma forma
de diferenciar mensagens de controle e mensagens de usuário direito, então mandar arquivos só funciona se a outra pessoa
tiver feito um update logo antes (ou o arquivo for a primeira mensagem enviada)

Algo do tipo:
A envia mensagem
A envia arquivo
B faz Update

Não funciona pq o sinal de controle para B começar o download do arquivo acaba se juntando a mensagem

Fora isso, parece estar funcionando corretamente, mas não tem aviso visual dentro da tela ainda

Also, eu tentei usar threads para fazer o download de imagens em outra thread para não travar o app,
não sei se isso está funcionando corretamente"""

class GUI:
    def __init__(self, width, height, name, target) -> None:
        self.name = name
        self.window = Tk()
        self.window.title("waiting...")

        self.canva = Canvas(self.window, width=width, height=height)
        self.canva.grid(columnspan=5)
        
        self.target_ip = target

        self.createWidgets()

        self.status = ''
        self.conn = None
        self.addr = None
        self.connector = None
        self.connect()
    
    def createWidgets(self):
        self.txt_area = Text(self.canva, border=1)
        self.txt_field = Entry(self.canva, width=50, border=1, bg='white')
        self.send_button = Button(self.canva, text='Send', padx=40, command=self.send)
        self.update_button = Button(self.canva, text='Update', padx=40, command=self.update)
        self.clear_button = Button(self.canva, text='Clear', padx=40, command=self.clear_chat)

        self.window.bind('<Return>', self.send)
        # self.window.bind('<Shift_R>', self.update)
        self.txt_area.bind('<Configure>', self.reset_tabstop)
        self.window.bind('<Shift_R>', self.get_file)
        self.txt_area.config(background='#c8a2c8')

        self.txt_area.grid(column=0, row=0, columnspan=5)
        self.txt_field.grid(column=0, row=1, columnspan=2)
        self.send_button.grid(column=2, row=1)
        self.update_button.grid(column=3, row=1)
        self.clear_button.grid(column=4, row=1)

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
        msg = msg.replace("\\n","\n")
        msg = f"\n{self.name}: {msg}\n{datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}\n"
        self.connector.sendall(bytes(msg, 'utf-8')) 
        msg = msg.replace('\n', '\n\t')
        self.txt_area.insert(END, msg)
        self.txt_field.delete(0, END)

    def reset_tabstop(self, event):
        event.widget.configure(tabs=(event.width-8, "right"))

    def update(self, event=None):
        try:
            while True:
                self.connector.settimeout(0.001)
                msg = self.connector.recv(1024)
                if not msg:
                    return
                msg = msg.decode('utf-8')
                if msg[0] == "!":
                    t = threading.Thread(target=lambda: self.recv_file(msg))
                    t.start()
                else:
                    msg = msg.replace("\\n","\n")
                    self.txt_area.insert(END, msg)
        except TimeoutError:
            print("Todas mensagens foram carregadas")

    def clear_chat(self, event=None):
        self.txt_area.delete(1.0, END)

    def get_file(self, event=None):
        file_path = filedialog.askopenfilename()
        if file_path == '':
            return
        self.send_file(file_path)
    
    def send_file(self, file_path):
        size_bytes = os.path.getsize(file_path)
        print(size_bytes)
        name = file_path.split('/')[-1].replace(';','')
        header = '!'+name+';'+str(size_bytes)
        print(header)
        self.connector.sendall(bytes(header, 'utf-8'))

        file = open(file_path, 'rb')
        l = file.read(1024)
        while l:
            self.connector_f.sendall(l)
            l = file.read(1024)
        file.close()

    def recv_file(self, header):
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

    def start(self):
        self.window.mainloop()

if __name__ == '__main__':
    nome = input("Qual o seu nome? ")
    interface = GUI(600, 800, nome, 'localhost').start()
    print("Goodbye")