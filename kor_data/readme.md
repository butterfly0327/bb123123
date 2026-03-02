# README-03 — 공공데이터포털(data.go.kr) 메타데이터 수집 (크롤링)

## 목표 (2차 MVP 범위)
- data.go.kr 내 “파일데이터 목록 / 오픈API 목록”의 카탈로그 메타(M1~M13)를 **HTML 크롤링만으로** 수집한다.
- 공식 OpenAPI, 메타파일, schema.org/DCAT 문서 본문 호출은 사용하지 않는다.
- 개별 원천 데이터 파일은 다운로드/분석하지 않는다.
- 즉, **목록 페이지 + 상세 페이지에 실제로 노출된 메타정보만** 저장한다.

## 수집 방식 (선택): 크롤링
- 1차 진입점(목록 페이지)
  - `https://www.data.go.kr/tcs/dss/selectDataSetList.do`
- 2차 상세 페이지
  - 파일데이터 상세: `https://www.data.go.kr/data/{data_id}/fileData.do`
  - 오픈API 상세: `https://www.data.go.kr/data/{data_id}/openapi.do`

### 수집 원칙
- 목록 페이지에서 detail URL을 수집하고,
- detail URL 유형에 따라 `fileData.do` / `openapi.do` 파서를 분기한다.
- 버튼/링크로 노출되는 `schema.org`, `DCAT`, `참고문서`, `요청주소`, `서비스URL` 등은 **링크 문자열만** 메타로 저장한다.
- 링크 대상 문서를 별도로 호출/파싱하지 않는다.

## 수집 대상 (내부 스키마)

### M1: 식별자 & 랜딩 URL
- `source = "datagokr_crawl"`
- `source_id = data_id`  
  - 상세 URL `/data/{data_id}/fileData.do` 또는 `/data/{data_id}/openapi.do`에서 추출
- `canonical_url`
- `item_type`
  - `fileData`
  - `openapi`

### M2: 제목
- 목록 카드 제목
- 상세 페이지 메인 제목
- 예:
  - `국민건강보험공단_보건소정보`
  - `지식재산처_표준특허 통계 정보제공 서비스`

### M3: 설명/문서
- 목록 카드의 본문 요약 설명
- 상세 페이지 `설명`
- 상세 페이지 `기타 유의사항`
- 상세 페이지 상단 소개 문구
- (오픈API 상세일 때) `상세기능` 이름 목록
- (있으면) 상세 페이지 내 활용 관련 안내 문구

### M4: 분류(도메인/서비스 분류)
- 목록 카드의 상단 분류 라벨
  - 예: `보건의료`, `재정금융`, `공공기관`, `국가행정기관`, `국가중점`
- 상세 페이지 `분류체계`
- 목록 페이지 선택 조건(필터) 값
  - 분류체계
  - 서비스유형
  - 제공기관유형
  - 확장자
  - 국가중점데이터 조건
- 내부 저장 예시
  - `category_main`
  - `provider_type`
  - `national_core_flag`
  - `service_type`

### M5: 제공 형태/포맷/리소스(링크 메타만)
#### 목록 카드에서 수집
- 포맷 배지/텍스트
  - 예: `CSV`, `XLSX`, `XML`, `JSON`
- CTA 텍스트
  - `다운로드`
  - `바로가기`
  - `활용신청`

#### 파일데이터 상세에서 수집
- `확장자`
- `제공형태`
- `매체유형`
- `schema.org` 링크 URL
- `DCAT` 링크 URL

#### 오픈API 상세에서 수집
- `API 유형`
- `데이터포맷`
- `참고문서` 파일명/링크
- `요청주소`
- `서비스URL`
- `schema.org` 링크 URL
- `DCAT` 링크 URL

## M6: 라이선스/이용조건
- 상세 페이지 `이용허락범위`
- 내부 저장 예시
  - `license_scope_text`
  - `license_scope_link_text`
- 주의:
  - 크롤링만 사용하므로 라이선스의 법적 의미를 재해석하지 않는다.
  - 페이지에 적힌 문구만 원문 그대로 저장한다.

## M7: 제공자/기관
### 파일데이터 상세
- `제공기관`
- `관리부서명`
- `관리부서 전화번호`

### 오픈API 상세
- `제공기관`
- `관리부서명`
- `관리부서 전화번호`

