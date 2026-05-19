"""
SmartEdu 安全增强模块
提供：速率限制、审计日志、安全缓存
"""
from functools import wraps
from flask import request, jsonify, g, current_app
from datetime import datetime
import time
import json

# ==================== 速率限制器 ====================

class RateLimiter:
    """基于内存的速率限制器（轻量级，无需 Redis）"""

    def __init__(self):
        self._requests = {}  # {ip: [(timestamp, count), ...]}
        self.default_limit = (100, 60)  # 默认：每分钟100次请求
        self.limits = {
            # 路由: (最大请求数, 时间窗口秒数)
            '/api/health': (200, 60),
            '/api/education-stages': (300, 60),
            '/api/subjects': (150, 60),
            '/api/statistics': (120, 60),
            '/api/version/select': (30, 60),  # 版本选择更严格
            # 写操作更严格
            'POST:/api/': (20, 60),
        }

    def _cleanup_old_requests(self):
        """清理过期记录"""
        current_time = time.time()
        for ip in list(self._requests.keys()):
            self._requests[ip] = [
                ts for ts in self._requests[ip]
                if current_time - ts < 60  # 只保留最近60秒
            ]
            if not self._requests[ip]:
                del self._requests[ip]

    def is_allowed(self, route_path=None):
        """检查是否允许请求"""
        ip = request.remote_addr or 'unknown'
        current_time = time.time()

        if ip not in self._requests:
            self._requests[ip] = []

        # 清理过期数据（每100次请求清理一次）
        if len(self._requests.get(ip, [])) > 100:
            self._cleanup_old_requests()

        # 获取该路由的限制
        limit = self.limits.get(route_path) or \
                next((v for k, v in self.limits.items() if route_path and k in route_path), None) or \
                self.default_limit

        max_requests, window = limit

        # 统计窗口内的请求数
        window_requests = [ts for ts in self._requests[ip] if current_time - ts < window]

        if len(window_requests) >= max_requests:
            return False, {
                'limit': max_requests,
                'window': window,
                'retry_after': int(min(self._requests[ip]) + window - current_time)
            }

        # 记录此次请求
        self._requests[ip].append(current_time)

        return True, {'remaining': max_requests - len(window_requests) - 1}

# 全局实例
rate_limiter = RateLimiter()

def rate_limit(route_path=None):
    """速率限制装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            allowed, info = rate_limiter.is_allowed(request.path)

            if not allowed:
                response = jsonify({
                    'error': 'Too many requests',
                    'message': f'Rate limit exceeded. Try again after {info["retry_after"]} seconds',
                    'code': 429
                })
                response.status_code = 429
                # 添加标准响应头
                response.headers['Retry-After'] = str(info['retry_after'])
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = '0'
                return response

            # 执行原始函数
            result = f(*args, **kwargs)

            # 添加速率限制头信息（如果结果是 Response 对象）
            if hasattr(result, 'headers'):
                result.headers['X-RateLimit-Remaining'] = str(info['remaining'])

            return result
        return decorated_function
    return decorator


# ==================== 审计日志 ====================

def get_client_ip():
    """获取客户端真实 IP"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    elif request.headers.get('X-Real-Ip'):
        return request.headers.get('X-Real-Ip')
    else:
        return request.remote_addr or 'unknown'

def create_audit_log(action_type, resource_type=None, resource_id=None,
                     user_id=None, details=None, status='success'):
    """
    创建审计日志记录

    Args:
        action_type: 操作类型（login, logout, read, create, update, delete, select_version 等）
        resource_type: 资源类型（user, subject, lesson_plan, textbook 等）
        resource_id: 资源 ID
        user_id: 用户 ID
        details: 详细信息字典
        status: 操作状态（success, failure, unauthorized, forbidden）
    """
    try:
        from models import db, AuditLog

        log_entry = AuditLog(
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent', '')[:500],
            request_method=request.method,
            request_path=request.path,
            query_string=str(request.args)[:1000],
            request_body=str(request.data[:2000]) if request.data else None,
            response_status='pending',  # 将在 after_request 中更新
            details=json.dumps(details, ensure_ascii=False) if details else None,
            status=status,
            created_at=datetime.utcnow()
        )

        db.session.add(log_entry)

        # 存储到 g 对象以便在 after_request 中更新状态
        if not hasattr(g, 'audit_logs'):
            g.audit_logs = []
        g.audit_logs.append(log_entry)

        return log_entry

    except Exception as e:
        print(f"⚠️ 审计日志创建失败: {e}")
        return None


