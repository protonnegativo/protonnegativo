#!/usr/bin/env python3
"""Rebuild the open source contributions table in the READMEs.

Lists the merged pull requests the user authored in repositories they do not
own, grouped by organization, most merges first. The table goes between the
contributions:start and contributions:end markers of each README.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

USER = "protonnegativo"

# Display names for owners whose login is not the name people know them by.
NAMES = {
    "projectdiscovery": "ProjectDiscovery",
    "google": "Google",
    "apple": "Apple",
    "microsoft": "Microsoft",
    "NationalSecurityAgency": "NSA",
    "kubescape": "Kubescape",
    "trufflesecurity": "Truffle Security",
    "mitmproxy": "mitmproxy",
    "skylot": "jadx",
    "hydralauncher": "Hydra Launcher",
    "facebook": "Meta",
    "aws": "Amazon",
    "aws-cloudformation": "Amazon",
    "NVIDIA": "NVIDIA",
    "teslamotors": "Tesla",
}

READMES = {
    "README.md": ("Organization", "Merged", "Pull requests"),
    "README.pt-BR.md": ("Organização", "Merges", "Pull requests"),
}

START = "<!-- contributions:start -->"
END = "<!-- contributions:end -->"


def search(query):
    token = os.environ.get("GITHUB_TOKEN", "")
    items, page = [], 1
    while True:
        url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
            {"q": query, "per_page": 100, "page": page, "sort": "created", "order": "desc"}
        )
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            batch = json.load(resp)["items"]
        items += batch
        if len(batch) < 100:
            return items
        page += 1


def groups():
    prs = search(f"author:{USER} is:pr is:merged -user:{USER}")
    orgs = {}
    for pr in prs:
        owner, repo = pr["repository_url"].split("/repos/")[1].split("/")
        name = NAMES.get(owner, owner)
        orgs.setdefault(name, []).append((repo, pr["number"], pr["html_url"]))
    return sorted(orgs.items(), key=lambda kv: (-len(kv[1]), kv[0].lower()))


def table(headers, orgs):
    lines = [f"| {headers[0]} | {headers[1]} | {headers[2]} |", "|---|:---:|---|"]
    for name, prs in orgs:
        links = " · ".join(f"[{repo}#{num}]({url})" for repo, num, url in prs)
        lines.append(f"| **{name}** | {len(prs)} | {links} |")
    return "\n".join(lines)


def main():
    orgs = groups()
    if not orgs:
        sys.exit("no merged pull requests found; leaving the READMEs as they are")
    for path, headers in READMES.items():
        with open(path, encoding="utf-8") as f:
            text = f.read()
        block = f"{START}\n{table(headers, orgs)}\n{END}"
        new, n = re.subn(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
        if n != 1:
            sys.exit(f"{path}: expected one {START} ... {END} block, found {n}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)


if __name__ == "__main__":
    main()
