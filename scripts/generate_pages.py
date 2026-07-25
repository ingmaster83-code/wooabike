#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wooabike 페이지 생성기 — 전국자전거대여소표준데이터 기반 지역별 페이지"""
import json
import os
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(BASE, "docs")
RAW_PATH = os.path.join(BASE, "scripts", "_bike_raw.json")

REGION_SHORT = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
    "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
    "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
    "강원특별자치도": "강원", "강원도": "강원", "충청북도": "충북",
    "충청남도": "충남", "전북특별자치도": "전북", "전라북도": "전북",
    "전라남도": "전남", "경상북도": "경북", "경상남도": "경남",
    "제주특별자치도": "제주", "제주도": "제주",
}

with open(RAW_PATH, encoding="utf-8") as f:
    raw = json.load(f)

# 신/구 지역명 통일 (예: 전북특별자치도 -> 전라북도)
REGION_CANON = {
    "전북특별자치도": "전라북도",
    "강원특별자치도": "강원도",
    "제주특별자치도": "제주도",
}
KNOWN_REGION_PREFIXES = sorted(
    {
        "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시",
        "대전광역시", "울산광역시", "세종특별자치시", "경기도",
        "강원특별자치도", "강원도", "충청북도", "충청남도",
        "전북특별자치도", "전라북도", "전라남도", "경상북도", "경상남도",
        "제주특별자치도", "제주도",
    },
    key=len, reverse=True,
)


def extract_region_city(addr):
    """공백 유무와 관계없이 알려진 시도 접두사로 지역/도시를 분리."""
    for prefix in KNOWN_REGION_PREFIXES:
        if addr.startswith(prefix):
            region = REGION_CANON.get(prefix, prefix)
            rest = addr[len(prefix):].strip()
            city = rest.split()[0] if rest else "기타"
            return region, city
    toks = addr.split()
    if not toks:
        return None, None
    return toks[0], (toks[1] if len(toks) > 1 else "기타")


by_region = defaultdict(lambda: defaultdict(list))
for it in raw:
    addr = it.get("rdnmadr") or it.get("lnmadr") or ""
    if not addr:
        continue
    region, city = extract_region_city(addr)
    if not region:
        continue
    by_region[region][city].append(it)

TOTAL = len(raw)
REGIONS = sorted(by_region.keys())

HEAD_STYLE = """<link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap" rel="stylesheet">"""


def esc(s):
    return (s or "").replace("&", "&amp;").replace('"', "&quot;")


def region_page(region, cities, depth):
    """depth: 0 = docs/지역/{region}.html, links use ../ once + 지역/{region}/{city}.html"""
    up = "../" * depth
    short = REGION_SHORT.get(region, region)
    all_records = [r for recs in cities.values() for r in recs]
    count = len(all_records)
    city_names = sorted(cities.keys())

    subnav = "".join(
        f'<a href="{esc(region)}/{esc(c)}.html" class="btn-sub-nav">{esc(c)} <span class="sub-cnt">{len(cities[c])}</span></a>'
        for c in city_names
    )

    records_json = json.dumps(all_records, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(short)} 자전거 대여소 {count}개 — 위치·요금·운영시간 | 우아자전거</title>
  <meta name="description" content="{esc(region)} 공공자전거 대여소 {count}개 위치와 요금을 한눈에. 무료·유료 대여소를 지도에서 바로 확인하세요.">
  <meta name="keywords" content="{esc(short)} 자전거 대여소,{esc(short)} 공공자전거,{esc(short)} 자전거 대여,{esc(short)} 따릉이">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://wooabike.wooahouse.com/지역/{esc(region)}.html">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{esc(short)} 자전거 대여소 {count}개 | 우아자전거">
  <meta property="og:description" content="{esc(region)} 공공자전거 대여소 {count}개 위치, 요금, 운영시간 안내">
  <meta property="og:url" content="https://wooabike.wooahouse.com/지역/{esc(region)}.html">
  <meta name="twitter:card" content="summary">
  {HEAD_STYLE}
  <link rel="stylesheet" href="{up}css/style.css">
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"CollectionPage",
   "name":"{esc(short)} 자전거 대여소 목록","url":"https://wooabike.wooahouse.com/지역/{esc(region)}.html",
   "description":"{esc(region)} 공공자전거 대여소 {count}개 위치, 요금, 운영시간"}}
  </script>
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a href="{up}" class="site-logo"><span class="logo-icon">🚲</span><span class="logo-text">우아자전거</span></a>
    <nav class="header-nav">
      <a href="{up}">대여소 찾기</a>
      <a href="{up}지역/" class="active-nav">지역별</a>
      <a href="https://wooahouse.com" target="_blank" rel="noopener">WooaHouse →</a>
    </nav>
    <button class="mobile-menu-btn" aria-label="메뉴">☰</button>
  </div>