def audit_action(action_type, resource_type=None, **kwargs):
    """审计装饰器 - 自动记录操作"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs_func):
            # 记录开始时间
            start_time = time.time()

            # 提取资源 ID（从 URL 参数或函数参数）
            resource_id = kwargs_func.get('id') or kwargs_func.get('code') or kwargs.get('resource_id')

            # 创建审计日志
            log = create_audit_log(
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                details={
                    'function': f.__name__,
                    'args': list(kwargs_func.keys()),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            try:
                # 执行原始函数
                result = f(*args, **kwargs_func)

                # 更新审计日志状态
                if log:
                    if hasattr(result, 'status_code'):
                        log.response_status = str(result.status_code)
                        if result.status_code >= 400:
                            log.status = 'failure'
                        elif result.status_code == 401:
                            log.status = 'unauthorized'
                        elif result.status_code == 403:
                            log.status = 'forbidden'
                    else:
                        log.response_status = '200'
                        log.status = 'success'

                return result

            except Exception as e:
                # 记录异常到审计日志
                if log:
                    log.status = 'error'
                    log.details = json.dumps({
                        'error': str(e),
                        'error_type': type(e).__name__
                    }, ensure_ascii=False)
                raise

            finally:
                # 记录耗时
                if log:
                    log.duration_ms = int((time.time() - start_time) * 1000)

        return decorated_function
    return decorator


# ==================== 增强缓存 ====================

class CacheStats:
    """缓存统计"""
    hits = 0
    misses = 0
    errors = 0

    @classmethod
    def record_hit(cls):
        cls.hits += 1

    @classmethod
    def record_miss(cls):
        cls.misses += 1

    @classmethod
    def record_error(cls):
        cls.errors += 1

    @classmethod
    def get_stats(cls):
        total = cls.hits + cls.misses
        hit_rate = (cls.hits / total * 100) if total > 0 else 0
        return {
            'hits': cls.hits,
            'misses': cls.misses,
            'errors': cls.errors,
            'hit_rate': f'{hit_rate:.2f}%',
            'total_requests': total
        }

    @classmethod
    def reset(cls):
        cls.hits = 0
        cls.misses = 0
        cls.errors = 0


def cached_with_stats(prefix, ttl=None):
    """带统计功能的缓存装饰器"""
    from cache_utils import get_from_cache, set_to_cache, get_cache_key, CACHE_TTL

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_key = get_cache_key(prefix, request.path, str(sorted(request.args.items())))

            # 尝试从缓存获取
            try:
                cached_result = get_from_cache(cache_key)
                if cached_result is not None:
                    CacheStats.record_hit()
                    return cached_result
            except Exception as e:
                CacheStats.record_error()
                print(f"⚠️ 缓存读取失败: {e}")

            # 缓存未命中
            CacheStats.record_miss()

            # 执行函数
            result = f(*args, **kwargs)

            # 存入缓存
            try:
                set_to_cache(cache_key, result)
            except Exception as e:
                CacheStats.record_error()
                print(f"⚠️ 缓存写入失败: {e}")

            return result
        return wrapper
    return decorator


# ==================== 安全工具函数 ====================

def sanitize_input(text, max_length=10000):
    """输入清理 - 防止 XSS 和注入攻击"""
    if not text:
        return text

    text = str(text)

    # 截断过长文本
    if len(text) > max_length:
        text = text[:max_length]

    # 移除危险字符模式
    dangerous_patterns = [
        '<script', '</script>', 'javascript:', 'onerror=', 'onload=',
        'document.cookie', 'eval(', 'expression('
    ]

    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            text = text.replace(pattern, '')

    return text


def validate_education_stage(stage_code):
    """验证教育阶段代码的有效性"""
    valid_stages = ['9-year', 'high-school', 'university']
    return stage_code in valid_stages, stage_code


def security_headers(response):
    """添加安全响应头"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Cache-Control'] = 'no-cache'  # API 不允许客户端缓存
    response.headers['Pragma'] = 'no-cache'
    return response
