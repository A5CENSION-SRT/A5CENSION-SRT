#!/usr/bin/env python3
"""Builds the animated SVGs for the profile README into ../assets.

Static art (header, terminal) is always built. The contribution chart and stats
are built from the GitHub GraphQL API when GH_TOKEN is set; with a token that
can see private contributions, they include private activity (aggregate
numbers only: no repo names or commit messages are written anywhere).

    GH_TOKEN=... GH_LOGIN=A5CENSION-SRT python3 scripts/build.py

Text is drawn as outlines (Noto Sans Mono, OFL) so it renders identically
everywhere without any web-font loading. Stdlib only.
"""
import json, os, sys, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "assets")
os.makedirs(OUT, exist_ok=True)
GL = json.load(open(os.path.join(HERE, "glyphs.json"), encoding="utf-8"))
LOGIN = os.environ.get("GH_LOGIN", "A5CENSION-SRT")

THEMES = {
    "dark":  dict(ink="#D8E6EA", accent="#A2D0C9", muted="#6F8777", red="#E0432B", blue="#4C8DF6",
                  lv=["#15221E", "#24463F", "#3A7168", "#5FA397", "#A2D0C9"], top=0.3, side=-0.34),
    "light": dict(ink="#0D1B16", accent="#2F6B62", muted="#5B6F66", red="#C2301C", blue="#1F5FD1",
                  lv=["#E1EAE6", "#B9D3CC", "#86B5AA", "#4F8C80", "#1F5C52"], top=0.25, side=-0.25),
}
EASE = "cubic-bezier(.16,1,.3,1)"


def mix(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(pa[i] + (pb[i] - pa[i]) * t) for i in range(3))


def shade(c, t):  # t>0 lighten, t<0 darken
    return mix(c, "#FFFFFF", t) if t > 0 else mix(c, "#000000", -t)


class Doc:
    def __init__(self, w, h, label):
        self.w, self.h, self.label = w, h, label
        self.defs, self.css, self.body = {}, [], []

    def glyph(self, fam, ch, x, y, size):
        f = GL[fam]
        if ch not in f["g"]:
            return ""
        gid = f"{fam}{ord(ch):x}"
        self.defs.setdefault(gid, f["g"][ch])
        k = size / f["upm"]
        return f'<use href="#{gid}" transform="translate({x:.2f} {y:.2f}) scale({k:.5f} {-k:.5f})"/>'

    def text(self, s, x, y, size, fam="r", fill="#fff", anchor="start", cls=""):
        adv = GL[fam]["adv"] * size / GL[fam]["upm"]
        w = adv * len(s)
        if anchor == "end": x -= w
        elif anchor == "middle": x -= w / 2
        parts = "".join(self.glyph(fam, ch, x + i * adv, y, size) for i, ch in enumerate(s))
        return f'<g fill="{fill}"{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>{parts}</g>', w

    def render(self):
        defs = "".join(f'<path id="{k}" d="{v}"/>' for k, v in self.defs.items())
        css = "".join(self.css)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{self.label}">'
                f'<title>{self.label}</title><defs>{defs}</defs><style>{css}'
                f'@media (prefers-reduced-motion:reduce){{*{{animation:none!important;opacity:1!important;transform:none!important}}}}'
                f'</style>{"".join(self.body)}</svg>')


def save(name, th, doc):
    s = doc.render()
    with open(os.path.join(OUT, f"{name}-{th}.svg"), "w", encoding="utf-8") as f:
        f.write(s)
    print(f"{name}-{th}.svg  {len(s) / 1024:.1f} KB")


PIX = {
 "A": ["01110","10001","10001","11111","10001","10001","10001"],
 "5": ["11111","10000","11110","00001","00001","10001","01110"],
 "C": ["01110","10001","10000","10000","10000","10001","01110"],
 "E": ["11111","10000","10000","11110","10000","10000","11111"],
 "N": ["10001","11001","10101","10101","10011","10001","10001"],
 "S": ["01111","10000","10000","01110","00001","00001","11110"],
 "I": ["01110","00100","00100","00100","00100","00100","01110"],
 "O": ["01110","10001","10001","10001","10001","10001","01110"],
 "-": ["00000","00000","00000","01110","00000","00000","00000"],
 "R": ["11110","10001","10001","11110","10100","10010","10001"],
 "T": ["11111","00100","00100","00100","00100","00100","00100"],
}