<script src="{up}js/wooa-sites-bar.js"></script>
</header>

<section class="region-hero">
  <nav class="breadcrumb-hero">
    <a href="{up}">홈</a> <span>›</span> <span>지역별</span> <span>›</span> <span>{esc(region)}</span>
  </nav>
  <h1>🚲 {esc(region)} 자전거 대여소</h1>
  <p class="sub">{count}개 자전거 대여소 위치, 요금, 운영시간을 확인하세요</p>
  <p class="keywords">{esc(short)} 자전거 대여소 · {esc(short)} 공공자전거 · {esc(short)} 무료 대여소</p>
  <div class="region-search-bar">
    <input type="text" id="regionSearchInput" placeholder="대여소명 또는 주소 검색">
    <button id="regionSearchBtn">검색</button>
  </div>
</section>

<div class="sub-nav-bar">
  <div class="sub-nav-inner">
    <span class="sub-nav-label">{esc(short)} 시/군/구 선택</span>
    <div class="sub-nav-btns">
      {subnav}
    </div>
  </div>
</div>

<div class="tab-bar">
  <div class="tab-inner">
    <button class="tab-btn active" data-tab="전체">전체 <span class="tab-cnt">{count}</span></button>
    <button class="tab-btn" data-tab="무료">무료</button>
    <button class="tab-btn" data-tab="무인">무인대여소</button>
    <button class="tab-btn" data-tab="유인">유인대여소</button>
  </div>
</div>

<div class="tab-bottom-ad">
  <ins class="adsbygoogle" style="display:inline-block;width:728px;max-width:100%;height:90px"
       data-ad-client="ca-pub-6464921081676309" data-ad-slot="7080296704"></ins>
</div>

<div class="region-layout">
  <div class="region-list-col">
    <div class="result-header">
      <div class="result-count">총 <strong id="listCount">{count}</strong>개</div>
      <a href="{up}" class="result-back">← 전국 검색</a>
    </div>
    <div id="parkingList"></div>
    <div id="loadMore" style="text-align:center;margin:20px 0;display:none;">
      <button id="loadMoreBtn" style="padding:10px 28px;background:var(--primary);color:#fff;border-radius:8px;font-size:.9rem;font-weight:600;">더 보기</button>
    </div>
  </div>
  <div class="region-aside">
    <div id="region-map"><div class="map-placeholder"><div class="icon">🗺️</div><p>지도 로딩 중...</p></div></div>
    <div class="mid-ad" style="margin-top:16px;min-height:600px;">
      <div class="ad-label">📢 광고</div>
      <ins class="adsbygoogle" style="display:inline-block;width:300px;height:600px"
           data-ad-client="ca-pub-6464921081676309" data-ad-slot="6255378195"></ins>
    </div>
  </div>
</div>

<section class="seo-section">
  <h2>{esc(region)} 자전거 대여소 안내</h2>
  <p>{esc(region)}의 공공자전거 대여소는 총 {count}개소입니다.
  {esc(short)} 무료 대여소 및 유료 대여소 요금·운영시간을 위 목록에서 확인하시고,
  지도보기·길찾기 버튼으로 바로 이동하세요.</p>
</section>

