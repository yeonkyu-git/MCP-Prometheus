# MCP Prometheus 📈

Prometheus 기반 모니터링용 MCP 서버입니다.
엔트리포인트는 `main.py`입니다.

## Quick Start 🚀

```powershell
cd d:\MCPTools
uv sync
uv run python mcp_prometheus/main.py
```

## 프로젝트 구조 🧩

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

## Tools 요약 🛠️

| Tool | 목적 | 비고 |
|---|---|---|
| `list_checks` | 등록된 체크 목록 조회 | `id`, `name`, `description` 반환 |
| `list_environments` | 환경별 Prometheus URL 조회 | `prod/dev_test/dr` |
| `list_servers` | 최근 up 기준 서버 목록 조회 | `(instance, job)` 기준 중복 제거 |
| `list_process_groups` | 프로세스 그룹 목록 조회 | `process_monitoring` 기준 |
| `run_check` | 단일 체크 실행 | 기본 권장 |
| `run_all_checks` | 전체 체크 병렬 실행 | `step=5m` 고정 |
| `run_promql` | 사용자 PromQL 직접 실행 | `approved=True` 필요 |

## `run_check` 입력 가이드 🧭

### 필수
- `check_id`

### 기간
- 상대: `hours`, `minutes`, `days`
- 절대: `start_time_utc_iso`, `end_time_utc_iso`
- 종료 오프셋: `end_offset_minutes`, `end_offset_hours`, `end_offset_days`

### 타겟 필터
- `server_name`
- `instance` (예: `host-or-ip:9100`)

필터 규칙:
- `server_name`와 `instance`를 함께 주면 AND 적용
- 하나만 주면 해당 라벨만 적용

## `run_promql` 가드레일 🔒

- `approved=False`: 실행하지 않고 확인 메시지 반환
- `approved=True`: 실행

모드:
- `instant=True` -> `/api/v1/query`
- `instant=False` -> `/api/v1/query_range`

## 사용 예시 📌

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

## CHECKS Catalog ✅

> Source: `domain/checks.py` (`CHECKS`)

### System / Resource
- `cpu_avg_pct`: CPU average usage (%) by instance/server_name
- `cpu_peak_pct`: window peak CPU usage (%) over selected range
- `mem_used_pct`: memory used ratio (%)
- `mem_swap_used_pct`: swap used ratio (%)
- `load15_avg`: 15-minute load average
- `cpu_iowait_pct`: CPU iowait ratio (%)

### Disk / Filesystem
- `disk_used_pct_by_mount`: filesystem used (%) by mountpoint/device (0-100 scale)
- `disk_used_top5_pct`: top 5 filesystem usage (%)
- `disk_inodes_used_pct`: inode usage (%)
- `fs_readonly`: readonly filesystem indicator (1=readonly)
- `disk_io_busy_pct`: disk I/O busy ratio (%)

### Availability
- `up`: target liveness (1=up, 0=down)

### Network / TCP
- `net_in_bytes`: inbound throughput (bytes/sec)
- `net_out_bytes`: outbound throughput (bytes/sec)
- `net_errs_per_sec`: RX+TX network errors per second
- `tcp_retrans_per_sec`: TCP retransmit segments per second
- `tcp_established`: established TCP connections
- `tcp_time_wait`: TIME_WAIT TCP sockets
- `tcp_inuse`: in-use TCP sockets
- `tcp_orphan`: orphan TCP sockets

### Process Monitoring
- `proc_cpu_pct`: process group CPU usage (%)
- `proc_mem_bytes`: process group memory usage (bytes)
- `proc_count`: process group process count

### PostgreSQL
- `pg_up`: PostgreSQL exporter up state (1=up, 0=down)
- `pg_qps`: PostgreSQL transactions/sec (commit + rollback)
- `pg_cache_hit_pct`: PostgreSQL buffer cache hit ratio (%)
- `pg_active_conn`: active PostgreSQL connections

## 환경 변수 요약 ⚙️

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

- 리포트 출력 시 `%` 단위를 명확히 표기하세요.
- 단일 서버 점검은 `instance` 또는 `server_name` 필터를 사용하세요.
- `disk_used_pct_by_mount` 값은 0~100 스케일입니다. (`0.8` = `0.8%`)
