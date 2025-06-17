from src.utils import HumanMouseMover, ChromeManager
from bs4 import BeautifulSoup
from typing import Dict
import random
import time

class SnSimei:
    def __init__(self, chrome_manager: ChromeManager) -> None:
        self.chrome_manager = chrome_manager
        self.browser = chrome_manager.browser
        self.tab = chrome_manager.tab
        self.human = chrome_manager.human
        self.mouse_mover = None

    def get_info_label_based(self, soup: str, label: str) -> str:
        info = soup.find(string=lambda text: label in text)
        return info.find_next('span').text.strip()

    def get_cnpj_info(self, cnpj: str) -> Dict[str, str]:
        self.tab.call_method("Page.enable")
        self.tab.call_method("DOM.enable")
        self.tab.call_method("Runtime.enable")
        self.tab.call_method("Input.setIgnoreInputEvents", ignore=False)

        self.mouse_mover = HumanMouseMover(self.tab)
        self.mouse_mover.start()

        self.tab.call_method("Page.navigate", url="https://consopt.www8.receita.fazenda.gov.br/consultaoptantes")
        self.human.wait_for_pageload()
        self.human.scroll_page()

        self.tab.call_method("Runtime.evaluate", expression="document.querySelector('#Cnpj').scrollIntoView();")
        time.sleep(0.6 + random.gauss(0, 0.1))

        input_box = self.tab.call_method("Runtime.evaluate", expression="""
            (() => {
                const rect = document.querySelector("#Cnpj").getBoundingClientRect();
                return {x: rect.left + rect.width / 2, y: rect.top + rect.height / 2};
            })();
        """, returnByValue=True)["result"]["value"]

        self.mouse_mover.stop()
        self.human.click(input_box["x"], input_box["y"])
        time.sleep(1.1 + random.gauss(0, 0.2))

        self.human.type_text(''.join(char for char in str(cnpj) if char.isdigit()))
        time.sleep(0.8 + random.gauss(0, 0.1))

        btn_box = self.tab.call_method("Runtime.evaluate", expression="""
            (() => {
                const rect = document.querySelector("button.btn-verde.h-captcha").getBoundingClientRect();
                return {x: rect.left + rect.width / 2, y: rect.top + rect.height / 2};
            })();
        """, returnByValue=True)["result"]["value"]

        prev_html = self.tab.call_method("Runtime.evaluate", expression="document.documentElement.outerHTML", returnByValue=True)["result"]["value"]

        start = time.time()
        self.human.click(btn_box["x"], btn_box["y"])
        time.sleep(self.human._hesitation_curve(time.time() - start))

        new_html = prev_html
        start_time = time.time()
        timeout = 15

        while new_html == prev_html:
            time.sleep(0.1)
            new_html = self.tab.call_method("Runtime.evaluate", expression="document.documentElement.outerHTML", returnByValue=True)["result"]["value"]
            if time.time() - start_time > timeout:
                break

        self.mouse_mover.stop()
        self.chrome_manager.close()

        soup = BeautifulSoup(new_html, "html.parser")
        msg = has.get_text(strip=True) if (has := soup.find("span", {"class": "text-danger field-validation-error"})) else ""
        if msg:
            return {"CNPJ": cnpj, "Exception": msg}
        labels = ["CNPJ", "Situação no Simples Nacional", "Nome Empresarial", "Situação no SIMEI"]
        info_dict = {label: "" for label in labels}
        info_dict = {label: self.get_info_label_based(soup, label) for label in info_dict}
        return info_dict
