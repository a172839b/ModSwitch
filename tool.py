import ctypes
import os
import sys

import psutil


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except:
        return False


def UAC_check(Exit=False, windows=False, *args):
    if not is_admin():
        arg = " ".join(sys.argv + [str(x) for x in args])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, arg, None, windows)
        if Exit:
            sys.exit()


def startfile(path, pass_error=True) -> None:
    try:
        os.startfile(path)
    except Exception as e:
        print(e)
        if not pass_error:
            raise e


KillWar3 = False


async def killWar3():
    global KillWar3
    if KillWar3:
        return
    KillWar3 = True
    # UAC確認
    UAC_check(True, '-killWat3')

    try:
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            if proc.info['name'].lower() == 'war3.exe':
                proc.kill()
    except Exception as e:
        pass
    finally:
        KillWar3 = False


def killWar3_not_check() -> bool:
    global KillWar3
    if KillWar3:
        return
    KillWar3 = True
    KillState = False
    try:
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            if proc.info['name'].lower() == 'war3.exe':
                proc.kill()
                KillState = True
    except Exception as e:
        return False
    finally:
        KillWar3 = False
        return KillState


def War3_is_open() -> bool:
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if proc.info['name'].lower() == 'war3.exe':
            return True
    return False
