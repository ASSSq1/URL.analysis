import json
from pathlib import Path

# 1) أسماء ملفات Apify اللي نزلتها
JSON_FILES = [
    "dataset_contact-info-scraper_2026-03-04_19-31-32-519.json",
    "dataset_contact-info-scraper_2026-03-05_02-05-17-975.json",
    "dataset_contact-info-scraper_2026-03-05_02-07-40-641.json",
    "dataset_contact-info-scraper_2026-03-05_02-15-02-872.json",
]

def load_all_apify_items():
    all_items = []
    for fname in JSON_FILES:
        path = Path(fname)
        if not path.exists():
            print(f"تحذير: الملف {fname} غير موجود، بتجاوزه.")
            continue

        print(f"📂 جاري قراءة الملف: {fname}")
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                print(f"  → يحتوي على {len(data)} عنصر")
                all_items.extend(data)
            else:
                print("  → يحتوي على عنصر واحد فقط")
                all_items.append(data)

    print(f"\n✅ تم تحميل {len(all_items)} عنصر من جميع ملفات Apify.\n")
    return all_items

def normalize_apify_output(item):
    # 1) الأساسيات
    domain = item.get("domain") or ""
    original_url = item.get("originalStartUrl") or (f"https://{domain}" if domain else "")

    # 2) الإيميلات
    emails_raw = item.get("emails") or []
    emails = []
    for e in emails_raw:
        emails.append({
            "email": e,
            "source": "website",
            "type": "generic"
        })

    # 3) الأرقام
    phones_raw = item.get("phones") or []
    phones_uncertain = item.get("phonesUncertain") or []
    phones = []

    for p in phones_raw:
        phones.append({
            "phone": p,
            "source": "website"
        })

    for p in phones_uncertain:
        phones.append({
            "phone": p,
            "source": "website_uncertain"
        })

    # 4) السوشال ← هنا التعديل المهم
    socials = {
        "instagram": item.get("instagrams") or [],
        "tiktok": item.get("tiktoks") or [],
        "snapchat": item.get("snapchats") or [],
        "x_twitter": item.get("twitters") or [],
        "facebook": item.get("facebooks") or [],
        "linkedin": item.get("linkedIns") or [],  # ✅ l صغيرة + I كبيرة + n صغيرة + s
        "youtube": item.get("youtubes") or []
    }

    normalized = {
        "source_url": original_url,
        "normalized_domain": domain,
        "emails": emails,
        "phones": phones,
        "socials": socials,
        "raw_provider": {
            "apify_contact_details": item
        }
    }

    return normalized

def main():
    print("🚀 بدء التطبيع (normalize) لنتائج Apify ...\n")

    all_items = load_all_apify_items()

    normalized_list = []
    for idx, item in enumerate(all_items, start=1):
        norm = normalize_apify_output(item)
        normalized_list.append(norm)
        # نطبع أول كم عنصر فقط كعينة
        if idx <= 3:
            print(f"🔎 مثال عنصر مطبَّع رقم {idx}: domain = {norm['normalized_domain']}, linkedin = {norm['socials']['linkedin']}")

    # حفظ الناتج في ملف واحد
    output_path = Path("normalized_output.json")
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(normalized_list, f, ensure_ascii=False, indent=2)

    print(f"\n💾 تم حفظ {len(normalized_list)} عنصر في الملف: {output_path.name}")

if __name__ == "__main__":
    main()