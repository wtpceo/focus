// 할인율
const discountRates = {
    "none": 0,
    "5": 0.05,
    "10": 0.10,
    "15": 0.15
};

// 아파트 카운터
let apartmentCounter = 0;

// 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 첫 번째 아파트 추가
    addApartment();

    // 개월수 선택 이벤트
    document.querySelectorAll('input[name="months"]').forEach(radio => {
        radio.addEventListener('change', updateTotalCalculation);
    });

    // 할인 선택 이벤트
    document.querySelectorAll('input[name="discount"]').forEach(radio => {
        radio.addEventListener('change', updateTotalCalculation);
    });
});

// 아파트 추가
function addApartment() {
    apartmentCounter++;
    const apartmentList = document.getElementById('apartment-list');

    const apartmentHtml = `
        <div class="apartment-item" data-id="${apartmentCounter}">
            <div class="apartment-header">
                <span class="apartment-number">아파트 ${apartmentCounter}</span>
                ${apartmentCounter > 1 ? `<button type="button" class="btn-remove" onclick="removeApartment(${apartmentCounter})">삭제</button>` : ''}
            </div>
            <div class="form-grid">
                <div class="form-group">
                    <label>아파트명</label>
                    <input type="text" class="apt-name" data-id="${apartmentCounter}" placeholder="OO아파트" oninput="updateTotalCalculation()">
                </div>
                <div class="form-group">
                    <label>모니터 대수</label>
                    <input type="number" class="apt-monitor" data-id="${apartmentCounter}" placeholder="0" min="0" value="0" oninput="updateTotalCalculation()">
                </div>
                <div class="form-group">
                    <label>대당 단가 (원)</label>
                    <input type="number" class="apt-price" data-id="${apartmentCounter}" placeholder="0" min="0" value="0" oninput="updateTotalCalculation()">
                </div>
                <div class="form-group">
                    <label>월 견적</label>
                    <div class="monthly-display" id="monthly-${apartmentCounter}">0원</div>
                </div>
            </div>
        </div>
    `;

    apartmentList.insertAdjacentHTML('beforeend', apartmentHtml);
    updateTotalCalculation();
}

// 아파트 삭제
function removeApartment(id) {
    const item = document.querySelector(`.apartment-item[data-id="${id}"]`);
    if (item) {
        item.remove();
        updateTotalCalculation();
    }
}

// 전체 계산 업데이트
function updateTotalCalculation() {
    let totalMonthly = 0;

    // 각 아파트별 월 견적 계산
    document.querySelectorAll('.apartment-item').forEach(item => {
        const id = item.dataset.id;
        const monitorCount = parseInt(item.querySelector('.apt-monitor').value) || 0;
        const unitPrice = parseInt(item.querySelector('.apt-price').value) || 0;
        const monthly = monitorCount * unitPrice;

        // 개별 월 견적 표시
        document.getElementById(`monthly-${id}`).textContent = monthly.toLocaleString() + '원';

        totalMonthly += monthly;
    });

    // 총 월 견적 표시
    document.getElementById('total-monthly').textContent = totalMonthly.toLocaleString() + '원';

    // 할인 계산
    const discountKey = document.querySelector('input[name="discount"]:checked').value;
    const discountRate = discountRates[discountKey] || 0;
    const discountAmount = Math.floor(totalMonthly * discountRate);
    const monthlyFinal = totalMonthly - discountAmount;

    // 할인 정보 표시
    const discountRow = document.getElementById('discount-row');
    if (discountRate > 0) {
        discountRow.style.display = 'flex';
        document.getElementById('discount-amount').textContent = '-' + discountAmount.toLocaleString() + '원';
    } else {
        discountRow.style.display = 'none';
    }

    // 월 최종 금액 표시
    document.getElementById('monthly-final').textContent = monthlyFinal.toLocaleString() + '원';

    // 개월수 계산
    const months = parseInt(document.querySelector('input[name="months"]:checked').value) || 3;
    const finalTotal = monthlyFinal * months;

    // 개월수 표시 업데이트
    document.getElementById('months-display').textContent = months;

    // 총 계약 금액 표시
    document.getElementById('final-total').textContent = finalTotal.toLocaleString() + '원';
}

// 아파트 데이터 수집
function collectApartments() {
    const apartments = [];
    document.querySelectorAll('.apartment-item').forEach(item => {
        const name = item.querySelector('.apt-name').value;
        const monitorCount = parseInt(item.querySelector('.apt-monitor').value) || 0;
        const unitPrice = parseInt(item.querySelector('.apt-price').value) || 0;

        if (name || monitorCount > 0) {
            apartments.push({
                apartment_name: name,
                monitor_count: monitorCount,
                unit_price: unitPrice,
                monthly_total: monitorCount * unitPrice
            });
        }
    });
    return apartments;
}

