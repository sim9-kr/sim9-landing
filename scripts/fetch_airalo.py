#!/usr/bin/env python3
"""
Airalo eSIM 플랜 수집 스크립트 v2
- flat=true 파라미터로 실제 플랜 데이터 수집
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

def fetch_packages(token: str) -> list:
    """flat=true로 실제 플랜 데이터 수집"""
    url = f"{AIRALO_BASE_URL}/v2/packages"
    headers = {"Authorization": f"Bearer {token}"}
    packages = []
    page = 1

    while True:
        resp = requests.get(url, headers=headers, params={
            "flat":  "true",  # 핵심: 플랜 단위로 펼쳐서 반환
            "limit": 100,
            "page":  page,
        })
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("data", [])
        if not batch:
            break

        packages.extend(batch)
        logger.info(f"  페이지 {page}: {len(batch)}개 수집")

        if not data.get("links", {}).get("next"):
            break
        page += 1

    logger.info(f"✅ 총 {len(packages)}개 패키지 수집 완료")

    # 첫 번째 패키지 구조 확인
    if packages:
        logger.info(f"샘플 키: {list(packages[0].keys())}")
        logger.info(f"샘플 데이터: {json.dumps(packages[0], indent=2)[:300]}")

    return packages

def normalize(pkg: dict) -> dict:
    """flat 응답 구조 정규화"""
    # 국가 코드
    countries = pkg.get("countries") or []
    country_code = countries[0] if len(countries) == 1 else "MULTI"

    # 용량
    data_gb = None
    is_unlimited = pkg.get("is_unlimited", False)
    amount = pkg.get("amount")  # MB 단위
    if amount and not is_unlimited:
        data_gb = round(amount / 1024, 2)

    plan_id = pkg.get("package_id") or pkg.get("slug")

    return {
        "provider":      "airalo",
        "plan_id":       str(plan_id) if plan_id else None,
        "plan_name":     pkg.get("title"),
        "country_code":  country_code,
        "country_codes": json.dumps(countries),
        "region":        pkg.get("slug", ""),
        "plan_type":     pkg.get("type", "local"),
        "data_gb":       data_gb,
        "is_unlimited":  is_unlimited,
        "validity_days": pkg.get("day"),
        "price_usd":     float(pkg.get("price", 0)),
        "net_price_usd": float(pkg.get("net_price", 0)),
        "affiliate_url": f"https://www.airalo.com/package/{plan_id}",
        "updated_at":    datetime.now(timezone.utc).isoformat(),
    }

def upsert_to_supabase(plans: list, supabase: Client):
    if not plans:
        logger.warning("저장할 데이터 없음")
        return

    # 기존 데이터 삭제 후 새로 저장
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
    logger.info("Airalo 패키지 수집 시작 v2")
    logger.info("=" * 50)

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    token = get_access_token()
    packages = fetch_packages(token)

    plans = [normalize(pkg) for pkg in packages]
    plans = [p for p in plans if p.get("plan_id")]

    logger.info(f"✅ 정규화 완료: {len(plans)}개")
    upsert_to_supabase(plans, supabase)

    logger.info("=" * 50)
    logger.info("완료")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
