from tkinter import *
from tkinter import filedialog
import pygame as pg
from threading import Thread


class audioPLayer:
    def __init__(self, audio_path) -> None:
        pg.mixer.init()
        self.path = audio_path
        self.root = Tk()
        self.root.title('Audio Player')
        
        self.isPlaying = False

        self.canva = Canvas(self.root, width=300, height=400)
        self.canva.pack()

        self.audio_name_label = Label(self.canva, text=self.path.split('/')[-1])
        self.audio_name_label.pack(side=LEFT)
        self.play_button = Button(self.canva, text="Play", command=self.play)
        self.play_button.pack(side=LEFT)
        self.pause_button = Button(self.canva,text="Pause", command=self.pause)
        self.pause_button.pack(side=LEFT)

        pg.mixer.music.load(self.path)
        pg.mixer.music.play(loops=0)

        self.start()

    def start(self):
        self.root.mainloop()        
    
    def play(self):
        self.isPlaying = True
        pg.mixer.music.unpause()        
    
    def pause(self):
        self.isPlaying = False
        pg.mixer.music.pause()
        
if __name__ == '__main__':
    audioPLayer(filedialog.askopenfilename())