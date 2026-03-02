# README — Figshare 메타데이터 수집 (API)

## 목표 (2차 MVP 범위)
- Figshare 공개 레코드(articles)의 메타(M1~M13)만 수집한다.
- 파일 다운로드/분석 없음(파일 목록/크기 메타만)

## 수집 방식 (선택): API (Figshare Public API)

## 수집 대상(M1~M13)
- M1: source="figshare", source_id(article_id), canonical_url
- M2: title
- M3: description
- M4: categories/subjects(제공 범위)
- M5: files[].name, files[].size, files[].download_url(저장만)
- M6: license.name/license.url
- M7: authors[], publisher(있으면)
- M8: tags[], keywords[]
- M9: published_date, modified_date
- M10: (제한) 스키마/컬럼 구조 기본 비움
- M11: total size(합), file count
- M12: visibility/public 여부, embargo(있으면)
- M13: views/downloads/statistics(제공 시)

## API 호출(개념)
- Search/List:
  - GET https://api.figshare.com/v2/articles?search_for={query}&page={p}&page_size={k}
- Detail:
  - GET https://api.figshare.com/v2/articles/{article_id}
- Files:
  - 보통 detail에 files 링크가 포함되며, files endpoint로 상세 조회

## 증분(이어 긁기)
- upsert_key=(source, article_id)
- checkpoint=max(modified_date)
- 다음 실행 시 modified_date 기준으로 변경된 레코드만 상세 재조회

## PoC 성공 기준
- 키워드 3개 * 200개씩 수집
- M1~M9/M11 90% 채움
- 파일목록 메타(M5) 포함 저장