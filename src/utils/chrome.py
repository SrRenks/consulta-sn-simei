from src.utils import HumanBehaviorSimulator
from src.utils import StealthToolkit
import subprocess
import requests
import pychrome
import platform
import shutil
import time
import json
import os

_original_recv_loop = pychrome.Tab._recv_loop

def _safe_recv_loop(self):
    try:
        _original_recv_loop(self)
    except json.decoder.JSONDecodeError:
        pass

pychrome.Tab._recv_loop = _safe_recv_loop


class ChromeManager:
    def __init__(self,
                 chrome_path=None,
                 remote_debugging_port=9222,
                 user_data_dir=None,
                 lang="pt-BR",
                 window_size="1280,800",
                 speed_threshold=1.0,
                 stealth_level="normal",
                 stealth_custom_methods=None):

        self.remote_debugging_port = remote_debugging_port
        self.lang = lang
        self.window_size = window_size
        self.speed_threshold = speed_threshold
        self.chrome_proc = None
        self.browser = None
        self.tab = None
        self.human = None

        self.stealth_level = stealth_level
        self.stealth_custom_methods = stealth_custom_methods or []

        system = platform.system()
        if system == "Windows":
            possible_paths = [
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google\\Chrome\\Application\\chrome.exe")]
            for path in possible_paths:
                if path and os.path.isfile(path):
                    self.chrome_path = path
                    break
            else:
                raise FileNotFoundError("Google Chrome/Chromium not found in common path")

            user_profile = os.environ.get("USERPROFILE")
            if not user_profile:
                raise EnvironmentError("env USERPROFILE not found")
            self.user_data_dir = user_data_dir or os.path.join(user_profile, "AppData", "Local", "Google", "Chrome", "User Data", "BotProfile")

        elif system == "Darwin":
            chrome_path = chrome_path or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if not os.path.isfile(chrome_path):
                raise FileNotFoundError("Google Chrome/Chromium not found in common path")
            self.chrome_path = chrome_path

            home = os.path.expanduser("~")
            self.user_data_dir = user_data_dir or os.path.join(home, "Library", "Application Support", "Google", "Chrome", "BotProfile")

        elif system == "Linux":
            chrome_path = chrome_path or shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
            if not chrome_path:
                raise FileNotFoundError("Google Chrome/Chromium not found in PATH")
            self.chrome_path = chrome_path

            home = os.path.expanduser("~")
            self.user_data_dir = user_data_dir or os.path.join(home, ".chrome-bot-profile")

        else:
            raise EnvironmentError(f"Unsupported OS: {system}")

        self.stealth_toolkit = None

    def await_proc(self, timeout=15, interval=0.5):
        start = time.time()
        while True:
            try:
                resp = requests.get(f"http://127.0.0.1:{self.remote_debugging_port}/json/version", timeout=1)
                if resp.status_code == 200:
                    return True
            except requests.exceptions.ConnectionError:
                pass
            except Exception as e:
                raise e
            if time.time() - start > timeout:
                raise TimeoutError(f"Chrome DevTools without response in {timeout}s")
            time.sleep(interval)

    def launch(self):
        flags = [
            self.chrome_path,
            f"--remote-debugging-port={self.remote_debugging_port}",
            f"--user-data-dir={self.user_data_dir}_{self.remote_debugging_port}",
            "--no-first-run",
            "--disable-extensions",
            f"--lang={self.lang}",
            f"--window-size={self.window_size}",
            "--start-maximized",
            "--disable-blink-features=AutomationControlled"
        ]

        self.chrome_proc = subprocess.Popen(flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.await_proc()

        self.browser = pychrome.Browser(url=f"http://127.0.0.1:{self.remote_debugging_port}")
        self.tab = self._get_active_tab()
        self.tab.start()

        self.human = HumanBehaviorSimulator(self.tab, speed_factor=self.speed_threshold)

        self.stealth_toolkit = StealthToolkit(
            tab=self.tab,
            level=self.stealth_level,
            custom_methods=self.stealth_custom_methods
        )
        self.stealth_toolkit.apply()

    def _get_active_tab(self):
        tabs = self.browser.list_tab()
        if not tabs:
            raise Exception("No chrome tab detected")
        return tabs[0]

    def close(self):
        if self.tab:
            self.tab.stop()
        if self.chrome_proc:
            self.chrome_proc.terminate()
            self.chrome_proc.wait()
