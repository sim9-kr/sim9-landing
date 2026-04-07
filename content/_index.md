---
title: "SIM9"
description: "일본 여행, 더 가볍고 빠르게."
cascade:
  showDate: false
  showAuthor: false
  showReadingTime: false
  showEdit: false

# Blowfish의 '메인 히어로' 스타일 설정
layout: "homepage"
---

# 🇯🇵 일본 여행의 새로운 기준, SIM9
### "도착하자마자 바로 터지는 자유"

복잡한 설정 없이, 합리적인 가격으로 일본 어디서나 연결되세요. 
지금 바로 나에게 맞는 eSIM을 찾아보세요.

<br>

{{< button href="https://shop.sim9.kr/" target="_blank" >}}
eSIM 구매하러 가기
{{< /button >}}

{{< button href="/posts/guide" outline=true >}}
사용 가이드 보기
{{< /button >}}

<section id="esim-section" style="padding: 50px 0; max-width: 1200px; margin: 0 auto;">
    <h2 style="text-align: center; margin-bottom: 30px;">🌍 실시간 인기 eSIM 플랜</h2>
    <div id="product-container" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; padding: 0 20px;">
        <p id="loading-msg" style="text-align: center; grid-column: 1/-1;">상품 정보를 불러오는 중입니다...</p>
    </div>
</section>

<script>
async function fetchSIM9Products() {
    try {
        const response = await fetch('https://api.sim9.kr/v1/products');
        const json = await response.json();
        const container = document.getElementById('product-container');
        const loadingMsg = document.getElementById('loading-msg');

        if (json.success) {
            loadingMsg.style.display = 'none';
            // 모든 카테고리(TEST 포함)를 다 출력함
            const displayData = json.data;

            displayData.forEach(product => {
                const card = `
                    <div style="border: 1px solid #eee; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); background: #fff; display: flex; flex-direction: column;">
                        <div style="font-size: 0.9rem; color: #666; margin-bottom: 5px;">${product.Region}</div>
                        <h3 style="font-size: 1.2rem; margin: 0 0 15px 0; color: #333;">${product.Name}</h3>
                        <div style="margin-top: auto;">
                            <div style="font-size: 1.4rem; font-weight: bold; color: #007bff;">
                                ₩${product.Price_KRW.toLocaleString()}
                            </div>
                            <div style="font-size: 0.85rem; color: #999; margin-bottom: 15px;">
                                (약 ${product.Price_USD_Disp})
                            </div>
                            <a href="https://shop.sim9.kr/product/${product.Slug}" 
                               style="display: block; text-align: center; background: #333; color: #fff; padding: 10px; border-radius: 6px; text-decoration: none; font-size: 0.9rem;">
                               상품 상세보기
                            </a>
                        </div>
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', card);
            });
        }
    } catch (error) {
        console.error('데이터 로드 실패:', error);
        document.getElementById('loading-msg').innerText = '상품 정보를 불러오지 못했습니다.';
    }
}
// 페이지 로드 시 실행
fetchSIM9Products();
</script>
