#!/usr/bin/env python3
"""
eSIM Access 플랜 수집 스크립트
- Package List API에서 상품 목록 조회
- Supabase esim_plans 테이블에 저장
"""

import os
import json
import hashlib
import time
import requests
import logging
from datetime import datetime, timezone
from supabase import create_client, Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ACCESS_CODE  = os.environ["ESIMACCESS_ACCESS_CODE"]
SECRET_KEY   = os.environ["ESIMACCESS_SECRET_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

BASE_URL = "https://api.esimaccess.com/api/v1/open"

def make_sign(timestamp: str) -> str:
    raw = ACCESS_CODE + timestamp + SECRET_KEY
    return hashlib.md5(raw.encode()).hexdigest().upper()

def get_headers() -> dict:
    timestamp = str(int(time.time() * 1000))
    return {
        "RT-AccessCode": ACCESS_CODE,
        "RT-Timestamp":  timestamp,
        "RT-Signature":  make_sign(timestamp),
        "Content-Type":  "application/json",
    }

def fetch_packages() -> list:
    url = f"{BASE_URL}/package/list"
    packages = []
    page = 1

    while True:
        payload = {
            "locationCode": "",
            "type": "BASE",
            "packageCode": "",
            "iccid": "",
            "pager": {"pageNum": page, "pageSize": 100}
        }
        resp = requests.post(url, headers=get_headers(), json=payload)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            logger.error(f"API 오류: {data}")
            break

        obj = data.get("obj", {})
        batch = obj.get("packageList") or obj.get("esimList") or []

        if not batch:
            break

        packages.extend(batch)
        logger.info(f"  페이지 {page}: {len(batch)}개 수집")

        total = obj.get("total", 0)
        if len(packages) >= total or len(batch) < 100:
            break
        page += 1

    logger.info(f"✅ 총 {len(packages)}개 수집 완료")
    return packages

def normalize(pkg: dict) -> dict:
    location = pkg.get("locationCode", "") or pkg.get("location", "")
    country_code = location.upper() if len(location) == 2 else "MULTI"

    # 용량: bytes → GB
    data_gb = None
    is_unlimited = False
    volume = pkg.get("volume") or pkg.get("dataAmount")
    if volume:
        gb = volume / 1024 / 1024 / 1024
        if gb >= 100:
            is_unlimited = True
        else:
            data_gb = round(gb, 2)

    # 가격: /1000 → USD
    price = pkg.get("price", 0) or pkg.get("retailPrice", 0)
    price_usd = round(float(price) / 1000, 2)

    net_price = pkg.get("wholesalePrice", 0) or price
    net_price_usd = round(float(net_price) / 1000, 2)

    plan_id = pkg.get("packageCode") or pkg.get("slug")

    return {
        "provider":      "esimaccess",
        "plan_id":       str(plan_id) if plan_id else None,
        "plan_name":     pkg.get("name") or pkg.get("packageName"),
        "country_code":  country_code,
        "country_codes": json.dumps([country_code]),
        "region":        pkg.get("region", ""),
        "plan_type":     "local" if len(location) == 2 else "regional",
        "data_gb":       data_gb,
        "is_unlimited":  is_unlimited,
        "validity_days": pkg.get("duration") or pkg.get("validity"),
        "price_usd":     price_usd,
        "net_price_usd": net_price_usd,
        "affiliate_url": "https://shop.sim9.kr",
        "updated_at":    datetime.now(timezone.utc).isoformat(),
    }

def upsert_to_supabase(plans: list, supabase: Client):
    if not plans:
        logger.warning("저장할 데이터 없음")
        return

    supabase.table("esim_plans").delete().eq("provider", "esimaccess").execute()
    logger.info("기존 esimaccess 데이터 삭제 완료")

    batch_size = 500
    total = 0
    for i in range(0, len(plans), batch_size):
        batch = plans[i:i + batch_size]
        supabase.table("esim_plans").insert(batch).execute()
        total += len(batch)
        logger.info(f"  저장 {total}/{len(plans)}")

    logger.info(f"✅ Supabase 저장 완료: {total}개")

def main():
    logger.info("=" * 50)
    logger.info("eSIM Access 패키지 수집 시작")
    logger.info("=" * 50)

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    packages = fetch_packages()

    plans = [normalize(p) for p in packages if isinstance(p, dict)]
    plans = [p for p in plans if p.get("plan_id")]

    logger.info(f"✅ 정규화 완료: {len(plans)}개")
    upsert_to_supabase(plans, supabase)

    logger.info("=" * 50)
    logger.info("완료")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
