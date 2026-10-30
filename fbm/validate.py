"""
fbm/validate.py — validate (and optionally fix) generated listing copy.

  python -m fbm.validate --in inventory.csv
  python -m fbm.validate --in inventory.csv --fix --report validate.json
  python -m fbm.validate --in inventory.csv --llm-check
"""
from __future__ import annotations
import argparse, csv, json, os, re
import requests

EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
BRANDS = {"stanley", "yeti", "nike", "adidas", "apple", "samsung", "anker", "jbl", "bose",
          "dyson", "ninja", "instant", "pot", "hydro", "flask", "owala", "fitbit", "garmin",
          "kindle", "google", "amazon", "logitech", "sony", "beats", "rayban", "oakley",
          "levis", "columbia", "northface"}
COMMON = {"the", "a", "an", "and", "or", "for", "with", "without", "your", "you", "new",
          "set", "pack", "kit", "pro", "max", "plus", "mini", "smart", "led", "usb",
          "home", "car", "pet", "dog", "cat", "kids", "baby", "women", "men", "large",
          "small", "black", "white", "grey", "gray", "blue", "red", "green", "pink",
          "steel", "stainless", "adjustable", "portable", "reusable", "wireless",
          "cordless", "bluetooth", "digital", "electric", "premium", "heavy", "duty",
          "non", "slip", "anti", "waterproof", "washable", "foldable", "collapsible",
          "upgraded", "inch", "ft", "oz", "ml", "lb", "kg", "gift", "travel", "outdoor",
          "indoor", "gym", "kitchen", "bathroom", "bedroom"}
BANNED = {"!!!", "!!", "100%", "cheap", "sale", "best", "hot"}


def flags_for(title, desc):
    f = []
    if len(title) > 80:
        f.append(f"title_too_long:{len(title)}")
    if EMOJI.search(title) or EMOJI.search(desc):
        f.append("emoji")
    caps = [w for w in re.findall(r"\b[A-Z]{3,}\b", title)
            if w.lower() not in {"usb", "led", "usb-c", "abs", "bpa", "ipx7", "hdmi", "av", "pc"}]
    if caps:
        f.append("all_caps:" + ",".join(caps))
    low = f"{title} {desc}".lower()
    for b in BANNED:
        if b in low:
            f.append(f"banned:{b}")
    for w in re.findall(r"(?<!\.\s)(?<!\A)\b([A-Z][a-z]{2,})\b", f"{title} {desc}"):
        wl = w.lower()
        if wl not in BRANDS and wl not in COMMON:
            f.append(f"possible_brand:{w}")
    if not desc.strip():
        f.append("empty_description")
    return f


def llm_brand_check(title, desc, model, base_url, key):
    prompt = (f"Title: {title}\nDescription: {desc}\n\n"
              "List any words that look like a BRAND CLAIM. For each, say plausible:yes/no. "
              'Return strict JSON: {"brands":[{"word":"","plausible":true}]}')
    r = requests.post(f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "temperature": 0,
              "messages": [{"role": "user", "content": prompt}]}, timeout=45)
    r.raise_for_status()
    txt = r.json()["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", txt, re.S)
    return json.loads(m.group(0)) if m else {"brands": []}


def fix(row):
    t = row["title"]
    t = EMOJI.sub("", t)
    t = re.sub(r"\b([A-Z]{3,})\b", lambda m: m.group(1).capitalize()
               if m.group(1).lower() not in {"usb", "led", "abs", "bpa", "hdmi", "av", "pc"}
               else m.group(1), t)
    t = re.sub(r"\s+", " ", t).strip(" -")
    if len(t) > 80:
        t = t[:80].rsplit(" ", 1)[0]
    row["title"] = t
    for b in BANNED:
        row["description"] = re.sub(re.escape(b), "", row["description"], flags=re.I)
    row["description"] = re.sub(r"\s+", " ", EMOJI.sub("", row["description"])).strip()
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="inventory.csv")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--report", default="")
    ap.add_argument("--llm-check", action="store_true")
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--base-url", default="https://api.openai.com/v1")
    args = ap.parse_args()

    key = os.getenv("OPENAI_API_KEY", "")
    with open(args.inp, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    seen, report = {}, []
    for r in rows:
        fl = flags_for(r["title"], r["description"])
        if r["title"] in seen:
            fl.append(f"duplicate_of:{seen[r['title']]}")
        seen[r["title"]] = r["sku"]
        if args.llm_check and key:
            try:
                bc = llm_brand_check(r["title"], r["description"], args.model, args.base_url, key)
                for b in bc.get("brands", []):
                    if not b.get("plausible", True):
                        fl.append(f"llm_implausible_brand:{b['word']}")
            except Exception as e:
                fl.append(f"llm_check_failed:{e}")
        if fl:
            report.append({"sku": r["sku"], "flags": fl})
        if args.fix and fl:
            fix(r)
        print(f"{r['sku']:8} {'OK' if not fl else ' | '.join(fl)}")

    if args.fix:
        cols = list(rows[0].keys())
        with open(args.inp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
        print(f"fixed and rewrote {args.inp}")
    if args.report:
        json.dump(report, open(args.report, "w"), indent=2); print(f"report -> {args.report}")
    print(f"{len(report)}/{len(rows)} rows flagged")


if __name__ == "__main__":
    main()