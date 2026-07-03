"""
请求日志中间件
2026-07-03

功能:
1. 记录每个请求的耗时、状态码、路径、用户、IP
2. 记录慢查询 (>500ms)
3. 记录错误请求 (status >= 400)
"""
import time
from fastapi import Request
from loguru import logger


async def logging_middleware(request: Request, call_next):
    """FastAPI 请求日志中间件"""
    start_time = time.time()
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    method = request.method
    path = request.url.path
    query = request.url.query
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        
        process_time = (time.time() - start_time) * 1000
        
        log_data = {
            "request_id": id(request),
            "method": method,
            "path": path,
            "query": query,
            "status_code": status_code,
            "duration_ms": round(process_time, 2),
            "client_ip": client_ip,
            "user_agent": user_agent[:200],
        }
        
        if process_time > 500:
            logger.warning("slow_request", extra={
                **log_data,
                "warning": "request took more than 500ms"
            })
        elif status_code >= 400:
            logger.error("request_error", extra=log_data)
        else:
            logger.info("request", extra=log_data)
        
        return response
    
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        
        logger.error("request_exception", extra={
            "request_id": id(request),
            "method": method,
            "path": path,
            "query": query,
            "duration_ms": round(process_time, 2),
            "client_ip": client_ip,
            "user_agent": user_agent[:200],
            "exception": str(e),
        })
        
        raise