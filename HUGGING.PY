#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VSCode에서 그냥 실행 버튼만 눌러도 동작하도록 만든 Hugging Face Datasets 메타데이터 수집 스크립트.
(원본 구조 유지 + 에러 메시지 정제 추가 버전)
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =========================
# 실행 설정
# =========================
TARGET_COUNT = 100
HUB_FETCH_LIMIT = 160
MAX_WORKERS = 4
MAX_RETRIES = 6
TIMEOUT_SECONDS = 30

USE_KEYWORD_MODE = False
KEYWORDS = ["sentiment", "weather", "anomaly"]
PER_KEYWORD_LIMIT = 60

HF_BASE = "https://huggingface.co"
VIEWER_BASE = "https://datasets-server.huggingface.co"
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN") or ""
USER_AGENT = "hf-datasets-metadata-poc/1.2"

BASE_DIR = Path(__file__).resolve().parent
OUT_JSON = BASE_DIR / "hf_datasets_metadata_100.json"
OUT_JSONL = BASE_DIR / "hf_datasets_metadata_100.jsonl"


# =========================
# 🔒 에러 메시지 정제 (추가된 부분)
# =========================

def sanitize_error_message(msg: Optional[str]) -> Optional[str]:
    """
    GitHub secret scanning 방지용:
    - presigned S3 URL 제거
    - X-Amz-* 파라미터 제거
    - AKIA 패턴 제거
    - 긴 hex 서명값 제거
    """
    if not isinstance(msg, str):
        return msg

    msg = re.sub(r'https://[^\s"]+', '[URL_REMOVED]', msg)
    msg = re.sub(r'X-Amz-[^&"\s]+', '[AWS_PARAM]', msg)
    msg = re.sub(r'AKIA[0-9A-Z]{16}', 'AKIA****************', msg)
    msg = re.sub(r'[0-9a-f]{32,}', '[HEX_REMOVED]', msg)

    return msg


# =========================
# 공통 유틸
# =========================

def log(message: str) -> None:
    print(message, flush=True)


def dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def backoff_sleep(attempt: int, retry_after: Optional[str] = None) -> None:
    if retry_after:
        try:
            time.sleep(float(retry_after))
            return
        except Exception:
            pass
    delay = min(30.0, 0.8 * (2 ** attempt))
    delay *= 0.5 + random.random()
    time.sleep(delay)


def build_headers() -> Dict[str, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"
    return headers


def http_get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = MAX_RETRIES,
    timeout: int = TIMEOUT_SECONDS,
) -> Tuple[Optional[Any], int, Optional[str]]:

    headers = build_headers()
    final_url = url
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        final_url = f"{url}?{query}"

    for attempt in range(max_retries):
        req = urllib.request.Request(final_url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = getattr(resp, "status", 200)
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw), status, None

        except urllib.error.HTTPError as e:
            status = e.code
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass

            clean_body = sanitize_error_message(body)

            if status in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                backoff_sleep(attempt, e.headers.get("Retry-After"))
                continue

            return None, status, f"http_{status}: {clean_body}"

        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                backoff_sleep(attempt)
                continue
            return None, -1, sanitize_error_message(f"url_error: {e}")

        except Exception as e:
            if attempt < max_retries - 1:
                backoff_sleep(attempt)
                continue
            return None, -1, sanitize_error_message(f"unexpected_error: {e}")

    return None, -1, "max_retries_exceeded"


# =========================
# Hub API 관련
# =========================

def fetch_hub_datasets_top(limit: int) -> List[Dict[str, Any]]:
    data, status, err = http_get_json(
        f"{HF_BASE}/api/datasets",
        params={"sort": "downloads", "limit": limit, "full": "true"},
    )
    if err:
        raise RuntimeError(err)
    return data if isinstance(data, list) else []


def is_collectable_public_dataset(item: Dict[str, Any]) -> bool:
    if item.get("disabled"):
        return False
    if item.get("private"):
        return False
    if item.get("gated") not in (False, None, "false", "False", ""):
        return False
    return True


# =========================
# Viewer API 관련
# =========================

def fetch_viewer_configs(repo_id: str):
    errors = []
    data, status, err = http_get_json(
        f"{VIEWER_BASE}/splits",
        params={"dataset": repo_id},
    )
    if err:
        errors.append({
            "where": "viewer_splits",
            "status": status,
            "error": sanitize_error_message(err)
        })
        return [], None, errors

    splits = data.get("splits") if isinstance(data, dict) else None
    configs = sorted({s.get("config") for s in splits if isinstance(s, dict) and s.get("config")}) if splits else []
    return configs, (configs[0] if configs else None), errors


def fetch_viewer_info(repo_id: str, config_name: str):
    errors = []
    data, status, err = http_get_json(
        f"{VIEWER_BASE}/info",
        params={"dataset": repo_id, "config": config_name},
    )
    if err:
        errors.append({
            "where": "viewer_info",
            "status": status,
            "error": sanitize_error_message(err)
        })
        return None, errors

    return data.get("dataset_info") if isinstance(data, dict) else None, errors


# =========================
# 간단 수집 로직 (원본 유지)
# =========================

def collect_one(item: Dict[str, Any]) -> Dict[str, Any]:
    repo_id = item.get("id")

    record = {
        "source": "huggingface",
        "source_id": repo_id,
        "canonical_url": f"{HF_BASE}/datasets/{repo_id}",
        "title": repo_id.split("/")[-1],
        "schema": {"features": [], "splits": {}},
        "stats": {},
        "_errors": [],
    }

    configs, selected, errors = fetch_viewer_configs(repo_id)
    record["_errors"].extend(errors)

    if selected:
        info, info_errors = fetch_viewer_info(repo_id, selected)
        record["_errors"].extend(info_errors)

        if info:
            record["schema"]["features"] = info.get("features") or []
            record["schema"]["splits"] = info.get("splits") or {}
            record["stats"]["dataset_size_bytes"] = info.get("dataset_size")
            record["stats"]["download_size_bytes"] = info.get("download_size")

    return record


# =========================
# main
# =========================

def main():
    log("Dataset metadata 수집 시작")

    hub_items = [
        x for x in fetch_hub_datasets_top(HUB_FETCH_LIMIT)
        if is_collectable_public_dataset(x)
    ][:TARGET_COUNT]

    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(collect_one, item) for item in hub_items]

        for i, future in enumerate(as_completed(futures), 1):
            record = future.result()
            results.append(record)
            log(f"[{i:03d}/{TARGET_COUNT:03d}] {record['source_id']}")

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    log("완료")


if __name__ == "__main__":
    main()