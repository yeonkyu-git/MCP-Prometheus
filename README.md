# MCP Prometheus ?뵊

Prometheus 湲곕컲 紐⑤땲?곕쭅 MCP ?쒕쾭?낅땲??  
?뷀듃由ы룷?명듃??`main.py`?낅땲??

## Quick Start ??

```powershell
cd d:\MCPTools
uv sync
uv run python mcp_prometheus/main.py
```

## ?꾨줈?앺듃 援ъ“ ?뾺截?
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

## Tools ?붿빟 ?㎞

| Tool | 紐⑹쟻 | 鍮꾧퀬 |
|---|---|---|
| `list_checks` | ?깅줉??泥댄겕 紐⑸줉 議고쉶 | `id`, `name`, `description` 諛섑솚 |
| `list_environments` | ?섍꼍 ?ㅼ? Prometheus URL 議고쉶 | `prod/dev_test/dr` |
| `list_servers` | 理쒓렐 up 湲곗? ?쒕쾭 紐⑸줉 議고쉶 | `(instance, job)` 湲곗? 以묐났 ?쒓굅 |
| `list_process_groups` | ?꾨줈?몄뒪 洹몃９ 紐⑸줉 議고쉶 | `process_monitoring` 湲곗? |
| `run_check` | ?⑥씪 泥댄겕 ?ㅽ뻾 | 湲곕낯 沅뚯옣 |
| `run_all_checks` | ?꾩껜 泥댄겕 蹂묐젹 ?ㅽ뻾 | `step` 怨좎젙 `5m` |
| `run_promql` | ?ъ슜??PromQL 吏곸젒 ?ㅽ뻾 | `approved=True` ?꾩슂 |

## `run_check` ?낅젰 媛?대뱶 ??
### ?꾩닔
- `check_id`

### 湲곌컙
- ?곷?: `hours`, `minutes`, `days`
- ?덈?: `start_time_utc_iso`, `end_time_utc_iso`
- 醫낅즺 ?ㅽ봽?? `end_offset_minutes`, `end_offset_hours`, `end_offset_days`

### ????꾪꽣
- `server_name`
- `instance` (?? `host-or-ip:9100`)

?꾪꽣 洹쒖튃:
- `server_name`怨?`instance`瑜?????二쇰㈃ AND ?곸슜
- ?섎굹留?二쇰㈃ ?대떦 ?쇰꺼留??곸슜

## `run_promql` 媛?쒕젅???썳截?
- `approved=False`: ?ㅽ뻾?섏? ?딄퀬 ?뺤씤 硫붿떆吏 諛섑솚
- `approved=True`: ?ㅽ뻾

紐⑤뱶:
- `instant=True` -> `/api/v1/query`
- `instant=False` -> `/api/v1/query_range`

## ?ъ슜 ?덉떆 ?㎦

### 1) ?뱀젙 ?쒕쾭 CPU ?됯퇏 (理쒓렐 24?쒓컙)

```json
{
  "check_id": "cpu_avg_pct",
  "hours": 24,
  "instance": "10.23.12.11:9100",
  "environment": "prod"
}
```

### 2) ?뱀젙 ?쒕쾭 ?붿뒪???ъ슜瑜?(mountpoint蹂?

```json
{
  "check_id": "disk_used_pct_by_mount",
  "hours": 24,
  "server_name": "CMS AP #1",
  "environment": "prod"
}
```

### 3) ?ъ슜??PromQL ?ㅽ뻾 (instant)

```json
{
  "promql": "up",
  "approved": true,
  "instant": true,
  "environment": "prod"
}
```

## ?뚯씪蹂??곸꽭 ??븷 ?뱴

### 理쒖긽??
- `main.py`
  - MCP ?쒕쾭 ?ㅽ뻾 ?쒖옉?먯엯?덈떎.
  - `tools` 紐⑤뱢?ㅼ쓣 import?댁꽌 tool ?깅줉(side effect)???꾨즺????`mcp.run()`???몄텧?⑸땲??

- `README.md`
  - ?꾨줈?앺듃 ?ъ슜 諛⑸쾿/?ㅺ퀎 媛쒖슂/?댁쁺 ??二쇱쓽?ы빆??臾몄꽌?뷀빀?덈떎.

- `pyproject.toml`
  - ?⑦궎吏 硫뷀??곗씠?곗? ?섏〈??`mcp`, `requests`, `python-dotenv`)??愿由ы빀?덈떎.

- `.gitignore`
  - `.env`, 罹먯떆/IDE ?뚯씪 ??而ㅻ컠?섎㈃ ???섎뒗 ?뚯씪???쒖쇅?⑸땲??

### `core/`

- `core/config.py`
  - ?섍꼍 蹂??濡쒕뵫怨??꾩뿭 ?ㅼ젙媛믪쓣 ?대떦?⑸땲??
  - ?? `PROM_ENV_URLS`, `PROM_URL`, ??꾩븘?? 寃쎈낫 ?꾧퀎移? 蹂묐젹 媛쒖닔 ?쒗븳.

