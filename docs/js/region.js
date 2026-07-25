/* ===== wooabike — region.js ===== */
// REGION_NAME, REGION_SHORT, BIKE_RECORDS 은 각 HTML에서 전역 정의

let modalMap = null;
let modalInfowindow = null;
let kakaoLoaded = false;
let allRecords = [];
let currentTab = '전체';
let shownCount = 0;
const PAGE = 50;

// ── Kakao SDK 로드 ───────────────────────────────
function loadKakaoSDK() {
  return new Promise((resolve, reject) => {
    if (typeof kakao !== 'undefined' && kakao.maps) { resolve(); return; }
    const script = document.createElement('script');
    script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_APP_KEY}&libraries=services&autoload=false`;
    script.onload = () => kakao.maps.load(resolve);
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// ── 지도 모달 ────────────────────────────────────
function createMapModal() {
  if (document.getElementById('mapModal')) return;
  const modal = document.createElement('div');
  modal.id = 'mapModal';
  modal.innerHTML = `
    <div class="map-modal-backdrop"></div>
    <div class="map-modal-box">
      <div class="map-modal-header">
        <div class="map-modal-title" id="mapModalTitle"></div>
        <button class="map-modal-close" id="mapModalClose">✕</button>
      </div>
      <div class="map-modal-info" id="mapModalInfo"></div>
      <div id="mapModalMap"></div>
      <div class="map-modal-footer">
        <a id="mapModalNavi" href="#" class="btn-modal-navi">🗺️ 카카오맵 길찾기 →</a>
      </div>
    </div>`;
  document.body.appendChild(modal);

  document.getElementById('mapModalClose').addEventListener('click', closeMapModal);
  modal.querySelector('.map-modal-backdrop').addEventListener('click', closeMapModal);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMapModal(); });
}

function openMapModal(r) {
  createMapModal();
  const name = r['bcyclLendNm'] || '대여소';
  const addr = r['rdnmadr'] || r['lnmadr'] || '';
  const fee = buildFeeText(r);
  const hours = buildHoursText(r);
  const holder = r['holderCo'];

  document.getElementById('mapModalTitle').textContent = name;
  document.getElementById('mapModalInfo').innerHTML = `
    ${addr ? `<span>📍 ${addr}</span>` : ''}
    <span>💰 ${fee}</span>
    ${hours ? `<span>⏰ ${hours}</span>` : ''}
    ${holder ? `<span>🚲 ${holder}대</span>` : ''}`;

  const naviUrl = r['latitude']
    ? `https://map.kakao.com/link/to/${encodeURIComponent(name)},${r['latitude']},${r['longitude']}`
    : `https://map.kakao.com/link/search/${encodeURIComponent(name)}`;
  document.getElementById('mapModalNavi').href = naviUrl;

  document.getElementById('mapModal').classList.add('open');
  document.body.style.overflow = 'hidden';

  if (kakaoLoaded && r['latitude'] && r['longitude']) {
    setTimeout(() => initModalMap(r), 50);
  } else if (!r['latitude']) {
    document.getElementById('mapModalMap').innerHTML =
      '<div class="map-no-coord">📍 좌표 정보가 없어 지도를 표시할 수 없습니다.</div>';
  } else {
    document.getElementById('mapModalMap').innerHTML =
      '<div class="map-no-coord">🗺️ 지도는 서비스 배포 후 이용 가능합니다.</div>';
  }
}

function initModalMap(r) {
  const container = document.getElementById('mapModalMap');
  container.innerHTML = '';
  const lat = parseFloat(r['latitude']);
  const lng = parseFloat(r['longitude']);
  const pos = new kakao.maps.LatLng(lat, lng);

  modalMap = new kakao.maps.Map(container, { center: pos, level: 4 });
  modalInfowindow = new kakao.maps.InfoWindow({ zIndex: 1 });

  const marker = new kakao.maps.Marker({ map: modalMap, position: pos });
  modalInfowindow.setContent(buildInfoWindow(r));
  modalInfowindow.open(modalMap, marker);
}

function closeMapModal() {
  const modal = document.getElementById('mapModal');
  if (modal) modal.classList.remove('open');
  document.body.style.overflow = '';
  if (modalMap) {
    modalMap = null;
    const container = document.getElementById('mapModalMap');
    if (container) container.innerHTML = '';
  }
}

// ── 인포윈도우 ───────────────────────────────────
function buildInfoWindow(r) {
  const addr = r['rdnmadr'] || r['lnmadr'] || '';
  const fee = buildFeeText(r);
  const naviUrl = `https://map.kakao.com/link/to/${encodeURIComponent(r['bcyclLendNm'] || '')},${r['latitude']},${r['longitude']}`;
  return `
    <div class="iw-wrap">
      <div class="iw-title">${r['bcyclLendNm'] || '대여소'}</div>
      ${addr ? `<div class="iw-row">📍 ${addr}</div>` : ''}
      ${fee ? `<div class="iw-row">💰 ${fee}</div>` : ''}
      ${r['holderCo'] ? `<div class="iw-row">🚲 ${r['holderCo']}대</div>` : ''}
      <a href="${naviUrl}" class="iw-link">길찾기 →</a>
    </div>`;
}

// ── 요금 / 운영시간 ──────────────────────────────
function buildFeeText(r) {
  if (r['chrgeSe'] === '무료' || !r['chrgeSe']) return '무료';
  const use = r['bcyclUseCharge'];
  return use ? use : '유료';
}

function buildHoursText(r) {
  const s = r['operOpenHm'], e = r['operCloseHm'];
  if (!s && !e) return '';
  if (s === '00:00' && (e === '23:59' || e === '24:00')) return '24시간';
  return `${s || '?'} ~ ${e || '?'}`;
}

function isUnmanned(r) {
  return (r['bcyclLendSe'] || '').includes('무인');
}

// ── 카드 HTML ────────────────────────────────────
function buildCard(r, index) {
  const name = r['bcyclLendNm'] || '대여소';
  const addr = r['rdnmadr'] || r['lnmadr'] || '';
  const gubun = r['bcyclLendSe'] || '';
  const badgeClass = isUnmanned(r) ? 'badge-nowai' : 'badge-buset';
  const isFree = !r['chrgeSe'] || r['chrgeSe'] === '무료';
  const fee = buildFeeText(r);
  const feeBadge = isFree ? '<span class="badge badge-free">무료</span>' : '<span class="badge badge-paid">유료</span>';
  const hours = buildHoursText(r);
  const holder = r['holderCo'];
  const airInjector = r['airInjectorYn'] === 'Y';
  const repairStand = r['repairStandYn'] === 'Y';
  const naviUrl = r['latitude'] ? `https://map.kakao.com/link/to/${encodeURIComponent(name)},${r['latitude']},${r['longitude']}` : '#';

  return `
    <div class="parking-card" data-index="${index}">
      <div class="card-top">
        <div class="card-name">${name}</div>
      </div>
      <div class="badge-row">
        ${gubun ? `<span class="badge ${badgeClass}">${gubun}</span>` : ''}
        ${feeBadge}
        ${airInjector ? '<span class="badge badge-type">🔧 공기주입기</span>' : ''}
        ${repairStand ? '<span class="badge badge-type">🛠️ 수리대</span>' : ''}
      </div>
      <div class="card-info">
        ${addr ? `<div class="card-row"><span class="ci">📍</span><span>${addr}</span></div>` : ''}
        ${hours ? `<div class="card-row"><span class="ci">⏰</span><span>${hours}</span></div>` : ''}
        <div class="card-row"><span class="ci">💰</span><span>${fee}</span></div>
        ${holder ? `<div class="card-row"><span class="ci">🚲</span><span>보유 ${holder}대</span></div>` : ''}
        ${r['phoneNumber'] ? `<div class="card-row"><span class="ci">📞</span><span>${r['phoneNumber']}</span></div>` : ''}
      </div>
      <div class="card-actions">
        <button class="btn-map" data-index="${index}" onclick="event.stopPropagation()">🗺️ 지도에서 보기</button>
        ${r['latitude'] ? `<a href="${naviUrl}" class="btn-navi" onclick="event.stopPropagation()">길찾기 →</a>` : ''}
      </div>
    </div>`;
}

// ── 인라인 광고 ──────────────────────────────────
function buildInlineAd() {
  return `<div class="inline-ad">
    <div class="ad-label">📢 광고</div>
    <ins class="adsbygoogle" style="display:block;width:100%;height:90px"
      data-ad-client="ca-pub-6464921081676309"
      data-ad-slot="7080296704"
      data-ad-format="auto" data-full-width-responsive="true"></ins>
  </div>`;
}

function buildCardsWithAds(records, from, to) {
  const parts = [];
  for (let i = from; i < to; i++) {
    parts.push(buildCard(records[i], i));
    if ((i - from + 1) % 10 === 0 && i + 1 < to) parts.push(buildInlineAd());
  }
  return parts.join('');
}

// ── 목록 렌더링 ──────────────────────────────────
function renderList(records) {
  const listEl = document.getElementById('parkingList');
  const countEl = document.getElementById('listCount');
  const loadMoreWrap = document.getElementById('loadMore');
  const loadMoreBtn = document.getElementById('loadMoreBtn');
  if (!listEl) return;

  if (countEl) countEl.textContent = records.length.toLocaleString();

  if (records.length === 0) {
    listEl.innerHTML = '<div class="empty-state"><div class="ei">🚲</div><p>해당 구분의 대여소가 없습니다.</p></div>';
    if (loadMoreWrap) loadMoreWrap.style.display = 'none';
    return;
  }

  shownCount = Math.min(PAGE, records.length);
  listEl.innerHTML = buildCardsWithAds(records, 0, shownCount);

  if (loadMoreWrap && loadMoreBtn) {
    if (shownCount < records.length) {
      loadMoreBtn.textContent = `더 보기 (${(records.length - shownCount).toLocaleString()}개 남음)`;
      loadMoreWrap.style.display = 'block';
      loadMoreBtn.onclick = () => {
        const next = Math.min(shownCount + PAGE, records.length);
        const frag = document.createElement('div');
        frag.innerHTML = buildCardsWithAds(records, shownCount, next);
        while (frag.firstChild) listEl.insertBefore(frag.firstChild, loadMoreWrap);
        shownCount = next;
        if (shownCount >= records.length) loadMoreWrap.style.display = 'none';
        else loadMoreBtn.textContent = `더 보기 (${(records.length - shownCount).toLocaleString()}개 남음)`;
        bindCardEvents(listEl, records);
        try { (adsbygoogle = window.adsbygoogle || []).push({}); } catch(e) {}
      };
    } else {
      loadMoreWrap.style.display = 'none';
    }
  }

  bindCardEvents(listEl, records);
  try { (adsbygoogle = window.adsbygoogle || []).push({}); } catch(e) {}
}

function bindCardEvents(listEl, records) {
  listEl.querySelectorAll('.btn-map').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.index);
      openMapModal(records[idx]);
    });
  });
}