def pixel_rects(ch, x, y, s):
    out = []
    for r, row in enumerate(PIX[ch]):
        c = 0
        while c < 5:
            if row[c] == "1":
                e = c
                while e < 5 and row[e] == "1": e += 1
                out.append(f'<rect x="{x + c * s}" y="{y + r * s}" width="{(e - c) * s}" height="{s}"/>')
                c = e
            else:
                c += 1
    return "".join(out)


# ------------------------------------------------------------------ header
PHRASES = ["software engineer", "full-stack engineer", "cloud, backend systems & AI", "open source enthusiast", "first-principles thinker"]


def step(i, k, ch):
    """variable typing speed, like React Bits TextType's variableSpeed"""
    base = 0.056 * (0.75 + 0.5 * ((i * 5 + k * 3 + ord(ch)) % 5) / 4)
    return base + (0.14 if ch in ",&" else 0.0)


def header(th):
    c = THEMES[th]
    d = Doc(900, 148, "Snehal Reddy Thadigotla (SWE), A5CENSION-SRT")
    d.css.append(
        f"@keyframes rise{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}"
        f".n{{opacity:0;animation:rise 1s {EASE} forwards}}")
    s = 5
    d.body.append(f'<g fill="{c["accent"]}">')
    px = 0
    for i, ch in enumerate("A5CENSION-SRT"):
        if ch == "-": px += s * 2
        fl = f' fill="{c["red"]}"' if ch == "-" else ""
        d.body.append(f'<g class="n"{fl} style="animation-delay:{0.15 + i * 0.07:.2f}s">{pixel_rects(ch, px, 14, s)}</g>')
        px += 6 * s + (s * 2 if ch == "-" else 0)
    d.body.append("</g>")
    nm, _ = d.text("Snehal Reddy Thadigotla  \u00b7  SWE", 0, 84, 18, "b", c["ink"])
    d.body.append(f'<g class="n" style="animation-delay:1.1s">{nm}</g>')

    size, Y, X0 = 16, 124, 20
    adv = GL["r"]["adv"] * size / 1000
    pr, _ = d.text(">", 0, Y, size, "b", c["red"])
    d.body.append(f'<g class="n" style="animation-delay:1.3s">{pr}</g>')

    # TextType: type each phrase, hold, backspace, move to the next, loop
    els, ev, t = [], [(0.0, X0)], 1.8
    for k, ph in enumerate(PHRASES):
        tt, appear = t, []
        for i, ch in enumerate(ph):
            appear.append(tt)
            ev.append((tt, X0 + (i + 1) * adv))
            tt += step(i, k, ch)
        td, gone = tt + 1.8, [0.0] * len(ph)
        for i in range(len(ph) - 1, -1, -1):
            gone[i] = td
            ev.append((td, X0 + i * adv))
            td += 0.032
        t = td + 0.45
        els.append((ph, appear, gone))
    T = round(t, 3)
    parts = []
    for ph, appear, gone in els:
        for i, ch in enumerate(ph):
            if ch == " ": continue
            parts.append(
                f'<g opacity="0" fill="{c["ink"]}">{d.glyph("r", ch, X0 + i * adv, Y, size)}'
                f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{appear[i] / T:.4f};{gone[i] / T:.4f}" '
                f'calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>')
    seq, last = [], -1.0
    for te, x in ev:
        if te <= last: te = last + 0.001
        seq.append((te, x)); last = te
    kt = ";".join(f"{e[0] / T:.4f}" for e in seq)
    cur = (f'<rect x="{X0}" y="{Y - 15}" width="2" height="19" fill="{c["red"]}" opacity="0">'
           f'<animate attributeName="x" values="{";".join(f"{e[1]:.1f}" for e in seq)}" keyTimes="{kt}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/>'
           f'<animate attributeName="opacity" values="0;1;1;0.1;1" keyTimes="0;0.001;0.3;0.65;1" calcMode="spline" keySplines="0 0 1 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1" begin="1.5s" dur="1.1s" repeatCount="indefinite"/></rect>')
    d.body.append("".join(parts) + cur)
    save("header", th, d)


