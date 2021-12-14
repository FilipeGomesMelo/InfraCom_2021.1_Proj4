from tkinter import *
from datetime import datetime
import socket

class GUI:
    def __init__(self, width, height, name, target) -> None:
        self.name = name
        self.window = Tk()
        self.window.title("waiting...")

        self.canva = Canvas(self.window, width=width, height=height)
        self.canva.grid(columnspan=4)
        
        self.target_ip = target

        self.createWidgets()

        self.status = ''
        self.conn = None
        self.addr = None
        self.connector = None
        self.connect()
    
    def createWidgets(self):
        self.txt_area = Text(self.canva, border=1)
        self.txt_field = Entry(self.canva, width=65, border=1, bg='white')
        self.send_button = Button(self.canva, text='Send', padx=40, command=self.send)
        self.update_button = Button(self.canva, text='Update', padx=40, command=self.update)

        self.window.bind('<Return>', self.send)
        self.window.bind('<Shift_R>', self.update)
        self.txt_area.config(background='#c8a2c8')

        self.txt_area.grid(column=0, row=0, columnspan=4)
        self.txt_field.grid(column=0, row=1, columnspan=2)
        self.send_button.grid(column=2, row=1)
        self.update_button.grid(column=3, row=1)

    def connect(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.target_ip, 28886))
            self.status = f'{self.name} - client'
            self.connector = self.s
        except ConnectionRefusedError:
            self.status = f'{self.name} - Server'
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind(('localhost', 28886))
            self.s.listen(1)
            self.conn, self.addr = self.s.accept()
            self.connector = self.conn
        finally:
            self.window.title(self.status)
    
    def send(self, event=None):
        msg = self.txt_field.get()
        if msg.replace(' ', '') == '':
            return
        msg = msg.replace("\\n","\n")
        msg = f"\n{self.name}: {msg}\n{datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}\n"
        self.connector.sendall(bytes(msg, 'utf-8')) 
        self.txt_area.insert(END, msg)
        self.txt_field.delete(0, END)

    def update(self, event=None):
        try:
            while True:
                self.connector.settimeout(0.001)
                msg = self.connector.recv(1024)
                if not msg:
                    return
                msg = msg.decode("utf-8").replace("\\n","\n")
                self.txt_area.insert(END, msg)
        except TimeoutError:
            print("Todas mensagens foram carregadas")

    def start(self):
        self.window.mainloop()

if __name__ == '__main__':
    nome = input("Qual o seu nome? ")
    interface = GUI(600, 800, nome, 'localhost').start()