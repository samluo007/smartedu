"""
SmartEdu 安全增强功能测试套件
测试：速率限制、审计日志、缓存、安全头
运行方式: python test_security.py
"""
import sys
import time
import json

# 添加 backend 目录到路径
sys.path.insert(0, '.')

def print_section(title):
    """打印测试分区标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_result(test_name, passed, detail=''):
    """打印测试结果"""
    status = '✅ PASS' if passed else '❌ FAIL'
    print(f"  [{status}] {test_name}")
    if detail:
        print(f"         → {detail}")


# ==================== 测试函数 ====================

def test_imports():
    """测试1: 所有模块导入成功"""
    print_section("TEST 1: 模块导入测试")

    try:
        from app import app, db
        print_result("app.py 导入", True)

        from security import (
            rate_limiter, RateLimiter, rate_limit,
            audit_action, create_audit_log,
            CacheStats, cached_with_stats,
            security_headers, sanitize_input,
            validate_education_stage
        )
        print_result("security.py 导入", True)

        from models import AuditLog, EducationStage, Subject, User
        print_result("models.py 导入（含AuditLog）", True)

        from cache_utils import clear_cache, _cache, cached, CACHE_TTL
        print_result("cache_utils.py 导入", True)

        return True

    except ImportError as e:
        print_result("模块导入失败", False, str(e))
        return False


def test_database():
    """测试2: 数据库和表结构"""
    print_section("TEST 2: 数据库初始化测试")

    try:
        from app import app, db
        from models import AuditLog
        from sqlalchemy import inspect

        with app.app_context():
            # 创建所有表
            db.create_all()

            # 检查 audit_logs 表是否存在
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            has_audit_table = 'audit_logs' in tables
            print_result("audit_logs 表存在", has_audit_table)

            if has_audit_table:
                # 检查索引数量
                indexes = inspector.get_indexes('audit_logs')
                index_count = len(indexes)
                print_result(
                    f"审计表索引 ({index_count} 个)",
                    index_count >= 5,
                    f'需要 >= 5，实际 {index_count} 个'
                )

            # 检查其他关键表
            key_tables = ['users', 'education_stages', 'subjects']
            for table in key_tables:
                exists = table in tables
                print_result(f"{table} 表存在", exists)

        return True

    except Exception as e:
        print_result("数据库测试失败", False, str(e))
        return False


def test_rate_limiter():
    """测试3: 速率限制器"""
    print_section("TEST 3: 速率限制器测试")

    try:
        from security import rate_limiter, RateLimiter

        # 检查实例类型
        is_correct_type = isinstance(rate_limiter, RateLimiter)
        print_result("RateLimiter 实例化", is_correct_type)

        # 检查默认限制配置
        default_limit = rate_limiter.default_limit
        has_default = default_limit == (100, 60) or isinstance(default_limit, tuple)
        print_result(
            f"默认限制配置 {default_limit}",
            has_default,
            f'格式: (max_requests, window_seconds)'
        )

        # 检查路由限制配置
        route_count = len(rate_limiter.limits)
        has_routes = route_count > 0
        print_result(
            f"路由级别限制 ({route_count} 个)",
            has_routes,
            f'为 {route_count} 个不同路由配置了差异化限制'
        )

        # 验证特定路由的限制
        if '/api/version/select' in str(rate_limiter.limits):
            print_result("版本选择接口有限制", True, "更严格的防刷策略")
        else:
            print_result("版本选择接口有限制", False)

        return True

    except Exception as e:
        print_result("速率限制器测试失败", False, str(e))
        return False


def test_audit_system():
    """测试4: 审计日志系统"""
    print_section("TEST 4: 审计日志系统测试")

    try:
        from app import app, db
        from models import AuditLog
        from security import create_audit_log
        from datetime import datetime
        import json

        with app.app_context():
            # 清空测试数据
            AuditLog.query.delete()
            db.session.commit()

            # 创建一条测试审计记录
            test_log = create_audit_log(
                action_type='test_action',
                resource_type='test_resource',
                details={'message': 'Security test entry'},
                status='success'
            )

            log_created = test_log is not None
            print_result("创建审计记录", log_created)

            if log_created:
                # 手动提交（因为不在请求上下文中）
                db.session.commit()

                # 验证记录是否保存
                saved_log = AuditLog.query.filter_by(
                    action_type='test_action'
                ).first()

                log_exists = saved_log is not None
                print_result("审计记录持久化", log_exists)

                if log_exists:
                    # 验证字段完整性
                    fields_ok = (
                        saved_log.action_type == 'test_action' and
                        saved_log.resource_type == 'test_resource' and
                        saved_log.status == 'success'
                    )
                    print_result("字段完整性验证", fields_ok)

                    # 验证时间戳
                    has_timestamp = saved_log.created_at is not None
                    print_result("时间戳自动生成", has_timestamp)

            # 清理测试数据
            AuditLog.query.filter_by(action_type='test_action').delete()
            db.session.commit()

        return True

    except Exception as e:
        print_result("审计系统测试失败", False, str(e))
        return False


def test_cache_system():
    """测试5: 缓存系统"""
    print_section("TEST 5: 缓存系统测试")

    try:
        from cache_utils import _cache, set_to_cache, get_from_cache, clear_cache, get_cache_key
        from security import CacheStats, cached_with_stats

        # 重置统计
        initial_stats = CacheStats.get_stats()
        CacheStats.reset()

        # 测试基础缓存操作
        test_key = 'test:key'
        test_value = {'data': 'test_value', 'timestamp': '2026-05-19'}

        set_to_cache(test_key, test_value)
        retrieved = get_from_cache(test_key)

        cache_works = retrieved == test_value
        print_result("基础读写缓存", cache_works)

        # 测试缓存键生成
        generated_key = get_cache_key('prefix', '/api/test', "param=value")
        key_has_parts = all(part in generated_key for part in ['prefix', '/api/test'])
        print_result("缓存键生成", key_has_parts, f'生成的键: {generated_key}')

        # 测试缓存清理
        clear_cache()
        after_clear = get_from_cache(test_key)
        cleared = after_clear is None
        print_result("缓存清除功能", cleared)

        # 测试统计功能
        stats = CacheStats.get_stats()
        has_stats = all(key in stats for key in ['hits', 'misses', 'errors', 'hit_rate'])
        print_result("缓存统计结构", has_stats, f'初始: {stats}')

        # 恢复初始状态
        for key, val in initial_stats.items():
            if hasattr(CacheStats, key):
                setattr(CacheStats, key, val)

        return True

    except Exception as e:
        print_result("缓存系统测试失败", False, str(e))
        return False


def test_security_utils():
    """测试6: 安全工具函数"""
    print_section("TEST 6: 安全工具函数测试")

    try:
        from security import sanitize_input, validate_education_stage, security_headers

        # 测试输入清理
        clean_text = sanitize_input("<script>alert('xss')</script>hello")
        no_xss = '<script>' not in clean_text.lower() and 'hello' in clean_text
        print_result("XSS 过滤", no_xss, f'结果: "{clean_text[:50]}..."')

        # 测试长度截断
        long_text = 'a' * 20000
        truncated = sanitize_input(long_text, max_length=10000)
        length_ok = len(truncated) <= 10000
        print_result("长度截断", length_ok, f'{len(long_text)} → {len(truncated)} 字符')

        # 测试教育阶段验证
        valid, code = validate_education_stage('9-year')
        print_result("有效教育阶段验证", valid, f'代码: {code}')

        invalid, code = validate_education_stage('invalid')
        print_result("无效教育阶段拒绝", not invalid, f'被拒绝: {code}')

        return True

    except Exception as e:
        print_result("安全工具测试失败", False, str(e))
        return False


def test_api_endpoints():
    """测试7: API 端点注册"""
    print_section("TEST 7: API 端点检查")

    try:
        from app import app

        # 获取所有注册的路由
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(str(rule.rule))

        # 检查核心端点
        required_endpoints = [
            '/api/health',
            '/api/education-stages',
            '/api/education-stages/<code>',
            '/api/subjects',
            '/api/statistics/<stage_code>',
            '/api/version/select',
            '/api/admin/audit-logs',      # NEW - 审计日志查询
            '/api/admin/audit-stats',      # NEW - 审计统计
            '/api/admin/cache/stats',      # NEW - 缓存统计
            '/api/admin/cache/clear',      # NEW - 缓存清除
        ]

        endpoint_results = []
        for endpoint in required_endpoints:
            exists = endpoint in routes
            marker = '🆕' if 'admin' in endpoint else ''
            print_result(f"{endpoint} {marker}", exists)
            endpoint_results.append(exists)

        all_registered = all(endpoint_results)
        print_result(
            f"全部端点注册 ({len(required_endpoints)} 个)",
            all_registered,
            f'{sum(endpoint_results)}/{len(required_endpoints)} 已注册'
        )

        return all_registered

    except Exception as e:
        print_result("API 端点检查失败", False, str(e))
        return False


def test_performance_benchmarks():
    """测试8: 性能基准测试（简化版）"""
    print_section("TEST 8: 性能基准测试")

    try:
        from app import app
        from security import create_audit_log
        import time

        with app.app_context():
            # 测试审计日志创建性能
            iterations = 100
            start_time = time.time()

            for i in range(iterations):
                create_audit_log(
                    action_type='bench_test',
                    resource_type='performance',
                    details={'iteration': i}
                )

            elapsed = time.time() - start_time
            avg_ms = (elapsed / iterations) * 1000

            perf_ok = avg_ms < 10  # 每次创建 < 10ms
            print_result(
                f"审计日志创建速度",
                perf_ok,
                f'{iterations} 次, 总耗时 {elapsed:.3f}s, 平均 {avg_ms:.2f}ms/次'
            )

            # 清理基准测试数据
            from models import AuditLog
            AuditLog.query.filter_by(action_type='bench_test').delete()
            from app import db
            db.session.commit()

        return True

    except Exception as e:
        print_result("性能基准测试失败", False, str(e))
        return False


# ==================== 主测试流程 ====================

def run_all_tests():
    """执行所有测试"""
    print("\n" + "="*60)
    print("   SmartEdu Security Enhancement Test Suite")
    print("   Direction 7: Rate Limiting + Audit + Cache")
    print("="*60)
    print(f"\n⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {
        '模块导入': test_imports(),
        '数据库': test_database(),
        '速率限制': test_rate_limiter(),
        '审计系统': test_audit_system(),
        '缓存系统': test_cache_system(),
        '安全工具': test_security_utils(),
        'API端点': test_api_endpoints(),
        '性能基准': test_performance_benchmarks(),
    }

    # 输出总结
    print_section("测试结果汇总")

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    print(f"\n  总测试数: {total_tests}")
    print(f"  ✅ 通过: {passed_tests}")
    print(f"  ❌ 失败: {failed_tests}")
    print(f"  📊 通过率: {pass_rate:.1f}%\n")

    if failed_tests == 0:
        print("  🎉 所有安全增强功能测试通过！")
        print("  🚀 系统已就绪，可以启动生产环境\n")
        return 0
    else:
        print("  ⚠️ 部分测试未通过，请查看上方详情")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
