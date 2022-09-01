from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import askopenfile
import time
from xmind2anki import Courier

ws = Tk()
ws.title('Xmind2Anki Pro 1.0.0')
ws.geometry('400x200')
ws.grid_columnconfigure((0, 4), weight=1)

xmind_file_path = ""


class Props:
    xmind_file_path: str


def open_file():
    file_path = askopenfile(mode='r', filetypes=[('Xmind Files', '*xmind')])
    if file_path is not None:
        Props.xmind_file_path = file_path.name.replace('/', '\\')
        activated()


def uploadFiles():
    progress_bar()
    courier = Courier(Props.xmind_file_path)
    courier.upload_all_changes_to_anki()


def disable():
    upld["state"] = "disabled"


def activated():
    upld["state"] = "normal"


def progress_bar():
    pb1.grid(row=4, column=1, columnspan=2, sticky="ew", pady=10)


def update_progress_bar():
    ws.update_idletasks()
    pb1['value'] += 20
    time.sleep(1)
    if pb1['value'] == 100:
        Label(ws, text='File Uploaded Successfully!', foreground='green').grid(row=4, columnspan=3, pady=10)

def update_progress_bar_error():
    Label(ws, text='File sent with error!', foreground='red').grid(row=4, columnspan=3, pady=10)


pb1 = Progressbar(
    ws,
    orient=HORIZONTAL,
    length=300,
    mode='determinate'
)


adhar = Label(
    ws,
    text='Upload Xmind file format to send Anki flashCard'
)
adhar.grid(row=0, column=1, columnspan=1)

adharbtn = Button(
    ws,
    text='Choose File',
    command=lambda: open_file()
)
adharbtn.grid(row=0, column=2, sticky="ew")

upld = Button(
    ws,
    text='Send to Anki',
    command=uploadFiles
)
upld.grid(row=3, column=1, columnspan=2, sticky="ew")


def open_ui():
    ws.mainloop()
