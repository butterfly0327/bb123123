# README — Zenodo 메타데이터 수집 (API)

## 목표 (2차 MVP 범위)
- Zenodo 레코드(데이터셋/리포트/소프트웨어 등) 중 “데이터셋 성격” 레코드의 메타(M1~M13) 수집
- 데이터 파일 다운로드/분석 없음 (파일 목록/용량 메타만)

## 수집 방식 (선택): API (Zenodo REST API)

## 수집 대상 (내부 스키마)
- M1: source="zenodo", source_id(record id 또는 DOI), canonical_url
- M2: metadata.title
- M3: metadata.description
- M4: communities/subjects(제공되는 범위)
- M5: files[].key, files[].size, files[].checksum, (format 추정은 확장자 기반)
- M6: metadata.license.id/name
- M7: metadata.creators[], metadata.publisher
- M8: metadata.keywords[]
- M9: created/updated/published, metadata.publication_date, metadata.version
- M10: (제한) 스키마/컬럼 구조는 표준 제공되지 않으므로 기본 비움
- M11: total file size(합), 파일 수
- M12: access_right(open/embargoed/restricted), embargo_date(있으면)
- M13: stats(views/downloads 제공 시)

## API 호출(개념)
- Search:
  - GET https://zenodo.org/api/records?q={query}&page={n}&size={k}
- Detail:
  - GET https://zenodo.org/api/records/{record_id}

## 레이트리밋/운영 주의
- Zenodo는 레이트리밋이 존재하므로(게스트/인증 분리) 429 백오프 필수
- 동시성 제한 + 재시도 + 실패 큐(DLQ) 사용

## 증분(이어 긁기)
- upsert_key = (source, record_id 또는 DOI)
- checkpoint = max(updated)
- 전략:
  - updated 시간 기준으로 “updated > checkpoint”인 레코드만 재수집

## PoC 성공 기준
- 키워드 5개로 각 100개 레코드 메타 수집
- M1~M9, M11, M12 90% 이상 채움
- 파일목록 메타(M5) 포함 저장

## 출력 예시(JSONL)
{
  "source":"zenodo",
  "source_id":"1234567",
  "canonical_url":"https://zenodo.org/records/1234567",
  "title":"...",
  "license_name":"cc-by-4.0",
  "distributions":[{"file_name":"data.csv","size_bytes":1234}],
  "access":{"visibility":"open"}
}