# README — data.europa.eu 메타데이터 수집 (API, CKAN + MQA)

## 목표 (2차 MVP 범위)
- EU 포털의 카탈로그 메타(M1~M13)를 수집한다.
- 실데이터 다운로드/분석 없음
- 가능하면 “MQA 품질 지표(사이트 제공)”를 M13으로 포함

## 수집 방식 (선택): API
- 1) CKAN Read-only API(패키지 검색/상세)
- 2) MQA 리포트/지표가 제공되는 경우 품질지표를 추가 수집(M13)

## 수집 대상(M1~M13)
- M1: source="ckan_edp", source_id(ckan id/name), canonical_url
- M2: title
- M3: description/notes
- M4: themes/subjects/groups(있으면)
- M5: distributions(resources) - format, access_url/download_url(링크만 저장)
- M6: license
- M7: publisher/organization
- M8: keywords/tags, language(있으면)
- M9: issued/modified/metadata_modified
- M10: (제한) 스키마/컬럼 구조 기본 비움
- M11: byteSize/size(제공 시), distributions 개수
- M12: access rights(있으면)
- M13: MQA 품질지표(가능하면), views/downloads(제공 시)

## API 엔드포인트(검증 절차)
1) CKAN action endpoint 확인
- 보통: {portal_base}/data/api/3/action/status_show 로 확인
- status_show가 success=true를 반환하면 CKAN action API로 수집 가능

2) 주요 액션
- package_search (목록)
- package_show (상세)

3) MQA 리포트(가능한 경우)
- 문서에 안내된 MQA report 다운로드 URL 패턴을 사용
- MQA 점수/항목을 M13.quality_score로 저장

## 페이지네이션/증분
- start/rows 또는 cursor(포털 구현에 따라)
- checkpoint=max(metadata_modified)
- 다음 실행 시 metadata_modified 기준으로 최신만 재수집

## PoC 성공 기준
- package_search로 5만 건 이상 수집 가능 확인
- 상위 500개에 대해 package_show로 상세 메타(M5/M6/M7) 채우기
- MQA가 가능하면 100개만 추가 수집하여 품질지표 연동 확인