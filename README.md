# 노빠꾸컴퍼니 홈페이지

현장 서버 뒤의 데이터 플랫폼 · IT 솔루션 · AI 개발 회사 홈페이지입니다.

## 개발

별도 빌드나 패키지 설치가 필요 없는 정적 HTML/CSS 사이트입니다.

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory /workspace/New-Project
```

- `index.html`: 첨부 홈페이지를 기준으로 구성한 홈페이지
- `brand.html`: 첨부 CI 가이드 v1.4
- `css/style.css`: 홈페이지 스타일, 흰 바탕과 Nobbakku Red `#D4362A`
- `css/fonts.css`, `brand/fonts/`: 로컬 Pretendard, Archivo, JetBrains Mono
- `brand/logo/`: CI 가이드에서 추출한 로고
- `img/`: 홈페이지용 AI 생성 이미지. 실제 고객 현장이나 납품 실적이 아닙니다.

문의 이메일은 `bmk3037@naver.com`입니다. 문의 폼은 입력한 내용을 `mailto:` 링크로 전달해 사용자의 메일 앱을 엽니다. 서버 전송이나 접수 저장 기능은 없습니다.

GitHub Pages는 `main` 브랜치의 루트를 게시하도록 설정합니다. 현재 작업 공간의 변경 사항은 커밋·푸시·배포 전에는 공개 사이트에 반영되지 않습니다.
