# README — data.gov Catalog(미국) 메타데이터 수집 (API, CKAN)

## 목표 (2차 MVP 범위)
- data.gov의 “카탈로그 메타(실데이터 아님)”만 수집한다.
- 데이터 파일 다운로드/분석 없음

## 수집 방식 (선택): API (CKAN Action API via api.gsa.gov)

## 근거
- data.gov 카탈로그는 CKAN 기반이며 API는 메타데이터만 제공한다.
- API Key를 x-api-key 헤더로 전달해야 한다.

## 수집 대상(M1~M13)
- M1: source="ckan_datagov", source_id(ckan package id/name), canonical_url
- M2: title
- M3: notes/description
- M4: groups, themes(있으면)
- M5: resources[].url, resources[].format, resources[].mimetype
- M6: license_title/license_url
- M7: organization.title, author/maintainer(공개된 범위)
- M8: tags[].name
- M9: metadata_created, metadata_modified
- M10: (제한) 스키마/컬럼 구조는 표준 제공되지 않으므로 기본 비움
- M11: resources[].size(제공 시), 리소스 개수
- M12: private(있으면), 접근 관련 메타
- M13: (선택) tracking_summary 제공 시 저장, 없으면 비움

## API 엔드포인트
- Base: https://api.gsa.gov/technology/datagov/v3/
- package_search:
  - GET /action/package_search?rows=100&start=0
- package_show:
  - GET /action/package_show?id={package_id}
- 인증:
  - Header: x-api-key: {API_KEY}
  - 샘플은 api_key=DEMO_KEY 형태로도 안내됨(운영에서는 헤더 권장)

## 페이지네이션
- package_search는 start/rows 기반
- checkpoint:
  - start offset
  - 또는 metadata_modified 기준 증분(fq 필터 사용)

## 증분(이어 긁기)
- upsert_key=(source, package_id)
- checkpoint=max(metadata_modified)
- 다음 실행 시:
  - fq=metadata_modified:[{checkpoint} TO *] 형태로 최신만 수집(가능하면)

## PoC 성공 기준
- package_search로 1만 건 이상 목록 수집 가능 확인
- 상위 200개는 package_show까지 호출해 M5/M6/M7 확정

## 출력 예시(JSONL)
{
  "source":"ckan_datagov",
  "source_id":"abcd-1234-...",
  "canonical_url":"https://catalog.data.gov/dataset/....",
  "title":"...",
  "tags":["climate","transportation"],
  "license_name":"...",
  "updated_at":"2025-01-01T00:00:00Z",
  "distributions":[{"format":"CSV","resource_url":"https://..."}]
}