#- Amadeo -> atcn
#- Pedro Victor -> pvlb
#- Bruna Alves -> baws
#- Filipe Melo -> fgm3
#- Weslley da Hora -> wbh
#- Julio Vinicius -> jvgs
#- Carlos Pereira -> crcp
#- Frederico Bresani -> fbs4 

import tkinter as tk, threading
from tkinter import filedialog
import time
import imageio
from PIL import Image, ImageTk

def play_video(path, fps=60):
    video_name = path #This is your video file path
    video = imageio.get_reader(video_name)

    def stream(label, video, fps=60):
        time.sleep(0.005)
        for image in video.iter_data():
            frame_image = ImageTk.PhotoImage(Image.fromarray(image))
            label.config(image=frame_image)
            label.image = frame_image
            time.sleep(1/fps)

    root = tk.Tk()
    root.title("Video Player")
    my_label = tk.Label(root)
    my_label.pack()
    thread = threading.Thread(target=stream, args=(my_label,video,fps), daemon=1)
    thread.start()
    root.mainloop()


if __name__ == '__main__':
    play_video(filedialog.askopenfilename())
