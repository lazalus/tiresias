"""
관리자 API 라우트
OpenAI 조직 비용과 같은 운영 통계를 제공합니다.
"""

from datetime import datetime, timezone
import json
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from flask import jsonify, request

from . import admin_bp
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('tiresias.api.admin')


def _bucket_date(bucket):
    start_iso = bucket.get('start_time_iso')
    if start_iso:
        return str(start_iso).split('T')[0]

    start_time = bucket.get('start_time')
    if start_time is None:
        return None

    try:
        return datetime.fromtimestamp(int(start_time), tz=timezone.utc).date().isoformat()
    except Exception:
        return None


@admin_bp.route('/openai-costs', methods=['GET'])
def get_openai_costs():
    """OpenAI 조직 비용을 조회합니다."""
    days = request.args.get('days', default=30, type=int) or 30
    days = max(1, min(days, 90))

    admin_key = request.headers.get('X-OpenAI-Admin-Key') or Config.OPENAI_ADMIN_KEY
    if not admin_key:
        return jsonify({
            'error': 'OPENAI_ADMIN_KEY가 구성되지 않았습니다.'
        }), 500

    start_time = int(datetime.now(tz=timezone.utc).timestamp()) - (days * 86400)

    all_buckets = []
    next_page = None

    try:
        for _ in range(5):
            params = {
                'start_time': start_time,
                'group_by': 'line_item',
                'limit': 31,
            }
            if next_page:
                params['page'] = next_page

            query = urlparse.urlencode(params)
            req = urlrequest.Request(
                f'https://api.openai.com/v1/organization/costs?{query}',
                headers={
                    'Authorization': f'Bearer {admin_key}',
                    'Content-Type': 'application/json',
                },
                method='GET',
            )

            with urlrequest.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))

            all_buckets.extend(data.get('data') or [])
            if not data.get('has_more'):
                break
            next_page = data.get('next_page')
            if not next_page:
                break

    except urlerror.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        logger.warning('OpenAI 비용 조회 HTTP 오류: status=%s body=%s', exc.code, body[:500])
        try:
            payload = json.loads(body)
            message = payload.get('error', {}).get('message') or payload.get('message') or body
        except Exception:
            message = body or str(exc)
        return jsonify({'error': message}), exc.code
    except Exception as exc:
        logger.exception('OpenAI 비용 조회 실패')
        return jsonify({'error': str(exc)}), 500

    total_cost = 0.0
    daily_costs = []
    for bucket in all_buckets:
        day_cost = 0.0
        for row in bucket.get('results') or []:
            amount = row.get('amount') or {}
            try:
                day_cost += float(amount.get('value') or 0)
            except (TypeError, ValueError):
                continue

        total_cost += day_cost
        day = _bucket_date(bucket)
        if day and day_cost > 0:
            daily_costs.append({
                'date': day,
                'cost_usd': round(day_cost, 3),
            })

    daily_costs.sort(key=lambda item: item['date'], reverse=True)

    return jsonify({
        'total_cost_usd': round(total_cost, 3),
        'total_cost_krw': round(total_cost * 1400),
        'days': days,
        'daily': daily_costs,
    })
