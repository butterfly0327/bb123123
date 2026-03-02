# README — Hugging Face Datasets 메타데이터 수집 (API)

## 목표 (2차 MVP 범위)
- Hugging Face Datasets Hub에서 “데이터셋 메타데이터(M1~M13)”를 수집한다.
- 데이터 파일 다운로드/로컬 분석은 하지 않는다.
- 스키마/스플릿/사이즈는 “Dataset Viewer API가 제공하는 메타”만 수집한다.

## 수집 방식 (선택): API
- Hub API: 카탈로그(목록/검색) + 인기지표(다운로드/좋아요) + 태그/라이선스/업데이트
- Dataset Viewer API: /info로 features, splits, size(메타) 수집

## 수집 대상 (내부 스키마)
- M1: source="huggingface", source_id(=repo_id), canonical_url
- M2: title
- M3: description (dataset card text), citation, homepage
- M4: tags/tasks/modalities (Hub 태그 기반)
- M5: distributions (가능하면 repo 파일 확장자/리소스 링크 메타)
- M6: license_name/license_url
- M7: publisher/owner/organization
- M8: tags, keywords, languages
- M9: created_at(있으면), updated_at(lastModified), version(있으면)
- M10: schema.features, schema.splits(이름/row/bytes 제공시)
- M11: num_rows/num_examples, dataset_size_bytes, download_size_bytes
- M12: access.visibility(public/gated/private), requires_login
- M13: signals.downloads, signals.likes, (가능하면) 최근 활동 지표

## API 엔드포인트(예시)
1) Hub (목록/검색)
- 권장: huggingface_hub 라이브러리(HfApi.list_datasets) 사용
- 또는 OpenAPI 스펙 기반으로 REST 호출(문서에서 openapi.json 제공)

2) Dataset Viewer (/info)
- GET https://datasets-server.huggingface.co/info?dataset={repo_id}&config={config_name}
- 응답의 dataset_info에서:
  - description/citation/homepage/license  -> M3/M6
  - features                               -> M10
  - splits.{split}.num_examples/num_bytes  -> M10/M11
  - download_size, dataset_size            -> M11

## 인증/레이트리밋
- 공개 데이터는 무토큰 호출도 가능하지만 429가 발생할 수 있음.
- 토큰을 쓰면 private/gated 접근 및 안정성이 좋아짐.
- 구현 필수: (1) 429 처리, (2) 지수 백오프, (3) 요청 동시성 제한.

## 증분(이어 긁기) 설계
### 핵심 키
- upsert_key = (source, source_id)

### 체크포인트
- checkpoint = lastModified(또는 수집 시각) + pagination cursor(사용 시)
- 전략:
  1) 1차: list_datasets로 목록을 페이지 단위로 가져오며 lastModified 저장
  2) 2차: lastModified가 이전 수집 시점보다 큰 repo만 /info를 호출

### 멱등성
- 같은 dataset을 여러 번 받아도 DB에서는 upsert로 덮어쓰기(최신 updated_at 기준)

## PoC 성공 기준(최소)
- 키워드 3개(예: “sentiment”, “weather”, “anomaly”)로 각 50개씩 수집
- 각 레코드에 대해 M1~M9, M12~M13은 90% 이상 채움
- /info 호출 가능한 레코드는 M10/M11까지 채워서 JSONL 출력

## 출력 포맷(JSONL 예시)
{
  "source":"huggingface",
  "source_id":"ibm/duorc",
  "canonical_url":"https://huggingface.co/datasets/ibm/duorc",
  "title":"duorc",
  "description_long":"...",
  "tags":["question-answering", "..."],
  "license_name":"...",
  "updated_at":"2025-01-01T00:00:00Z",
  "schema":{"features":[{"name":"plot","dtype":"string"}], "splits":{"train":{"num_examples":60721,"num_bytes":248966361}}},
  "stats":{"dataset_size_bytes":356348071,"download_size_bytes":21001846},
  "access":{"visibility":"public","requires_login":false},
  "signals":{"downloads":12345,"likes":321}
}