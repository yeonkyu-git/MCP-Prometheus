# MCP Prometheus 🔎

Prometheus 기반 모니터링 MCP 서버입니다.  
엔트리포인트는 `main.py`입니다.

## Quick Start 🚀

```powershell
cd d:\MCPTools
uv sync
uv run python mcp_prometheus/main.py
```

## 프로젝트 구조 🗂️

```text
mcp_prometheus/
  main.py
  core/
    config.py
    runtime.py
    server.py
    time_utils.py
  domain/
    checks.py
  infra/
    prom_client.py
  tools/
    catalog.py
    checks_runner.py
    promql.py
  utils/
    query_utils.py
    summarize.py
```

## Tools 요약 🧰

| Tool | 목적 | 비고 |
|---|---|---|
| `list_checks` | 등록된 체크 목록 조회 | `id`, `name`, `description` 반환 |
| `list_environments` | 환경 키와 Prometheus URL 조회 | `prod/dev_test/dr` |
| `list_servers` | 최근 up 기준 서버 목록 조회 | `(instance, job)` 기준 중복 제거 |
| `list_process_groups` | 프로세스 그룹 목록 조회 | `process_monitoring` 기준 |
| `run_check` | 단일 체크 실행 | 기본 권장 |
| `run_all_checks` | 전체 체크 병렬 실행 | `step` 고정 `5m` |
| `run_promql` | 사용자 PromQL 직접 실행 | `approved=True` 필요 |

## `run_check` 입력 가이드 ✅

### 필수
- `check_id`

### 기간
- 상대: `hours`, `minutes`, `days`
- 절대: `start_time_utc_iso`, `end_time_utc_iso`
- 종료 오프셋: `end_offset_minutes`, `end_offset_hours`, `end_offset_days`

### 대상 필터
- `server_name`
- `instance` (예: `host-or-ip:9100`)

필터 규칙:
- `server_name`과 `instance`를 둘 다 주면 AND 적용
- 하나만 주면 해당 라벨만 적용

## `run_promql` 가드레일 🛡️

- `approved=False`: 실행하지 않고 확인 메시지 반환
- `approved=True`: 실행

모드:
- `instant=True` -> `/api/v1/query`
- `instant=False` -> `/api/v1/query_range`

## 사용 예시 🧪

### 1) 특정 서버 CPU 평균 (최근 24시간)

```json
{
  "check_id": "cpu_avg_pct",
  "hours": 24,
  "instance": "10.23.12.11:9100",
  "environment": "prod"
}
```

### 2) 특정 서버 디스크 사용률 (mountpoint별)

```json
{
  "check_id": "disk_used_pct_by_mount",
  "hours": 24,
  "server_name": "CMS AP #1",
  "environment": "prod"
}
```

### 3) 사용자 PromQL 실행 (instant)

```json
{
  "promql": "up",
  "approved": true,
  "instant": true,
  "environment": "prod"
}
```

## 파일별 상세 역할 📚

### 최상위

- `main.py`
  - MCP 서버 실행 시작점입니다.
  - `tools` 모듈들을 import해서 tool 등록(side effect)을 완료한 뒤 `mcp.run()`을 호출합니다.

- `README.md`
  - 프로젝트 사용 방법/설계 개요/운영 시 주의사항을 문서화합니다.

- `pyproject.toml`
  - 패키지 메타데이터와 의존성(`mcp`, `requests`, `python-dotenv`)을 관리합니다.

- `.gitignore`
  - `.env`, 캐시/IDE 파일 등 커밋하면 안 되는 파일을 제외합니다.

### `core/`

- `core/config.py`
  - 환경 변수 로딩과 전역 설정값을 담당합니다.
  - 예: `PROM_ENV_URLS`, `PROM_URL`, 타임아웃, 경보 임계치, 병렬 개수 제한.

- `core/server.py`
  - `FastMCP` 인스턴스 생성과 로거 초기화 담당.
  - `ENV_URLS`를 로드해 tool들이 공통으로 참조할 수 있게 제공합니다.

- `core/runtime.py`
  - 런타임 공통 로직(환경 해석, 샘플 볼륨 검증, alert 적용 조건 판단)을 처리합니다.
  - 각 tool에서 중복 없이 재사용합니다.

- `core/time_utils.py`
  - 시간 범위 계산/파싱 유틸을 제공합니다.
  - `hours/minutes/days`, 절대시간, end offset, step 파싱 등을 일관되게 처리합니다.

### `domain/`

- `domain/checks.py`
  - allowlist 체크 정의의 단일 소스입니다.
  - 각 체크의 `id`, `name`, `description`, `promql`을 관리합니다.
  - `run_check`/`run_all_checks`는 이 파일에 있는 체크만 실행합니다.

### `infra/`

- `infra/prom_client.py`
  - Prometheus HTTP API 호출 전담 모듈입니다.
  - `query_range`, `query`, `label values` 호출을 감싸고 retry/timeout/header를 통일합니다.
  - bearer token이 있으면 자동으로 Authorization 헤더를 추가합니다.

### `tools/`

- `tools/catalog.py`
  - 조회형 메타 툴 모음입니다.
  - `list_checks`, `list_environments`, `list_servers`, `list_process_groups` 제공.

- `tools/checks_runner.py`
  - 체크 실행 툴 모음입니다.
  - `run_check`: 단일 체크 실행
  - `run_all_checks`: 전체 체크 병렬 실행(현재 `step=5m` 고정)
  - 내부 `_run_single_check`는 병렬 처리용 private helper입니다.

- `tools/promql.py`
  - 사용자가 입력한 PromQL을 직접 실행하는 툴입니다.
  - 승인(`approved`) 기반으로 instant/range 모드를 지원합니다.

- `tools/__init__.py`
  - tools 패키지 인식용 파일입니다.

### `utils/`

- `utils/query_utils.py`
  - 체크 템플릿 PromQL 렌더링(`{range}` 치환)과 타겟 필터 적용을 담당합니다.
  - `server_name`/`instance` 필터를 PromQL에 안전하게 결합합니다.

- `utils/summarize.py`
  - Prometheus 응답 샘플을 통계 요약(avg/max/min/count 등)으로 가공합니다.
  - alert 설정이 있을 때 warning/critical 지속 판단에 필요한 보조 계산을 수행합니다.

- `utils/__init__.py`
  - utils 패키지 인식용 파일입니다.

## 환경 변수 ⚙️

```env
PROM_ENV_URLS={"prod":"http://...:9090","dev_test":"http://...:9090","dr":"http://...:9090"}
PROM_URL=http://...:9090
PROM_BEARER_TOKEN=
PROM_TIMEOUT_SEC=15

ALERT_WARN_PCT=85
ALERT_CRIT_PCT=95
ALERT_SUSTAIN_MINUTES=5

PROM_MAX_SAMPLES_PER_SERIES=5000
PROM_MAX_PARALLEL_CHECKS=6
```

환경 선택 우선순위:
1. `environment`
2. `env_hint`
3. `PROM_URL` fallback

## 운영 팁 💡

- 리포트 출력 시 `%` 단위를 항상 명시하세요.
- 디스크 사용률 체크는 `instance` 또는 `server_name`으로 대상을 제한하세요.
- `disk_used_pct_by_mount` 값은 0~100 스케일입니다.  
  예: `0.8`은 `80%`가 아니라 `0.8%`입니다.
