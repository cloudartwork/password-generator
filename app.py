#!/usr/bin/env python3
import html
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional, Union
from urllib.parse import parse_qs


HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
COUNT_MAX = 10000
LENGTH_MIN = 4
LENGTH_MAX = 64

SIMILAR_CHARS = set("oO0iIl1L")
AMBIGUOUS_CHARS = set(",.;:'`~\"\\/(){}[]")

GROUPS = {
    "numbers": "0123456789",
    "lowercase": "abcdefghijklmnopqrstuvwxyz",
    "uppercase": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "symbols": "!@#$%^&*-_=+?",
}


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def parse_int(raw: str, default: int) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def count_valid_passwords(group_sizes: List[int], length: int) -> Union[int, float]:
    if length > 18:
        return float("inf")

    total_size = sum(group_sizes)
    if total_size == 0:
        return 0

    total = 0
    subset_count = 1 << len(group_sizes)
    for mask in range(subset_count):
        removed = 0
        bits = 0
        for index, size in enumerate(group_sizes):
            if mask & (1 << index):
                removed += size
                bits += 1

        available = total_size - removed
        if available <= 0:
            continue

        term = available**length
        total += term if bits % 2 == 0 else -term

    return total


def filter_chars(source: str, exclude_similar: bool, exclude_ambiguous: bool) -> str:
    chars = []
    for char in source:
        if exclude_similar and char in SIMILAR_CHARS:
            continue
        if exclude_ambiguous and char in AMBIGUOUS_CHARS:
            continue
        chars.append(char)
    return "".join(chars)


def make_defaults() -> dict:
    return {
        "length": 16,
        "count": 5,
        "include_symbols": False,
        "include_numbers": True,
        "include_lowercase": True,
        "include_uppercase": True,
        "exclude_similar": True,
        "exclude_ambiguous": False,
    }


def parse_options(form: Optional[Dict[str, List[str]]] = None) -> dict:
    defaults = make_defaults()
    if not form:
        return defaults

    return {
        "length": clamp(parse_int(form.get("length", ["16"])[0], 16), LENGTH_MIN, LENGTH_MAX),
        "count": clamp(parse_int(form.get("count", ["5"])[0], 5), 1, COUNT_MAX),
        "include_symbols": "include_symbols" in form,
        "include_numbers": "include_numbers" in form,
        "include_lowercase": "include_lowercase" in form,
        "include_uppercase": "include_uppercase" in form,
        "exclude_similar": "exclude_similar" in form,
        "exclude_ambiguous": "exclude_ambiguous" in form,
    }


def build_passwords(options: dict) -> List[str]:
    selected_groups = []

    if options["include_numbers"]:
        selected_groups.append(filter_chars(GROUPS["numbers"], options["exclude_similar"], options["exclude_ambiguous"]))
    if options["include_lowercase"]:
        selected_groups.append(filter_chars(GROUPS["lowercase"], options["exclude_similar"], options["exclude_ambiguous"]))
    if options["include_uppercase"]:
        selected_groups.append(filter_chars(GROUPS["uppercase"], options["exclude_similar"], options["exclude_ambiguous"]))
    if options["include_symbols"]:
        selected_groups.append(filter_chars(GROUPS["symbols"], options["exclude_similar"], options["exclude_ambiguous"]))

    if not selected_groups:
        raise ValueError("최소 한 가지 문자 종류를 선택해주세요.")
    if any(not group for group in selected_groups):
        raise ValueError("제외 규칙 때문에 사용할 수 없는 문자군이 생겼습니다. 옵션을 조정해주세요.")

    length = options["length"]
    count = options["count"]

    if length < len(selected_groups):
        raise ValueError("현재 조건을 모두 포함하려면 길이가 더 길어야 합니다.")

    combinations = count_valid_passwords([len(group) for group in selected_groups], length)
    if combinations < count:
        raise ValueError("현재 조건으로 만들 수 있는 경우의 수보다 요청 개수가 많습니다. 길이를 늘리거나 조건을 넓혀주세요.")

    pool = "".join(selected_groups)
    results: set[str] = set()

    while len(results) < count:
        chars = [secrets.choice(group) for group in selected_groups]
        while len(chars) < length:
            chars.append(secrets.choice(pool))

        secrets.SystemRandom().shuffle(chars)
        results.add("".join(chars))

    return list(results)