- `core/server.py`
  - `FastMCP` ?몄뒪?댁뒪 ?앹꽦怨?濡쒓굅 珥덇린???대떦.
  - `ENV_URLS`瑜?濡쒕뱶??tool?ㅼ씠 怨듯넻?쇰줈 李몄“?????덇쾶 ?쒓났?⑸땲??

- `core/runtime.py`
  - ?고???怨듯넻 濡쒖쭅(?섍꼍 ?댁꽍, ?섑뵆 蹂쇰ⅷ 寃利? alert ?곸슜 議곌굔 ?먮떒)??泥섎━?⑸땲??
  - 媛?tool?먯꽌 以묐났 ?놁씠 ?ъ궗?⑺빀?덈떎.

- `core/time_utils.py`
  - ?쒓컙 踰붿쐞 怨꾩궛/?뚯떛 ?좏떥???쒓났?⑸땲??
  - `hours/minutes/days`, ?덈??쒓컙, end offset, step ?뚯떛 ?깆쓣 ?쇨??섍쾶 泥섎━?⑸땲??

### `domain/`

- `domain/checks.py`
  - allowlist 泥댄겕 ?뺤쓽???⑥씪 ?뚯뒪?낅땲??
  - 媛?泥댄겕??`id`, `name`, `description`, `promql`??愿由ы빀?덈떎.
  - `run_check`/`run_all_checks`?????뚯씪???덈뒗 泥댄겕留??ㅽ뻾?⑸땲??

### `infra/`

- `infra/prom_client.py`
  - Prometheus HTTP API ?몄텧 ?꾨떞 紐⑤뱢?낅땲??
  - `query_range`, `query`, `label values` ?몄텧??媛먯떥怨?retry/timeout/header瑜??듭씪?⑸땲??
  - bearer token???덉쑝硫??먮룞?쇰줈 Authorization ?ㅻ뜑瑜?異붽??⑸땲??

### `tools/`

- `tools/catalog.py`
  - 議고쉶??硫뷀? ??紐⑥쓬?낅땲??
  - `list_checks`, `list_environments`, `list_servers`, `list_process_groups` ?쒓났.

- `tools/checks_runner.py`
  - 泥댄겕 ?ㅽ뻾 ??紐⑥쓬?낅땲??
  - `run_check`: ?⑥씪 泥댄겕 ?ㅽ뻾
  - `run_all_checks`: ?꾩껜 泥댄겕 蹂묐젹 ?ㅽ뻾(?꾩옱 `step=5m` 怨좎젙)
  - ?대? `_run_single_check`??蹂묐젹 泥섎━??private helper?낅땲??

- `tools/promql.py`
  - ?ъ슜?먭? ?낅젰??PromQL??吏곸젒 ?ㅽ뻾?섎뒗 ?댁엯?덈떎.
  - ?뱀씤(`approved`) 湲곕컲?쇰줈 instant/range 紐⑤뱶瑜?吏?먰빀?덈떎.

- `tools/__init__.py`
  - tools ?⑦궎吏 ?몄떇???뚯씪?낅땲??

### `utils/`

- `utils/query_utils.py`
  - 泥댄겕 ?쒗뵆由?PromQL ?뚮뜑留?`{range}` 移섑솚)怨??寃??꾪꽣 ?곸슜???대떦?⑸땲??
  - `server_name`/`instance` ?꾪꽣瑜?PromQL???덉쟾?섍쾶 寃고빀?⑸땲??

- `utils/summarize.py`
  - Prometheus ?묐떟 ?섑뵆???듦퀎 ?붿빟(avg/max/min/count ???쇰줈 媛怨듯빀?덈떎.
  - alert ?ㅼ젙???덉쓣 ??warning/critical 吏???먮떒???꾩슂??蹂댁“ 怨꾩궛???섑뻾?⑸땲??

- `utils/__init__.py`
  - utils ?⑦궎吏 ?몄떇???뚯씪?낅땲??

## ?섍꼍 蹂???숋툘

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

?섍꼍 ?좏깮 ?곗꽑?쒖쐞:
1. `environment`
2. `env_hint`
3. `PROM_URL` fallback

## ?댁쁺 ???뮕

- 由ы룷??異쒕젰 ??`%` ?⑥쐞瑜???긽 紐낆떆?섏꽭??
- ?붿뒪???ъ슜瑜?泥댄겕??`instance` ?먮뒗 `server_name`?쇰줈 ??곸쓣 ?쒗븳?섏꽭??
- `disk_used_pct_by_mount` 媛믪? 0~100 ?ㅼ??쇱엯?덈떎.  
  ?? `0.8`? `80%`媛 ?꾨땲??`0.8%`?낅땲??

---
<!-- CHECKS_START -->

## CHECKS Catalog

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
<!-- CHECKS_END -->

