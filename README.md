# 노빠꾸컴퍼니 웹사이트

데이터 인프라부터 AI 솔루션까지 개발하는 소프트웨어 회사 **노빠꾸컴퍼니** 웹사이트입니다.
> 개발에 실패는 없다. 노빠꾸 정신.

## 구조
- `index.html` — 랜딩페이지 (히어로, 회사, 서비스, 프로세스, 노빠꾸 정신, 문의)
- `brand.html` — 브랜드 가이드 페이지 (톤앤매너, 로고, 컬러, 타이포, 그래픽 요소, 적용 예시)
- `BRAND.md` — 브랜드 가이드 문서 v1.0 (톤앤매너 원칙, Do/Don't, 로고 · 컬러 · 서체 규칙)
- `brand/logo/` — 로고 SVG 원본 (심볼, 가로형, 세로형, 국문, 단색) + 프로필용 PNG
- `brand/og-image.png` — 링크 공유 미리보기 이미지
- `brand/fonts/README.md` — 브랜드 글꼴 안내 (Archivo, Pretendard, JetBrains Mono · SIL OFL)
- `brand/tools/` — 로고 · 이미지 생성 스크립트
- `css/style.css` — 스타일

새 카피나 디자인을 만들 때는 먼저 `BRAND.md`를 보고 톤앤매너와 컬러 규칙(빨강 · 네이비 · 보라 · 흰색 사용 안 함)을 맞춰 주세요.

## 로고 다시 만들기
로고 SVG는 손으로 고치지 않고 스크립트로 만듭니다. 설계값(획 굵기, 기울기 등)은 `brand/tools/build_logos.py` 위쪽에 있습니다.

```bash
pip install fonttools uharfbuzz brotli
python3 brand/tools/build_logos.py      # brand/logo/*.svg, brand/og-image.svg 생성 (글꼴은 처음에 자동으로 내려받음)
node brand/tools/export_png.js          # symbol-512.png, og-image.png 생성 (Playwright 필요)
```

## 수정할 것
- 문의 이메일: `index.html`의 `hello@example.com`을 실제 주소로 바꿔 주세요.

## 배포 (GitHub Pages)
저장소 **Settings → Pages → Source: Deploy from a branch → `main` / `(root)`** 로 저장하면
`https://bmk3037.github.io/New-Project/` 에서 볼 수 있습니다.
