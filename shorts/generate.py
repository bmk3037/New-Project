"""주제 하나를 structure.md의 구조로 숏츠 대본 초안으로 만든다.

ANTHROPIC_API_KEY가 필요하다. 결과는 사람이 감수한 뒤에 쓴다.

    python3 shorts/generate.py "엘리베이터가 정전돼도 멈춘 층에서 문이 열리는 이유"
    python3 shorts/generate.py "편의점 냉장고" --notes "야간 정전, 온도 기록" --out shorts/scripts/06-cvs-fridge.md
"""
import argparse
from pathlib import Path

import anthropic

HERE = Path(__file__).parent
MODEL = "claude-opus-5-5"


def build_system():
    structure = (HERE / "structure.md").read_text()
    example = (HERE / "scripts" / "01-breaker-rain.md").read_text()
    return (
        "너는 생활 전기 숏츠 채널의 대본 작가다. 아래 구조 사양을 반드시 따른다.\n\n"
        f"<structure>\n{structure}\n</structure>\n\n"
        "출력은 아래 예시와 같은 마크다운 형식 하나만 낸다. 앞뒤 설명은 쓰지 않는다.\n"
        "확실하지 않은 수치는 쓰지 말거나, 감수 체크리스트에 확인 항목으로 올린다.\n\n"
        f"<example>\n{example}\n</example>"
    )


def generate(topic, notes=""):
    client = anthropic.Anthropic()
    prompt = f"주제: {topic}"
    if notes:
        prompt += f"\n참고: {notes}"
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        output_config={"effort": "high"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=build_system(),
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()
    if message.stop_reason == "refusal":
        raise SystemExit(f"생성 거절: {message.stop_details}")
    return "".join(b.text for b in message.content if b.type == "text")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic", help="소재 한 줄")
    ap.add_argument("--notes", default="", help="넣고 싶은 사실·각도")
    ap.add_argument("--out", help="저장할 경로. 없으면 화면에 출력")
    args = ap.parse_args()

    script = generate(args.topic, args.notes)
    if args.out:
        Path(args.out).write_text(script)
        print(f"저장: {args.out}")
    else:
        print(script)


if __name__ == "__main__":
    main()
