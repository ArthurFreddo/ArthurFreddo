"""Render a GitHub profile card using public REST API data."""

import json
import sys
from itertools import count
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


def get_json(path):
    request = Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-profile-card-generator",
        },
    )
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def public_stats(username):
    user_path = f"/users/{quote(username, safe='')}"
    user = get_json(user_path)
    repositories = {}

    for page in count(1):
        batch = get_json(f"{user_path}/repos?type=owner&sort=full_name&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("GitHub returned an invalid repository list")
        for repo in batch:
            stars = repo["stargazers_count"]
            if repo["private"] or type(stars) is not int or stars < 0:
                raise ValueError("GitHub returned invalid public repository statistics")
            repositories[repo["id"]] = stars
        if len(batch) < 100:
            break

    followers = user["followers"]
    if type(followers) is not int or followers < 0:
        raise ValueError("GitHub returned an invalid follower count")

    return len(repositories), sum(repositories.values()), followers


def render(username, metrics):
    title = f"{escape(username)}’s Public GitHub Stats"
    columns = []
    labels = ("Public Repositories", "Stars Earned", "Followers")
    for x, label, value in zip((90, 247.5, 405), labels, metrics):
        columns.append(f'''    <text x="{x}" y="109" fill="#fe428e" font-size="26" font-weight="700">{value:,}</text>
    <text x="{x}" y="139" fill="#a9fef7" font-size="13">{label}</text>''')
    column_markup = "\n".join(columns)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" aria-labelledby="title">
  <title id="title">{title}</title>
  <rect x="0.5" y="0.5" width="494" height="194" rx="5" fill="#141321" stroke="#e4e2e2"/>
  <g font-family="system-ui, sans-serif" text-anchor="middle">
    <text x="247.5" y="51" fill="#fe428e" font-size="22" font-weight="700">{title}</text>
{column_markup}
  </g>
</svg>
'''


if __name__ == "__main__":
    username, filename = sys.argv[1:]
    svg = render(username, public_stats(username))
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
