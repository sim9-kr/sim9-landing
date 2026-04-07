async function fetchSIM9Products() {
    try {
        var response = await fetch('https://api-sim9.sim9-kr.workers.dev/v1/products');
        var json = await response.json();
        var container = document.getElementById('product-container');
        var loadingMsg = document.getElementById('loading-msg');

        if (json.success) {
            loadingMsg.style.display = 'none';
            var displayData = json.data;

            displayData.forEach(function(product) {
                var retailPrice = product.Retail_KRW;
                
                var thumb = '/images/sim9_07.png';
                if(product.Region === 'Japan') thumb = '/images/sim9_01.png';
                if(product.Region === 'Vietnam') thumb = '/images/sim9_03.png';
                if(product.Region === 'Thailand') thumb = '/images/sim9_04.png';
                if(product.Region === 'India') thumb = '/images/sim9_05.png';
                if(product.Region === 'United States') thumb = '/images/sim9_02.png';
                if(product.Region === 'United Kingdom') thumb = '/images/sim9_08.png';

                var card = '<div style="background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 20px rgba(0,0,0,0.05); transition: transform 0.3s ease; border: 1px solid #f0f0f0;">';
                card += '<img src="' + thumb + '" style="width: 100%; height: 160px; object-fit: cover;">';
                card += '<div style="padding: 20px;">';
                card += '<div style="font-size: 0.8rem; color: #ff4757; font-weight: bold; margin-bottom: 5px; text-transform: uppercase;">' + product.Region + '</div>';
                card += '<h3 style="font-size: 1.1rem; margin: 0 0 15px 0; color: #222; height: 45px; overflow: hidden;">' + product.Name + '</h3>';
                card += '<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 20px;">';
                card += '<span style="font-size: 1.5rem; font-weight: 800; color: #222;">\u20A9' + retailPrice.toLocaleString() + '</span>';
                card += '</div>';
                card += '<a href="https://shop.sim9.kr/product/detail.html?product_no=' + (product.id || 77) + '" target="_blank" style="display: block; text-align: center; background: #222; color: white; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 0.9rem;">상품 상세보기</a>';
                card += '</div></div>';

                container.insertAdjacentHTML('beforeend', card);
            });
        }
    } catch (error) {
        console.error('Data Load Error:', error);
        document.getElementById('loading-msg').innerText = '데이터를 불러올 수 없습니다.';
    }
}
fetchSIM9Products();
