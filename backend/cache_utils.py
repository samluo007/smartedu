"""
缓存工具模块
为频繁访问的数据提供缓存支持，提升系统响应速度
"""
from functools import wraps
from flask import request
import time

# 简单内存缓存
_cache = {}
_cache_timestamps = {}
CACHE_TTL = 300  # 缓存有效期（秒），默认5分钟

def get_cache_key(prefix, *args):
    """生成缓存键"""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"

def get_from_cache(key):
    """从缓存获取数据"""
    if key in _cache:
        # 检查是否过期
        if time.time() - _cache_timestamps[key] < CACHE_TTL:
            return _cache[key]
        else:
            # 过期，删除缓存
            del _cache[key]
            del _cache_timestamps[key]
    return None

def set_to_cache(key, value):
    """设置缓存"""
    _cache[key] = value
    _cache_timestamps[key] = time.time()

def clear_cache(prefix=None):
    """清除缓存（可选按前缀清除）"""
    global _cache, _cache_timestamps
    if prefix:
        keys_to_delete = [k for k in _cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del _cache[key]
            del _cache_timestamps[key]
    else:
        _cache.clear()
        _cache_timestamps.clear()

def cached(prefix, ttl=None):
    """缓存装饰器
    
    Args:
        prefix: 缓存键前缀
        ttl: 缓存有效期（秒），默认使用 CACHE_TTL
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键（包含请求参数）
            cache_key = get_cache_key(prefix, request.path, str(sorted(request.args.items())))
            
            # 尝试从缓存获取
            cached_result = get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 缓存未命中，执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            set_to_cache(cache_key, result)
            
            return result
        return wrapper
    return decorator

# 常用缓存前缀
CACHE_PREFIX_EDUCATION_STAGES = 'education_stages'
CACHE_PREFIX_SUBJECTS = 'subjects'
CACHE_PREFIX_TEXTBOOKS = 'textbooks'
CACHE_PREFIX_KNOWLEDGE_POINTS = 'knowledge_points'
CACHE_PREFIX_STATISTICS = 'statistics'
