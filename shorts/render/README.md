# 영상 조립 엔진

도면 애니메이션, 자막, Flow 사진·영상, 타입캐스트 음성을 합쳐 1080×1920 숏츠 영상을 만듭니다.

## 편 폴더 구성

```
render/ep07/
  timeline.json   비트별 내레이션 문장, 강조 단어, 장면 순서
  sheets.html     도면 장면(SVG). data-draw 등 속성으로 움직임을 정한다
  assets/         narration.mp3, A.png, B.png … (사람이 넣는 파일)
```

## 넣을 파일

| 파일 | 내용 |
|---|---|
| `assets/narration.mp3` | 타입캐스트에서 받은 음성. 있으면 장면 길이를 음성 길이에 맞춥니다 |
| `assets/A.png` 등 | Flow 사진. `.png`, `.jpg`, `.webp` 모두 됩니다. 천천히 확대되는 움직임이 들어갑니다 |
| `assets/A.mp4` 등 | Flow 영상. 같은 자리에 사진과 영상이 둘 다 있으면 영상을 씁니다 |

빠진 파일은 회색 임시 화면이나 무음으로 채웁니다. 그래서 파일이 다 모이기 전에도 미리보기를 뽑을 수 있습니다.

**파일 올리는 법:** GitHub 웹에서 이 브랜치의 `shorts/render/ep07/assets/` 폴더로 가서 **Add file → Upload files**로 올리면 됩니다. 그다음 세션에서 "에셋 올렸어"라고 말하면 받아서 다시 렌더링합니다.

## 실행

```sh
cd shorts/render
NODE_PATH=$(npm root -g) node render.js ep07            # out/ep07.mp4 (30fps)
NODE_PATH=$(npm root -g) node render.js ep07 --fps 10   # 빠른 미리보기
NODE_PATH=$(npm root -g) node render.js ep07 --still 20 # 20초 지점 한 장
```

- **필요한 것:** Node의 `playwright`와 Chromium, `ffmpeg`
- **렌더 시간:** 이 환경 기준으로 1프레임에 약 0.2초입니다. 90초짜리 30fps 영상이면 10분쯤 걸립니다.

## 도면 움직임 속성

숫자는 장면 길이에 대한 비율(0~1)입니다. 음성 길이가 바뀌어도 그대로 맞습니다.

| 속성 | 뜻 |
|---|---|
| `data-draw="a b"` | 선이 a~b 동안 그려진다 |
| `data-fade="a b"` | a~b 동안 나타난다 |
| `data-out="a b"` | a~b 동안 사라진다 |
| `data-grow="a b"` | a~b 동안 아래에서 위로 자란다 (막대 게이지) |
| `data-cls="a 이름"` | a 이후 class를 붙인다 (예: `off`는 회색) |

## 알려진 한계

- **음성에 맞추는 방식:** 음성을 전체 길이로만 맞춥니다. 비트별 길이는 글자 수 비율로 나누기 때문에, 문장마다 말 빠르기가 다르면 자막이 조금 어긋날 수 있습니다. 타입캐스트에서 자막 파일(SRT)을 받을 수 있으면 그걸로 맞추도록 고칠 수 있습니다.
