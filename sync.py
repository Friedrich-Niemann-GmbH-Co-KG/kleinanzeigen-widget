
import json
import os
import urllib.request
import urllib.parse

API_KEY = os.environ["KLAZ_API_KEY"]
SELLER_ID = os.environ["KLAZ_SELLER_ID"]

BASE_URL = (
    "https://api.kleinanzeigen-agent.de"
    "/api/v2/kleinanzeigen/sellers/"
    + urllib.parse.quote(SELLER_ID, safe="")
    + "/ads"
)

def get_image(ad):
    images = ad.get("images") or []
    for image in images:
        if isinstance(image, str) and image.startswith("https://"):
            return image
        if isinstance(image, dict):
            for key in ("url", "image_url", "src"):
                value = image.get(key)
                if isinstance(value, str) and value.startswith("https://"):
                    return value
    return ""

def format_price(ad):
    price = ad.get("price") or {}
    amount = price.get("amount")
    if amount is None:
        return "Preis auf Anfrage"
    return f"{amount:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def fetch_ads():
    result = []
    page = 0

    while True:
        params = urllib.parse.urlencode({
            "page": page,
            "size": 100
        })
        request = urllib.request.Request(
            BASE_URL + "?" + params,
            headers={"klaz_key": API_KEY}
        )

        with urllib.request.urlopen(request, timeout=40) as response:
            payload = json.load(response)

        if payload.get("success") is not True:
            raise RuntimeError("API meldet einen Fehler")

        data = payload["data"]

        for ad in data.get("ads", []):
            if ad.get("deleted") is True:
                continue
            if ad.get("status") not in (None, "ACTIVE"):
                continue

            result.append({
                "id": str(ad.get("ad_id", "")),
                "titel": ad.get("title", ""),
                "preis": format_price(ad),
                "bild": get_image(ad)
            })

        meta = data.get("meta", {})
        if not meta.get("has_next_page"):
            break

        next_page = meta.get("next_page")
        if next_page is None or int(next_page) <= page:
            raise RuntimeError("Ungültige Seitennavigation")
        page = int(next_page)

    return result

if __name__ == "__main__":
    ads = fetch_ads()

    if not ads:
        raise RuntimeError(
            "Keine aktiven Anzeigen gefunden. "
            "Bestehende Daten bleiben erhalten."
        )

    with open("ads.json.tmp", "w", encoding="utf-8") as f:
        json.dump(ads, f, ensure_ascii=False, indent=2)

    os.replace("ads.json.tmp", "ads.json")
    print(f"{len(ads)} Anzeigen erfolgreich importiert")
