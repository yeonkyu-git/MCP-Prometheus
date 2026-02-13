from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Check:
    id: str
    name: str
    description: str
    promql: str
    kind: str = "range"


CHECKS: Dict[str, Check] = {
    "cpu_avg_pct": Check(
        id="cpu_avg_pct",
        name="CPU Average Usage (%)",
        description="CPU usage trend by instance/server_name.",
        promql='100 - (avg by (instance,server_name) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
    ),
    "cpu_peak_pct": Check(
        id="cpu_peak_pct",
        name="CPU Peak Usage (%)",
        description="Window peak CPU usage over selected range.",
        promql='max_over_time((100 - (avg by (instance,server_name) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))[{range}:])',
    ),
    "mem_used_pct": Check(
        id="mem_used_pct",
        name="Memory Used (%)",
        description="Memory usage ratio.",
        promql="100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)",
    ),
    "mem_swap_used_pct": Check(
        id="mem_swap_used_pct",
        name="Swap Used (%)",
        description="Swap usage ratio.",
        promql="100 * (1 - node_memory_SwapFree_bytes / node_memory_SwapTotal_bytes)",
    ),
    "disk_used_pct_by_mount": Check(
        id="disk_used_pct_by_mount",
        name="Disk Used (%) by Mount [0-100]",
        description="Filesystem usage percent by mountpoint/device on a 0-100 scale (example: 0.8 means 0.8%, not 80%). Use with instance/server_name filter for one server.",
        promql='100 * (1 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{fstype!~"tmpfs|overlay"}))',
    ),
    "disk_used_top5_pct": Check(
        id="disk_used_top5_pct",
        name="Disk Used Top 5 (%)",
        description="Top 5 filesystem usage excluding tmpfs/overlay.",
        promql='topk(5, 100 * (1 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{fstype!~"tmpfs|overlay"})))',
    ),
    "disk_inodes_used_pct": Check(
        id="disk_inodes_used_pct",
        name="Disk Inodes Used (%)",
        description="Filesystem inode usage ratio excluding tmpfs/overlay.",
        promql='100 * (1 - (node_filesystem_files_free{fstype!~"tmpfs|overlay"} / node_filesystem_files{fstype!~"tmpfs|overlay"}))',
    ),
    "fs_readonly": Check(
        id="fs_readonly",
        name="Filesystem Readonly",
        description="Readonly filesystem indicator (1=readonly).",
        promql='max by (instance,server_name,device,mountpoint,fstype) (node_filesystem_readonly{fstype!~"tmpfs|overlay"})',
    ),
    "load15_avg": Check(
        id="load15_avg",
        name="Load 15m (avg)",
        description="15-minute load average by instance/server_name.",
        promql="avg by (instance, server_name) (node_load15)",
    ),
    "up": Check(
        id="up",
        name="Up",
        description="Target liveness (1=up, 0=down).",
        promql="up",
    ),
    "cpu_iowait_pct": Check(
        id="cpu_iowait_pct",
        name="CPU IOWAIT (%)",
        description="CPU iowait ratio.",
        promql='avg by (instance,server_name) (rate(node_cpu_seconds_total{mode="iowait"}[5m])) * 100',
    ),
    "net_in_bytes": Check(
        id="net_in_bytes",
        name="Network Inbound (bytes/sec)",
        description="Inbound network throughput excluding lo/docker/veth.",
        promql='sum by (instance,server_name) (rate(node_network_receive_bytes_total{device!~"lo|docker.*|veth.*"}[5m]))',
    ),
    "net_out_bytes": Check(
        id="net_out_bytes",
        name="Network Outbound (bytes/sec)",
        description="Outbound network throughput excluding lo/docker/veth.",
        promql='sum by (instance,server_name) (rate(node_network_transmit_bytes_total{device!~"lo|docker.*|veth.*"}[5m]))',
    ),
    "net_errs_per_sec": Check(
        id="net_errs_per_sec",
        name="Network Errors (per sec)",
        description="RX+TX network errors per second.",
        promql='sum by (instance,server_name) (rate(node_network_receive_errs_total{device!~"lo|docker.*|veth.*"}[5m]) + rate(node_network_transmit_errs_total{device!~"lo|docker.*|veth.*"}[5m]))',
    ),
    "tcp_retrans_per_sec": Check(
        id="tcp_retrans_per_sec",
        name="TCP Retransmits (per sec)",
        description="TCP retransmit segments per second.",
        promql='sum by (instance,server_name) (rate(node_netstat_Tcp_RetransSegs[5m]))',
    ),
    "disk_io_busy_pct": Check(
        id="disk_io_busy_pct",
        name="Disk I/O Busy (%)",
        description="Disk busy time ratio.",
        promql="avg by (instance,server_name) (rate(node_disk_io_time_seconds_total[5m])) * 100",
    ),
    "tcp_established": Check(
        id="tcp_established",
        name="TCP Established",
        description="Current established TCP connections.",
        promql="sum by (instance,server_name) (node_netstat_Tcp_CurrEstab)",
    ),
    "tcp_time_wait": Check(
        id="tcp_time_wait",
        name="TCP Time Wait",
        description="Current TIME_WAIT TCP sockets.",
        promql="sum by (instance,server_name) (node_sockstat_TCP_tw)",
    ),
    "tcp_inuse": Check(
        id="tcp_inuse",
        name="TCP In Use",
        description="Current in-use TCP sockets.",
        promql="sum by (instance,server_name) (node_sockstat_TCP_inuse)",
    ),
    "tcp_orphan": Check(
        id="tcp_orphan",
        name="TCP Orphan",
        description="Current orphan TCP sockets.",
        promql="sum by (instance,server_name) (node_sockstat_TCP_orphan)",
    ),
    "proc_cpu_pct": Check(
        id="proc_cpu_pct",
        name="Process Group CPU (%)",
        description="CPU usage by process group from process_monitoring job.",
        promql='sum by (instance,server_name,groupname) (rate(namedprocess_namegroup_cpu_seconds_total{job="process_monitoring"}[5m])) * 100',
    ),
    "proc_mem_bytes": Check(
        id="proc_mem_bytes",
        name="Process Group Memory (bytes)",
        description="Memory usage by process group from process_monitoring job.",
        promql='max by (instance,server_name,groupname) (namedprocess_namegroup_memory_bytes{job="process_monitoring"})',
    ),
    "proc_count": Check(
        id="proc_count",
        name="Process Group Count",
        description="Process count by process group from process_monitoring job.",
        promql='max by (instance,server_name,groupname) (namedprocess_namegroup_num_procs{job="process_monitoring"})',
    ),
    "pg_up": Check(
        id="pg_up",
        name="PostgreSQL Up",
        description="PostgreSQL exporter up state (1=up, 0=down).",
        promql='up{job=~"PROD DB PostgreSQL|TEST DB PostgreSQL|DEV DB PostgreSQL"}',
    ),
    "pg_qps": Check(
        id="pg_qps",
        name="PostgreSQL QPS",
        description="PostgreSQL commit+rollback throughput (transactions/sec).",
        promql='sum by (instance,server_name,datname) (rate(pg_stat_database_xact_commit{job=~"PROD DB PostgreSQL|TEST DB PostgreSQL|DEV DB PostgreSQL"}[5m]) + rate(pg_stat_database_xact_rollback{job=~"PROD DB PostgreSQL|TEST DB PostgreSQL|DEV DB PostgreSQL"}[5m]))',
    ),
    "pg_cache_hit_pct": Check(
        id="pg_cache_hit_pct",
        name="PostgreSQL Cache Hit (%)",
        description="PostgreSQL buffer cache hit ratio.",
        promql='100 * sum by (instance,server_name,datname) (rate(pg_stat_database_blks_hit{job=~"PROD DB PostgreSQL|TEST DB PostgreSQL|DEV DB PostgreSQL"}[5m])) / sum by (instance,server_name,datname) (rate(pg_stat_database_blks_hit{job=~"PROD DB PostgreSQL|TEST DB PostgreSQL|DEV DB PostgreSQL"}[5m]) + rate(pg_stat_database_blks_read{job=~"PROD DB PostgreSQL|TEST DB PostgreSQL|DEV DB PostgreSQL"}[5m]))',
    ),
    "pg_active_conn": Check(
        id="pg_active_conn",
        name="PostgreSQL Active Connections",
        description="Current active PostgreSQL connections.",
        promql='sum by (instance,server_name,datname) (pg_stat_activity_count{state="active",job=~"PROD DB PostgreSQL|TEST DB PostgreSQL|DEV DB PostgreSQL"})',
    ),
}