### 일부 파일데이터/자동변환 API 구간
- `관리기관`
- `관리기관 전화번호`

### 데이터항목(컬럼) 정보 표에 있을 경우
- `제공기관코드`

## M8: 태그/키워드/언어
- 목록 카드 `키워드`
- 상세 페이지 `키워드`
- 언어는 일반적으로 명시되지 않으므로 기본 `null`
- 내부 저장 예시
  - `keywords[]`
  - `language = null`

## M9: 최신성/변경 이력
- 목록 카드 `수정일`
- 상세 페이지 `등록일`
- 상세 페이지 `수정일`
- 상세 페이지 `업데이트 주기`
- 상세 페이지 `차기 등록 예정일`
- 상세 페이지 `공간범위`
- 상세 페이지 `시간범위`

## M10: 스키마/라벨 구조 (사이트가 노출하는 범위만)
### 파일데이터 상세에서 수집 가능한 스키마
상세 페이지의 `데이터항목(컬럼) 정보` 표에서 아래를 구조화한다.
- `항목명`
- `항목명(영문명)`
- `항목 설명`
- `도메인분류`
- `데이터타입`
- `최대길이`
- `표현형식`
- `단위`
- `생성출처`
  - `정보시스템명`
  - `DB명`
  - `Table명`
- `코드`

### 오픈API 상세에서 수집 가능한 스키마
#### 상세기능 단위
- 기능명
- 활용승인 절차
- 신청가능 트래픽
- 요청주소
- 서비스URL

#### 요청변수(Request Parameter) 표
- `항목명(국문)`
- `항목명(영문)`
- `항목크기`
- `항목구분`
- `샘플데이터`
- `항목설명`

#### 출력결과(Response Element) 표
- `항목명(국문)`
- `항목명(영문)`
- `항목크기`
- `항목구분`
- `샘플데이터`
- `항목설명`

### 주의
- 실제 응답 JSON/XML을 호출해서 스키마를 재구성하지 않는다.
- 페이지에 보이는 표만 신뢰 원본으로 사용한다.

## M11: 규모 지표
### 목록 카드에서 수집
- `조회수`
- `다운로드` (파일데이터 카드)
- `활용신청` (오픈API 카드)
- `주기성 데이터` (있는 카드만)

### 파일데이터 상세에서 수집
- `전체 행`
- `누적 다운로드(바로가기)`
- `다운로드(바로가기)`

### 오픈API 상세에서 수집
- `활용신청`

## M12: 접근 제약
- 상세 페이지 `비용부과유무`
- 상세 페이지 `비용부과기준 및 단위`
- 오픈API 상세 `심의유형`
- 오픈API 상세 `신청가능 트래픽`
- 상세 페이지/버튼/안내문 기반 접근 메모
  - `다운로드`
  - `활용신청`
  - `바로가기`
  - `로그인 필요 여부를 암시하는 문구`
  - `회원 가입 및 활용신청 필요`와 같은 안내문(페이지에 있을 때만 원문 저장)
- 내부 저장 예시
  - `access.cost_flag`
  - `access.cost_unit`
  - `access.deliberation_type`
  - `access.traffic_limit_text`
  - `access.note_raw`

## M13: 인기/품질/커뮤니티 지표
- 상세 상단의 `좋아요 수`
- 상세 상단의 `싫어요 수`
- 상세 상단의 `관심`
- 목록/상세의 `조회수`
- 목록/상세의 `다운로드`
- 목록/상세의 `활용신청`
- 상세 페이지의 `활용사례` 섹션 링크(있으면)
- 상세 페이지의 `추천데이터` 섹션 링크(있으면)

## 크롤링 사용 준비
- 공개 HTML만 수집한다.
- 로그인/활용신청/다운로드 실행은 하지 않는다.
- JavaScript 실행 없이 서버사이드 HTML에서 우선 파싱한다.
- HTML만으로 부족한 필드는 `null`로 둔다.
- robots.txt 및 서비스 운영 정책을 확인한 뒤 저속으로 실행한다.
- 권장 기본값
  - 동시성: 1~3
  - 요청 간 지연: 1~3초 랜덤
  - 재시도: 429/5xx에 대해서만 exponential backoff
  - User-Agent: 프로젝트명/연락처 포함

