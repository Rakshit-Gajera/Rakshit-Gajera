#!/usr/bin/env python3
"""Draws the last year of GitHub contributions as a spiral galaxy.

Reads the contribution calendar from the GitHub API and writes assets/galaxy.svg
and assets/galaxy-m.svg. Standard library only. Needs GH_TOKEN in the environment.
"""
import json
import math
import os
import random
import urllib.request
from datetime import date

USER = "Rakshit-Gajera"
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Content-Type": "application/json", "User-Agent": "readme-galaxy"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    days = [(d["date"], d["contributionCount"]) for d in days if d["date"] <= date.today().isoformat()]
    return cal["totalContributions"], days


def stats(days):
    longest = run = active = 0
    for _, c in days:
        if c:
            run += 1
            active += 1
            longest = max(longest, run)
        else:
            run = 0
    current = 0
    tail = days[:-1] if days and days[-1][1] == 0 else days  # today not over yet
    for _, c in reversed(tail):
        if not c:
            break
        current += 1
    best = max(days, key=lambda d: d[1])
    return {"current": current, "longest": longest, "active": active, "best": best}


def level(c, peak):
    if c == 0:
        return 0
    x = math.log1p(c) / math.log1p(max(peak, 1))
    return 1 if x < 0.34 else 2 if x < 0.55 else 3 if x < 0.78 else 4


COLORS = ["#40404a", "#a65f22", "#ee9436", "#ffc873", "#fff6e2"]
RADII = [2.2, 3.4, 4.5, 5.6, 7.0]


def nice_date(iso):
    y, m, d = map(int, iso.split("-"))
    return f"{d} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m - 1]} {y}"


def galaxy_group(days, cx, cy, radius, tilt, core_b64, core_w, spin=240):
    random.seed(29)
    peak = max(c for _, c in days)
    n = len(days)
    r0 = core_w * 0.34
    turns = 5.2
    dots, today = [], None
    dust = []
    for _ in range(420):
        a, r = random.uniform(0, math.tau), r0 + (radius * 1.08 - r0) * random.random() ** 0.7
        dust.append(f'<circle cx="{r * math.cos(a):.1f}" cy="{r * math.sin(a):.1f}" r="{random.uniform(.4, 1.1):.1f}" fill="#9fb0d8" opacity="{random.uniform(.08, .42):.2f}"/>')
    for i, (_, c) in enumerate(days):
        s = (i + 6) / (n + 5)
        th = turns * math.tau * math.sqrt(s) + 0.4
        r = r0 + (radius - r0) * math.sqrt(s)
        x, y = r * math.cos(th) + random.uniform(-2.2, 2.2), r * math.sin(th) + random.uniform(-2.2, 2.2)
        lv = level(c, peak)
        if lv >= 3:
            dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{RADII[lv] * 2.3:.1f}" fill="#ff9d3c" opacity=".2"/>')
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{RADII[lv]}" fill="{COLORS[lv]}"/>')
        if i == n - 1:
            today = (x, y)
    ping = (
        f'<circle cx="{today[0]:.1f}" cy="{today[1]:.1f}" r="7" fill="none" stroke="#4ade80" stroke-width="2">'
        '<animate attributeName="r" dur="2.4s" repeatCount="indefinite" values="6;20"/><animate attributeName="opacity" dur="2.4s" repeatCount="indefinite" values="1;0"/></circle>'
        f'<circle cx="{today[0]:.1f}" cy="{today[1]:.1f}" r="5" fill="#4ade80"/>'
    )
    h = core_w * 0.76
    return (
        f'<g transform="translate({cx} {cy}) scale(1 {tilt})"><g>'
        f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="{spin}s" repeatCount="indefinite"/>'
        + "".join(dust) + "".join(dots) + ping + "</g></g>"
        f'<image x="{cx - core_w / 2}" y="{cy - h / 2}" width="{core_w}" height="{h}" href="data:image/webp;base64,{core_b64}"/>'
    )


