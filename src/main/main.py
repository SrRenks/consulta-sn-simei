from src.utils import SnSimei, ChromeManager
from typing import List, Dict
import concurrent.futures
from tqdm import tqdm
import pandas as pd
import argparse
import re


class SNSimeiManager:
    def __init__(self, cnpj_list: List[str]) -> None:
        self.cnpj_list = []
        invalid = []

        for raw_cnpj in cnpj_list:
            cnpj = self._normalize(cnpj=str(raw_cnpj))
            if self._is_valid_cnpj(cnpj):
                self.cnpj_list.append(cnpj)
            else:
                invalid.append(raw_cnpj)

        if invalid:
            raise ValueError(f"Invalid CNPJs: {', '.join(map(str, invalid))}")

    def _normalize(self, cnpj: str) -> str:
        return re.sub(r'\D', '', cnpj)

    def _is_valid_cnpj(self, cnpj: str) -> bool:
        if len(cnpj) != 14 or len(set(cnpj)) == 1:
            return False
        def calc_digit(numbers: str, weights: list[int]) -> str:
            total = sum(int(n) * w for n, w in zip(numbers, weights))
            rest = total % 11
            return str(0 if rest < 2 else 11 - rest)

        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights2 = [6] + weights1

        base, verifiers = cnpj[:12], cnpj[12:]
        dv = calc_digit(base, weights1) + calc_digit(base + calc_digit(base, weights1), weights2)
        return dv == verifiers

    def __extract_cnpj_info(self, cnpj, port: int) -> Dict[str, str]:
        chrome_manager = ChromeManager(speed_threshold=0.8, remote_debugging_port=port)
        chrome_manager.launch()
        try:
            scraper = SnSimei(chrome_manager)
            return scraper.get_cnpj_info(cnpj)
        except Exception as e:
            raise e
        finally:
            chrome_manager.close()

    def extract_cnpj_list_info(self) -> List[Dict[str, str]]:
        base_port = 9222
        cnpj_port_tuples = list(zip(cnpj_list, range(base_port, base_port + len(cnpj_list))))
        with tqdm(total=len(cnpj_port_tuples), leave=True, ascii=' ━', colour='GREEN', dynamic_ncols=True, unit="user",
                    desc="extracting SN/SIMEI cnpj status") as pbar:

            data = pd.DataFrame()
            with concurrent.futures.ThreadPoolExecutor(3) as executor:
                futures = [executor.submit(self.__extract_cnpj_info, cnpj, port) for cnpj, port in cnpj_port_tuples]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    df_result = pd.DataFrame([result])
                    data = pd.concat([data, df_result], ignore_index=True)
                    pbar.update(1)

            return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="input file path (xlsx)")
    parser.add_argument("-o", "--output", required=True, help="output file path (xlsx)")

    args = parser.parse_args()
    cnpj_list = pd.read_excel(args.input)["CNPJ"].to_list()
    manager = SNSimeiManager(cnpj_list)
    data = manager.extract_cnpj_list_info()
    data.to_excel(args.output)
