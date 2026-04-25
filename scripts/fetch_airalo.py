#!/usr/bin/env python3
import os
import json
import requests
import logging
from datetime import datetime, timezone
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    url = f"{AIRALO_BASE_URL}/v2/packages"
    headers = {"Authorization": f"Bearer {token}"}
    packages = []
    page = 1

    while True:
        resp = requests.get(url, headers=headers, params={"limit": 100, "page": page})
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

    # 첫 번째 패키지 구조 출력 (디버그)
    if packages:
        logger.info(f"첫 번째 패키지 키 목록: {list(packages[0].keys())}")
        logger.info(f"첫 번째 패키지 샘플: {json.dumps(packages[0], indent=2)[:500]}")

    logger.info(f"✅ 총 {len(packages)}개 패키지 수집 완료")
    return packages

def normalize(pkg: dict) -> dict:
    operators = pkg.get("operators") or []
    country_codes = []
    for op in operators:
        for country in op.get("countries") or []:
            code = country.get("country_code", "")
            if code:
                country_codes.append(code.upper())
    country_code = country_codes[0] if len(country_codes) == 1 else "MULTI"

    data_gb = None
    is_unlimited = False
    amount = pkg.get("amount")
    if amount:
        if amount >= 999999:
            is_unlimited = True
        else:
            data_gb = round(amount / 1024, 2)

    plan_id = pkg.get("package_id") or pkg.get("id") or pkg.get("slug")

    return {
        "provider":      "airalo",
        "plan_id":       str(plan_id) if plan_id else None,
        "plan_name":     pkg.get("title"),
        "country_code":  country_code,
        "country_codes": json.dumps(country_codes),
        "region":        pkg.get("region_slug", ""),
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

    batch_size = 100
    total = 0
    for i in range(0, len(plans), batch_size):
        batch = plans[i:i + batch_size]
        supabase.table("esim_plans").upsert(batch, on_conflict="provider,plan_id").execute()
        total += len(batch)
        logger.info(f"  저장 {total}/{len(plans)}")

    logger.info(f"✅ Supabase 저장 완료: {total}개")

def main():
    logger.info("=" * 50)
    logger.info("Airalo 패키지 수집 시작")
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
