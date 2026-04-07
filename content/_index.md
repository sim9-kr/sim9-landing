---
title: "SIM9 - 일본 여행의 새로운 기준"
description: "도착하자마자 바로 터지는 자유, SIM9 eSIM"
layout: "homepage"
cascade:
  showDate: false
  showAuthor: false
  showReadingTime: false
---

<section style="position: relative; padding: 120px 20px; background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('/images/sim9_06.png'); background-size: cover; background-position: center; color: white; text-align: center; border-radius: 20px; margin-bottom: 60px;">
    <h1 style="font-size: 3rem; font-weight: 800; margin-bottom: 20px; text-shadow: 2px 2px 10px rgba(0,0,0,0.5);">🇯🇵 일본 여행, 더 가볍고 빠르게.</h1>
    <p style="font-size: 1.5rem; margin-bottom: 40px; opacity: 0.9;">"도착하자마자 바로 터지는 자유, SIM9 eSIM"</p>
    <div style="display: flex; justify-content: center; gap: 15px;">
        <a href="https://shop.sim9.kr/" target="_blank" style="background: #ff4757; color: white; padding: 15px 35px; border-radius: 50px; font-weight: bold; text-decoration: none; transition: 0.3s;">eSIM 구매하러 가기</a>
        <a href="/posts/guide" style="background: rgba(255,255,255,0.2); color: white; padding: 15px 35px; border-radius: 50px; font-weight: bold; text-decoration: none; backdrop-filter: blur(5px);">사용 가이드 보기</a>
    </div>
</section>

<section style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin-bottom: 80px;">
    <div style="text-align: center; padding: 20px;">
        <img src="/images/sim9_08.png" style="width: 100%; border-radius: 15px; margin-bottom: 20px; height: 200px; object-fit: cover;">
        <h3>현지 망 직결</h3>
        <p style="color: #666;">소프트뱅크, NTT 도코모 등 현지 1위 사업자 망을 사용하여 끊김 없는 속도를 제공합니다.</p>
    </div>
    <div style="text-align: center; padding: 20px;">
        <img src="/images/sim9_02.png" style="width: 100%; border-radius: 15px; margin-bottom: 20px; height: 200px; object-fit: cover;">
        <h3>3분 개통 완료</h3>
        <p style="color: #666;">구매 즉시 이메일로 발송되는 QR코드로 공항에서 바로 개통하세요.</p>
    </div>
    <div style="text-align: center; padding: 20px;">
        <img src="/images/sim9_05.png" style="width: 100%; border-radius: 15px; margin-bottom: 20px; height: 200px; object-fit: cover;">
        <h3>24시간 고객지원</h3>
        <p style="color: #666;">일본 현지에서도, 한국에서도. 문제 발생 시 실시간으로 대응해 드립니다.</p>
    </div>
</section>

<hr style="border: 0; border-top: 1px solid #eee; margin: 60px 0;">

<section id="esim-section" style="max-width: 1200px; margin: 0 auto;">
    <h2 style="text-align: center; margin-bottom: 10px; font-size: 2rem;">🌍 실시간 인기 eSIM 플랜</h2>
    <p style="text-align: center; color: #999; margin-bottom: 40px;">실시간 환율이 적용된 최적의 가격을 확인하세요.</p>
    
    <div id="product-container" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; padding: 0 20px;">
        <p id="loading-msg" style="text-align: center; grid-column: 1/-1;">최신 플랜 정보를 불러오는 중입니다...</p>
    </div>
</section>

<script>
async function fetchSIM9Products() {
    try {
        // 확실히 작동하는 workers.dev 주소로 변경했습니다.
        const response = await fetch('https://api-sim9.sim9-kr.workers.dev/v1/products');
        const json = await response.json();
        const container = document.getElementById('product-container');
        const loadingMsg = document.getElementById('loading-msg');

        if (json.success) {
            loadingMsg.style.display = 'none';
            const displayData = json.data;

            displayData.forEach(product => {
                const testPrice = product.Price_KRW; // 현재 Worker 코드에서 이미 계산되어 나옵니다.
                
                // 국가별 썸네일 매칭 로직 (새로운 파일명으로 변경)
                let thumb = '/images/sim9_07.png';
                if(product.Region === 'Japan') thumb = '/images/sim9_01.png';
                if(product.Region === 'Vietnam') thumb = '/images/sim9_03.png';

                const card = `
                    <div style="background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 20px rgba(0,0,0,0.05); transition: transform 0.3s ease; border: 1px solid #f0f0f0;">
                        <img src="${thumb}" style="width: 100%; height: 160px; object-fit: cover;">
                        <div style="padding: 20px;">
                            <div style="font-size: 0.8rem; color: #ff4757; font-weight: bold; margin-bottom: 5px; text-transform: uppercase;">${product.Region}</div>
                            <h3 style="font-size: 1.1rem; margin: 0 0 15px 0; color: #222; height: 45px; overflow: hidden;">${product.Name}</h3>
                            <div style="display: flex; align-items: baseline; gap: 5px; margin-bottom: 20px;">
                                <span style="font-size: 1.5rem; font-weight: 800; color: #222;">₩${testPrice.toLocaleString()}</span>
                            </div>
                            <a href="https://shop.sim9.kr/product/detail.html?product_no=${product.id || 77}" 
                               target="_blank"
                               style="display: block; text-align: center; background: #222; color: white; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 0.9rem;">
                               상품 상세보기
                            </a>
                        </div>
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', card);
            });
        }
    } catch (error) {
        console.error('Data Load Error:', error);
        document.getElementById('loading-msg').innerText = '데이터를 불러올 수 없습니다. API 주소를 확인해 주세요.';
    }
}
fetchSIM9Products();
</script>
