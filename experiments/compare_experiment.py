"""과제: 개별 체이닝과 선형 탐지를 같은 조건에서 비교한다.

두 테이블 모두 칸 수를 M으로 고정하고(max_load=None), 같은 무작위 URL을 적재율 α까지 넣는다.
  - 성공 탐색: 넣은 키를 모두 한 번씩 찾을 때의 평균 비용
  - 실패 탐색: 넣지 않은 키를 찾을 때의 평균 비용
비용은 주제 08과 같은 단위로 센다. 체이닝은 비교한 노드 수, 선형 탐지는 들여다본 칸 수다.
선형 탐지는 적재율이 1이면 넣을 칸이 없으므로 0.9까지만 잰다.

실행: make compare  →  experiments/compare.csv, compare-hit.svg, compare-miss.svg
"""

import csv
import random
import string
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from hash_table import HashTable  # noqa: E402
from probing_table import ProbingHashTable  # noqa: E402

M = 4093
MISSES = 2000
SEED = 2026
ALPHAS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9]


def random_url(rng):
    path = "".join(rng.choices(string.ascii_letters + string.digits, k=10))
    return f"https://example.com/{path}"


def theory(alpha):
    """(체이닝 성공, 체이닝 실패, 선형 탐지 성공, 선형 탐지 실패)"""
    return (1 + alpha / 2, alpha,
            0.5 * (1 + 1 / (1 - alpha)), 0.5 * (1 + 1 / (1 - alpha) ** 2))


def keys_for(alpha, seed):
    """α까지 채울 서로 다른 URL과, 그 안에 없는 URL을 같은 순서로 만든다."""
    rng = random.Random(seed)
    n = int(alpha * M)
    seen = []
    marks = HashTable(capacity=M)  # 중복 확인용. dict를 쓰지 않는다
    while len(seen) < n:
        u = random_url(rng)
        if u not in marks:
            marks.put(u, True)
            seen.append(u)
    misses = []
    while len(misses) < MISSES:
        u = random_url(rng)
        if u not in marks:
            misses.append(u)
    return seen, misses


def measure(table_cls, keys, misses):
    t = table_cls(capacity=M, max_load=None)
    for k in keys:
        t.put(k, True)
    hit = sum(t.find(k)[1] for k in keys) / len(keys)
    miss = sum(t.find(u)[1] for u in misses) / len(misses)
    return hit, miss


def main():
    rows = []
    print(f"M = {M}, 실패 탐색 {MISSES}회")
    print(f"{'α':>5} | {'체이닝 성공':>9} {'실패':>6} | {'선형 탐지 성공':>11} {'실패':>7}")
    for i, a in enumerate(ALPHAS):
        keys, misses = keys_for(a, SEED + i)
        ch, cm = measure(HashTable, keys, misses)
        lh, lm = measure(ProbingHashTable, keys, misses)
        rows.append((a, ch, cm, lh, lm) + theory(a))
        print(f"{a:>5} | {ch:>9.2f} {cm:>6.2f} | {lh:>11.2f} {lm:>7.2f}")

    with open(HERE / "compare.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["alpha", "chain_hit", "chain_miss", "probe_hit", "probe_miss",
                    "chain_hit_theory", "chain_miss_theory", "probe_hit_theory", "probe_miss_theory"])
        for r in rows:
            w.writerow([r[0]] + [f"{x:.3f}" for x in r[1:]])

    (HERE / "compare-hit.svg").write_text(
        chart(rows, "성공 탐색의 평균 비용", 6, [(1, 5, "체이닝"), (3, 7, "선형 탐지")]), encoding="utf-8")
    (HERE / "compare-miss.svg").write_text(
        chart(rows, "실패 탐색의 평균 비용", 60, [(2, 6, "체이닝"), (4, 8, "선형 탐지")]), encoding="utf-8")
    print("저장: experiments/compare.csv, compare-hit.svg, compare-miss.svg")


def chart(rows, title, ymax, series):
    """series: (실험값 열, 이론값 열, 이름). 실선과 점은 실험, 점선은 이론이다."""
    w, h = 640, 400
    left, right, top, bottom = 56, 170, 40, 48
    pw, ph = w - left - right, h - top - bottom
    colors = ["#0072B2", "#D55E00"]

    def x(a):
        return left + a * pw

    def y(v):
        return top + ph - min(v, ymax) / ymax * ph

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
           f'font-family="sans-serif" font-size="12">',
           f'<rect width="{w}" height="{h}" fill="#fbfbf9"/>',
           f'<text x="{left}" y="22" fill="#24292f" font-size="14" font-weight="bold">{title}</text>']
    step = ymax // 6 if ymax >= 12 else 1
    for v in range(0, ymax + 1, step):
        out.append(f'<line x1="{left}" x2="{left + pw}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#dfe1e4"/>')
        out.append(f'<text x="{left - 8}" y="{y(v) + 4:.1f}" text-anchor="end" fill="#6e7781">{v}</text>')
    for a in (0, 0.25, 0.5, 0.75, 1):
        out.append(f'<text x="{x(a):.1f}" y="{top + ph + 18}" text-anchor="middle" fill="#6e7781">{a}</text>')
    out.append(f'<text x="{left + pw / 2}" y="{h - 10}" text-anchor="middle" fill="#24292f">적재율 α</text>')
    legend = 0
    for k, (col, tcol, name) in enumerate(series):
        color = colors[k]
        for c, dash, label in ((col, "", f"{name} · 실험"), (tcol, "6 4", f"{name} · 이론")):
            pts = " ".join(f"{x(r[0]):.1f},{y(r[c]):.1f}" for r in rows)
            dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
            out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"{dash_attr}/>')
            if not dash:
                for r in rows:
                    out.append(f'<circle cx="{x(r[0]):.1f}" cy="{y(r[c]):.1f}" r="3" fill="{color}"/>')
            ly = top + 10 + legend * 20
            legend += 1
            out.append(f'<line x1="{left + pw + 16}" x2="{left + pw + 40}" y1="{ly}" y2="{ly}" '
                       f'stroke="{color}" stroke-width="2"{dash_attr}/>')
            out.append(f'<text x="{left + pw + 46}" y="{ly + 4}" fill="#24292f">{label}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    main()
