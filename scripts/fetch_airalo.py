#!/usr/bin/env python3
"""
Airalo eSIM 플랜 수집 스크립트 v3
- operators → packages 직접 파싱
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

AIRALO_CLIENT_ID     = os.environ["AIRALO_CLIENT_ID"]
AIRALO_CLIENT_SECRET = os.environ["AIRALO_CLIENT_SECRET"]
SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_KEY         = os.environ["SUPABASE_KEY"]

AIRALO_BASE_URL = "https://partners-api.airalo.com"

def get_access_token() -> str:
    url = f"{AIRALO_BASE_URL}/v2/token"
    resp = requests.post(url, data={
        "client_id":     AIRALO_CLIENT_ID,
        "client_secret": AIRALO_CLIENT_SECRET,
        "grant_type":    "client_credentials",
    })
    resp.raise_for_status()
    token = resp.json()["data"]["access_token"]
    logger.info("✅ Airalo 토큰 발급 완료")
    return token

def fetch_raw(token: str) -> list:
    """국가별 operators 포함 전체 데이터 수집"""
    url = f"{AIRALO_BASE_URL}/v2/packages"
    headers = {"Authorization": f"Bearer {token}"}
    countries = []
    page = 1

    while True:
        resp = requests.get(url, headers=headers, params={
            "limit": 100,
            "page":  page,
        })
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("data", [])
        if not batch:
            break

        countries.extend(batch)
        logger.info(f"  페이지 {page}: {len(batch)}개 국가 수집")

        if not data.get("links", {}).get("next"):
            break
        page += 1

    logger.info(f"✅ 총 {len(countries)}개 국가 수집")
    return countries

def extract_plans(countries: list) -> list:
    """operators → packages 파싱해서 플랜 단위로 추출"""
    plans = []

    for country in countries:
        country_slug = country.get("slug", "")
        country_code = country.get("country_code", "")
        operators = country.get("operators") or []

        for operator in operators:
            operator_title = operator.get("title", "")
            operator_type  = operator.get("type", "local")
            packages = operator.get("packages") or []

            # 디버그: 첫 번째 operator 구조 출력
            if not plans and operator:
                logger.info(f"Operator 키: {list(operator.keys())}")
                logger.info(f"Packages 수: {len(packages)}")
                if packages:
                    logger.info(f"Package 샘플: {json.dumps(packages[0], indent=2)[:300]}")

            for pkg in packages:
                plan_id = pkg.get("package_id") or pkg.get("id")
                if not plan_id:
                    continue

                # 용량 파싱
                data_gb = None
                is_unlimited = pkg.get("is_unlimited", False)
                amount = pkg.get("amount")  # MB
                if amount and not is_unlimited:
                    data_gb = round(amount / 1024, 2)

                # 국가 코드
                countries_list = pkg.get("countries") or [country_code]
                c_code = countries_list[0] if len(countries_list) == 1 else "MULTI"

                plans.append({
                    "provider":      "airalo",
                    "plan_id":       str(plan_id),
                    "plan_name":     pkg.get("title") or f"{operator_title} {pkg.get('data', '')}",
                    "country_code":  c_code,
                    "country_codes": json.dumps(countries_list),
                    "region":        country_slug,
                    "plan_type":     operator_type,
                    "data_gb":       data_gb,
                    "is_unlimited":  is_unlimited,
                    "validity_days": pkg.get("day"),
                    "price_usd":     float(pkg.get("price", 0)),
                    "net_price_usd": float(pkg.get("net_price", 0)),
                    "affiliate_url": f"https://www.airalo.com/package/{plan_id}",
                    "updated_at":    datetime.now(timezone.utc).isoformat(),
                })

    logger.info(f"✅ 총 {len(plans)}개 플랜 추출")
    return plans

def upsert_to_supabase(plans: list, supabase: Client):
    if not plans:
        logger.warning("저장할 데이터 없음")
        return

    supabase.table("esim_plans").delete().eq("provider", "airalo").execute()
    logger.info("기존 Airalo 데이터 삭제 완료")

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
    logger.info("Airalo 패키지 수집 시작 v3")
    logger.info("=" * 50)

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    token = get_access_token()
    countries = fetch_raw(token)
    plans = extract_plans(countries)

    logger.info(f"✅ 최종 플랜 수: {len(plans)}개")
    upsert_to_supabase(plans, supabase)

    logger.info("=" * 50)
    logger.info("완료")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