<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-grid">
      <div class="footer-col"><p class="footer-logo">🚲 우아자전거</p><p>전국 공공자전거 대여소 정보<br>설치 불필요 · 로그인 불필요</p><a href="https://wooahouse.com" target="_blank" style="color:#10B981;margin-top:8px;display:inline-block;">wooahouse.com →</a></div>
      <div class="footer-col"><p class="footer-heading">정보</p><a href="{up}privacy.html">개인정보처리방침</a><a href="{up}">메인으로</a></div>
    </div>
    <div class="footer-bottom"><p>&copy; 2026 WooaHouse. All rights reserved.</p><p>데이터 출처: 공공데이터포털 전국자전거대여소표준데이터</p></div>
  </div>
</footer>

<script src="{up}js/config.js"></script>
<script>
  const BIKE_RECORDS = {records_json};
  const REGION_NAME = '{esc(region)}';
  const REGION_SHORT = '{esc(short)}';
</script>
<script src="{up}js/region.js"></script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6464921081676309" crossorigin="anonymous"></script>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</body>
</html>"""
    return html


def city_page(region, city, records):
    short = REGION_SHORT.get(region, region)
    count = len(records)
    records_json = json.dumps(records, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(city)} 자전거 대여소 {count}개 — 위치·요금·운영시간 | 우아자전거</title>
  <meta name="description" content="{esc(region)} {esc(city)} 공공자전거 대여소 {count}개 위치와 요금 안내. {esc(city)} 무료 대여소 정보를 지도에서 바로 확인하세요.">
  <meta name="keywords" content="{esc(city)} 자전거 대여소,{esc(city)} 공공자전거,{esc(region)} {esc(city)} 자전거,{esc(short)} {esc(city)} 따릉이">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://wooabike.wooahouse.com/지역/{esc(region)}/{esc(city)}.html">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{esc(city)} 자전거 대여소 {count}개 | 우아자전거">
  <meta property="og:description" content="{esc(region)} {esc(city)} 공공자전거 대여소 {count}개 위치, 요금, 운영시간">
  <meta property="og:url" content="https://wooabike.wooahouse.com/지역/{esc(region)}/{esc(city)}.html">
  <meta name="twitter:card" content="summary">
  {HEAD_STYLE}
  <link rel="stylesheet" href="../../css/style.css">
  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"CollectionPage",
   "name":"{esc(city)} 자전거 대여소 목록","url":"https://wooabike.wooahouse.com/지역/{esc(region)}/{esc(city)}.html",
   "description":"{esc(region)} {esc(city)} 공공자전거 대여소 {count}개 위치, 요금, 운영시간"}}
  </script>
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a href="../../" class="site-logo"><span class="logo-icon">🚲</span><span class="logo-text">우아자전거</span></a>
    <nav class="header-nav">
      <a href="../../">대여소 찾기</a>
      <a href="../" class="active-nav">지역별</a>
      <a href="https://wooahouse.com" target="_blank" rel="noopener">WooaHouse →</a>
    </nav>
    <button class="mobile-menu-btn" aria-label="메뉴">☰</button>
  </div>
<script src="../../js/wooa-sites-bar.js"></script>
</header>

<section class="region-hero">
  <nav class="breadcrumb-hero">
    <a href="../../">홈</a> <span>›</span>
    <a href="../{esc(region)}.html">{esc(region)}</a> <span>›</span>
    <span>{esc(city)}</span>
  </nav>
  <h1>🚲 {esc(city)} 자전거 대여소</h1>
  <p class="sub">{count}개 자전거 대여소 위치, 요금, 운영시간을 확인하세요</p>
  <p class="keywords">{esc(city)} 자전거 대여소 · {esc(city)} 공공자전거 · {esc(region)} {esc(city)} 자전거</p>
  <div class="region-search-bar">
    <input type="text" id="regionSearchInput" placeholder="대여소명 또는 주소 검색">
    <button id="regionSearchBtn">검색</button>
  </div>
</section>

<div class="tab-bar">
  <div class="tab-inner">
    <button class="tab-btn active" data-tab="전체">전체 <span class="tab-cnt">{count}</span></button>
    <button class="tab-btn" data-tab="무료">무료</button>
    <button class="tab-btn" data-tab="무인">무인대여소</button>
    <button class="tab-btn" data-tab="유인">유인대여소</button>
  </div>
</div>

<div class="tab-bottom-ad">
  <ins class="adsbygoogle" style="display:inline-block;width:728px;max-width:100%;height:90px"
       data-ad-client="ca-pub-6464921081676309" data-ad-slot="7080296704"></ins>
</div>

<div class="region-layout">
  <div class="region-list-col">
    <div class="result-header">
      <div class="result-count">총 <strong id="listCount">{count}</strong>개</div>
      <a href="../{esc(region)}.html" class="result-back">← {esc(region)}</a>
    </div>
    <div id="parkingList"></div>
    <div id="loadMore" style="text-align:center;margin:20px 0;display:none;">
      <button id="loadMoreBtn" style="padding:10px 28px;background:var(--primary);color:#fff;border-radius:8px;font-size:.9rem;font-weight:600;">더 보기</button>
    </div>
  </div>
  <div class="region-aside">
    <div id="region-map"><div class="map-placeholder"><div class="icon">🗺️</div><p>지도 로딩 중...</p></div></div>
    <div class="mid-ad" style="margin-top:16px;min-height:600px;">
      <div class="ad-label">📢 광고</div>
      <ins class="adsbygoogle" style="display:inline-block;width:300px;height:600px"
           data-ad-client="ca-pub-6464921081676309" data-ad-slot="6255378195"></ins>
    </div>
  </div>
</div>

<section class="seo-section">
  <h2>{esc(city)} 자전거 대여소 안내</h2>
  <p>{esc(region)} {esc(city)}의 자전거 대여소는 총 {count}개소입니다.
  무료 대여소 및 유료 대여소 요금·운영시간을 위 목록에서 확인하시고,
  지도보기·길찾기 버튼으로 바로 이동하세요.
  {esc(region)} 전체 목록은 <a href="../{esc(region)}.html">{esc(region)} 대여소 페이지</a>에서 확인하세요.</p>
</section>

<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-grid">
      <div class="footer-col"><p class="footer-logo">🚲 우아자전거</p><p>전국 공공자전거 대여소 정보<br>설치 불필요 · 로그인 불필요</p><a href="https://wooahouse.com" target="_blank" style="color:#10B981;margin-top:8px;display:inline-block;">wooahouse.com →</a></div>
      <div class="footer-col"><p class="footer-heading">상위 지역</p><a href="../{esc(region)}.html">{esc(region)} 전체</a></div>
      <div class="footer-col"><p class="footer-heading">정보</p><a href="../../privacy.html">개인정보처리방침</a><a href="../../">메인으로</a></div>
    </div>
    <div class="footer-bottom"><p>&copy; 2026 WooaHouse. All rights reserved.</p><p>데이터 출처: 공공데이터포털 전국자전거대여소표준데이터</p></div>
  </div>
</footer>

<script src="../../js/config.js"></script>
<script>
  const BIKE_RECORDS = {records_json};
  const REGION_NAME = '{esc(city)}';
  const REGION_SHORT = '{esc(city)}';
</script>
<script src="../../js/region.js"></script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6464921081676309" crossorigin="anonymous"></script>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</body>
</html>"""
    return html


