from src.utils import HumanBehaviorSimulator
import subprocess
import pychrome
import requests
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
                 speed_threshold=1.0):

        self.remote_debugging_port = remote_debugging_port
        self.lang = lang
        self.window_size = window_size
        self.speed_threshold = speed_threshold
        self.chrome_proc = None
        self.browser = None
        self.tab = None
        self.human = None

        system = platform.system()
        if system == "Windows":
            possible_paths = [
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google\\Chrome\\Application\\chrome.exe")]
            chrome_path_found = None
            for path in possible_paths:
                if path and os.path.isfile(path):
                    chrome_path_found = path
                    break

            if not chrome_path_found:
                raise FileNotFoundError("Google Chrome/Chromium not find in common path")

            self.chrome_path = chrome_path_found

            user_profile = os.environ.get("USERPROFILE")
            if not user_profile:
                raise EnvironmentError("env USERPROFILE not found")
            if user_data_dir is None:

                self.user_data_dir = os.path.join(user_profile, "AppData", "Local", "Google", "Chrome", "User Data", "BotProfile")
            else:
                self.user_data_dir = user_data_dir

        elif system == "Darwin":
            if chrome_path is None:
                chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if not os.path.isfile(chrome_path):
                raise FileNotFoundError("Google Chrome/Chromium not find in common path")
            self.chrome_path = chrome_path

            if user_data_dir is None:
                home = os.path.expanduser("~")
                self.user_data_dir = os.path.join(home, "Library", "Application Support", "Google", "Chrome", "BotProfile")
            else:
                self.user_data_dir = user_data_dir

        elif system == "Linux":
            if chrome_path is None:
                chrome_path = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
                if not chrome_path:
                    raise FileNotFoundError("Google Chrome/Chromium not find in PATH")
            self.chrome_path = chrome_path

            if user_data_dir is None:
                home = os.path.expanduser("~")
                self.user_data_dir = os.path.join(home, ".chrome-bot-profile")
            else:
                self.user_data_dir = user_data_dir

    def await_proc(self,timeout=15, interval=0.5):
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
            "--disable-blink-features=AutomationControlled"]

        self.chrome_proc = subprocess.Popen(flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.await_proc()
        self.browser = pychrome.Browser(url=f"http://127.0.0.1:{self.remote_debugging_port}")
        self.tab = self._get_active_tab()
        self.tab.start()

        self.human = HumanBehaviorSimulator(self.tab, speed_factor=self.speed_threshold)
        self.apply_stealth()

    def _get_active_tab(self):
        tabs = self.browser.list_tab()
        if not tabs:
            raise Exception("None chrome tab detected")

        return tabs[0]

    def apply_stealth(self):
        self.tab.call_method("Runtime.evaluate", expression="""(() => {
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US', 'en']});

            // Simular userAgent
            Object.defineProperty(navigator, 'userAgent', {
                get: () => "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            });

            // Simular WebGL Vendor e Renderer (para evitar fingerprinting básico)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return "Intel Inc."; // UNMASKED_VENDOR_WEBGL
                if (parameter === 37446) return "Intel Iris OpenGL Engine"; // UNMASKED_RENDERER_WEBGL
                return getParameter(parameter);
            };
            })();""")

    def close(self):
        if self.tab:
            self.tab.stop()

        if self.chrome_proc:
            self.chrome_proc.terminate()
            self.chrome_proc.wait()
