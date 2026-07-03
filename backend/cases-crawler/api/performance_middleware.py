"""
性能监控中间件
2026-07-03

功能:
1. 请求耗时统计
2. 慢请求日志 (可配置阈值)
3. 响应头添加 Server-Timing
4. 性能指标收集 (内存存储，可扩展)
"""
import time
import threading
from collections import defaultdict
from fastapi import Request
from loguru import logger

from core.config import settings


class PerformanceMetrics:
    """性能指标收集器 (单例模式)"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_metrics()
        return cls._instance

    def _init_metrics(self):
        self.request_count = 0
        self.total_latency = 0.0
        self.error_count = 0
        self.slow_request_count = 0
        self.endpoint_stats = defaultdict(lambda: {
            "count": 0,
            "total_latency": 0.0,
            "error_count": 0,
            "slow_count": 0,
            "min_latency": float("inf"),
            "max_latency": 0.0,
        })
        self.recent_latencies = []
        self._max_recent = 10000

    def record_request(self, path: str, latency_ms: float, status_code: int, is_slow: bool):
        """记录一次请求的性能数据"""
        with self._lock:
            self.request_count += 1
            self.total_latency += latency_ms
            if status_code >= 400:
                self.error_count += 1
            if is_slow:
                self.slow_request_count += 1

            stats = self.endpoint_stats[path]
            stats["count"] += 1
            stats["total_latency"] += latency_ms
            if status_code >= 400:
                stats["error_count"] += 1
            if is_slow:
                stats["slow_count"] += 1
            stats["min_latency"] = min(stats["min_latency"], latency_ms)
            stats["max_latency"] = max(stats["max_latency"], latency_ms)

            self.recent_latencies.append(latency_ms)
            if len(self.recent_latencies) > self._max_recent:
                self.recent_latencies = self.recent_latencies[-self._max_recent:]

    def get_summary(self) -> dict:
        """获取性能指标摘要"""
        with self._lock:
            avg_latency = self.total_latency / self.request_count if self.request_count > 0 else 0
            error_rate = self.error_count / self.request_count * 100 if self.request_count > 0 else 0
            slow_rate = self.slow_request_count / self.request_count * 100 if self.request_count > 0 else 0

            sorted_latencies = sorted(self.recent_latencies)
            p50 = self._percentile(sorted_latencies, 50)
            p95 = self._percentile(sorted_latencies, 95)
            p99 = self._percentile(sorted_latencies, 99)

            endpoint_top = sorted(
                self.endpoint_stats.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:10]

            return {
                "total_requests": self.request_count,
                "total_errors": self.error_count,
                "total_slow": self.slow_request_count,
                "avg_latency_ms": round(avg_latency, 2),
                "error_rate_pct": round(error_rate, 2),
                "slow_rate_pct": round(slow_rate, 2),
                "p50_latency_ms": round(p50, 2),
                "p95_latency_ms": round(p95, 2),
                "p99_latency_ms": round(p99, 2),
                "top_endpoints": [
                    {
                        "path": path,
                        "count": stats["count"],
                        "avg_latency_ms": round(
                            stats["total_latency"] / stats["count"], 2
                        ) if stats["count"] > 0 else 0,
                        "error_count": stats["error_count"],
                    }
                    for path, stats in endpoint_top
                ],
            }

    def _percentile(self, sorted_list: list, p: float) -> float:
        """计算百分位数"""
        if not sorted_list:
            return 0.0
        idx = int(p / 100 * len(sorted_list))
        idx = min(max(idx, 0), len(sorted_list) - 1)
        return sorted_list[idx]

    def reset(self):
        """重置所有指标"""
        with self._lock:
            self._init_metrics()


metrics = PerformanceMetrics()

SLOW_REQUEST_THRESHOLD = getattr(settings, "slow_request_threshold_ms", 1000)


async def performance_middleware(request: Request, call_next):
    """FastAPI 性能监控中间件"""
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        is_slow = process_time > SLOW_REQUEST_THRESHOLD

        path = request.url.path
        status_code = response.status_code

        metrics.record_request(path, process_time, status_code, is_slow)

        response.headers["Server-Timing"] = (
            f"total;dur={process_time:.2f}"
        )
        response.headers["X-Request-Time"] = f"{process_time:.2f}ms"

        if is_slow:
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "")[:200]
            logger.warning(
                "slow_request_detected",
                extra={
                    "method": request.method,
                    "path": path,
                    "query": request.url.query,
                    "duration_ms": round(process_time, 2),
                    "status_code": status_code,
                    "threshold_ms": SLOW_REQUEST_THRESHOLD,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                },
            )

        return response

    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        path = request.url.path

        metrics.record_request(path, process_time, 500, process_time > SLOW_REQUEST_THRESHOLD)

        logger.error(
            "request_error_perf",
            extra={
                "method": request.method,
                "path": path,
                "duration_ms": round(process_time, 2),
                "error": str(e),
            },
        )
        raise
