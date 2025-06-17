from pychrome.tab import Tab
import threading
import random
import math
import time


class HumanMouseMover:
    def __init__(self, tab: Tab) -> None:
        self.tab = tab
        self.running = False
        self.paused = False
        self._lock = threading.Lock()
        self.thread = threading.Thread(target=self._move_loop, daemon=True)
        self.center_x = 800
        self.center_y = 400

    def start(self) -> None:
        self.running = True
        self.thread.start()

    def stop(self) -> None:
        if self.running:
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)


    def pause(self) -> None:
        with self._lock:
            self.paused = True

    def resume(self) -> None:
        with self._lock:
            self.paused = False

    def _move_loop(self) -> None:
        t = 0
        while self.running:
            with self._lock:
                if self.paused:
                    time.sleep(0.1)
                    continue

            x = self.center_x + 50 * math.sin(t * 0.3) + random.uniform(-5, 5)
            y = self.center_y + 30 * math.cos(t * 0.5) + random.uniform(-5, 5)

            try:
                self.tab.call_method(
                    "Input.dispatchMouseEvent",
                    type="mouseMoved",
                    x=x,
                    y=y,
                    button="none",
                    buttons=0,
                    clickCount=0
                )
            except Exception as e:
                pass

            t += 1
            time.sleep(0.05 + random.uniform(0, 0.05))

class HumanBehaviorSimulator:
    def __init__(self, tab: Tab, speed_factor: float = 1.0) -> None:
        self.tab = tab
        self.speed_factor = max(0.1, speed_factor)

    def _smooth_step(self, t: float) -> float:
        return t * t * (3 - 2 * t)

    def _sigmoid(self, x: float) -> float:
        return 1 / (1 + math.exp(-x))

    def _gaussian_noise(self, mean: float = 0, std_dev: float = 1) -> float:
        adjusted_std = std_dev * self.speed_factor
        return random.gauss(mean, adjusted_std)

    def _attention_curve(self, position: int, total_steps: int, base: float =0.25, peak_delay: float =0.5) -> float:
        normalized = position / max(total_steps - 1, 1)
        delay = base + (math.sin(normalized * math.pi) * peak_delay)
        noise = self._gaussian_noise(0, 0.02)
        result = max(0.05, delay + noise)
        return result * self.speed_factor

    def _hesitation_curve(self, time_passed: float, intensity: float = 1.0) -> float:
        base = 0.3
        decay = 0.4 * math.exp(-time_passed * intensity)
        result = base + decay
        return result * self.speed_factor

    def wait_for_pageload(self, timeout: int = 15) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            result = self.tab.call_method("Runtime.evaluate", expression="document.readyState")
            if result["result"]["value"] == "complete":
                return True
            time.sleep(0.3 * self.speed_factor)
        return False

    def scroll_page(self) -> None:
        for _ in range(random.randint(2, 6)):
            delta = random.randint(20, 60)

            x = random.randint(300, 600)
            y = random.randint(300, 600)

            self.tab.call_method("Input.dispatchMouseEvent",
                type="mouseWheel",
                x=x,
                y=y,
                deltaX=0,
                deltaY=delta,
                modifiers=0
            )

            time.sleep((abs(math.sin(time.time())) * 0.2 + 0.1) * self.speed_factor)

    def type_text(self, text: str) -> None:
        typed = ""
        digits = "0123456789"

        for i, char in enumerate(text):
            vk = ord(char)

            if random.random() < 0.05 and len(typed) > 1:
                wrong_digit = random.choice([d for d in digits if d != char])
                vk_wrong = ord(wrong_digit)

                self.tab.call_method("Input.dispatchKeyEvent", type="keyDown", windowsVirtualKeyCode=vk_wrong)
                time.sleep(0.005 * self.speed_factor)
                self.tab.call_method("Input.dispatchKeyEvent", type="char", text=wrong_digit)
                time.sleep(0.005 * self.speed_factor)
                self.tab.call_method("Input.dispatchKeyEvent", type="keyUp", windowsVirtualKeyCode=vk_wrong)
                time.sleep(0.04 * self.speed_factor)

                self.tab.call_method("Input.dispatchKeyEvent", type="keyDown", windowsVirtualKeyCode=8)
                self.tab.call_method("Input.dispatchKeyEvent", type="keyUp", windowsVirtualKeyCode=8)
                time.sleep(0.04 * self.speed_factor)

            self.tab.call_method("Input.dispatchKeyEvent", type="keyDown", windowsVirtualKeyCode=vk)
            time.sleep(0.003 * self.speed_factor)
            self.tab.call_method("Input.dispatchKeyEvent", type="char", text=char)
            time.sleep(0.003 * self.speed_factor)
            self.tab.call_method("Input.dispatchKeyEvent", type="keyUp", windowsVirtualKeyCode=vk)

            typed += char
            time.sleep(self._attention_curve(i, len(text)))

    def move_mouse(self, start_x: int, start_y: int, end_x: int, end_y: int, steps: int = 20):
        for i in range(steps):
            t = self._smooth_step(i / (steps - 1))
            x = start_x + (end_x - start_x) * t + self._gaussian_noise(0, 1.2)
            y = start_y + (end_y - start_y) * t + self._gaussian_noise(0, 1.2)
            self.tab.call_method("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
            time.sleep((0.015 + self._gaussian_noise(0, 0.005)) * self.speed_factor)

    def click(self, x: int, y: int) -> None:
        self.move_mouse(random.randint(0, 100), random.randint(0, 100), x, y)
        self.tab.call_method("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button="left", clickCount=1)
        time.sleep((0.08 + self._gaussian_noise(0, 0.02)) * self.speed_factor)
        self.tab.call_method("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left", clickCount=1)
