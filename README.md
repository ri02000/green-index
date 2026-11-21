# Green Index · 독립 제품 검색 웹사이트

## 현재 상태 (2026-11-21)
- GitHub 저장소: https://github.com/ri02000/green-index
- 공개 웹사이트 목표 주소: https://ri02000.github.io/green-index/
- `index.html`: 제품 검색 및 상세 보기 (모바일/데스크톱 반응형)
- `share.html`: 선택 제품 안내 페이지 (제품번호를 URL 조각으로 전달)
- `products.csv`: 133개 제품 데이터 내보내기
- 133개 제품에 1차 설명이 입력되어 있으며, 자료의 정확성·최신성에 대한 전체 검증은 아직 완료되지 않음.
- 현재 공유 승인 데이터는 3개 제품, 나머지는 공유 제한
- 실제 제품 사진은 미수집. 이미지 없는 상태를 명확히 표시.
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
- 제품 사진은 이용권한 확인 후 추가
