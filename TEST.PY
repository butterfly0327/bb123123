import re
import json
import time
import random
from typing import List, Dict, Tuple, Optional

import requests
from bs4 import BeautifulSoup

BASE = "https://www.data.go.kr"
LIST_URL = f"{BASE}/tcs/dss/selectDataSetList.do"

TARGET_COUNT = 100
PER_PAGE = 100
DTYPE = "FILE"      # FILE / API
SORT = "updtDt"

SLEEP_MIN = 1.0
SLEEP_MAX = 2.0
TIMEOUT = 20
RETRY = 3

HEADERS = {
    "User-Agent": "data-go-kr-metadata-crawler/1.0 (contact: your@email.com)",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

LINK_RE = re.compile(r'href="(/(?:en/)?data/(\d+)/(fileData|openapi)\.do)"')


# -------------------------------------------------------
# 공통 유틸
# -------------------------------------------------------

def sleep():
    time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))


def safe_get(session: requests.Session, url: str, *, params=None):
    last_err = None
    for _ in range(RETRY):
        try:
            r = session.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_err = e
            time.sleep(2)
    raise last_err


def text_or_none(el):
    return el.get_text(strip=True) if el else None


def find_label_value(soup: BeautifulSoup, label: str) -> Optional[str]:
    th = soup.find("th", string=lambda x: x and label in x)
    if th:
        td = th.find_next("td")
        if td:
            return td.get_text(strip=True)
    return None


# -------------------------------------------------------
# 1️⃣ 목록 수집
# -------------------------------------------------------

def fetch_list_html(session, page):
    params = {
        "currentPage": str(page),
        "dType": DTYPE,
        "perPage": str(PER_PAGE),
        "sort": SORT,
    }
    return safe_get(session, LIST_URL, params=params)


def extract_dataset_refs(html):
    found = LINK_RE.findall(html)
    ordered = []
    seen = set()
    for _, ds_id, kind in found:
        key = (ds_id, kind)
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


# -------------------------------------------------------
# 2️⃣ fileData 상세 파서
# -------------------------------------------------------

def parse_file_detail(ds_id: str, html: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")

    title = text_or_none(soup.select_one("h3.tit"))

    data = {
        "source": "datagokr_crawl",
        "source_id": ds_id,
        "item_type": "fileData",
        "canonical_url": f"{BASE}/data/{ds_id}/fileData.do",
        "title": title,
        "description_long": find_label_value(soup, "설명"),
        "classification": {
            "category_main": find_label_value(soup, "분류체계"),
            "provider_type": find_label_value(soup, "제공기관"),
        },
        "resources_meta": {
            "extension": find_label_value(soup, "확장자"),
            "media_type": find_label_value(soup, "매체유형"),
            "delivery_type": find_label_value(soup, "제공형태"),
        },
        "provider": {
            "organization": find_label_value(soup, "제공기관"),
            "department": find_label_value(soup, "관리부서명"),
            "phone": find_label_value(soup, "관리부서 전화번호"),
        },
        "license": {
            "scope_text": find_label_value(soup, "이용허락범위"),
        },
        "freshness": {
            "registered_at": find_label_value(soup, "등록일"),
            "updated_at": find_label_value(soup, "수정일"),
            "update_cycle": find_label_value(soup, "업데이트 주기"),
        },
        "stats": {
            "row_count": find_label_value(soup, "전체 행"),
            "download_count": find_label_value(soup, "다운로드"),
        },
        "access": {
            "cost_flag": find_label_value(soup, "비용부과유무"),
            "cost_unit": find_label_value(soup, "비용부과기준 및 단위"),
        },
        "schema": {
            "columns": parse_file_columns(soup)
        }
    }

    return data


def parse_file_columns(soup):
    columns = []
    table = soup.find("table", summary=lambda x: x and "데이터항목" in x)
    if not table:
        return []

    for row in table.find_all("tr")[1:]:
        cells = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cells) >= 3:
            columns.append({
                "name_kr": cells[0],
                "description": cells[2] if len(cells) > 2 else None,
                "data_type": cells[4] if len(cells) > 4 else None,
            })
    return columns


# -------------------------------------------------------
# 3️⃣ openAPI 상세 파서
# -------------------------------------------------------

def parse_openapi_detail(ds_id: str, html: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")

    title = text_or_none(soup.select_one("h3.tit"))

    data = {
        "source": "datagokr_crawl",
        "source_id": ds_id,
        "item_type": "openapi",
        "canonical_url": f"{BASE}/data/{ds_id}/openapi.do",
        "title": title,
        "description_long": find_label_value(soup, "설명"),
        "classification": {
            "category_main": find_label_value(soup, "분류체계"),
            "provider_type": find_label_value(soup, "제공기관"),
        },
        "resources_meta": {
            "api_type": find_label_value(soup, "API 유형"),
            "data_format": find_label_value(soup, "데이터포맷"),
            "request_url": find_label_value(soup, "요청주소"),
            "service_url": find_label_value(soup, "서비스URL"),
        },
        "provider": {
            "organization": find_label_value(soup, "제공기관"),
            "department": find_label_value(soup, "관리부서명"),
            "phone": find_label_value(soup, "관리부서 전화번호"),
        },
        "license": {
            "scope_text": find_label_value(soup, "이용허락범위"),
        },
        "freshness": {
            "registered_at": find_label_value(soup, "등록일"),
            "updated_at": find_label_value(soup, "수정일"),
        },
        "access": {
            "cost_flag": find_label_value(soup, "비용부과유무"),
            "traffic_limit_text": find_label_value(soup, "신청가능 트래픽"),
        },
        "schema": {
            "request_params": parse_openapi_table(soup, "요청변수"),
            "response_elements": parse_openapi_table(soup, "출력결과"),
        }
    }

    return data


def parse_openapi_table(soup, keyword):
    tables = soup.find_all("table")
    results = []
    for table in tables:
        if keyword in table.get_text():
            for row in table.find_all("tr")[1:]:
                cells = [c.get_text(strip=True) for c in row.find_all("td")]
                if len(cells) >= 3:
                    results.append({
                        "name_kr": cells[0],
                        "name_en": cells[1] if len(cells) > 1 else None,
                        "description": cells[-1],
                    })
    return results


# -------------------------------------------------------
# 메인 실행
# -------------------------------------------------------

def main():
    session = requests.Session()
    refs = []
    page = 1

    # 목록에서 100개 ID 확보
    while len(refs) < TARGET_COUNT:
        html = fetch_list_html(session, page)
        page_refs = extract_dataset_refs(html)
        if not page_refs:
            break
        for key in page_refs:
            if key not in refs:
                refs.append(key)
            if len(refs) >= TARGET_COUNT:
                break
        page += 1
        sleep()

    refs = refs[:TARGET_COUNT]

    # 상세 파싱
    results = []
    for ds_id, kind in refs:
        detail_url = f"{BASE}/data/{ds_id}/{kind}.do"
        html = safe_get(session, detail_url)

        if kind == "fileData":
            parsed = parse_file_detail(ds_id, html)
        else:
            parsed = parse_openapi_detail(ds_id, html)

        results.append(parsed)
        sleep()

    # 저장
    with open("datagokr_full_100.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"완료: {len(results)}건 저장")


if __name__ == "__main__":
    main()