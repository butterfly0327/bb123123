# README — Harvard Dataverse 메타데이터 수집 (API)

## 목표 (2차 MVP 범위)
- Harvard Dataverse의 공개 dataset 메타(M1~M13)를 수집한다.
- 데이터 파일 다운로드/분석 없음(파일 목록/크기 메타는 API가 제공하면 수집)

## 수집 방식 (선택): API (Dataverse Search API + Native API)

## 수집 대상(M1~M13)
- M1: source="dataverse_harvard", source_id(persistentId/doi), canonical_url
- M2: title
- M3: description/abstract
- M4: subjects/keywords(제공 범위)
- M5: files metadata(제공 시: 파일명/크기/형식)
- M6: license/terms(제공 시)
- M7: authors/contacts(공개 범위)
- M8: keywords/language(제공 시)
- M9: publicationDate, lastUpdateTime(제공 시)
- M10: (제한) 스키마/컬럼 구조 기본 비움
- M11: file count/total size(제공 시)
- M12: restricted/permission(제공 시)
- M13: views/downloads(기본은 비움: 인스턴스 설정에 따름)

## API 호출(개념)
1) Search API (목록)
- GET https://dataverse.harvard.edu/api/search?q={query}&type=dataset&per_page={k}&start={offset}

2) Native API (상세)
- persistentId를 이용해 상세 메타 획득:
  - GET https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId={doi}

## 증분(이어 긁기)
- upsert_key=(source, persistentId)
- checkpoint:
  - search 결과의 “publication date” 또는 “last update time”이 제공되면 max값 저장
  - 제공되지 않으면 “최근 정렬 + offset” 기반으로 최신 영역만 반복 수집

## PoC 성공 기준
- 검색어 5개로 각 200개 dataset 수집
- 상세 API를 100개에 대해 호출하여 M3/M7/M9 채움