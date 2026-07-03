"""
SLA 监控系统
2026-07-03

功能:
1. 可用性监控 (Uptime)
2. 响应时间 SLA
3. 错误率监控
4. SLA 报告生成
"""
import time
import json
import os
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import List, Optional, Dict, Any
from loguru import logger

from core.config import settings


class SLAMonitor:
    """SLA 监控器 (单例模式)"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_monitor()
        return cls._instance

    def _init_monitor(self):
        self.start_time = time.time()
        self._uptime_data = deque(maxlen=86400)
        self._response_times = defaultdict(lambda: deque(maxlen=10000))
        self._error_counts = defaultdict(int)
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._total_latency = 0.0
        self._violations: List[dict] = []
        self._daily_stats: Dict[str, dict] = {}
        self._sla_config = {
            "uptime_target_pct": getattr(settings, "sla_uptime_target", 99.9),
            "response_time_target_ms": getattr(settings, "sla_response_time_target", 500),
            "response_time_percentile": 0.95,
            "error_rate_target_pct": getattr(settings, "sla_error_rate_target", 1.0),
            "availability_window_hours": 24,
        }
        self._lock = threading.Lock()
        self._monitor_thread = threading.Thread(target=self._background_monitor, daemon=True)
        self._monitor_thread.start()

    def _background_monitor(self):
        """后台监控线程"""
        while True:
            try:
                self._record_uptime_sample()
                self._cleanup_old_data()
            except Exception as e:
                logger.error(f"SLA monitor error: {e}")
            time.sleep(60)

    def _record_uptime_sample(self):
        """记录可用性采样"""
        with self._lock:
            timestamp = time.time()
            sample = {
                "timestamp": timestamp,
                "uptime": True,
                "error_rate": self._calculate_error_rate(),
                "avg_response_time": self._calculate_avg_response_time(),
            }
            self._uptime_data.append(sample)

    def _cleanup_old_data(self):
        """清理过期数据"""
        cutoff = time.time() - 86400 * 30
        with self._lock:
            while self._uptime_data and self._uptime_data[0]["timestamp"] < cutoff:
                self._uptime_data.popleft()

    def record_request(self, endpoint: str, latency_ms: float, status_code: int):
        """记录一次请求的 SLA 数据"""
        with self._lock:
            self._total_requests += 1
            self._total_latency += latency_ms
            self._response_times[endpoint].append(latency_ms)

            is_success = 200 <= status_code < 400
            if is_success:
                self._successful_requests += 1
            else:
                self._failed_requests += 1
                self._error_counts[endpoint] += 1

            self._check_sla_violations(endpoint, latency_ms, status_code)

            today = datetime.now().strftime("%Y-%m-%d")
            if today not in self._daily_stats:
                self._daily_stats[today] = {
                    "date": today,
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "total_latency": 0.0,
                    "violations": 0,
                }

            day_stats = self._daily_stats[today]
            day_stats["total_requests"] += 1
            day_stats["total_latency"] += latency_ms
            if is_success:
                day_stats["successful_requests"] += 1
            else:
                day_stats["failed_requests"] += 1

    def _check_sla_violations(self, endpoint: str, latency_ms: float, status_code: int):
        """检查 SLA 违规"""
        target = self._sla_config["response_time_target_ms"]
        if latency_ms > target:
            violation = {
                "timestamp": time.time(),
                "type": "response_time",
                "endpoint": endpoint,
                "value": latency_ms,
                "target": target,
                "message": f"Response time {latency_ms:.2f}ms exceeds target {target}ms",
            }
            self._violations.append(violation)
            if len(self._violations) > 1000:
                self._violations = self._violations[-1000:]

    def _calculate_error_rate(self) -> float:
        """计算错误率 (百分比)"""
        if self._total_requests == 0:
            return 0.0
        return (self._failed_requests / self._total_requests) * 100

    def _calculate_avg_response_time(self) -> float:
        """计算平均响应时间"""
        if self._total_requests == 0:
            return 0.0
        return self._total_latency / self._total_requests

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        idx = int(percentile * len(sorted_values))
        idx = min(max(idx, 0), len(sorted_values) - 1)
        return sorted_values[idx]

    def get_current_status(self) -> dict:
        """获取当前 SLA 状态"""
        with self._lock:
            uptime_pct = self._calculate_uptime_percentage()
            error_rate = self._calculate_error_rate()
            avg_latency = self._calculate_avg_response_time()

            all_latencies = []
            for endpoint_latencies in self._response_times.values():
                all_latencies.extend(endpoint_latencies)

            p95_latency = self._calculate_percentile(all_latencies, 0.95)
            p99_latency = self._calculate_percentile(all_latencies, 0.99)

            config = self._sla_config
            uptime_ok = uptime_pct >= config["uptime_target_pct"]
            latency_ok = p95_latency <= config["response_time_target_ms"]
            error_rate_ok = error_rate <= config["error_rate_target_pct"]

            overall_status = "healthy" if (uptime_ok and latency_ok and error_rate_ok) else "degraded"

            return {
                "overall_status": overall_status,
                "uptime_percentage": round(uptime_pct, 4),
                "uptime_target": config["uptime_target_pct"],
                "uptime_ok": uptime_ok,
                "average_response_time_ms": round(avg_latency, 2),
                "p95_response_time_ms": round(p95_latency, 2),
                "p99_response_time_ms": round(p99_latency, 2),
                "response_time_target_ms": config["response_time_target_ms"],
                "response_time_ok": latency_ok,
                "error_rate_pct": round(error_rate, 4),
                "error_rate_target_pct": config["error_rate_target_pct"],
                "error_rate_ok": error_rate_ok,
                "total_requests": self._total_requests,
                "successful_requests": self._successful_requests,
                "failed_requests": self._failed_requests,
                "total_violations": len(self._violations),
                "uptime_seconds": int(time.time() - self.start_time),
            }

    def _calculate_uptime_percentage(self) -> float:
        """计算可用性百分比"""
        if not self._uptime_data:
            return 100.0

        total = len(self._uptime_data)
        up = sum(1 for s in self._uptime_data if s["uptime"])
        return (up / total) * 100 if total > 0 else 100.0

    def get_uptime_history(self, hours: int = 24) -> List[dict]:
        """获取可用性历史数据"""
        with self._lock:
            cutoff = time.time() - hours * 3600
            history = [
                s for s in self._uptime_data
                if s["timestamp"] >= cutoff
            ]
            return history

    def get_violations(self, limit: int = 50, offset: int = 0) -> dict:
        """获取 SLA 违规记录"""
        with self._lock:
            violations = list(reversed(self._violations))
            paginated = violations[offset:offset + limit]
            return {
                "total": len(self._violations),
                "violations": paginated,
            }

    def get_daily_report(self, days: int = 7) -> List[dict]:
        """获取每日 SLA 报告"""
        with self._lock:
            today = datetime.now().date()
            reports = []

            for i in range(days - 1, -1, -1):
                date = today - timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")

                if date_str in self._daily_stats:
                    stats = self._daily_stats[date_str]
                    total = stats["total_requests"]
                    success = stats["successful_requests"]
                    uptime = (success / total * 100) if total > 0 else 100.0
                    avg_latency = (stats["total_latency"] / total) if total > 0 else 0

                    reports.append({
                        "date": date_str,
                        "total_requests": total,
                        "successful_requests": success,
                        "failed_requests": stats["failed_requests"],
                        "uptime_pct": round(uptime, 4),
                        "avg_response_time_ms": round(avg_latency, 2),
                        "violations": stats["violations"],
                    })
                else:
                    reports.append({
                        "date": date_str,
                        "total_requests": 0,
                        "successful_requests": 0,
                        "failed_requests": 0,
                        "uptime_pct": 100.0,
                        "avg_response_time_ms": 0,
                        "violations": 0,
                    })

            return reports

    def get_endpoint_stats(self) -> List[dict]:
        """获取各端点的 SLA 统计"""
        with self._lock:
            stats = []
            for endpoint, latencies in self._response_times.items():
                latency_list = list(latencies)
                errors = self._error_counts.get(endpoint, 0)
                total = len(latency_list) + errors
                success = len(latency_list)

                avg_latency = sum(latency_list) / len(latency_list) if latency_list else 0
                p95 = self._calculate_percentile(latency_list, 0.95)
                p99 = self._calculate_percentile(latency_list, 0.99)

                error_rate = (errors / total * 100) if total > 0 else 0

                stats.append({
                    "endpoint": endpoint,
                    "total_requests": total,
                    "successful_requests": success,
                    "failed_requests": errors,
                    "error_rate_pct": round(error_rate, 4),
                    "avg_response_time_ms": round(avg_latency, 2),
                    "p95_response_time_ms": round(p95, 2),
                    "p99_response_time_ms": round(p99, 2),
                })

            stats.sort(key=lambda x: x["total_requests"], reverse=True)
            return stats

    def generate_full_report(self) -> dict:
        """生成完整 SLA 报告"""
        status = self.get_current_status()
        daily = self.get_daily_report(30)
        endpoints = self.get_endpoint_stats()
        violations = self.get_violations(100)

        return {
            "generated_at": datetime.now().isoformat(),
            "current_status": status,
            "daily_stats": daily,
            "endpoint_stats": endpoints,
            "recent_violations": violations,
            "sla_config": self._sla_config,
        }

    def reset(self):
        """重置所有 SLA 数据"""
        with self._lock:
            self._init_monitor()


sla_monitor = SLAMonitor()
