"""
fbm/copygen.py — generate Marketplace copy from a spec, with variant rotation.

Input : skus.csv  (sku,product,niche,keywords,features,price,cost,source,photos)
Output: inventory.csv (bot format) + copy_variants.json (3 titles per SKU)

Usage:
  python -m fbm.copygen --in skus.csv --out inventory.csv --model gpt-4o-mini
  python -m fbm.copygen --base-url https://openrouter.ai/api/v1 --model <model>
  python -m fbm.copygen --offline          # no API, template fallback
"""
from __future__ import annotations
import argparse, csv, json, os, re, time
import requests

SYS = """You write Facebook Marketplace listing copy for a US dropshipper.
Rules:
- Title: <= 80 chars, keyword-first (the words a buyer types), plain language,
  no emoji, no ALL CAPS, at most one dash.
- Description: 3-5 short sentences, benefit-led and concrete, ends with a
  shipping/guarantee line. No emoji.
- No brand names unless the item is genuinely generic.
- Pick a Facebook Marketplace category and condition.
Return STRICT JSON only:
{"titles":["...","...","..."],"description":"...","category":"...","condition":"New"}"""


def parse_json(s):
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def call_llm(row, model, base_url, key):
    user = (f"Product: {row['product']}\nNiche: {row['niche']}\n"
            f"Keywords: {row.get('keywords', '')}\nFeatures: {row.get('features', '')}\n"
            f"List price: ${row.get('price', '')}")
    r = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "temperature": 0.7,
              "messages": [{"role": "system", "content": SYS},
                           {"role": "user", "content": user}]},
        timeout=60)
    r.raise_for_status()
    return parse_json(r.json()["choices"][0]["message"]["content"])


def offline(row):
    kw = row.get("keywords", row["product"]).split(",")[0].strip().title()
    return {"titles": [f"{kw} - {row['product']}"[:80],
                       f"{row['product']} - {kw} for Home"[:80],
                       f"New {row['product']} - Fast Free Shipping"[:80]],
            "description": (f"{row['product']} built for everyday use. "
                            f"{row.get('features', 'Great value and easy to use.')} "
                            "Ships fast with tracking and a money-back guarantee."),
            "category": row.get("category", "Home & Kitchen"), "condition": "New"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="skus.csv")
    ap.add_argument("--out", default="inventory.csv")
    ap.add_argument("--variants", default="copy_variants.json")
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--base-url", default="https://api.openai.com/v1")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    key = os.getenv("OPENAI_API_KEY", "")
    if not args.offline and not key:
        print("no OPENAI_API_KEY set -> falling back to offline mode"); args.offline = True

    with open(args.inp, newline="", encoding="utf-8") as f:
        spec = list(csv.DictReader(f))

    variants, out_rows = {}, []
    for i, row in enumerate(spec, 1):
        try:
            data = offline(row) if args.offline else call_llm(row, args.model, args.base_url, key)
        except Exception as e:
            print(f"{row.get('sku', '?')}: LLM failed ({e}) -> offline fallback")
            data = offline(row)
        titles = (data.get("titles") or [row["product"]])[:3]
        variants[row["sku"]] = titles
        out_rows.append({
            "sku": row["sku"], "title": titles[0], "price": row.get("price", ""),
            "category": data.get("category", "Home & Kitchen"),
            "condition": data.get("condition", "New"),
            "description": data.get("description", ""),
            "photos": row.get("photos", ""), "cost": row.get("cost", ""),
            "source": row.get("source", "")})
        print(f"[{i}/{len(spec)}] {row['sku']} -> {titles[0][:60]}")
        time.sleep(0.4)

    cols = ["sku", "title", "price", "category", "condition", "description",
            "photos", "cost", "source"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out_rows)
    with open(args.variants, "w", encoding="utf-8") as f:
        json.dump(variants, f, indent=2)
    print(f"wrote {args.out} and {args.variants}")


if __name__ == "__main__":
    main()