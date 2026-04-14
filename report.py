import json, base64, datetime, urllib.request, os
from pathlib import Path

# 設定ファイルから読み込み（なければ環境変数）
def load_config():
    cfg_path = Path(__file__).parent / "auto" / "config.json"
    if cfg_path.exists():
        return json.loads(cfg_path.read_text())
    # リモート環境では環境変数から
    return {
        "youtube": {
            "api_key": os.environ.get("YT_KEY", ""),
            "channel_id": os.environ.get("CHANNEL_ID", "")
        },
        "github": {
            "token": os.environ.get("GH_TOKEN", ""),
            "repo": os.environ.get("GH_REPO", "")
        }
    }

cfg = load_config()
YT_KEY = cfg["youtube"]["api_key"]
CHANNEL_ID = cfg["youtube"]["channel_id"]
GH_TOKEN = cfg["github"]["token"]
GH_REPO = cfg["github"]["repo"]

def yt(url):
    try:
        r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return json.loads(urllib.request.urlopen(r, timeout=10).read())
    except Exception as e:
        return {"error": str(e)}

ch = yt(f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={CHANNEL_ID}&key={YT_KEY}")
s = ch.get("items", [{}])[0].get("statistics", {})
subs = int(s.get("subscriberCount", 0))
views = int(s.get("viewCount", 0))

sr = yt(f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={CHANNEL_ID}&order=date&maxResults=5&type=video&key={YT_KEY}")
ids = ",".join([i["id"]["videoId"] for i in sr.get("items", [])])
vd = yt(f"https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id={ids}&key={YT_KEY}")
videos = [(v["snippet"]["title"], int(v["statistics"].get("viewCount", 0))) for v in vd.get("items", [])]

now = datetime.datetime.utcnow()
jst = now + datetime.timedelta(hours=9)
fname = now.strftime("%Y-%m-%d-%H") + ".md"
vlines = "\n".join([f"- {t} ({c:,}回)" for t, c in videos[:3]])

report = f"""# Hourly Report {jst.strftime("%Y-%m-%d %H:%M")} JST

## YouTube
- 登録者数: {subs:,}
- 合計再生数: {views:,}
{vlines}

## SUZURI
- 商品数: 5点

## 動画企画（承認待ち）
1. 妊娠8ヶ月、眠れない夜の話 — 産前リアル・共感系
2. お金ないけど子供3人欲しい理由 — 正直トーク
3. 旦那と話してないとき何してる？ — ぐでぐで日常

## 優先アクション
- メンバー限定動画を1本録る（5分・スマホそのまま）
"""

b64 = base64.b64encode(report.encode()).decode()

sha = None
try:
    req2 = urllib.request.Request(
        f"https://api.github.com/repos/{GH_REPO}/contents/reports/{fname}",
        headers={"Authorization": f"token {GH_TOKEN}", "User-Agent": "bot"}
    )
    ex = json.loads(urllib.request.urlopen(req2).read())
    sha = ex["sha"]
except:
    pass

payload = {"message": f"report {fname}", "content": b64}
if sha:
    payload["sha"] = sha

data = json.dumps(payload).encode()
req3 = urllib.request.Request(
    f"https://api.github.com/repos/{GH_REPO}/contents/reports/{fname}",
    data=data,
    headers={"Authorization": f"token {GH_TOKEN}", "Content-Type": "application/json", "User-Agent": "bot"},
    method="PUT"
)
try:
    urllib.request.urlopen(req3, timeout=15)
    print(f"OK: reports/{fname}")
except Exception as e:
    print(f"ERROR: {e}")

print(report)