def index_page():
    cards = []
    for region in REGIONS:
        short = REGION_SHORT.get(region, region)
        count = sum(len(v) for v in by_region[region].values())
        cards.append(
            f'<a href="지역/{esc(region)}.html" class="region-card">'
            f'<span class="region-card-name">{esc(short)}</span>'
            f'<span class="region-card-count">{count}개</span></a>'
        )
    cards_html = "".join(cards)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>전국 자전거 대여소 찾기 — 공공자전거 위치·요금 | 우아자전거</title>
  <meta name="description" content="전국 {TOTAL:,}개 공공자전거 대여소 위치와 요금을 한눈에 확인하세요. 무료·유료 대여소, 무인·유인 대여소를 지역별로 검색할 수 있습니다.">
  <meta name="keywords" content="자전거 대여소,공공자전거,따릉이,자전거 대여,전국 자전거 대여소,무료 자전거">
  <meta name="robots" content="index, follow">
  <meta name="naver-site-verification" content="13c72c24b403c43188cd4220f66892cbb603f711" />
  <link rel="canonical" href="https://wooabike.wooahouse.com/">
  <meta property="og:type" content="website">
  <meta property="og:title" content="전국 자전거 대여소 찾기 | 우아자전거">
  <meta property="og:description" content="전국 {TOTAL:,}개 공공자전거 대여소 위치와 요금을 한눈에">
  <meta property="og:url" content="https://wooabike.wooahouse.com/">
  <meta name="twitter:card" content="summary">
  {HEAD_STYLE}
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a href="./" class="site-logo"><span class="logo-icon">🚲</span><span class="logo-text">우아자전거</span></a>
    <nav class="header-nav">
      <a href="./" class="active-nav">대여소 찾기</a>
      <a href="지역/">지역별</a>
      <a href="https://wooahouse.com" target="_blank" rel="noopener">WooaHouse →</a>
    </nav>
    <button class="mobile-menu-btn" aria-label="메뉴">☰</button>
  </div>
