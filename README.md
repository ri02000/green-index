# Green Index · 독립 제품 검색 웹사이트

## 현재 상태 (2026-11-21)
- GitHub 저장소: https://github.com/ri02000/green-index
- 공개 웹사이트 목표 주소: https://ri02000.github.io/green-index/
- `index.html`: 제품 검색 및 상세 보기 (모바일/데스크톱 반응형)
- `share.html`: 선택 제품 안내 페이지 (제품번호를 URL 조각으로 전달)
- `products.csv`: 135개 제품 데이터 내보내기
- 135개 제품에 1차 설명이 입력되어 있으며, 자료의 정확성·최신성에 대한 전체 검증은 아직 완료되지 않음.
- 전체 등록 제품의 선택과 맞춤 공유를 지원함. 공식 상세 정보 최종 검증이 끝나지 않은 제품은 공유 화면에 초안으로 표시함. 핵심 항목 공식 대조와 공유 기능 동작은 별도 상태.
- 사진 표시 대상: 72개 제품(사용자 제공 저장 사진 24개, 도테라 공식 이미지 서버 외부 링크 48개). 63개 제품은 아직 사진이 없음.
- 사용자 제공 사진은 `photos/<제품번호>.webp`에 저장. 공식 서버의 이미지 48개는 GitHub에 복사하지 않고 외부 HTTPS 이미지 URL만 참조함. 제품번호·파일 형식·HTTP 응답 검사를 통과했으나, 실제 최신 라벨·법적 게시 권한까지 검증한 것은 아님.
- 공식 이미지 CDN의 일부 접근 제한은 유지되지만, 제품 페이지를 대상으로 한 이미지 URL 수집은 성공함. 실제 응답을 확인한 공식 링크만 시험 표시했으며 제한을 우회하지 않음. 제품별 후보와 실패 원인은 별도 CSV/JSON에 보관.
- `index.html`에 검색용 제품 데이터가 내장되어 있고, `products.csv`는 별도 데이터 확인용. GitHub Pages에서 SQLite 서버는 구동하지 않음.
- URL 공유는 다른 제품을 화면에 노출하지 않는 UI 기능이지만, 계정 인증이나 비공개 접근 통제가 아님.

## GitHub Pages 활성화 (처음 한 번)
1. GitHub에 로그인 후 https://github.com/ri02000/green-index/settings/pages 방문
2. **Build and deployment → Source** 를 **Deploy from a branch** 로 선택
3. **Branch** 를 **main**, 폴더를 **/(root)** 로 선택 후 **Save**
4. 배포 성공 메시지가 나오면 https://ri02000.github.io/green-index/ 에서 접속 확인
5. 즐겨찾기에 사이트 주소를 저장해 Windows, Mac, iPhone, Android에서 같은 주소로 사용

## 계정 관리
- GitHub 사용자명: `ri02000`
- 비밀번호를 모르면 GitHub 로그인 화면의 **Forgot password?**로 재설정
- 이메일 계정 복구 수단을 확인하고, 재설정한 비밀번호는 브라우저/운영체제 비밀번호 관리자에 보관
- 비밀번호, 로그인 인증 코드를 대화에 적어 보내지 말 것

## 품질 원칙
- 공식 자료에서 확인한 사실과 해석/키워드/미검증 내용을 분리
- 건강 관련 치료 효과를 확인 없이 주장하지 않음
- 공유 승인과 데이터 입력 완료를 구별
- 제품 이미지의 현재 포장 일치 및 제3자 저작권·공개 사용 권한은 별도로 검토. 공식 CDN에 공개된 사진이라고 재게시가 자동으로 허가되는 것은 아님.

## 사진 수집 진행 상황 (2026-11-21)
- GitHub에 저장된 WebP: 24개 제품 (원본 이미지 25개 중 블랙 스프루스 사진이 2장으로 중복)
- 총 등록 제품: 135개. 이 수가 한국 공식 쇼핑몰 전체 상품 수를 뜻하지는 않음.
- 현재 미등록 상품도 공식 자료와 대조하여 수집해야 함.
- 공식 이미지 URL 후보: `image_candidates.csv` 및 `image_sources.csv`. 자동 수집: `scripts/discover_official_photo_urls.py`, 이미지 응답 확인: `scripts/probe_official_image_urls.py`, 정형 CDN 경로 검사: `scripts/probe_cdn_patterns.py`.
- 제품번호로 연결되는 후보 주소 215개(등록 제품 108종 기준), 그중 사진이 없던 제품 48종은 실제 이미지 응답을 확인하여 외부 링크로 표시. 후보 숫자는 제품 사진 수가 아님.
- 근거와 실패 사항: `image_crawl_report.json`, `official_image_probe.csv`, `official_image_probe_report.json`, `image_pattern_probe.csv`, `image_pattern_probe_report.json`.
- 자동 수집은 GitHub Actions 워크플로 `.github/workflows/import_official_photos.yml`로 실행되며 실제 이미지 파일 대량 다운로드는 수행하지 않음.