// 폼 데이터 수집
function collectFormData() {
    // 문서 유형 (복수 선택 가능)
    const docTypes = [];
    document.querySelectorAll('input[name="doc_type"]:checked').forEach(checkbox => {
        docTypes.push(checkbox.value);
    });

    const customer = {
        company: document.getElementById('company').value,
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value
    };

    const apartments = collectApartments();
    const discount = document.querySelector('input[name="discount"]:checked').value;
    const months = document.querySelector('input[name="months"]:checked').value;

    const manager = {
        name: document.getElementById('manager_name').value,
        position: document.getElementById('manager_position').value,
        phone: document.getElementById('manager_phone').value,
        email: document.getElementById('manager_email').value
    };

    const sendMethods = [];
    document.querySelectorAll('input[name="send_method"]:checked').forEach(checkbox => {
        sendMethods.push(checkbox.value);
    });

    return {
        doc_types: docTypes,
        customer,
        apartments,
        discount,
        months,
        manager,
        send_methods: sendMethods
    };
}

// 미리보기
async function preview() {
    const data = collectFormData();

    if (data.doc_types.length === 0) {
        alert('문서 유형을 하나 이상 선택해주세요.');
        return;
    }

    if (data.apartments.length === 0) {
        alert('아파트 정보를 하나 이상 입력해주세요.');
        return;
    }

    try {
        const response = await fetch('/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        showPreview(result);
    } catch (error) {
        alert('미리보기 생성 중 오류가 발생했습니다.');
        console.error(error);
    }
}

// 미리보기 표시
function showPreview(data) {
    // 문서 유형 표시
    let docTypeNames = [];
    if (data.doc_types.includes('proposal')) docTypeNames.push('제안서');
    if (data.doc_types.includes('estimate')) docTypeNames.push('견적서');
    const docTypeName = docTypeNames.join(' + ');
    const today = new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });

    let apartmentsHtml = '';
    data.apartments.forEach((apt, index) => {
        apartmentsHtml += `
            <div class="apartment-card">
                <div class="apartment-card-header">
                    <span class="apartment-index">${index + 1}</span>
                    <span class="apartment-name-display">${apt.apartment_name}</span>
                </div>
                <div class="apartment-card-body">
                    <div class="apartment-detail">
                        <span class="detail-label">모니터 대수</span>
                        <span class="detail-value">${apt.monitor_count}대</span>
                    </div>
                    <div class="apartment-detail">
                        <span class="detail-label">대당 단가</span>
                        <span class="detail-value">${apt.unit_price.toLocaleString()}원</span>
                    </div>
                    <div class="apartment-detail highlight">
                        <span class="detail-label">월 견적</span>
                        <span class="detail-value">${apt.monthly_total.toLocaleString()}원</span>
                    </div>
                </div>
            </div>
        `;
    });

    let discountHtml = '';
    if (data.discount_rate > 0) {
        discountHtml = `
            <div class="summary-row discount">
                <span>${data.discount_label}</span>
                <span>-${data.discount_amount.toLocaleString()}원</span>
            </div>
        `;
    }

    const html = `
        <div class="preview-document">
            <!-- 헤더 -->
            <div class="preview-header">
                <div class="doc-title">${docTypeName}</div>
                <div class="doc-date">${today}</div>
            </div>

            <!-- 수신자 정보 -->
            <div class="preview-recipient">
                <div class="recipient-label">수 신</div>
                <div class="recipient-info">
                    <div class="company-name">${data.customer.company || '-'}</div>
                    <div class="contact-name">${data.customer.name || '-'} 님 귀하</div>
                </div>
            </div>

            <!-- 인사말 -->
            <div class="preview-greeting">
                <p>안녕하세요, <strong>(주)위즈더플래닝</strong>입니다.</p>
                <p>귀사의 무궁한 발전을 기원하며, 아래와 같이 ${docTypeName}을 송부드립니다.</p>
                ${data.doc_types.includes('proposal') ? '<p class="attachment-notice">📎 포커스미디어 제안서 PDF가 함께 첨부됩니다.</p>' : ''}
            </div>

            <!-- 광고 내역 -->
            <div class="preview-content-section">
                <div class="section-title">
                    <span class="title-icon">📋</span>
                    <span>포커스미디어 광고 내역</span>
                </div>
                <div class="apartments-list-preview">
                    ${apartmentsHtml}
                </div>
            </div>

            <!-- 금액 요약 -->
            <div class="preview-summary">
                <div class="summary-box">
                    <div class="summary-row">
                        <span>총 월 견적</span>
                        <span>${data.total_monthly.toLocaleString()}원</span>
                    </div>
                    ${discountHtml}
                    <div class="summary-row highlight">
                        <span>월 최종 금액</span>
                        <span>${data.monthly_final.toLocaleString()}원</span>
                    </div>
                    <div class="summary-divider"></div>
                    <div class="summary-row total">
                        <span>총 계약 금액 (${data.months}개월)</span>
                        <span class="total-amount">${data.final_total.toLocaleString()}원</span>
                    </div>
                    <div class="vat-notice">※ 부가세 별도</div>
                </div>
            </div>

            <!-- 비고 -->
            <div class="preview-notes">
                <div class="section-title">
                    <span class="title-icon">📌</span>
                    <span>안내사항</span>
                </div>
                <ul>
                    <li>본 ${docTypeName}의 유효기간은 발행일로부터 30일입니다.</li>
                    <li>세부 사항은 협의 후 조정될 수 있습니다.</li>
                    <li>문의사항이 있으시면 아래 담당자에게 연락 부탁드립니다.</li>
                </ul>
            </div>

            <!-- 발신자 정보 -->
            <div class="preview-sender">
                <div class="sender-company">
                    <div class="company-logo">(주)위즈더플래닝</div>
                    <div class="company-details">
                        <p>사업자번호: 668-81-00391</p>
                        <p>주소: 서울시 금천구 디지털로 178 A동 2518호, 19호</p>
                        <p>대표전화: 1670-0704</p>
                    </div>
                </div>
                ${data.manager && data.manager.name ? `
                <div class="sender-manager">
                    <div class="manager-title">담당자</div>
                    <div class="manager-info">
                        <p><strong>${data.manager.name}</strong> ${data.manager.position || ''}</p>
                        ${data.manager.phone ? `<p>Tel: ${data.manager.phone}</p>` : ''}
                        ${data.manager.email ? `<p>Email: ${data.manager.email}</p>` : ''}
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;

    document.getElementById('preview-content').innerHTML = html;
    document.getElementById('preview-modal').classList.add('show');
}