# ---------------------------------------------------------------- terminal
def terminal(th):
    c = THEMES[th]
    size = 16
    adv = GL["r"]["adv"] * size / 1000
    T, X0 = 11.0, 24
    d = Doc(900, 148, "terminal: whoami, cat about.txt")
    lines = [("whoami", ("A5CENSION-SRT", c["accent"])),
             ("cat about.txt", ("first-principles thinking, scalable systems, resilient code.", c["muted"]))]
    ys = [28, 92]

    def fade_in(t, dur=0.18):
        a, b = t / T, (t + dur) / T
        return (f'<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;{a:.4f};{b:.4f};1" '
                f'dur="{T}s" repeatCount="1" fill="freeze"/>')

    els, ev = [], [(0.0, X0, ys[0] - 15)]
    t = 0.7
    for k, (cmd, outp) in enumerate(lines):
        y = ys[k]
        els.append(f'<g opacity="0" fill="{c["red"]}">{d.glyph("r", "$", 0, y, size)}{fade_in(t)}</g>')
        ev.append((t, X0, y - 15))
        tt = t + 0.25  # a beat before typing starts
        for i, ch in enumerate(cmd):
            if ch != " ":
                els.append(f'<g opacity="0" fill="{c["ink"]}">{d.glyph("r", ch, X0 + i * adv, y, size)}{fade_in(tt, 0.12)}</g>')
            ev.append((tt, X0 + (i + 1) * adv, y - 15))
            tt += step(i, k, ch)
        t = tt
        if outp:
            txt, col = outp
            to = t + 0.4  # enter, then output appears
            for i, ch in enumerate(txt):
                if ch == " ": continue
                els.append(f'<g opacity="0" fill="{col}">{d.glyph("r", ch, X0 + i * adv, y + 26, size)}{fade_in(to, 0.45)}</g>')
            t = to + 0.9
            if k + 1 < len(ys):
                ev.append((t, X0, ys[k + 1] - 15))
                t += 0.1
    seq, last = [], -1.0
    for te, x, y in ev:
        if te <= last: te = last + 0.001
        seq.append((te, x, y)); last = te
    kt = ";".join(f"{e[0] / T:.4f}" for e in seq)
    hide = t
    cur = (f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{hide / T:.4f};{(hide + 0.3) / T:.4f};1" dur="{T}s" repeatCount="1" fill="freeze"/>'
           f'<rect x="{X0}" y="{ys[0] - 15}" width="8" height="18" fill="{c["accent"]}">'
           f'<animate attributeName="x" values="{";".join(f"{e[1]:.1f}" for e in seq)}" keyTimes="{kt}" calcMode="discrete" dur="{T}s" repeatCount="1" fill="freeze"/>'
           f'<animate attributeName="y" values="{";".join(f"{e[2]:.1f}" for e in seq)}" keyTimes="{kt}" calcMode="discrete" dur="{T}s" repeatCount="1" fill="freeze"/>'
           f'<animate attributeName="opacity" values="1;0.1;1" keyTimes="0;0.5;1" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1" dur="1.1s" repeatCount="indefinite"/></rect></g>')
    d.body.append(f'<g>{"".join(els)}{cur}</g>')
    save("terminal", th, d)


# -------------------------------------------------------------- data (API)
QUERY = """
query($login:String!){ user(login:$login){
 contributionsCollection{
  totalCommitContributions totalPullRequestContributions totalPullRequestReviewContributions
  totalIssueContributions restrictedContributionsCount
  contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount weekday } } } }
 repositories(first:100, ownerAffiliations:OWNER, isFork:false){ totalCount nodes{ stargazerCount
  languages(first:8, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name } } } } }
} }"""


def fetch():
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not tok:
        raise SystemExit("GH_TOKEN not set: skipping contribution chart and stats")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {tok}", "Content-Type": "application/json", "User-Agent": "profile-readme-build"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]


def streaks(days):
    counts = [n for _, n in days]
    best = run = 0
    for n in counts:
        run = run + 1 if n else 0
        best = max(best, run)
    cur, i = 0, len(counts) - 1
    if i >= 0 and counts[i] == 0: i -= 1  # today may not have activity yet
    while i >= 0 and counts[i]:
        cur += 1; i -= 1
    return cur, best


