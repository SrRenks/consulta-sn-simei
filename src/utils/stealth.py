import os

class StealthToolkit:

    BASE_DIR = os.path.join(os.path.dirname(__file__), "../../resources")

    PATCHES = {
        "base": "stealth_injection.js",
        "canvas": "spoof_canvas_fingerprint.js",
        "webgl": "spoof_webgl_precision.js",
        "toString": "override_function_toString.js",
        "plugins_mimetypes": "mock_navigator_plugins_and_mimetypes.js",
        "chrome_runtime": "mock_chrome_runtime.js",
        "webrtc": "mock_webrtc.js",
        "audio": "mock_audio_fingerprint.js",
        "connection": "mock_navigator_connection.js",
        "media": "mock_media_devices.js",
        "navigator_props": "navigator_properties.js",
        "screen_props": "screen_properties.js",
        "webgl_spoof": "webgl_spoof.js",
        "canvas_noise": "canvas_noise.js",
        "audio_oscillator": "audio_oscillator_patch.js",
        "permissions_query": "permissions_query_patch.js",
        "rtc_peerconnection": "rtc_peerconnection_patch.js",
        "intl_datetime": "intl_datetime_patch.js",
    }

    LEVELS = {
        "low": ["base", "canvas", "toString"],
        "normal": ["base", "canvas", "webgl", "toString", "plugins_mimetypes", "chrome_runtime"],
        "strict": list(PATCHES.keys())
    }


    def __init__(self, tab, level="normal", custom_methods=None):
        self.tab = tab
        self.level = level
        self.custom_methods = custom_methods or []

    def apply(self):
        if self.level == "custom":
            patches = self.custom_methods
        else:
            patches = self.LEVELS.get(self.level)
            if not patches:
                raise ValueError(f"invalid stealth level: {self.level}")

        for patch_key in patches:
            file_name = self.PATCHES.get(patch_key)
            if not file_name:
                continue

            script_path = os.path.join(self.BASE_DIR, file_name)
            self._inject_script(script_path)

    def _inject_script(self, path):
        with open(path, "r", encoding="utf-8") as f:
            js_code = f.read()
        self.tab.call_method("Runtime.evaluate", expression=js_code)