// 모달 닫기
function closeModal() {
    document.getElementById('preview-modal').classList.remove('show');
}

function closeResultModal() {
    document.getElementById('result-modal').classList.remove('show');
}

// PDF 생성 및 발송
async function generateAndSend() {
    closeModal();

    const data = collectFormData();

    if (data.doc_types.length === 0) {
        alert('문서 유형을 하나 이상 선택해주세요.');
        return;
    }

    if (data.apartments.length === 0) {
        alert('아파트 정보를 하나 이상 입력해주세요.');
        return;
    }

    if (data.send_methods.length === 0) {
        alert('발송 방법을 하나 이상 선택해주세요.');
        return;
    }

    if (data.send_methods.includes('email') && !data.customer.email) {
        alert('이메일 발송을 위해 이메일 주소를 입력해주세요.');
        return;
    }

    if (data.send_methods.includes('kakao') && !data.customer.phone) {
        alert('카카오톡 발송을 위해 연락처를 입력해주세요.');
        return;
    }

    try {
        const genResponse = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const genResult = await genResponse.json();

        if (!genResult.success) {
            alert('PDF 생성에 실패했습니다.');
            return;
        }

        const sendResponse = await fetch('/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pdf_paths: genResult.pdf_paths,
                customer: data.customer,
                send_methods: data.send_methods,
                doc_types: data.doc_types
            })
        });

        const sendResult = await sendResponse.json();
        showResult(sendResult, genResult.pdf_paths);

    } catch (error) {
        alert('처리 중 오류가 발생했습니다.');
        console.error(error);
    }
}

// 결과 표시
function showResult(result, pdfPaths) {
    let html = '';

    if (result.email !== null) {
        if (result.email.success) {
            html += `<div class="result-item result-success">✅ 이메일 발송 완료</div>`;
        } else {
            html += `<div class="result-item result-error">❌ 이메일 발송 실패: ${result.email.error || '알 수 없는 오류'}</div>`;
        }
    }

    if (result.kakao !== null) {
        if (result.kakao.success) {
            html += `<div class="result-item result-success">✅ 카카오톡 알림톡 발송 완료</div>`;
        } else {
            html += `<div class="result-item result-error">❌ 카카오톡 발송 실패: ${result.kakao.error || '알 수 없는 오류'}</div>`;
        }
    }

    html += `<div style="margin-top: 20px;">`;
    if (pdfPaths && pdfPaths.length > 0) {
        pdfPaths.forEach((path, idx) => {
            const fileName = path.split('/').pop();
            html += `<a href="/download/${path}" class="btn btn-secondary" download style="margin-right: 10px; margin-bottom: 10px;">${fileName}</a>`;
        });
    }
    html += `</div>`;

    document.getElementById('result-content').innerHTML = html;
    document.getElementById('result-modal').classList.add('show');
}