def stat(x, y, value, label, vs, ls, gap):
    return (
        f'<text x="{x}" y="{y}" font-family="B" font-weight="800" font-size="{vs}" letter-spacing="-1.4" fill="#f1f1ee">{value}</text>'
        f'<text x="{x}" y="{y + gap}" font-family="J" font-size="{ls}" letter-spacing="1" fill="#a3a39e">{label}</text>'
    )


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def svg(W, H, body, fonts):
    css = "".join(
        f"@font-face{{font-family:{fam};font-weight:{wt};src:url(data:font/woff;base64,{fonts[key]})}}"
        for key, fam, wt in [("bri", "B", 800), ("mono", "J", 400)]
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub contributions over the last year drawn as a spiral galaxy">'
        f"<style>{css}</style>"
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="26" fill="#050506" stroke="#26262a"/>{body}</svg>'
    )


def main():
    total, days = fetch()
    s = stats(days)
    fonts = json.load(open(os.path.join(ASSETS, "src", "fonts.json")))
    core = open(os.path.join(ASSETS, "src", "bh-core.b64")).read().strip()
    best = f"{s['best'][1]} on {nice_date(s['best'][0])}"

    legend = "".join(f'<circle cx="{i * 26}" cy="0" r="{RADII[i]}" fill="{COLORS[i]}"/>' for i in range(5))
    d = galaxy_group(days, 410, 322, 372, 0.66, core, 210)
    d += '<text x="800" y="94" font-family="J" font-size="17" letter-spacing="3" fill="#a3a39e">THE LAST 12 MONTHS</text>'
    d += f'<text x="798" y="212" font-family="B" font-weight="800" font-size="124" letter-spacing="-5" fill="#ffb45e">{total}</text>'
    d += '<text x="800" y="252" font-family="J" font-size="20" fill="#e4e4df">contributions on GitHub</text>'
    d += stat(800, 340, plural(s["current"], "day"), "current streak", 40, 16, 28)
    d += stat(1020, 340, plural(s["longest"], "day"), "longest streak", 40, 16, 28)
    d += stat(800, 440, plural(s["active"], "day"), "active days", 40, 16, 28)
    d += stat(1020, 440, str(s["best"][1]), "busiest day", 40, 16, 28)
    d += f'<g transform="translate(806 532)">{legend}</g><text x="944" y="538" font-family="J" font-size="15" fill="#8d8d88">each dot is one day</text>'
    d += '<text x="800" y="572" font-family="J" font-size="15" fill="#8d8d88"><tspan fill="#4ade80">green</tspan> marks today</text>'
    open(os.path.join(ASSETS, "galaxy.svg"), "w", encoding="utf-8").write(svg(1280, 620, d, fonts))

    m = galaxy_group(days, 360, 318, 326, 0.72, core, 180)
    m += '<text x="360" y="62" text-anchor="middle" font-family="J" font-size="22" letter-spacing="3" fill="#a3a39e">THE LAST 12 MONTHS</text>'
    m += f'<text x="360" y="716" text-anchor="middle" font-family="B" font-weight="800" font-size="118" letter-spacing="-4" fill="#ffb45e">{total}</text>'
    m += '<text x="360" y="762" text-anchor="middle" font-family="J" font-size="25" fill="#e4e4df">contributions on GitHub</text>'
    m += stat(56, 852, plural(s["current"], "day"), "current streak", 46, 22, 36)
    m += stat(392, 852, plural(s["longest"], "day"), "longest streak", 46, 22, 36)
    m += stat(56, 962, plural(s["active"], "day"), "active days", 46, 22, 36)
    m += stat(392, 962, str(s["best"][1]), "busiest day", 46, 22, 36)
    open(os.path.join(ASSETS, "galaxy-m.svg"), "w", encoding="utf-8").write(svg(720, 1040, m, fonts))
    print(f"total={total} days={len(days)} current={s['current']} longest={s['longest']} active={s['active']} best={best}")


if __name__ == "__main__":
    main()