<script src="js/wooa-sites-bar.js"></script>
</header>

<section class="hero">
  <h1>🚲 전국 자전거 대여소 찾기</h1>
  <p class="sub">전국 {TOTAL:,}개 공공자전거 대여소 위치·요금·운영시간을 한눈에 확인하세요</p>
  <div class="region-search-bar" style="max-width:520px;margin:24px auto 0;">
    <input type="text" id="homeSearchInput" placeholder="지역명, 대여소명으로 검색">
    <button id="homeSearchBtn">검색</button>
  </div>
</section>

<div class="main-layout">
  <div class="main-col">
    <div class="tab-bottom-ad">
      <ins class="adsbygoogle" style="display:inline-block;width:728px;max-width:100%;height:90px"
           data-ad-client="ca-pub-6464921081676309" data-ad-slot="7080296704"></ins>
    </div>

    <section class="section">
      <h2 class="section-title" style="text-align:center;margin-bottom:24px;">📍 지역별로 찾기</h2>
      <div class="region-grid">
        {cards_html}
      </div>
    </section>

    <section class="seo-intro">
      <h2 style="font-size:1.2rem;font-weight:700;margin-bottom:16px;">우아자전거 — 전국 공공자전거 대여소 정보</h2>
      <p style="color:var(--text-muted);font-size:.9rem;line-height:1.9">
        <strong>우아자전거</strong>는 전국 지자체가 운영하는 공공자전거 대여소 위치, 요금, 운영시간을 한곳에서 검색할 수 있는 무료 서비스입니다.
        무인 대여소와 유인 대여소, 무료 대여소와 유료 대여소를 구분해서 확인할 수 있고,
        각 대여소의 정확한 주소와 지도, 길찾기까지 바로 연결됩니다.
        <br><br>
        서울·경기·인천 등 수도권부터 강원·충청·전라·경상·제주까지 전국 17개 시도의 자전거 대여소 정보를 지역별로 모아 확인하세요.
      </p>
    </section>
  </div>

  <aside class="sidebar">
    <div class="sidebar-box">
      <h3>💡 우아자전거란?</h3>
      <ul>
        <li>🚲 지자체가 운영하는 공공자전거</li>
        <li>💰 무료 · 유료 대여소 구분</li>
        <li>🙋 유인 · 무인 대여소 구분</li>
        <li>⏰ 운영시간 내 대여 가능</li>
        <li>📍 전국 약 {TOTAL:,}개소</li>
      </ul>
    </div>
    <div class="sidebar-ad">
      <ins class="adsbygoogle" style="display:inline-block;width:300px;height:600px"
           data-ad-client="ca-pub-6464921081676309" data-ad-slot="6255378195"></ins>
    </div>
  </aside>
</div>

<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-grid">
      <div class="footer-col"><p class="footer-logo">🚲 우아자전거</p><p>전국 공공자전거 대여소 정보<br>설치 불필요 · 로그인 불필요</p><a href="https://wooahouse.com" target="_blank" style="color:#10B981;margin-top:8px;display:inline-block;">wooahouse.com →</a></div>
      <div class="footer-col"><p class="footer-heading">관련 사이트</p><a href="https://wooaparking.wooahouse.com" target="_blank">🅿️ 우아파킹 (주차장)</a><a href="https://wooatrail.wooahouse.com" target="_blank">🥾 우아트레일 (둘레길)</a></div>
      <div class="footer-col"><p class="footer-heading">정보</p><a href="privacy.html">개인정보처리방침</a></div>
    </div>
    <div class="footer-bottom"><p>&copy; 2026 WooaHouse. All rights reserved.</p><p>데이터 출처: 공공데이터포털 전국자전거대여소표준데이터</p></div>
  </div>
