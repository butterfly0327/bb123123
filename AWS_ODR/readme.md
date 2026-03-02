# README — AWS Open Data Registry 메타데이터 수집 (GitHub Repo 기반, API)

## 목표 (2차 MVP 범위)
- AWS Open Data Registry의 “레지스트리 메타(YAML/JSON)”를 수집한다.
- 실제 데이터(S3 객체 등) 다운로드/분석 없음

## 수집 방식 (선택): API (Repo 파일 파싱)
- Git clone 또는 GitHub Contents API로 datasets/*.yaml 파일을 가져와 파싱

## 수집 대상(M1~M13)
- M1: source="aws_odr", source_id(레지스트리 key/파일명), canonical_url(registry page)
- M2: Name
- M3: Description
- M4: Tags, Themes
- M5: Resources(S3 bucket, region, ARN, access pattern)
- M6: License(명시된 경우)
- M7: ManagedBy/Contact
- M8: Tags
- M9: UpdateFrequency + Git commit time(갱신 시각)
- M10: (제한) 스키마/컬럼 구조 없음
- M11: (대부분 없음) 레지스트리 파일 자체에 size는 잘 없음
- M12: 접근 제약(공개/요금/요청 조건이 명시된 경우)
- M13: 커뮤니티 지표 없음(기본 비움)

## 수집 방법
1) Repo: https://github.com/awslabs/open-data-registry
2) datasets/ 디렉토리 내 YAML을 모두 파싱
3) 내부 표준 스키마로 매핑 후 DB upsert

## 증분(이어 긁기)
- checkpoint = git commit SHA(또는 마지막 커밋 timestamp)
- 다음 실행 시:
  - 변경된 파일만(diff) 파싱하여 업데이트

## PoC 성공 기준
- YAML 파싱으로 100% 레코드 생성
- 각 레코드에서 M1~M9, M12 최소 채움