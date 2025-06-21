import vt
import os
from dotenv import load_dotenv

load_dotenv()

client = vt.Client(os.getenv("VIRUSTOTAL_API_KEY"))


def extract_summary(data: dict) -> str:
    summary = data.get("attributes", {}).get("stats", {})
    return ", ".join(f"{k}: {v}" for k, v in summary.items())


def url_scan_result(url):
    print("reached url_scan_result")
    analysis_url =client.scan_url(url, wait_for_completion=True)
    dct1 = analysis_url.to_dict()
    print(dct1)
    result1 = extract_summary(dct1)
    print(result1)
    client.close()
    return result1


def file_scan_result(file):
    print("reached file_scan_result")
    analysis_file =client.scan_file(file, wait_for_completion=True)
    dct2 = analysis_file.to_dict()
    print(dct2)
    result2 = extract_summary(dct2)
    print(result2)
    client.close()
    return result2
