#!/usr/bin/env python3
"""
澳大利亚签证处理时间爬虫
直接调用 immi.homeaffairs.gov.au 的内部 API 获取数据，无需 Selenium。
"""

import json
import time
import requests
from datetime import datetime


BASE_URL = "https://immi.homeaffairs.gov.au"
HEADERS = {
    "Content-Type": "application/json",
    "Referer": f"{BASE_URL}/visas/getting-a-visa/visa-processing-times/global-visa-processing-times",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
}


class VisaProcessingTimeScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    # ------------------------------------------------------------------
    # API 调用
    # ------------------------------------------------------------------

    def _post(self, path: str, payload: dict) -> dict | None:
        """发送 POST 请求，返回解析后的 JSON 数据，失败返回 None。"""
        url = BASE_URL + path
        try:
            resp = self.session.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            body = resp.json()
            if body.get("d", {}).get("success"):
                return body["d"]["data"]
            else:
                print(f"  API 返回失败: {body.get('d', {}).get('message')}")
                return None
        except requests.RequestException as e:
            print(f"  请求失败 ({url}): {e}")
            return None

    def get_visa_list(self) -> list[dict]:
        """获取所有签证及其 StreamCode 列表。"""
        data = self._post("/_layouts/15/api/GPT.aspx/GetProcessGuideVisas", {})
        if not data:
            return []
        print(f"获取到 {len(data)} 条签证/子类别条目")
        return data

    def get_processing_info(self, visa_code: str, stream_code: str) -> dict | None:
        """获取单个签证（含子类别）的处理时间信息。"""
        payload = {"gptRequest": {"VisaSubclassCode": visa_code, "StreamCode": stream_code}}
        results = self._post("/_layouts/15/api/GPT.aspx/GetProcessGuideInfo", payload)
        if not results:
            return None

        # API 可能返回多条（同一签证的所有子类别），找到匹配当前 StreamCode 的那条
        for item in results:
            if item.get("StreamCode") == stream_code:
                return item
        # 如果没有精确匹配（如 StreamCode 为空的签证），返回第一条
        return results[0] if results else None

    # ------------------------------------------------------------------
    # 数据保存
    # ------------------------------------------------------------------

    def save_to_json(self, data: list[dict], filename: str = "visa_data.json"):
        """全量覆盖写入 JSON 文件。"""
        output = {
            "last_updated": datetime.now().isoformat(),
            "source_url": f"{BASE_URL}/visas/getting-a-visa/visa-processing-times/global-visa-processing-times",
            "visa_count": len(data),
            "visas": data,
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filename}（共 {len(data)} 条）")

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------

    def run(self, max_visas: int | None = None):
        print("=" * 60)
        print("澳大利亚签证处理时间爬虫（API 直连模式）")
        print("=" * 60)

        # 1. 获取签证列表
        visa_entries = self.get_visa_list()
        if not visa_entries:
            print("未能获取签证列表，退出")
            return

        if max_visas is not None:
            # 按 VisaSubclassCode 去重计数，取前 max_visas 个签证（含其所有子类别）
            seen_codes: list[str] = []
            filtered: list[dict] = []
            for entry in visa_entries:
                code = entry["VisaSubclassCode"]
                if code not in seen_codes:
                    if len(seen_codes) >= max_visas:
                        break
                    seen_codes.append(code)
                filtered.append(entry)
            visa_entries = filtered
            print(f"将爬取前 {max_visas} 个签证（共 {len(visa_entries)} 条子类别条目）")

        # 2. 逐条查询处理时间
        all_data: list[dict] = []
        total = len(visa_entries)

        for idx, entry in enumerate(visa_entries, 1):
            visa_code = entry["VisaSubclassCode"]
            visa_text = entry["VisaSubclassText"]
            stream_code = entry.get("StreamCode", "")
            stream_text = entry.get("StreamText", "")

            label = f"{visa_text}" + (f" - {stream_text}" if stream_text else "")
            print(f"\n[{idx}/{total}] 查询: {label}")

            info = self.get_processing_info(visa_code, stream_code)

            if info:
                p50 = info.get("Percent50Text") or (
                    f"{info['Percent50']} days" if info.get("Percent50") else "N/A"
                )
                p90 = info.get("Percent90Text") or (
                    f"{info['Percent90']} days" if info.get("Percent90") else "N/A"
                )

                record = {
                    "visa_type": visa_text,
                    "visa_value": visa_code,
                    "visa_stream": stream_text if stream_text else None,
                    "processing_time_50_percent": p50,
                    "processing_time_90_percent": p90,
                    "percent_50_days": info.get("Percent50"),
                    "percent_90_days": info.get("Percent90"),
                    "query_date": datetime.now().isoformat(),
                }
                all_data.append(record)
                print(f"  ✓ 50%={p50}, 90%={p90}")

                # 增量保存
                self.save_to_json(all_data)
            else:
                print(f"  ✗ 未获取到数据")

            # 礼貌性延迟，避免过于频繁请求
            if idx < total:
                time.sleep(0.3)

        print("\n" + "=" * 60)
        print(f"爬取完成！共获取 {len(all_data)} 条签证数据")
        print("=" * 60)


if __name__ == "__main__":
    import sys

    # 使用方法:
    #   python scraper.py            # 爬取前5个签证（默认）
    #   python scraper.py 10         # 爬取前10个签证
    #   python scraper.py all        # 爬取所有签证
    max_visas = 5
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        arg = args[0]
        if arg.lower() == "all":
            max_visas = None
            print("将爬取所有签证的处理时间数据")
        else:
            try:
                max_visas = int(arg)
                print(f"将爬取前 {max_visas} 个签证的处理时间数据")
            except ValueError:
                print(f"无效的参数: {arg}")
                print("使用方法:")
                print("  python scraper.py             # 爬取前5个签证（默认）")
                print("  python scraper.py 10          # 爬取前10个签证")
                print("  python scraper.py all         # 爬取所有签证")
                sys.exit(1)

    scraper = VisaProcessingTimeScraper()
    scraper.run(max_visas=max_visas)
