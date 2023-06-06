import asyncio
from tkinter import ttk, NSEW
import tkinter as tk

from Frame import ModPackageManagerFrame, resource_path
from tool import UAC_check


class App:
    def __init__(self):
        self.window: Window = None

    async def exec(self):
        UAC_check(True)
        self.window = Window(asyncio.get_event_loop())
        await self.window.show()


class Window:
    def __init__(self, loop):
        self.loop = loop
        # 視窗初始化設定
        self.root = tk.Tk(className=f"模組包切換器v1,0")
        self.root.protocol("WM_DELETE_WINDOW", self.cancel_callback)
        # 設定視窗寬高
        window_width = 700
        window_height = 400
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.minsize(window_width, window_height)
        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.root.tk.call('source', resource_path('forest-dark.tcl'))
        style = ttk.Style(self.root)
        style.theme_use('forest-dark')

        # GUI布局
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.frame = ModPackageManagerFrame(self.root)
        self.frame.grid(row=0, column=0, sticky=NSEW)
        self.run = True

    def cancel_callback(self):
        self.frame.cancel_callback()
        self.run = False
        self.root.attributes('-disabled', False)
        self.root.destroy()

    async def show(self):
        while self.run:
            self.root.update()
            await asyncio.sleep(0.1)


if __name__ == '__main__':
    asyncio.run(App().exec())
