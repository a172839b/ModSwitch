import asyncio
import os
import shutil
import sys
from pathlib import Path
from tkinter import *
from tkinter import ttk
import tkinter as tk
import tkinter.font as tkFont
from tkinter.filedialog import askdirectory, askopenfilename

import winsound

from jsonTool import read, write
from tool import is_admin, killWar3_not_check, War3_is_open, killWar3


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def startfile(path, pass_error=True) -> None:
    try:
        os.startfile(path)
    except Exception as e:
        print(e)
        if not pass_error:
            raise e


class MyFrame(ttk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self._font = tkFont.Font(family="Consolas", size=12)

    def cancel_callback(self):
        # 關閉時執行的事件
        ...


# 路徑選擇輸入框
class EntryFrame(MyFrame):
    def __init__(self, master, pathName: str, title: str, openBtn=True, btnName='打開', filemode=False, **kw):
        super().__init__(master, **kw)
        self._path = tk.StringVar(value=read(pathName, ''))
        self._pathName = pathName
        self.columnconfigure(2, weight=2)
        ttk.Label(self, text=title). \
            grid(row=0, column=0, sticky=NSEW, padx=2, pady=2)
        ttk.Entry(self, textvariable=self._path, font=self._font, state='readonly'). \
            grid(row=0, column=1, columnspan=2, sticky=NSEW, padx=2, pady=2)
        if openBtn:
            ttk.Button(self, text=btnName, command=lambda: startfile(self._path.get())). \
                grid(row=0, column=4, sticky=NSEW, padx=2, pady=2)
        ttk.Button(self, text="路徑選擇", command=self.select_callback). \
            grid(row=0, column=5, sticky=NSEW, padx=2, pady=2)
        self.select_callback = None
        self.filemode = filemode

    def select_callback(self):
        if self.filemode:
            return self.selectFile()
        else:
            return self.selectPath()

    def selectPath(self):
        path_ = askdirectory()
        if path_:
            self._path.set(path_)
            write(self._pathName, path_)
            if callable(self.select_callback):
                self.select_callback()

    def selectFile(self):
        path_ = askopenfilename()
        if path_:
            self._path.set(path_)
            write(self._pathName, path_)
            if callable(self.select_callback):
                self.select_callback()

    @property
    def path(self) -> str:
        return self._path.get()


class ModPackageManagerFrame(MyFrame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.loop = asyncio.get_event_loop()

        self.columnconfigure(0, weight=1)
        # self.rowconfigure(3, weight=1)
        self.entry = EntryFrame(self, 'war3_path', '魔獸根目錄:')
        self.entry.grid(row=0, column=0, columnspan=3, sticky=NSEW)
        self.entry.select_callback = self.select_callback

        self.war3exe = EntryFrame(self, 'war3_exe_path', '魔獸執行檔:', btnName='執行', filemode=True)
        self.war3exe.grid(row=1, column=0, columnspan=3, sticky=NSEW)
        # self.entry.select_callback = self.select_callback

        # OptionMenu
        self.item_list = ["停用模組包"]
        self.combobox = ttk.Combobox(self, state="readonly", values=self.item_list)
        self.combobox.current(0)
        self.combobox.grid(row=2, column=0, padx=2, pady=5, sticky="nsew")
        self.combobox.bind('<<ComboboxSelected>>', self.on_combobox_selected)
        self.combobox.bind('<Button-1>', self.combo_events)

        ttk.Button(self, text='打開', command=lambda: startfile(self.modPath)) \
            .grid(row=2, column=1, padx=2, pady=5, sticky=NSEW)

        self.restart = BooleanVar(value=read('modpack_restart', False))
        ttk.Checkbutton(self, text='自動重啟', variable=self.restart). \
            grid(row=3, column=0, sticky=EW, padx=2, pady=2)

        self.last_item = None
        self.modPath: Path = None
        if self.entry.path != "":
            self.update_path()
            self.refresh()

        ttk.Label(self, text='使用說明: 在目錄底下會有\"__MODPACK__\"資料夾，進入資料夾中，新增資料夾並將模組放入。') \
            .grid(row=4, column=0, padx=20, pady=20, sticky=NSEW)

    def combo_events(self, evt):
        w = evt.widget
        w.event_generate('<Down>')
        self.refresh()

    def cancel_callback(self):
        write('modpack_restart', self.restart.get())

    def on_combobox_selected(self, event):
        selection = self.combobox.get()

        if not self.modPath.is_dir():
            return

        last_mod = read('last_mod', {"name": "停用模組包", "mods": []}, f'{self.modPath}/temp')
        if last_mod['name'] == selection:
            return

        # 檢測魔獸開啟
        isKillWar3 = False
        if is_admin():
            isKillWar3 = killWar3_not_check()
        elif War3_is_open():
            winsound.PlaySound(resource_path('sound/fail.wav'), winsound.SND_ASYNC)
            tk.messagebox.showinfo(title='檔案使用中', message='請關閉魔獸後再次嘗試')
            self.refresh()
            return

        # 新舊版本過度銜接用
        if '__MODPACK__' not in selection and selection != '停用模組包':
            selection = f'{self.modPath}/{selection}'
        if '__MODPACK__' not in last_mod['name'] and last_mod['name'] != '停用模組包':
            last_mod['name'] = f'{self.modPath}/{last_mod["name"]}'

        # 上次有裝模組，則還原
        retry = 2
        while retry > 0:
            try:
                for f in last_mod['mods']:
                    s_tmp = Path(f'{self.entry.path}/{f}')
                    if s_tmp.is_dir():
                        self.move_file(s_tmp, f"{last_mod['name']}/{f}")
                        try:
                            s_tmp.rmdir()
                        except OSError as e:
                            pass
                    else:
                        self.move_file(s_tmp, f"{last_mod['name']}")
                break
            except PermissionError as e:
                killWar3()
            finally:
                retry -= 1

        if selection == '停用模組包':
            write('last_mod', {"name": "停用模組包", "mods": []}, f'{self.modPath}/temp')
            # 重啟魔獸
            if isKillWar3 and self.restart.get() and Path(self.war3exe.path).is_file():
                startfile(self.war3exe.path)
            winsound.PlaySound(resource_path('sound/ok.wav'), winsound.SND_ASYNC)
            return

        # 移動模組包
        tmp = self.move_file(selection, self.entry.path)

        # 紀錄最後安裝的模組
        write('last_mod', {'name': self.combobox.get(),
                           'mods': tmp}, f'{self.modPath}/temp')

        winsound.PlaySound(resource_path('sound/ok.wav'), winsound.SND_ASYNC)
        # 重啟魔獸
        if isKillWar3 and self.restart.get() and Path(self.war3exe.path).is_file():
            startfile(self.war3exe.path)

    def update_path(self):
        self.modPath = Path(self.entry.path + '\__MODPACK__')
        if not self.modPath.is_dir():
            try:
                self.modPath.mkdir(parents=True)
            except:
                ...

    def select_callback(self):
        self.update_path()
        self.refresh()

    def refresh(self):
        if self.modPath is None:
            return
        self.item_list = ["停用模組包"]
        for item in self.modPath.iterdir():
            if not item.is_dir():
                continue
            self.item_list.append(item.name)
        self.combobox['values'] = self.item_list
        try:
            last_mod = read('last_mod', {"name": "停用模組包", "mods": []}, f'{self.modPath}/temp')
            self.combobox.set(last_mod['name'])
        except Exception as e:
            ...

    @staticmethod
    def move_file(source, dest) -> []:
        source = Path(source)
        dest = Path(dest)
        if not dest.exists():
            dest.mkdir()

        moved_files = []  # 創建一個空列表來存放移動的檔案名稱

        if source.is_dir():
            for item in source.iterdir():
                if item.is_file():
                    shutil.move(item, dest / item.name)
                    moved_files.append(item.name)
                elif item.is_dir():
                    shutil.move(item, dest / item.name)
                    moved_files.append(item.name)

        elif source.is_file():
            shutil.move(source, dest / source.name)
            moved_files.append(source.name)
        return moved_files