# --------------------------------------------------------- contribution chart
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def contrib(th, user):
    c = THEMES[th]
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    W, H = 860, 262
    d = Doc(W, H, f"{cal['totalContributions']} contributions in the last year")
    allc = [x["contributionCount"] for wk in weeks for x in wk["contributionDays"]]
    nz = sorted(n for n in allc if n)
    mx = max(allc) or 1
    q = [nz[min(len(nz) - 1, int(len(nz) * p))] for p in (0.25, 0.5, 0.75)] if nz else [1, 2, 3]

    def level(n):
        if n == 0: return 0
        return 1 if n <= q[0] else 2 if n <= q[1] else 3 if n <= q[2] else 4

    cw, bw, ox, oy, rdx, rdy, maxh = 15.4, 10.0, 4.0, 10.5, 2.0, 12.5, 78
    gy0, x0 = 142, 2
    glint = "#FFFFFF" if th == "light" else "#E6F6F2"
    d.css.append(
        f"@keyframes rise{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}"
        f"@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}"
        f"@keyframes ping{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}"
        f"@keyframes glint{{0%,12%,100%{{opacity:0}}5%{{opacity:.8}}}}"
        f"@keyframes draw{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}"
        f".b{{opacity:0;animation:rise 1.2s {EASE} forwards}}"
        f".z{{opacity:0;animation:fade .9s ease-out forwards}}"
        f".t{{opacity:0;animation:fade .7s ease-out .1s forwards}}"
        f".p{{animation:ping 2.2s ease-in-out infinite}}"
        f".gl{{fill:{glint};opacity:0;animation:glint 9s ease-in-out infinite}}"
        f".ld{{transform-box:fill-box;transform-origin:bottom center;transform:scaleY(0);animation:draw 1s {EASE} 2.4s forwards}}")
    for i, col in enumerate(c["lv"]):
        d.css.append(f".f{i}{{fill:{col}}}.t{i}{{fill:{shade(col, c['top'])}}}.s{i}{{fill:{shade(col, c['side'])}}}")

    d.css.append(f".fr{{fill:{c['red']}}}.tr{{fill:{shade(c['red'], c['top'])}}}.sr{{fill:{shade(c['red'], c['side'])}}}"
                 f".fb{{fill:{c['blue']}}}.tb{{fill:{shade(c['blue'], c['top'])}}}.sb{{fill:{shade(c['blue'], c['side'])}}}")
    hot = {(wi, x["weekday"]) for _, wi, x in sorted(
        ((x["contributionCount"], wi, x) for wi, wk in enumerate(weeks) for x in wk["contributionDays"]),
        key=lambda t: -t[0])[:4]}
    warm = {(wi, x["weekday"]) for _, wi, x in sorted(
        ((x["contributionCount"], wi, x) for wi, wk in enumerate(weeks) for x in wk["contributionDays"]),
        key=lambda t: -t[0])[4:9]}
    zero, items, last, peak = [], [], None, None
    for wi, wk in enumerate(weeks):
        for day in wk["contributionDays"]:
            di, n = day["weekday"], day["contributionCount"]
            x = x0 + wi * cw + (6 - di) * rdx
            gy = gy0 + di * rdy
            lv = level(n)
            if (wi, di) in hot and n:
                lv = "r"
            elif (wi, di) in warm and n:
                lv = "b"
            if n == 0:
                h = 1.6
                zero.append(f'<polygon class="t0" points="{x:.1f},{gy - h:.1f} {x + bw:.1f},{gy - h:.1f} {x + bw + ox:.1f},{gy - h - oy:.1f} {x + ox:.1f},{gy - h - oy:.1f}"/>'
                            f'<rect class="f0" x="{x:.1f}" y="{gy - h:.1f}" width="{bw}" height="{h}"/>')
                continue
            h = 2.5 + maxh * (n / mx) ** 0.62
            delay = 0.25 + wi * 0.017 + di * 0.012
            top = f"{x:.1f},{gy - h:.1f} {x + bw:.1f},{gy - h:.1f} {x + bw + ox:.1f},{gy - h - oy:.1f} {x + ox:.1f},{gy - h - oy:.1f}"
            items.append((di, wi,
                f'<g class="b" style="animation-delay:{delay:.2f}s">'
                f'<rect class="f{lv}" x="{x:.1f}" y="{gy - h:.1f}" width="{bw}" height="{h:.1f}"/>'
                f'<polygon class="t{lv}" points="{top}"/>'
                f'<polygon class="s{lv}" points="{x + bw:.1f},{gy - h:.1f} {x + bw + ox:.1f},{gy - h - oy:.1f} {x + bw + ox:.1f},{gy - oy:.1f} {x + bw:.1f},{gy:.1f}"/>'
                f'<polygon class="gl" points="{top}" style="animation-delay:{3.0 + wi * 0.07 + di * 0.01:.2f}s"/></g>'))
            last = (x, gy, h)
            if peak is None or n > peak[0]:
                peak = (n, day["date"], x, gy, h)
    items.sort(key=lambda t: (t[0], t[1]))
    d.body.append(f'<g class="z" style="animation-delay:.1s">{"".join(zero)}</g>')
    d.body += [b for _, _, b in items]

    # month labels along the front edge
    seen, last_wi = None, -99
    front = gy0 + 6 * rdy + 18
    for wi, wk in enumerate(weeks):
        m = int(wk["contributionDays"][0]["date"][5:7]) - 1
        if m != seen:
            seen = m
            # skip a label that would crowd the previous one or run off the right edge
            if wi - last_wi >= 4 and wi < len(weeks) - 3:
                last_wi = wi
                t, _ = d.text(MONTHS[m], x0 + wi * cw, front, 10, "r", c["muted"])
                d.body.append(f'<g class="t">{t}</g>')

    # today marker
    if last:
        x, gy, h = last
        d.body.append(f'<g class="t"><rect class="p" x="{x + bw / 2 - 1.5:.1f}" y="{gy - h - oy - 10:.1f}" width="3" height="3" fill="{c["red"]}"/></g>')

    # peak callout: leader line + label, drawn after the bars
    if peak:
        n, date, x, gy, h = peak
        px = x + (bw + ox) / 2
        ty = gy - h - oy
        mon = MONTHS[int(date[5:7]) - 1]
        lab, lw = d.text(f"peak {n}  ·  {mon} {int(date[8:10])}", px - 12, ty - 14, 11, "r", c["ink"], anchor="end")
        d.body.append(f'<g class="t" style="animation-delay:2.6s"><rect class="ld" x="{px - 0.5:.1f}" y="{ty - 22:.1f}" width="1" height="18" fill="{c["red"]}"/>'
                      f'<rect x="{px - 12:.1f}" y="{ty - 23:.1f}" width="12" height="1" fill="{c["red"]}"/>{lab}</g>')

    total = f"{cal['totalContributions']:,}"
    active = sum(1 for n in allc if n)
    num, _ = d.text(total, 0, 34, 34, "b", c["accent"])
    cap, _ = d.text(f"contributions in the last year  ·  active {active} of {len(allc)} days", 0, 56, 12, "r", c["muted"])
    d.body.append(f'<g class="t">{num}{cap}</g>')
    more, mw = d.text("more", W, 21, 11, "r", c["muted"], anchor="end")
    leg = "".join(f'<rect class="f{i}" x="{W - mw - 8 - (5 - i) * 14:.1f}" y="12" width="10" height="10"/>' for i in range(5))
    less, _ = d.text("less", W - mw - 8 - 5 * 14 - 6, 21, 11, "r", c["muted"], anchor="end")
    d.body.append(f'<g class="t">{less}{leg}{more}</g>')
    save("contrib", th, d)


