# README — Kaggle Datasets 메타데이터 수집 (API)

## 목표 (2차 MVP 범위)
- Kaggle의 dataset catalog 메타(M1~M13)만 수집한다.
- 데이터 파일 다운로드/분석은 하지 않는다.

## 수집 방식 (선택): API (공식 Kaggle API/CLI)
- 크롤링은 ToS/정책 리스크가 커서 PoC에서도 제외한다.

## 수집 대상 (내부 스키마)
- M1: source="kaggle", source_id(=dataset ref: owner/dataset), canonical_url
- M2: title
- M3: subtitle/description(제공되는 범위)
- M4: topics/categories(제공되는 범위)
- M5: file list 메타(파일명, 확장자, 파일 크기) ※ 다운로드 없음
- M6: license_name
- M7: owner/author
- M8: tags/keywords
- M9: lastUpdated/versions(제공되는 범위)
- M10: (제한) Kaggle은 “스키마/클래스 구조”를 표준 API로 항상 제공하지 않으므로 기본은 비워둔다.
- M11: dataset size(표기되는 총 크기), file sizes(가능하면)
- M12: isPrivate / 접근제약(표기되는 범위)
- M13: downloadCount, voteCount, usabilityRating(표기되는 범위)

## 사전 준비(인증)
1) Kaggle 계정 생성/로그인
2) Settings에서 API Token(kaggle.json) 발급
3) 서버/컨테이너에 안전하게 주입
- ~/.kaggle/kaggle.json 또는 환경변수/시크릿으로 관리

## API/CLI 호출 설계(메타만)
- 목록/검색:
  - CLI: kaggle datasets list (검색어/정렬/페이지네이션)
  - Python: KaggleApi().dataset_list(...)
- 상세(메타):
  - CLI: kaggle datasets view -d {owner/dataset}  (메타 확인)
  - 파일목록(메타):
    - CLI: kaggle datasets files {owner/dataset}

※ PoC에서는 “다운로드 명령”을 사용하지 않는다.

## 증분(이어 긁기) 설계
- upsert_key = (source, source_id)
- checkpoint = lastUpdated(가능하면) + page cursor(페이지)
- 전략:
  1) 주기적으로 “최근 업데이트 정렬”로 목록을 가져와서 lastUpdated 기준으로 업데이트 대상만 상세 조회
  2) 전체 스캔이 필요하면, page를 순회하며 “마지막 성공 page”를 checkpoint로 저장

## 정책/리스크
- HTML 크롤링은 하지 않는다(약관/차단 리스크).
- API 요청도 과다하면 429가 발생할 수 있으니:
  - QPS 제한(예: 1~2 rps부터 시작)
  - 429 백오프/재시도
  - 에러율 모니터링

## PoC 성공 기준(최소)
- 키워드 기반으로 500개 메타 수집(JSONL)
- 각 레코드에서 M1~M3, M6~M9, M11, M13을 80% 이상 채움
- 파일목록(메타)까지 가져와 M5를 “확장자/파일크기” 형태로 채운다(가능한 범위)

## 출력 포맷(JSONL 예시)
{
  "source":"kaggle",
  "source_id":"zynicide/wine-reviews",
  "canonical_url":"https://www.kaggle.com/datasets/zynicide/wine-reviews",
  "title":"Wine Reviews",
  "license_name":"CC0: Public Domain",
  "updated_at":"2024-10-01T00:00:00Z",
  "stats":{"dataset_size_bytes":123456789},
  "distributions":[{"format":"csv","file_name":"winemag-data-130k-v2.csv","size_bytes":...}],
  "signals":{"downloads":123456,"votes":7890,"usability_rating":0.82}
}