</footer>

<script src="js/config.js"></script>
<script>
  document.getElementById('homeSearchBtn').addEventListener('click', doSearch);
  document.getElementById('homeSearchInput').addEventListener('keydown', e => {{ if (e.key === 'Enter') doSearch(); }});
  function doSearch() {{
    const q = document.getElementById('homeSearchInput').value.trim();
    if (q) location.href = '지역/?q=' + encodeURIComponent(q);
  }}
</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6464921081676309" crossorigin="anonymous"></script>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</body>
</html>"""


def region_index_page():
    cards = []
    for region in REGIONS:
        short = REGION_SHORT.get(region, region)
        count = sum(len(v) for v in by_region[region].values())
        cards.append(
            f'<a href="{esc(region)}.html" class="region-card">'
            f'<span class="region-card-name">{esc(short)}</span>'
            f'<span class="region-card-count">{count}개</span></a>'
        )
    cards_html = "".join(cards)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>지역별 자전거 대여소 — 전국 17개 시도 | 우아자전거</title>
  <meta name="description" content="전국 17개 시도별 공공자전거 대여소 목록. 지역을 선택해서 대여소 위치와 요금을 확인하세요.">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://wooabike.wooahouse.com/지역/">
  {HEAD_STYLE}
  <link rel="stylesheet" href="../css/style.css">
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a href="../" class="site-logo"><span class="logo-icon">🚲</span><span class="logo-text">우아자전거</span></a>
    <nav class="header-nav">
      <a href="../">대여소 찾기</a>
      <a href="./" class="active-nav">지역별</a>
      <a href="https://wooahouse.com" target="_blank" rel="noopener">WooaHouse →</a>
    </nav>
    <button class="mobile-menu-btn" aria-label="메뉴">☰</button>
  </div>
<script src="../js/wooa-sites-bar.js"></script>
</header>
<section class="hero">
  <h1>📍 지역별 자전거 대여소</h1>
  <p class="sub">전국 17개 시도 중 지역을 선택하세요</p>
</section>
<section class="section" style="max-width:1100px;margin:0 auto;padding:40px 20px;">
  <div class="region-grid">
    {cards_html}
  </div>
</section>
<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-bottom"><p>&copy; 2026 WooaHouse. All rights reserved.</p></div>
  </div>
</footer>
</body>
</html>"""


def main():
    os.makedirs(os.path.join(DOCS, "지역"), exist_ok=True)

    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_page())

    with open(os.path.join(DOCS, "지역", "index.html"), "w", encoding="utf-8") as f:
        f.write(region_index_page())

    for region, cities in by_region.items():
        region_dir = os.path.join(DOCS, "지역", region)
        os.makedirs(region_dir, exist_ok=True)
        with open(os.path.join(DOCS, "지역", f"{region}.html"), "w", encoding="utf-8") as f:
            f.write(region_page(region, cities, depth=1))
        for city, records in cities.items():
            with open(os.path.join(region_dir, f"{city}.html"), "w", encoding="utf-8") as f:
                f.write(city_page(region, city, records))

    write_sitemap()

    total_pages = 2 + len(REGIONS) + sum(len(v) for v in by_region.values())
    print(f"생성 완료: 시도 {len(REGIONS)}개, 시군구 {sum(len(v) for v in by_region.values())}개, 총 {total_pages}개 페이지")


def write_sitemap():
    urls = ["https://wooabike.wooahouse.com/"]
    for region, cities in by_region.items():
        urls.append(f"https://wooabike.wooahouse.com/지역/{region}.html")
        for city in cities:
            urls.append(f"https://wooabike.wooahouse.com/지역/{region}/{city}.html")
    entries = "\n".join(
        f"  <url><loc>{u}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>"
        for u in urls
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n'
    with open(os.path.join(DOCS, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)


if __name__ == "__main__":
    main()
