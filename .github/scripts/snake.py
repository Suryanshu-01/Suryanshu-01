"""Generate a contribution-graph SVG with a snake that glides over the cells
(it does not eat them). Usage: snake.py <user> <outdir>  (needs GITHUB_TOKEN).
Set SNAKE_SAMPLE=1 to use random sample data instead of the API."""
import json, os, random, sys, urllib.request

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{weeks{contributionDays{contributionLevel}}}}}}"""
LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
THEMES = {
    "dark": dict(cells=["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"], snake="#a371f7"),
    "light": dict(cells=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"], snake="#8250df"),
}
CELL, PITCH, PAD = 12, 15, 12
BODY, STEP = 7, 0.09  # snake length (segments) and seconds between segments


def fetch(login):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"]},
    )
    data = json.load(urllib.request.urlopen(req))
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [[LEVELS.index(d["contributionLevel"]) for d in w["contributionDays"]] for w in weeks]


def sample():
    random.seed(1)
    return [[random.choice([0, 0, 0, 1, 2, 3, 4]) for _ in range(7)] for _ in range(53)]


def build(weeks, theme):
    t = THEMES[theme]
    cols = len(weeks)
    w, h = PAD * 2 + cols * PITCH, PAD * 2 + 7 * PITCH
    cx = lambda c: PAD + c * PITCH + CELL / 2
    cy = lambda r: PAD + r * PITCH + CELL / 2
    pts = []
    for c in range(cols):
        rows = range(len(weeks[c])) if c % 2 == 0 else reversed(range(len(weeks[c])))
        pts += [(cx(c), cy(r)) for r in rows]
    # path is relative to the first point so animateMotion offsets the segment
    x0, y0 = pts[0]
    d = "M0,0 " + " ".join(f"L{x - x0:.1f},{y - y0:.1f}" for x, y in pts[1:])
    dur = len(pts) * STEP
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">']
    for c, col in enumerate(weeks):
        for r, lvl in enumerate(col):
            out.append(f'<rect x="{PAD + c * PITCH}" y="{PAD + r * PITCH}" width="{CELL}" height="{CELL}" rx="2" fill="{t["cells"][lvl]}"/>')
    for i in range(BODY - 1, -1, -1):  # tail first so the head draws on top
        size = CELL - 2 - (i * 0.5 if i else 0)
        op = 1 if i == 0 else max(0.25, 0.9 - i * 0.11)
        out.append(
            f'<rect x="{x0 - size / 2:.1f}" y="{y0 - size / 2:.1f}" width="{size}" height="{size}" rx="3" '
            f'fill="{t["snake"]}" opacity="{op:.2f}">'
            f'<animateMotion dur="{dur:.1f}s" begin="{i * STEP:.2f}s" repeatCount="indefinite" path="{d}"/></rect>'
        )
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    user, outdir = sys.argv[1], sys.argv[2]
    weeks = sample() if os.environ.get("SNAKE_SAMPLE") else fetch(user)
    os.makedirs(outdir, exist_ok=True)
    for theme, name in (("light", "github-snake.svg"), ("dark", "github-snake-dark.svg")):
        with open(os.path.join(outdir, name), "w") as f:
            f.write(build(weeks, theme))