# ------------------------------------------------------------------- stats
def stats(th, user):
    c = THEMES[th]
    cc = user["contributionsCollection"]
    days = [(x["date"], x["contributionCount"]) for wk in cc["contributionCalendar"]["weeks"] for x in wk["contributionDays"]]
    cur, best = streaks(days)
    repos = user["repositories"]
    stars = sum(r["stargazerCount"] for r in repos["nodes"])
    langs = {}
    for r in repos["nodes"]:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    tot = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    rest = tot - sum(v for _, v in top)
    segs = [(k, v / tot) for k, v in top] + ([("other", rest / tot)] if rest > 0 else [])

    W, H = 860, 178
    d = Doc(W, H, "profile stats")
    d.css.append(
        f"@keyframes up{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}"
        f"@keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}"
        f".m{{opacity:0;animation:up .9s {EASE} forwards}}"
        f".g{{transform-box:fill-box;transform-origin:left center;transform:scaleX(0);animation:grow 1.2s {EASE} forwards}}")
    metrics = [("COMMITS", cc["totalCommitContributions"]), ("PULL REQUESTS", cc["totalPullRequestContributions"]),
               ("REPOSITORIES", repos["totalCount"]), ("STARS EARNED", stars), ("LONGEST STREAK", best)]
    colw = W / len(metrics)
    for i, (lab, val) in enumerate(metrics):
        x = i * colw
        l, _ = d.text(lab, x, 14, 11, "r", c["muted"])
        v, vw = d.text(f"{val:,}", x, 54, 32, "b", c["red"] if lab == "LONGEST STREAK" else c["ink"])
        unit = ""
        if lab == "LONGEST STREAK":
            unit, _ = d.text("days", x + vw + 8, 54, 12, "r", c["muted"])
        d.body.append(f'<g class="m" style="animation-delay:{0.1 + i * 0.09:.2f}s">{l}{v}{unit}</g>')
    # language bar
    by, bh, gap = 92, 8, 3
    tints = [mix(c["accent"], c["muted"], i / max(1, len(segs) - 1) * 0.85) for i in range(len(segs))]
    if th == "light":
        tints = [mix(c["accent"], "#A9C9C1", i / max(1, len(segs) - 1)) for i in range(len(segs))]
    pal = [c["blue"], c["accent"], c["red"], mix(c["accent"], c["muted"], 0.5), mix(c["blue"], c["muted"], 0.45), c["muted"]]
    tints = [pal[i % len(pal)] for i in range(len(segs))]
    x = 0.0
    avail = W - gap * (len(segs) - 1)
    for i, (name, frac) in enumerate(segs):
        w = max(2.0, avail * frac)
        d.body.append(f'<rect class="g" x="{x:.1f}" y="{by}" width="{w:.1f}" height="{bh}" fill="{tints[i]}" style="animation-delay:{0.5 + i * 0.1:.2f}s"/>')
        x += w + gap
    lx = 0.0
    for i, (name, frac) in enumerate(segs):
        label = f"{name} {frac * 100:.1f}%"
        t, tw = d.text(label, lx + 14, 128, 12, "r", c["muted"])
        d.body.append(f'<g class="m" style="animation-delay:{0.9 + i * 0.07:.2f}s"><rect x="{lx:.1f}" y="119" width="8" height="8" fill="{tints[i]}"/>{t}</g>')
        lx += 14 + tw + 22
    save("stats", th, d)


