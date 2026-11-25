"""URL 단축기 웹 서버. 표준 모듈 http.server만 쓴다.

  GET  /          URL을 넣는 폼
  POST /shorten   짧은 링크를 만들어 보여 준다
  GET  /table     현재 해시 테이블: 칸마다 연결 리스트와 호너 해시 계산 근거
  GET  /<코드>    원래 URL로 302 이동

실행: make serve
저장은 메모리에만 한다. 서버를 끄면 링크가 사라진다.
"""

import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from hash_table import horner_hash, horner_steps
from shortener import Shortener

store = Shortener()

PAGE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>URL 단축기</title>
<style>
 body {{ font-family: sans-serif; max-width: 36rem; margin: 3rem auto; padding: 0 1rem; line-height: 1.6; }}
 input[type=url] {{ width: 100%; padding: .6rem; font-size: 1rem; box-sizing: border-box; }}
 button {{ margin-top: .6rem; padding: .6rem 1.2rem; font-size: 1rem; }}
 .short {{ font-size: 1.4rem; word-break: break-all; }}
 .error {{ color: #b3261e; }}
</style></head><body>
<h1>URL 단축기</h1>
{body}
<form method="post" action="/shorten">
 <input type="url" name="url" placeholder="https://..." required>
 <button>줄이기</button>
</form>
<p>저장된 링크 {count}개 · <a href="/table">해시 테이블 보기</a></p>
</body></html>
"""

TABLE_PAGE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>현재 해시 테이블</title>
<style>
 body {{ font-family: sans-serif; margin: 2rem; line-height: 1.5; }}
 table {{ border-collapse: collapse; width: 100%; }}
 th, td {{ border: 1px solid #ccc; padding: .5rem; vertical-align: top; text-align: left; }}
 .empty {{ color: #888; }}
 .chain {{ display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; }}
 .node {{ border: 1px solid #888; padding: .5rem .7rem; font-family: monospace; }}
 .node a {{ word-break: break-all; }}
 details code {{ display: block; white-space: normal; max-width: 60rem; }}
</style></head><body>
<h1>현재 해시 테이블</h1>
{body}
<p><a href="/">돌아가기</a></p>
</body></html>
"""


def trace(key, m):
    """호너 해시를 한 글자씩 적은 계산 근거"""
    return " → ".join(f"({h} * 31 + ord({c!r})={ord(c)}) % {m} = {nh}" for h, c, nh in horner_steps(key, m))


def node_html(key, code, base, m, extra=""):
    link = f"{base}/{code}"
    return (f'<div class="node">URL 키: {html.escape(key)}<br>짧은 코드: {html.escape(code)}<br>'
            f'<a href="{html.escape(link)}">{html.escape(link)}</a>{extra}'
            f'<details><summary>해시 계산 (칸 {horner_hash(key, m)})</summary>'
            f'<code>{html.escape(trace(key, m))}</code></details></div>')


def chains_html(t, base):
    """개별 체이닝: 칸마다 연결 리스트를 맨 앞 노드부터 화살표로 잇는다."""
    m = t.capacity
    rows = []
    for i, items in enumerate(t.chains()):
        if not items:
            rows.append(f'<tr><td>{i}</td><td colspan="2" class="empty">비어 있음</td></tr>')
            continue
        nodes = " → ".join(node_html(k, v, base, m) for k, v in items)
        rows.append(f'<tr><td>{i}</td><td>{len(items)}개 노드</td>'
                    f'<td><div class="chain">{nodes} → NULL</div></td></tr>')
    head = ("<p>원본 URL을 키로 호너 해시를 계산하고, 같은 칸에 떨어진 URL은 연결 리스트로 잇는 "
            "개별 체이닝입니다. 새 노드는 리스트의 맨 앞에 들어갑니다.</p>"
            f"<p>{len(t)}개 항목 / {m}개 칸 · 적재율 {t.load_factor:.2f}</p>"
            "<table><tr><th>칸</th><th>체인 길이</th><th>URL 키, 짧은 코드와 계산 근거</th></tr>")
    return head + "".join(rows) + "</table>"


def table_html(t, base):
    return chains_html(t, base)


class Handler(BaseHTTPRequestHandler):
    def base_url(self):
        host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host", "localhost")
        proto = self.headers.get("X-Forwarded-Proto", "http")
        return f"{proto}://{host}"

    def send_page(self, status, body):
        data = PAGE.format(body=body, count=len(store)).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self.send_page(200, "")
            return
        if self.path == "/table":
            data = TABLE_PAGE.format(body=table_html(store.url_table, self.base_url())).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        code = self.path.lstrip("/")
        url = store.expand(code)
        if url is None:
            self.send_page(404, f'<p class="error">없는 코드입니다: {html.escape(code)}</p>')
            return
        self.send_response(302)
        self.send_header("Location", url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        if self.path != "/shorten":
            self.send_page(404, '<p class="error">없는 주소입니다</p>')
            return
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        url = form.get("url", [""])[0]
        try:
            code = store.shorten(url)
        except ValueError as e:
            self.send_page(400, f'<p class="error">{html.escape(str(e))}</p>')
            return
        short = f"{self.base_url()}/{code}"
        self.send_page(200, f'<p class="short"><a href="{html.escape(short)}">{html.escape(short)}</a></p>'
                            f'<p>{html.escape(url.strip())}</p>')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    port = parser.parse_args().port
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"http://localhost:{port} 에서 듣는 중. 끄려면 Ctrl+C")
    server.serve_forever()


if __name__ == "__main__":
    main()
