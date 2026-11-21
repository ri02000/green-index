# Green Index website · GitHub Pages deployment-ready

## 사이트 상태 (2026-11-21)
- 133개 제품의 제품명·번호·설명 요약을 포함한 정적 HTML
- 단독 인터넷 접속 가능하게 배포하기 전까지는 미공개 파일
- 3개만 공유 승인, 130개는 공유 제한. 승인했다고 해서 의료 효능이 입증된 것은 아님.
- 제품 상세 정보를 완전히 검증한 것은 아님. 실제 제품 사진 0장.
- 홈페이지가 읽는 제품 데이터는 HTML 내장형이며 `products.db`는 별도 원본 백업/향후 서버 개발용. 온라인 검색 중 SQLite 서버가 동작하는 것은 아님.
- 개인별 공유 화면은 `share.html#s=60200528` 같은 URL 조각으로 제한된 제품만 표시하지만 접근 통제 또는 비공개 인증 방식은 아님.
- 현재 GitHub 연동에서는 `ri02000/FPV-Flight-Replay-3D` 저장소만 확인됨. Green Index 전용 저장소가 만들어지면 별도 연결/업로드가 필요함.

## 한 번 배포 절차
1. https://github.com/new?name=green-index 에서 `ri02000` 계정으로 Public 저장소 생성.
2. 저장소 루트에 `index.html`, `share.html`, `favicon.svg`, `manifest.webmanifest`, `.nojekyll`, `robots.txt` 업로드. 배포 데이터는 HTML에 자체 포함되어 별도 서버 불필요.
3. Settings > Pages > Build and deployment > Source=Deploy from a branch > Branch=main /(root) > Save.
4. Pages 배포 성공 시 https://ri02000.github.io/green-index/ 로 접속. 실제로 게시되기 전까지 주소를 정상 작동한다고 주장하지 말 것.

개인별 링크는 공유 승인된 제품만 표시함. 현재 검색·읽기 중심의 시험판이므로 치료 효과를 단정하지 않음.