"""
fbm/returns.py — canned message tree + RMA flow.
"""
from __future__ import annotations
import re
from fbm import core as C
from fbm import suppliers as Suppliers

INTENTS = {
    "tracking": r"\b(tracking|track|where.*order|shipped|arrive)\b",
    "shipping": r"\b(ship|deliver|how long|when will)\b",
    "return":   r"\b(return|refund|money back|send.*back)\b",
    "damaged":  r"\b(broken|damaged|defective|cracked|doesn'?t work)\b",
    "wrong":    r"\b(wrong|not as described|different)\b",
    "thanks":   r"\b(thanks|thank you|love it|great)\b",
}
SEED = {
 "tracking": "Hi! Your order is on the way - tracking: {tracking}. It updates within 24h. Thanks!",
 "shipping": "Hi! Standard delivery is 5-8 business days and you'll get tracking as soon as it ships.",
 "return":   "No problem! You're covered - I'll send a prepaid return label. Ship it back within 30 days for a full refund.",
 "damaged":  "So sorry! Send a photo and I'll ship a replacement right away - no need to return the broken one.",
 "wrong":    "Apologies! Send a photo and I'll ship the correct item immediately.",
 "thanks":   "Thank you so much! A quick review really helps my small shop. Enjoy!",
}


def classify(text):
    t = text.lower()
    for intent, pat in INTENTS.items():
        if re.search(pat, t):
            return intent
    return None


def reply(text, tracking=""):
    intent = classify(text)
    return (intent, SEED[intent].format(tracking=tracking or "(pending)")) if intent else (None, None)


def rma(sku_row):
    return (f"RMA {sku_row['sku']}:\n 1) {Suppliers.rma_info(sku_row)}\n"
            " 2) approve in the buyer's favour (account health > one unit)\n"
            " 3) log it to events")