# ------------------------------------------------------------------- stack
def stack(th):
    c = THEMES[th]
    icons = json.load(open(os.path.join(HERE, "icons.json"), encoding="utf-8"))
    W, H = 860, 92
    d = Doc(W, H, "tech stack: " + ", ".join(i["label"] for i in icons))
    d.css.append(f"@keyframes up{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}"
                 f".i{{opacity:0;animation:up .9s {EASE} forwards}}")
    n, size = len(icons), 30
    k = size / 24
    for i, ic in enumerate(icons):
        cx = (i + 0.5) * W / n
        col = c["blue"] if ic["label"] == "docker" else c["red"] if ic["label"] == "git" else c["accent"]
        lab, _ = d.text(ic["label"], cx, 76, 9, "r", c["muted"], anchor="middle")
        d.body.append(
            f'<g class="i" style="animation-delay:{0.1 + i * 0.06:.2f}s">'
            f'<path transform="translate({cx - size / 2:.2f} 12) scale({k})" d="{ic["d"]}" fill="{col}"/>{lab}</g>')
    save("stack", th, d)


def links(th):
    c = THEMES[th]
    ic = json.load(open(os.path.join(HERE, "linkicons.json"), encoding="utf-8"))
    for key in ("portfolio", "linkedin", "leetcode"):
        w = int(len(key) * 8.2 + 74)
        d = Doc(w, 40, key)
        d.css.append("@keyframes fade{from{opacity:0}to{opacity:1}}.t{opacity:0;animation:fade .8s ease-out forwards}")
        t, _ = d.text(key, 42, 25, 13, "r", c["ink"])
        if key == "portfolio":
            g = (f'<g transform="translate(18 10)" fill="none" stroke="{c["red"]}" stroke-width="1.6">'
                 f'<circle cx="10" cy="10" r="8.5"/><ellipse cx="10" cy="10" rx="3.6" ry="8.5"/><path d="M1.5 10h17"/></g>')
        else:
            g = f'<path transform="translate(18 10) scale(0.83)" d="{ic[key]}" fill="{c["red"]}"/>'
        ax = w - 24
        arrow = (f'<path d="M{ax} 25 L{ax + 8} 17 M{ax + 1} 17 H{ax + 8} V24" fill="none" stroke="{c["muted"]}" '
                 f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>')
        d.body.append(f'<g class="t"><rect x="0.5" y="0.5" width="{w - 1}" height="39" rx="20" fill="{c["red"]}" fill-opacity=".08" '
                      f'stroke="{c["red"]}" stroke-opacity=".45"/>{g}{t}{arrow}</g>')
        save(key, th, d)


if __name__ == "__main__":
    for th in THEMES:
        header(th)
        terminal(th)
        stack(th)
        links(th)
    user = fetch()
    for th in THEMES:
        contrib(th, user)
        stats(th, user)