def checkbox(name: str, checked: bool, label: str) -> str:
    return (
        f'<label class="check">'
        f'<input type="checkbox" name="{name}" {"checked" if checked else ""} />'
        f"<span>{label}</span>"
        f"</label>"
    )


def render_page(options: dict, passwords: Optional[List[str]] = None, status: str = "", error: str = "") -> str:
    passwords = passwords or []
    result_text = "\n".join(passwords) if passwords else "생성된 비밀번호가 줄바꿈으로 여기에 표시됩니다."
    status_text = error or status or "아직 생성된 비밀번호가 없습니다."
    status_color = "#b42318" if error else "#555555"
    include_symbols = checkbox("include_symbols", options["include_symbols"], "기호 포함 (예: _-#*+)")
    include_numbers = checkbox("include_numbers", options["include_numbers"], "숫자 포함 (e.g. 123456)")
    include_lowercase = checkbox("include_lowercase", options["include_lowercase"], "소문자 포함 (예: abcdef)")
    include_uppercase = checkbox("include_uppercase", options["include_uppercase"], "대문자 포함 (예: ABCDEF)")
    exclude_similar = checkbox("exclude_similar", options["exclude_similar"], "유사 문자 제외하기 (예: o,O,0,i,I,l,1,L)")
    exclude_ambiguous = checkbox(
        "exclude_ambiguous",
        options["exclude_ambiguous"],
        r"애매한 문자 제외 (예: ,.;:'`~\()/{}[])",
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>비밀번호 난수 생성기</title>
  <style>
    :root {{
      --panel: #ffffff;
      --text: #1d1d1b;
      --muted: #6c6c66;
      --line: #d8d8d0;
      --accent: #2cab79;
      --accent-deep: #218c63;
      --soft: #f2f5f1;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      font-family: "Pretendard", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(44, 171, 121, 0.08), transparent 24%),
        linear-gradient(180deg, #ffffff 0%, #f7f8f4 100%);
      color: var(--text);
      min-height: 100vh;
    }}
    .wrap {{
      width: min(1040px, calc(100% - 32px));
      margin: 36px auto 48px;
      background: var(--panel);
      border: 1px solid rgba(29, 29, 27, 0.08);
      border-radius: 24px;
      box-shadow: 0 18px 46px rgba(29, 29, 27, 0.06);
      padding: 28px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 42px);
      letter-spacing: -0.03em;
    }}
    .sub {{
      margin: 0 0 28px;
      color: var(--muted);
      line-height: 1.6;
    }}
    .grid {{
      display: grid;
      gap: 28px;
      grid-template-columns: minmax(320px, 420px) 1fr;
      align-items: start;
    }}
    label,
    .group-title {{
      display: block;
      margin: 0 0 10px;
      font-size: 15px;
      font-weight: 700;
    }}
    .field {{
      margin-bottom: 20px;
    }}
    input[type="text"],
    input[type="number"],
    textarea {{
      width: 100%;
      padding: 0 14px;
      border: 1px solid var(--line);
      border-radius: 12px;
      font: inherit;
      color: var(--text);
      background: #fff;
    }}
    input[type="text"],
    input[type="number"] {{
      height: 48px;
    }}
    textarea {{
      min-height: 440px;
      max-height: 560px;
      padding: 16px 18px;
      overflow: auto;
      resize: vertical;
      white-space: pre-wrap;
      word-break: break-all;
      border-radius: 18px;
      background: var(--soft);
      font: 15px/1.7 "SF Mono", "Menlo", "Consolas", monospace;
    }}
    input[type="range"] {{
      width: 100%;
      accent-color: var(--accent);
    }}
    .range-row {{
      display: grid;
      gap: 12px;
      grid-template-columns: 112px 1fr;
      align-items: center;
    }}
    .toolbar,
    .actions {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}
    button {{
      border: 0;
      border-radius: 12px;
      padding: 12px 16px;
      background: var(--accent);
      color: white;
      font: inherit;
      font-weight: 600;
      cursor: pointer;
    }}
    button.secondary {{
      background: #ecf7f1;
      color: var(--accent-deep);
    }}
    .check-list {{
      display: grid;
      gap: 12px;
    }}
    .check {{
      display: flex;
      gap: 10px;
      align-items: flex-start;
      font-weight: 400;
      line-height: 1.45;
      margin: 0;
    }}
    .check input {{
      width: 18px;
      height: 18px;
      margin-top: 2px;
      accent-color: var(--accent);
    }}
    .status {{
      color: {status_color};
      white-space: pre-wrap;
      margin-bottom: 12px;
      min-height: 24px;
      font-size: 14px;
    }}
    .hint {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }}
    @media (max-width: 900px) {{
      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>비밀번호 난수 생성기</h1>
    <p class="sub">길이, 문자 구성, 제외 규칙을 조절하고 한 번에 여러 개의 비밀번호를 생성할 수 있습니다.</p>
    <div class="grid">
      <form method="post" action="/">
        <div class="field">
          <label for="lengthNumber">비밀번호 길이</label>
          <div class="range-row">
            <input id="lengthNumber" name="length" type="number" min="{LENGTH_MIN}" max="{LENGTH_MAX}" value="{options["length"]}" />
            <input id="lengthRange" type="range" min="{LENGTH_MIN}" max="{LENGTH_MAX}" value="{options["length"]}" />
          </div>
        </div>
        <div class="field">
          <label for="countNumber">생성 개수</label>
          <input id="countNumber" name="count" type="number" min="1" max="{COUNT_MAX}" value="{options["count"]}" />
        </div>
        <div class="field">
          <div class="group-title">조건</div>
          <div class="check-list">
            {include_symbols}
            {include_numbers}
            {include_lowercase}
            {include_uppercase}
            {exclude_similar}
            {exclude_ambiguous}
          </div>
        </div>
        <div class="field">
          <button type="submit" name="action" value="generate">생성</button>
          <button type="submit" name="action" value="clear" class="secondary">결과 비우기</button>
        </div>
        <div class="hint">같은 한 번의 생성 요청 안에서는 중복 없이 뽑습니다. 1만 개까지 생성할 수 있습니다.</div>
      </form>

      <section>
        <div class="group-title">생성 결과</div>
        <div class="status">{html.escape(status_text)}</div>
        <textarea id="resultBox" readonly>{html.escape(result_text)}</textarea>
        <div class="toolbar" style="margin-top:10px;">
          <button type="button" id="copyAll" class="secondary">전체 복사 (엑셀용)</button>
        </div>
      </section>
    </div>
  </div>
  <script>
    document.getElementById("copyAll").addEventListener("click", async () => {{
      const text = document.getElementById("resultBox").value;
      if (!text || text.includes("생성된 비밀번호가 줄바꿈으로 여기에 표시됩니다.")) return;
      try {{
        await navigator.clipboard.writeText(text);
      }} catch (error) {{
        console.error(error);
      }}
    }});
    const lengthNumber = document.getElementById("lengthNumber");
    const lengthRange = document.getElementById("lengthRange");
    lengthRange.addEventListener("input", () => {{
      lengthNumber.value = lengthRange.value;
    }});
    lengthNumber.addEventListener("input", () => {{
      lengthRange.value = lengthNumber.value;
    }});
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        page = render_page(parse_options()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        form = parse_qs(body, keep_blank_values=True)
        options = parse_options(form)
        action = form.get("action", ["generate"])[0]

        passwords: List[str] = []
        status = ""
        error = ""

        if action == "clear":
            status = "결과를 비웠습니다."
        else:
            try:
                passwords = build_passwords(options)
                status = f'{len(passwords)}개의 비밀번호를 생성했습니다.'
            except ValueError as exc:
                error = str(exc)

        page = render_page(options, passwords=passwords, status=status, error=error).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
