#!/usr/bin/env python3
"""Append one live hotel price to a JSONL snapshot (used while re-pricing stays on Booking.com).

usage: addrow.py <file.jsonl> <cc> <stay_id> <checkin> <checkout> <price|none> <score|none> <reviews|none> <booking_id|none> <name> [note]
price = total for the stay in EUR for 2 adults + children aged 5 and 7, free cancellation ("none" = not offered)."""
import datetime
import json
import sys


def num(x, cast=float):
    return None if x.lower() in ("none", "null", "-", "") else cast(x.replace(",", ""))


def main(a):
    if len(a) < 10:
        sys.exit(__doc__)
    path, cc, sid, ci, co, price, score, reviews, bid, name = a[:10]
    d1, d2 = datetime.date.fromisoformat(ci), datetime.date.fromisoformat(co)
    if not d1 < d2:
        sys.exit("checkout must be after checkin")
    row = dict(cc=cc, id=sid, name=name, booking_id=num(bid, int), checkin=ci, checkout=co, nights=(d2 - d1).days,
               price=num(price), score=num(score), reviews=num(reviews, int), note=a[10] if len(a) > 10 else "")
    with open(path, "a", encoding="utf8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("saved", cc, sid, ci, co, row["price"])


if __name__ == "__main__":
    main(sys.argv[1:])