## 수집 파이프라인(권장)
1. 목록 페이지 크롤링
   - seed URL: `selectDataSetList.do`
   - 수집:
     - 전체/파일데이터/오픈API 개수
     - 필터 조건 값
     - 정렬 옵션 값
     - 카드별 detail URL, title, 요약 설명, 제공기관, 수정일, 조회수, 다운로드/활용신청, 키워드, 포맷, 국가중점 여부

2. 상세 페이지 분기 크롤링
   - `fileData.do`:
     - 파일데이터 정보 섹션
     - 데이터항목(컬럼) 정보 표
   - `openapi.do`:
     - 오픈API 정보 섹션
     - 상세기능
     - 요청변수/출력결과 표

3. 정규화 저장
   - 내부 M1~M13 스키마로 upsert
   - `item_type=fileData/openapi`에 따라 nullable 필드 처리

## 증분(이어 긁기) 설계
- `upsert_key = (source, source_id)`

### 1차 체크포인트: 목록 페이지
- 파티션 단위로 저장
  - `service_type` (fileData/openapi)
  - `category`
  - `provider_type`
  - `sort`
  - `page_no`
- 우선순위
  - `수정일자순`
  - `조회많은순`
  - `활용많은순`

### 2차 체크포인트: 상세 페이지
- `detail_updated_at`
- `last_crawled_at`

### 권장 전략
- 매일:
  - `수정일자순`으로 상위 K페이지 재수집
- 매주:
  - `조회많은순`, `활용많은순` 상위 K페이지 재수집
- 상세 페이지는
  - `수정일`이 동일하면 M1~M12 재파싱 생략 가능
  - 단, M13(조회수/다운로드/활용신청/좋아요)은 변동 가능하므로 주기적 refresh 허용

## PoC 성공 기준(최소)
- 목록 페이지에서 fileData / openapi 상세 URL 1,000개 이상 확보
- fileData 상세 200건, openapi 상세 200건 파싱 성공
- fileData 기준
  - M1~M9, M11, M12 채움률 90% 이상
  - M10(컬럼 정보) 채움률 80% 이상
- openapi 기준
  - M1~M9, M12 채움률 90% 이상
  - M10(요청/응답 표) 채움률 80% 이상
- 크롤러 중단 후 재시작 시 checkpoint 기준 이어서 수집 가능

## 출력 포맷(JSONL 예시)
{
  "source": "datagokr_crawl",
  "source_id": "15062804",
  "item_type": "fileData",
  "canonical_url": "https://www.data.go.kr/data/15062804/fileData.do",
  "title": "공공데이터활용지원센터_공공데이터포털 목록개방현황",
  "description_long": "공공기관이 등록하여 공공데이터포털에서 개방중인 목록 정보...",
  "classification": {
    "category_main": "일반공공행정",
    "category_sub": "일반행정",
    "provider_type": "공공데이터활용지원센터",
    "national_core_flag": false
  },
  "resources_meta": {
    "format_badges": ["CSV"],
    "extension": "CSV",
    "media_type": "텍스트",
    "delivery_type": "공공데이터포털에서 다운로드(원문파일등록)",
    "metadata_links": {
      "schema_org": "https://...",
      "dcat": "https://..."
    }
  },
  "provider": {
    "organization": "공공데이터활용지원센터",
    "department": "공공데이터활용지원센터",
    "phone": null
  },
  "keywords": ["개방목록", "데이터", "오픈데이터", "파일데이터", "제공표준", "openAPI"],
  "license": {
    "scope_text": "이용허락범위 제한 없음"
  },
  "freshness": {
    "registered_at": "2026-02-13",
    "updated_at": "2026-02-13",
    "update_cycle": "월간",
    "next_register_at": "2026-03-13",
    "spatial_scope": "대한민국",
    "temporal_scope": "2010년11월 - 2026년 01월"
  },
  "schema": {
    "columns": [
      {
        "name_kr": "목록키",
        "name_en": null,
        "description": "데이터 키 번호",
        "data_type": "VARCHAR",
        "max_length": 8
      }
    ]
  },
  "stats": {
    "row_count": 87581,
    "download_count": 134,
    "cumulative_download_count": 69106,
    "view_count": null
  },
  "access": {
    "cost_flag": "무료",
    "cost_unit": "건",
    "note_raw": "파일데이터는 로그인 없이 다운로드를 통해 이용할 수 있음"
  },
  "signals": {
    "like_count": 4,
    "dislike_count": 0,
    "interest": true
  }
}