// ── 탭 필터 ──────────────────────────────────────
function filterByTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  let filtered;
  if (tab === '전체') {
    filtered = allRecords;
  } else if (tab === '무료') {
    filtered = allRecords.filter(r => !r['chrgeSe'] || r['chrgeSe'] === '무료');
  } else if (tab === '무인') {
    filtered = allRecords.filter(r => isUnmanned(r));
  } else if (tab === '유인') {
    filtered = allRecords.filter(r => !isUnmanned(r));
  } else {
    filtered = allRecords;
  }
  renderList(filtered);
}

// ── 키워드 검색 ──────────────────────────────────
function filterByKeyword(keyword) {
  const kw = keyword.trim().toLowerCase();
  const base = currentTab === '전체' ? allRecords
    : currentTab === '무료' ? allRecords.filter(r => !r['chrgeSe'] || r['chrgeSe'] === '무료')
    : currentTab === '무인' ? allRecords.filter(r => isUnmanned(r))
    : currentTab === '유인' ? allRecords.filter(r => !isUnmanned(r))
    : allRecords;
  const filtered = kw
    ? base.filter(r =>
        (r['bcyclLendNm'] || '').toLowerCase().includes(kw) ||
        (r['rdnmadr'] || '').toLowerCase().includes(kw) ||
        (r['lnmadr'] || '').toLowerCase().includes(kw)
      )
    : base;
  renderList(filtered);
}

// ── 초기화 ───────────────────────────────────────
async function init() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => filterByTab(btn.dataset.tab));
  });

  const searchInput = document.getElementById('regionSearchInput');
  const searchBtn = document.getElementById('regionSearchBtn');
  searchInput?.addEventListener('keydown', e => { if (e.key === 'Enter') filterByKeyword(searchInput.value); });
  searchBtn?.addEventListener('click', () => filterByKeyword(searchInput?.value || ''));

  if (typeof BIKE_RECORDS !== 'undefined') {
    allRecords = BIKE_RECORDS;
  }

  try {
    await loadKakaoSDK();
    kakaoLoaded = true;
  } catch {
    kakaoLoaded = false;
  }

  renderList(allRecords);
}

document.addEventListener('DOMContentLoaded', init);
