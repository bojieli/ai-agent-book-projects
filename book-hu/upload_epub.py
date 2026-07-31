#! /usr/bin/env python3
"""Upload EPUB to GitHub fork"""
import json, base64, sys, requests
sys.stdout.reconfigure(line_buffering=True)

TOKEN = "ghp_jy…4OXJ"
OWNER = "barmivalami0-ux"
REPO = "ai-agent-book"
FILE = "/home/leno/.openclaw/workspace/book-hu/AI-Agent-Book_HU.epub"
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
API = "https://api.github.com"

def api(method, path, data=None):
    r = requests.request(method, f"{API}{path}", headers=HEADERS, json=data, timeout=120)
    if r.status_code not in (200, 201):
        print(f"❌ {method} {path}: {r.status_code} {r.text[:100]}")
        return None
    return r.json()

# Get base
base = api("GET", f"/repos/{OWNER}/{REPO}/git/refs/heads/main")
if not base: sys.exit(1)
base_sha = base["object"]["sha"]
print(f"Base commit: {base_sha[:8]}")

commit = api("GET", f"/repos/{OWNER}/{REPO}/git/commits/{base_sha}")
tree_sha = commit["tree"]["sha"]
print(f"Base tree: {tree_sha[:8]}")

# Create blob from EPUB
with open(FILE, "rb") as f:
    content = base64.b64encode(f.read()).decode("ascii")
print(f"EPUB base64: {len(content)} chars")

blob = api("POST", f"/repos/{OWNER}/{REPO}/git/blobs", {
    "content": content, "encoding": "base64"
})
if not blob: sys.exit(1)
blob_sha = blob["sha"]
print(f"EPUB blob: {blob_sha[:8]}")

# Get current tree
tree_data = api("GET", f"/repos/{OWNER}/{REPO}/git/trees/{tree_sha}")
tree_items = tree_data["tree"]

# Add EPUB file to tree
tree_items.append({
    "path": "book-hu/AI-Agent-Book_HU.epub",
    "mode": "100644",
    "type": "blob",
    "sha": blob_sha
})

# Create new tree
new_tree = api("POST", f"/repos/{OWNER}/{REPO}/git/trees", {
    "base_tree": tree_sha,
    "tree": tree_items
})
if not new_tree: sys.exit(1)
new_tree_sha = new_tree["sha"]
print(f"New tree: {new_tree_sha[:8]}")

# Create commit
new_commit = api("POST", f"/repos/{OWNER}/{REPO}/git/commits", {
    "message": "📱 Add EPUB fájl a könnyű letöltésért\n\nAz AI Agent - Tervezési elvek és gyakorlat magyar fordítása EPUB formátumban, 132 beágyazott ábrával.",
    "tree": new_tree_sha,
    "parents": [base_sha],
    "author": {"name": "Ady AI", "email": "ady-ai@users.noreply.github.com"},
    "committer": {"name": "Ady AI", "email": "ady-ai@users.noreply.github.com"}
})
if not new_commit: sys.exit(1)
print(f"Commit: {new_commit['sha'][:8]}")

# Update ref
result = api("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/main", {
    "sha": new_commit["sha"], "force": False
})
if result:
    print(f"\n🎉 EPUB felkerült a GitHub-ra!")
    print(f"   https://github.com/{OWNER}/{REPO}/blob/main/book-hu/AI-Agent-Book_HU.epub")
    print(f"\n📥 Közvetlen letöltés (bárki számára):")
    print(f"   https://raw.githubusercontent.com/{OWNER}/{REPO}/main/book-hu/AI-Agent-Book_HU.epub")
else:
    print("❌ Hiba")
