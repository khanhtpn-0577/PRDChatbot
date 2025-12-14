import json
import re

def extract_json_objects(text: str):
    """
    Trích xuất tất cả JSON objects trong một chuỗi.
    Trả về list Python dict.
    """
    json_blocks = re.findall(r"\{.*?\}", text, flags=re.DOTALL)
    results = []

    for block in json_blocks:
        try:
            results.append(json.loads(block))
        except Exception:
            continue  # bỏ qua block lỗi

    return results


def parse_prd_json(text: str):
    """
    Trường hợp LLM trả JSON dạng mảng [ {...}, {...} ]
    hoặc nhiều mảng chồng nhau → parse hết.
    """
    text = text.strip()

    try:
        # TH1: full JSON array đúng chuẩn
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except:
        pass

    # TH2: trích từng object trong text
    objs = extract_json_objects(text)
    return objs if objs else None
