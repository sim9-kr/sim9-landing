#!/usr/bin/env python3
"""
eSIM Go 플랜 수집 스크립트
- eSIM Go Catalogue API에서 번들 목록 조회
- Supabase esim_plans 테이블에 저장
- GitHub Actions에서 매일 자동 실행
"""

import os
import json
import requests
import logging
from datetime import datetime, timezone
from supabase import create_client, Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ESIMGO_API_KEY = os.environ["ESIMGO_API_KEY"]
SUPABASE_URL   = os.environ["SUPABASE_URL"]
SUPABASE_KEY   = os.environ["SUPABASE_KEY"]

ESIMGO_BASE_URL = "https://api.esim-go.com/v2.4"

def fetch_catalogue() -> list:
    url = f"{ESIMGO_BASE_URL}/catalogue"
    headers = {"X-API-Key": ESIMGO_API_KEY}
    bundles = []
    page = 1

    while True:
        resp = requests.get(url, headers=headers, params={
            "page":    page,
            "perPage": 100,
        })
        resp.raise_for_status()
        data = resp.json()

        # 응답 구조 확인 (첫 페이지만)
        if page == 1:
            logger.info(f"응답 타입: {type(data)}")
            if isinstance(data, dict):
                logger.info(f"응답 키: {list(data.keys())}")
            logger.info(f"샘플: {json.dumps(data, indent=2)[:400]}")

        # dict면 bundles 또는 data 키에서 추출
        if isinstance(data, dict):
            batch = data.get("bundles") or data.get("data") or []
        else:
            batch = data

        if not batch:
            break

        bundles.extend(batch)
        logger.info(f"  페이지 {page}: {len(batch)}개 수집")

        if len(batch) < 100:
            break
        page += 1

    logger.info(f"✅ 총 {len(bundles)}개 번들 수집 완료")

    if bundles:
        logger.info(f"번들 타입: {type(bundles[0])}")
        if isinstance(bundles[0], dict):
            logger.info(f"번들 키: {list(bundles[0].keys())}")
            logger.info(f"번들 샘플: {json.dumps(bundles[0], indent=2)[:400]}")

    return bundles

def normalize(bundle: dict) -> dict:
    countries = bundle.get("countries") or []
    country_codes = [c.get("iso", "") for c in countries if c.get("iso")]
    country_code = country_codes[0] if len(country_codes) == 1 else "MULTI"

    data_amount = bundle.get("dataAmount")
    is_unlimited = bundle.get("unlimited", False)
    data_gb = None
    if data_amount and not is_unlimited:
        data_gb = round(data_amount / 1024, 2)

    price = bundle.get("price", 0)
    price_usd = round(price / 100, 2) if price > 100 else float(price)

    plan_id = bundle.get("name")

    return {
        "provider":      "esimgo",
        "plan_id":       str(plan_id) if plan_id else None,
        "plan_name":     bundle.get("description"),
        "country_code":  country_code,
        "country_codes": json.dumps(country_codes),
        "region":        countries[0].get("region", "") if countries else "",
        "plan_type":     "local" if len(country_codes) == 1 else "regional",
        "data_gb":       data_gb,
        "is_unlimited":  is_unlimited,
        "validity_days": bundle.get("duration"),
        "price_usd":     price_usd,
        "net_price_usd": price_usd,
        "affiliate_url": "https://esim-go.com",
        "updated_at":    datetime.now(timezone.utc).isoformat(),
    }

def upsert_to_supabase(plans: list, supabase: Client):
    if not plans:
        logger.warning("저장할 데이터 없음")
        return

    supabase.table("esim_plans").delete().eq("provider", "esimgo").execute()
    logger.info("기존 eSIM Go 데이터 삭제 완료")

    batch_size = 100
    total = 0
    for i in range(0, len(plans), batch_size):
        batch = plans[i:i + batch_size]
        supabase.table("esim_plans").insert(batch).execute()
        total += len(batch)
        logger.info(f"  저장 {total}/{len(plans)}")

    logger.info(f"✅ Supabase 저장 완료: {total}개")

def main():
    logger.info("=" * 50)
    logger.info("eSIM Go 카탈로그 수집 시작")
    logger.info("=" * 50)

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    bundles = fetch_catalogue()

    plans = []
    for b in bundles:
        if isinstance(b, dict):
            plans.append(normalize(b))
    plans = [p for p in plans if p.get("plan_id")]

    logger.info(f"✅ 정규화 완료: {len(plans)}개")
    upsert_to_supabase(plans, supabase)

    logger.info("=" * 50)
    logger.info("완료")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
