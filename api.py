from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
import json
from pathlib import Path
import requests
import time
import re

from dotenv import load_dotenv
import os
from openai import OpenAI

# تحميل متغيرات البيئة
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY غير موجود في .env")
if not APIFY_API_TOKEN:
    print("⚠️ تحذير: APIFY_API_TOKEN غير موجود - سيتم استخدام البيانات المحلية فقط")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="28 Digital Presence Analyzer")

# تفعيل CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== اكتشاف نوع الرابط =====================

# كلمات يجب تجاهلها عند استخراج اسم النشاط
IGNORE_PATH_WORDS = {
    "ar", "en", "ar-sa", "en-sa", "ar-ae", "en-ae", "ar-kw", "en-kw",
    "home", "index", "main", "about", "contact", "products", "services",
    "category", "categories", "page", "pages", "blog", "news",
    "sa", "ae", "kw", "eg", "jo", "bh", "om", "qa",
    "www", "http", "https", "com", "net", "org", "site",
}


def extract_business_name_from_url(url: str) -> Optional[str]:
    """استخراج اسم النشاط من الرابط إذا كان موجوداً في المسار"""
    try:
        # إزالة البروتوكول
        path = url.replace("https://", "").replace("http://", "")
        parts = path.split("/")
        
        # الدومين
        domain = parts[0] if parts else ""
        
        # إذا فيه مسار بعد الدومين
        if len(parts) > 1:
            # نجرب من آخر جزء ونرجع للخلف
            for i in range(len(parts) - 1, 0, -1):
                part = parts[i].lower().strip()
                
                # تنظيف
                part_clean = part.replace("-", " ").replace("_", " ").replace("%20", " ")
                part_clean = part_clean.split(".")[0].split("?")[0].strip()
                
                # تجاهل الكلمات غير المفيدة
                if part_clean and len(part_clean) > 2:
                    # تحقق أن الكلمة ليست من الكلمات المستثناة
                    words_in_part = part_clean.split()
                    is_ignored = all(w.lower() in IGNORE_PATH_WORDS for w in words_in_part)
                    
                    if not is_ignored and len(part_clean) > 3:
                        print(f"📝 تم استخراج اسم النشاط من الرابط: {part_clean}")
                        return part_clean
        
        # إذا ما لقينا شي مفيد في المسار، نستخدم اسم الدومين
        domain_name = domain.replace("www.", "").split(".")[0]
        if domain_name and len(domain_name) > 2:
            print(f"📝 استخدام اسم الدومين: {domain_name}")
            return domain_name
        
        return None
    except Exception as e:
        print(f"⚠️ خطأ في استخراج الاسم: {e}")
        return None


def detect_url_type(url: str) -> Dict[str, Any]:
    """اكتشاف نوع الرابط وتحديد المصدر المناسب"""
    url_lower = url.lower()
    
    # Google Maps
    if "google.com/maps" in url_lower or "maps.google" in url_lower or "goo.gl/maps" in url_lower:
        return {"type": "google_maps", "url": url}
    
    # Instagram
    if "instagram.com" in url_lower:
        username = extract_instagram_username(url)
        return {"type": "instagram", "username": username, "url": url}
    
    # TikTok
    if "tiktok.com" in url_lower:
        username = extract_tiktok_username(url)
        return {"type": "tiktok", "username": username, "url": url}
    
    # Twitter/X
    if "twitter.com" in url_lower or "x.com" in url_lower:
        username = extract_twitter_username(url)
        return {"type": "twitter", "username": username, "url": url}
    
    # Snapchat
    if "snapchat.com" in url_lower:
        username = extract_snapchat_username(url)
        return {"type": "snapchat", "username": username, "url": url}
    
    # YouTube
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        channel = extract_youtube_channel(url)
        return {"type": "youtube", "channel": channel, "url": url}
    
    # موقع عادي
    return {"type": "website", "url": url}


def extract_instagram_username(url: str) -> Optional[str]:
    """استخراج اسم المستخدم من رابط Instagram"""
    patterns = [
        r"instagram\.com/([^/?]+)",
        r"instagr\.am/([^/?]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            username = match.group(1)
            if username not in ["p", "reel", "stories", "explore"]:
                return username
    return None


def extract_tiktok_username(url: str) -> Optional[str]:
    """استخراج اسم المستخدم من رابط TikTok"""
    pattern = r"tiktok\.com/@([^/?]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def extract_twitter_username(url: str) -> Optional[str]:
    """استخراج اسم المستخدم من رابط Twitter/X"""
    patterns = [
        r"twitter\.com/([^/?]+)",
        r"x\.com/([^/?]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            username = match.group(1)
            if username not in ["home", "explore", "search", "settings"]:
                return username
    return None


def extract_snapchat_username(url: str) -> Optional[str]:
    """استخراج اسم المستخدم من رابط Snapchat"""
    pattern = r"snapchat\.com/add/([^/?]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def extract_youtube_channel(url: str) -> Optional[str]:
    """استخراج قناة YouTube"""
    patterns = [
        r"youtube\.com/channel/([^/?]+)",
        r"youtube\.com/c/([^/?]+)",
        r"youtube\.com/@([^/?]+)",
        r"youtube\.com/user/([^/?]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


# ===================== Google Maps Scraper مع Reviews =====================

def fetch_google_maps_with_reviews(url_or_query: str, is_url: bool = False) -> Optional[Dict[str, Any]]:
    """جلب بيانات Google Maps مع المراجعات التفصيلية"""
    if not APIFY_API_TOKEN:
        print("⚠️ APIFY_API_TOKEN غير موجود")
        return None
    
    actor_id = "compass~crawler-google-places"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_API_TOKEN}"
    
    # إعداد الـ payload
    if is_url:
        payload = {
            "startUrls": [{"url": url_or_query}],
            "maxCrawledPlacesPerSearch": 1,
            "scrapeReviewsPersonalData": True,
            "reviewsSort": "newest",
            "reviewsStartDate": "",
            "maxReviews": 50,
            "language": "ar",
        }
    else:
        payload = {
            "searchStringsArray": [url_or_query],
            "maxCrawledPlacesPerSearch": 1,
            "scrapeReviewsPersonalData": True,
            "reviewsSort": "newest",
            "maxReviews": 50,
            "language": "ar",
            "region": "sa",
        }
    
    print(f"🗺️ جاري البحث في Google Maps: {url_or_query}")
    
    try:
        response = requests.post(run_url, json=payload, timeout=30)
        response.raise_for_status()
        run_data = response.json()
        run_id = run_data["data"]["id"]
        print(f"✅ بدأ بحث Maps: {run_id}")
    except Exception as e:
        print(f"⚠️ خطأ في تشغيل Maps: {str(e)}")
        return None
    
    # انتظار الاكتمال
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
    max_wait = 120
    waited = 0
    
    while waited < max_wait:
        try:
            status_resp = requests.get(status_url, timeout=10)
            status_data = status_resp.json()
            status = status_data["data"]["status"]
            
            if status == "SUCCEEDED":
                print("✅ اكتمل بحث Maps")
                break
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                print(f"⚠️ فشل Maps: {status}")
                return None
            
            time.sleep(3)
            waited += 3
            print(f"⏳ انتظار Maps... ({waited}s)")
            
        except Exception as e:
            print(f"⚠️ خطأ: {str(e)}")
            return None
    
    if waited >= max_wait:
        print("⚠️ انتهت المهلة")
        return None
    
    # جلب النتائج
    dataset_id = status_data["data"]["defaultDatasetId"]
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
    
    try:
        dataset_resp = requests.get(dataset_url, timeout=30)
        items = dataset_resp.json()
        
        if not items:
            print("⚠️ لا توجد نتائج")
            return None
        
        place = items[0]
        
        # استخراج المراجعات
        reviews = []
        raw_reviews = place.get("reviews") or []
        for r in raw_reviews[:50]:
            reviews.append({
                "text": r.get("text") or r.get("snippet") or "",
                "rating": r.get("stars") or r.get("rating"),
                "author": r.get("name") or r.get("author"),
                "date": r.get("publishedAtDate") or r.get("date"),
                "likes": r.get("likesCount") or 0,
            })
        
        return {
            "name": place.get("title") or place.get("name"),
            "rating": place.get("totalScore") or place.get("rating"),
            "reviews_count": place.get("reviewsCount"),
            "address": place.get("address"),
            "phone": place.get("phone"),
            "website": place.get("website"),
            "url": place.get("url") or place.get("googleMapsUrl"),
            "category": place.get("categoryName") or place.get("category"),
            "location": place.get("location"),
            "opening_hours": place.get("openingHours"),
            "reviews": reviews,
            "images_count": place.get("imageCount") or len(place.get("imageUrls") or []),
        }
        
    except Exception as e:
        print(f"⚠️ خطأ في جلب النتائج: {str(e)}")
        return None


# ===================== تحليل Sentiment =====================

SENTIMENT_PROMPT = """
أنت محلل متخصص في تحليل مراجعات العملاء للأنشطة التجارية. المطلوب تحليل المراجعات التالية بعمق واستخراج insights حقيقية ومفيدة.

## المطلوب:

1. **تحليل المشاعر** - حلل كل مراجعة وصنّفها:
   - positive_percentage: نسبة الإيجابية
   - neutral_percentage: نسبة المحايدة
   - negative_percentage: نسبة السلبية

2. **المواضيع المذكورة** - استخرج المواضيع الفعلية من النص:
   - مثال: "جودة الطعام"، "سرعة الخدمة"، "نظافة المكان"، "الأسعار"، "الموظفين"، "الموقع"
   - اذكر فقط المواضيع الموجودة فعلاً في المراجعات

3. **نقاط القوة** - ما الذي يمدحه العملاء بالتحديد؟
   - اكتب جمل محددة مثل: "سرعة تقديم الطلبات" وليس "الخدمة جيدة"

4. **نقاط الضعف** - ما الذي ينتقده العملاء بالتحديد؟
   - اكتب جمل محددة مثل: "ارتفاع الأسعار مقارنة بالكمية" وليس "الأسعار"

5. **كلمات مفتاحية** - الكلمات المتكررة في المراجعات

6. **ملخص** - ملخص صادق من 2-3 جمل يعكس الانطباع العام الحقيقي

## تعليمات مهمة:
- اقرأ كل مراجعة بعناية
- لا تخترع معلومات غير موجودة
- كن محدداً ودقيقاً في التحليل
- إذا المراجعات قليلة أو غير واضحة، اذكر ذلك

أرجع JSON فقط:
{
  "sentiment": {
    "positive_percentage": 65,
    "neutral_percentage": 20,
    "negative_percentage": 15
  },
  "topics": [
    {"topic": "جودة الطعام", "percentage": 45},
    {"topic": "الخدمة", "percentage": 30}
  ],
  "strengths": ["نقطة قوة محددة 1", "نقطة قوة محددة 2"],
  "weaknesses": ["نقطة ضعف محددة 1", "نقطة ضعف محددة 2"],
  "keywords": ["كلمة1", "كلمة2"],
  "summary": "ملخص صادق ومحدد..."
}
"""


def analyze_reviews_sentiment(reviews: List[Dict]) -> Optional[Dict[str, Any]]:
    """تحليل المراجعات واستخراج Sentiment والمواضيع"""
    if not reviews:
        return None
    
    # تجميع نصوص المراجعات
    reviews_text = "\n".join([
        f"- تقييم {r.get('rating', '?')}/5: {r.get('text', '')}"
        for r in reviews if r.get('text')
    ])
    
    if not reviews_text.strip():
        return None
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SENTIMENT_PROMPT},
                {"role": "user", "content": f"حلل المراجعات التالية:\n\n{reviews_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"⚠️ خطأ في تحليل Sentiment: {str(e)}")
        return None


# ===================== Prompts للتحليل =====================

WEBSITE_ANALYSIS_PROMPT = """
أنت محلل تسويق رقمي متخصص. ستحصل على بيانات حقيقية عن موقع إلكتروني تشمل:
- معلومات التواصل (إيميلات، أرقام هواتف)
- حسابات السوشال ميديا
- بيانات Google Maps (إن وُجدت)
- تحليل مراجعات العملاء (إن وُجد)

## مهمتك:
قدّم تحليلاً مخصصاً وفريداً بناءً على البيانات الفعلية أمامك.

## قواعد التحليل:
1. **الملخص**: اكتب ملخصاً يذكر اسم النشاط وأرقاماً حقيقية من البيانات
   - مثال جيد: "مطعم شيفز سبون حاصل على تقييم 4.3 من 850 مراجعة، مع تواجد قوي على انستقرام وتيك توك"
   - مثال سيء: "النشاط لديه حضور رقمي جيد ويحتاج تحسينات"

2. **النتيجة**: احسبها بناءً على:
   - وجود إيميل (+10%)
   - وجود هاتف (+10%)
   - كل منصة سوشال موجودة (+10% بحد أقصى 40%)
   - تقييم Google Maps: أقل من 3 (-10%)، 3-4 (+10%)، 4-4.5 (+15%)، فوق 4.5 (+20%)
   - عدد المراجعات: أقل من 50 (+5%)، 50-200 (+10%)، فوق 200 (+15%)

3. **المشاكل**: اذكر مشاكل حقيقية وملموسة من البيانات
   - مثال جيد: "لا يوجد حساب واتساب للتواصل السريع"
   - مثال سيء: "يحتاج تحسين التواجد الرقمي"

4. **التوصيات**: قدّم توصيات عملية ومحددة
   - مثال جيد: "إضافة رقم واتساب للطلبات السريعة خاصة أن 40% من المراجعات تذكر سرعة الخدمة"
   - مثال سيء: "تحسين التواصل مع العملاء"

أرجع JSON فقط:
{
  "analysis_summary_ar": "ملخص مخصص يذكر الاسم والأرقام الفعلية",
  "digital_presence_score": 0.65,
  "issues": ["مشكلة محددة 1", "مشكلة محددة 2"],
  "recommendations_ar": ["توصية عملية محددة 1", "توصية عملية محددة 2"]
}
"""


GOOGLE_BUSINESS_PROMPT = """
أنت محلل متخصص في Google Business Profile. ستحصل على بيانات حقيقية من Google Maps تشمل:
- اسم النشاط والتصنيف
- التقييم وعدد المراجعات
- تحليل sentiment للمراجعات (إن وُجد)

## مهمتك:
قدّم تحليلاً مخصصاً وفريداً يعتمد 100% على البيانات الفعلية أمامك.

## قواعد صارمة:
1. **الملخص** - يجب أن يذكر:
   - اسم النشاط الفعلي
   - التقييم الفعلي (مثال: 4.3/5)
   - عدد المراجعات الفعلي
   - نتيجة تحليل المراجعات إن وُجدت
   - مثال: "مطعم شيفز سبون حاصل على تقييم 4.3 من 850 مراجعة. تحليل المراجعات يُظهر رضا بنسبة 72% مع إشادة خاصة بجودة الطعام، بينما 15% من المراجعات تنتقد أوقات الانتظار."

2. **النتيجة** - احسبها بدقة:
   - تقييم 4.5+ = 0.85-0.95
   - تقييم 4.0-4.4 = 0.70-0.84
   - تقييم 3.5-3.9 = 0.55-0.69
   - تقييم 3.0-3.4 = 0.40-0.54
   - أقل من 3.0 = 0.20-0.39
   - أضف 0.05 لكل 100 مراجعة (بحد أقصى 0.10)

3. **تحليل التقييم** - اكتب تحليلاً مفصلاً يربط:
   - التقييم الرقمي
   - عدد المراجعات
   - نتائج تحليل sentiment (إن وُجدت)
   - المواضيع الأكثر ذكراً

4. **المشاكل** - استخرجها من:
   - نقاط الضعف في تحليل المراجعات
   - المواضيع السلبية المذكورة
   - أي فجوات في البيانات

5. **التوصيات** - اربطها بالمشاكل المحددة:
   - إذا كانت "الخدمة بطيئة" مشكلة، قدّم حلاً محدداً

6. **الموقف التنافسي**:
   - ممتاز: تقييم 4.5+ مع 200+ مراجعة
   - جيد: تقييم 4.0+ مع 100+ مراجعة
   - متوسط: تقييم 3.5+ مع 50+ مراجعة
   - ضعيف: أقل من ذلك

أرجع JSON فقط:
{
  "analysis_summary_ar": "ملخص مخصص بالأرقام الفعلية",
  "digital_presence_score": 0.75,
  "rating_analysis": "تحليل مفصل للتقييم والمراجعات",
  "issues": ["مشكلة محددة من المراجعات 1", "مشكلة محددة 2"],
  "recommendations_ar": ["توصية عملية مرتبطة بالمشكلة 1", "توصية 2"],
  "competitive_position": "جيد"
}
"""


def call_llm_analysis(data: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    """استدعاء LLM للتحليل"""
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False, indent=2)},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"⚠️ خطأ في LLM: {str(e)}")
        return {"error": str(e)}


# ===================== Contact Scraper =====================

def fetch_contacts_from_apify(url: str) -> Dict[str, Any]:
    """استدعاء Apify Contact Info Scraper"""
    if not APIFY_API_TOKEN:
        raise HTTPException(status_code=500, detail="APIFY_API_TOKEN غير موجود")
    
    actor_id = "vdrmota~contact-info-scraper"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_API_TOKEN}"
    
    payload = {
        "startUrls": [{"url": url}],
        "maxRequestsPerStartUrl": 50,
        "maxDepth": 2,
        "sameDomain": True,
    }
    
    print(f"🚀 جاري استدعاء Apify لـ: {url}")
    
    try:
        response = requests.post(run_url, json=payload, timeout=30)
        response.raise_for_status()
        run_data = response.json()
        run_id = run_data["data"]["id"]
        print(f"✅ بدأ التشغيل: {run_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في Apify: {str(e)}")
    
    # انتظار الاكتمال
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
    max_wait = 120
    waited = 0
    
    while waited < max_wait:
        try:
            status_resp = requests.get(status_url, timeout=10)
            status_data = status_resp.json()
            status = status_data["data"]["status"]
            
            if status == "SUCCEEDED":
                break
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                raise HTTPException(status_code=500, detail=f"فشل Apify: {status}")
            
            time.sleep(3)
            waited += 3
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    if waited >= max_wait:
        raise HTTPException(status_code=504, detail="انتهت المهلة")
    
    # جلب النتائج
    dataset_id = status_data["data"]["defaultDatasetId"]
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
    
    try:
        dataset_resp = requests.get(dataset_url, timeout=30)
        items = dataset_resp.json()
        
        if not items:
            raise HTTPException(status_code=404, detail="لم يتم العثور على بيانات")
        
        item = items[0]
        domain = item.get("domain") or ""
        
        return {
            "source_url": url,
            "normalized_domain": domain,
            "emails": [{"email": e, "source": "website"} for e in (item.get("emails") or [])],
            "phones": [{"phone": p, "source": "website"} for p in (item.get("phones") or [])],
            "socials": {
                "instagram": item.get("instagrams") or [],
                "tiktok": item.get("tiktoks") or [],
                "snapchat": item.get("snapchats") or [],
                "x_twitter": item.get("twitters") or [],
                "facebook": item.get("facebooks") or [],
                "linkedin": item.get("linkedIns") or [],
                "youtube": item.get("youtubes") or [],
                "whatsapp": item.get("whatsapps") or [],
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_contacts_from_local(url: str) -> Optional[Dict[str, Any]]:
    """البحث في الملف المحلي"""
    normalized_path = Path("normalized_output.json")
    if not normalized_path.exists():
        return None
    
    try:
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        
        with normalized_path.open("r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print("⚠️ ملف normalized_output.json فارغ")
                return None
            items = json.loads(content)
        
        for item in items:
            if item.get("normalized_domain") == domain:
                print(f"✅ وُجد محلياً: {domain}")
                return item
        
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️ خطأ في قراءة JSON: {e}")
        return None
    except Exception as e:
        print(f"⚠️ خطأ: {e}")
        return None


# ===================== API Endpoints =====================

class AnalyzeRequest(BaseModel):
    url: str


@app.post("/analyze-url")
def analyze_url(req: AnalyzeRequest):
    """تحليل أي رابط - موقع أو Google Maps أو سوشال ميديا"""
    
    url = req.url.strip()
    url_info = detect_url_type(url)
    
    print(f"🔍 نوع الرابط: {url_info['type']}")
    
    # =============== Google Maps ===============
    if url_info["type"] == "google_maps":
        print("📍 معالجة رابط Google Maps...")
        
        # جلب البيانات مع المراجعات
        maps_data = fetch_google_maps_with_reviews(url, is_url=True)
        
        if not maps_data:
            raise HTTPException(status_code=404, detail="لم يتم العثور على بيانات")
        
        # تحليل المراجعات
        reviews_analysis = None
        if maps_data.get("reviews"):
            reviews_analysis = analyze_reviews_sentiment(maps_data["reviews"])
        
        # تحليل شامل
        analysis_data = {
            "name": maps_data.get("name"),
            "rating": maps_data.get("rating"),
            "reviews_count": maps_data.get("reviews_count"),
            "category": maps_data.get("category"),
            "reviews_analysis": reviews_analysis,
        }
        
        analysis = call_llm_analysis(analysis_data, GOOGLE_BUSINESS_PROMPT)
        
        return {
            "type": "google_business",
            "business": maps_data,
            "reviews_analysis": reviews_analysis,
            "analysis": analysis,
        }
    
    # =============== Website ===============
    elif url_info["type"] == "website":
        print("🌐 معالجة موقع...")
        
        # استخراج الدومين أولاً
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        clean_domain = domain.replace("www.", "")
        
        # جلب بيانات الاتصال
        contacts = get_contacts_from_local(url)
        if not contacts:
            try:
                contacts = fetch_contacts_from_apify(url)
            except HTTPException as e:
                # إذا فشل Apify، نكمل بدون بيانات الاتصال
                print(f"⚠️ فشل جلب بيانات الاتصال: {e.detail}")
                contacts = {
                    "source_url": url,
                    "normalized_domain": clean_domain,
                    "emails": [],
                    "phones": [],
                    "socials": {}
                }
        
        # جلب بيانات Google Maps - استخدام اسم النشاط من الرابط أو الدومين
        business_name_from_url = extract_business_name_from_url(url)
        
        if business_name_from_url:
            # إذا الاسم قصير أو عام، نضيف السعودية
            if len(business_name_from_url) <= 10:
                search_query = f"{business_name_from_url} السعودية"
            else:
                search_query = business_name_from_url
        else:
            # استخدام اسم الدومين
            domain_name = clean_domain.replace(".com", "").replace(".sa", "").replace(".net", "").replace(".org", "").replace(".site", "")
            search_query = f"{domain_name} السعودية"
        
        print(f"🗺️ البحث في Maps عن: {search_query}")
        maps_data = fetch_google_maps_with_reviews(search_query)
        
        # تحليل المراجعات
        reviews_analysis = None
        if maps_data and maps_data.get("reviews"):
            reviews_analysis = analyze_reviews_sentiment(maps_data["reviews"])
        
        # =============== جلب بيانات السوشال ميديا ===============
        social_profiles = {}
        socials = contacts.get("socials", {})
        
        # Instagram
        instagram_links = socials.get("instagram", [])
        if instagram_links:
            ig_username = extract_instagram_username(instagram_links[0])
            if ig_username:
                print(f"📸 جلب بيانات Instagram: @{ig_username}")
                ig_data = fetch_instagram_profile(ig_username)
                if ig_data:
                    social_profiles["instagram"] = ig_data
        
        # Twitter
        twitter_links = socials.get("x_twitter", [])
        if twitter_links:
            tw_username = extract_twitter_username(twitter_links[0])
            if tw_username:
                print(f"🐦 جلب بيانات Twitter: @{tw_username}")
                tw_data = fetch_twitter_profile(tw_username)
                if tw_data:
                    social_profiles["twitter"] = tw_data
        
        # =============== تحليل شامل ===============
        analysis_data = {
            **contacts,
            "google_maps": maps_data,
            "reviews_analysis": reviews_analysis,
            "social_profiles": social_profiles,
        }
        
        analysis = call_llm_analysis(analysis_data, WEBSITE_ANALYSIS_PROMPT)
        
        return {
            "type": "website",
            "contacts": contacts,
            "google_maps": maps_data,
            "reviews_analysis": reviews_analysis,
            "social_profiles": social_profiles,
            "analysis": analysis,
        }
    
    # =============== Instagram ===============
    elif url_info["type"] == "instagram":
        username = url_info.get("username")
        if not username:
            raise HTTPException(status_code=400, detail="لم يتم العثور على اسم المستخدم")
        
        print(f"📸 تحليل Instagram: @{username}")
        profile_data = fetch_instagram_profile(username)
        
        if not profile_data:
            raise HTTPException(status_code=404, detail=f"لم يتم العثور على حساب @{username}")
        
        analysis = call_llm_analysis(profile_data, SOCIAL_MEDIA_PROMPT)
        
        return {
            "type": "instagram",
            "profile": profile_data,
            "analysis": analysis,
        }
    
    # =============== Twitter/X ===============
    elif url_info["type"] == "twitter":
        username = url_info.get("username")
        if not username:
            raise HTTPException(status_code=400, detail="لم يتم العثور على اسم المستخدم")
        
        print(f"🐦 تحليل Twitter: @{username}")
        profile_data = fetch_twitter_profile(username)
        
        if not profile_data:
            raise HTTPException(status_code=404, detail=f"لم يتم العثور على حساب @{username}")
        
        analysis = call_llm_analysis(profile_data, SOCIAL_MEDIA_PROMPT)
        
        return {
            "type": "twitter",
            "profile": profile_data,
            "analysis": analysis,
        }
    
    # =============== Other Social Media (للمستقبل) ===============
    else:
        return {
            "type": url_info["type"],
            "message": f"تحليل {url_info['type']} سيتم إضافته قريباً",
            "detected": url_info,
        }


@app.post("/analyze-business")
def analyze_business(req: AnalyzeRequest):
    """تحليل نشاط تجاري بالاسم"""
    
    input_text = req.url.strip()
    
    # إذا كان رابط، نستخرج اسم الدومين
    if input_text.startswith("http"):
        domain = input_text.replace("https://", "").replace("http://", "").split("/")[0]
        search_query = domain.replace("www.", "").replace(".com", "").replace(".sa", "")
    else:
        search_query = input_text
    
    print(f"🏢 البحث عن: {search_query}")
    
    # البحث في Google Maps
    maps_data = fetch_google_maps_with_reviews(search_query)
    
    if not maps_data:
        raise HTTPException(status_code=404, detail=f"لم يتم العثور على '{search_query}'")
    
    # تحليل المراجعات
    reviews_analysis = None
    if maps_data.get("reviews"):
        reviews_analysis = analyze_reviews_sentiment(maps_data["reviews"])
    
    # تحليل شامل
    analysis = call_llm_analysis({
        "name": maps_data.get("name"),
        "rating": maps_data.get("rating"),
        "reviews_count": maps_data.get("reviews_count"),
        "category": maps_data.get("category"),
        "reviews_analysis": reviews_analysis,
    }, GOOGLE_BUSINESS_PROMPT)
    
    return {
        "type": "google_business",
        "business": maps_data,
        "reviews_analysis": reviews_analysis,
        "analysis": analysis,
    }


@app.get("/health")
def health():
    return {"status": "ok", "version": "3.0"}


# ===================== Instagram Scraper =====================

def fetch_instagram_profile(username: str) -> Optional[Dict[str, Any]]:
    """جلب بيانات حساب Instagram"""
    if not APIFY_API_TOKEN:
        print("⚠️ APIFY_API_TOKEN غير موجود")
        return None
    
    # تنظيف اسم المستخدم
    username = username.replace("@", "").strip()
    
    actor_id = "apify~instagram-profile-scraper"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_API_TOKEN}"
    
    payload = {
        "usernames": [username],
    }
    
    print(f"📸 جاري جلب بيانات Instagram: @{username}")
    
    try:
        response = requests.post(run_url, json=payload, timeout=30)
        response.raise_for_status()
        run_data = response.json()
        run_id = run_data["data"]["id"]
        print(f"✅ بدأ جلب Instagram: {run_id}")
    except Exception as e:
        print(f"⚠️ خطأ في Instagram: {str(e)}")
        return None
    
    # انتظار الاكتمال
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
    max_wait = 120
    waited = 0
    
    while waited < max_wait:
        try:
            status_resp = requests.get(status_url, timeout=10)
            status_data = status_resp.json()
            status = status_data["data"]["status"]
            
            if status == "SUCCEEDED":
                print("✅ اكتمل جلب Instagram")
                break
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                print(f"⚠️ فشل Instagram: {status}")
                return None
            
            time.sleep(3)
            waited += 3
            print(f"⏳ انتظار Instagram... ({waited}s)")
            
        except Exception as e:
            print(f"⚠️ خطأ: {str(e)}")
            return None
    
    if waited >= max_wait:
        print("⚠️ انتهت المهلة")
        return None
    
    # جلب النتائج
    dataset_id = status_data["data"]["defaultDatasetId"]
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
    
    try:
        dataset_resp = requests.get(dataset_url, timeout=30)
        items = dataset_resp.json()
        
        if not items:
            print("⚠️ لا توجد نتائج Instagram")
            return None
        
        profile = items[0]
        
        # حساب معدل التفاعل
        followers = profile.get("followersCount") or profile.get("followers") or 0
        posts_count = profile.get("postsCount") or profile.get("posts") or 0
        
        # جلب متوسط اللايكات والتعليقات من آخر المنشورات
        latest_posts = profile.get("latestPosts") or []
        total_likes = 0
        total_comments = 0
        for post in latest_posts[:12]:  # آخر 12 منشور
            total_likes += post.get("likesCount") or post.get("likes") or 0
            total_comments += post.get("commentsCount") or post.get("comments") or 0
        
        avg_engagement = 0
        if followers > 0 and len(latest_posts) > 0:
            avg_interactions = (total_likes + total_comments) / len(latest_posts[:12])
            avg_engagement = round((avg_interactions / followers) * 100, 2)
        
        return {
            "platform": "instagram",
            "username": profile.get("username"),
            "full_name": profile.get("fullName") or profile.get("full_name"),
            "bio": profile.get("biography") or profile.get("bio"),
            "followers": followers,
            "following": profile.get("followingCount") or profile.get("following") or 0,
            "posts_count": posts_count,
            "is_verified": profile.get("verified") or profile.get("isVerified") or False,
            "is_business": profile.get("isBusinessAccount") or False,
            "category": profile.get("businessCategoryName") or profile.get("category"),
            "profile_pic": profile.get("profilePicUrl") or profile.get("profilePicUrlHD"),
            "website": profile.get("externalUrl") or profile.get("website"),
            "engagement_rate": avg_engagement,
            "avg_likes": round(total_likes / max(len(latest_posts[:12]), 1)),
            "avg_comments": round(total_comments / max(len(latest_posts[:12]), 1)),
            "latest_posts": [
                {
                    "type": p.get("type"),
                    "likes": p.get("likesCount") or p.get("likes"),
                    "comments": p.get("commentsCount") or p.get("comments"),
                    "caption": (p.get("caption") or "")[:200],
                    "timestamp": p.get("timestamp"),
                }
                for p in latest_posts[:6]
            ],
        }
        
    except Exception as e:
        print(f"⚠️ خطأ في جلب نتائج Instagram: {str(e)}")
        return None


# ===================== Twitter/X Scraper =====================

def fetch_twitter_profile(username: str) -> Optional[Dict[str, Any]]:
    """جلب بيانات حساب Twitter/X"""
    if not APIFY_API_TOKEN:
        print("⚠️ APIFY_API_TOKEN غير موجود")
        return None
    
    # تنظيف اسم المستخدم
    username = username.replace("@", "").strip()
    
    actor_id = "quacker~twitter-scraper"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_API_TOKEN}"
    
    payload = {
        "getFollowers": False,
        "getFollowing": False,
        "getRetweeters": False,
        "handle": [username],
        "tweetsDesired": 20,
        "profilesDesired": 1,
    }
    
    print(f"🐦 جاري جلب بيانات Twitter: @{username}")
    
    try:
        response = requests.post(run_url, json=payload, timeout=30)
        response.raise_for_status()
        run_data = response.json()
        run_id = run_data["data"]["id"]
        print(f"✅ بدأ جلب Twitter: {run_id}")
    except Exception as e:
        print(f"⚠️ خطأ في Twitter: {str(e)}")
        return None
    
    # انتظار الاكتمال
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
    max_wait = 120
    waited = 0
    
    while waited < max_wait:
        try:
            status_resp = requests.get(status_url, timeout=10)
            status_data = status_resp.json()
            status = status_data["data"]["status"]
            
            if status == "SUCCEEDED":
                print("✅ اكتمل جلب Twitter")
                break
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                print(f"⚠️ فشل Twitter: {status}")
                return None
            
            time.sleep(3)
            waited += 3
            print(f"⏳ انتظار Twitter... ({waited}s)")
            
        except Exception as e:
            print(f"⚠️ خطأ: {str(e)}")
            return None
    
    if waited >= max_wait:
        print("⚠️ انتهت المهلة")
        return None
    
    # جلب النتائج
    dataset_id = status_data["data"]["defaultDatasetId"]
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
    
    try:
        dataset_resp = requests.get(dataset_url, timeout=30)
        items = dataset_resp.json()
        
        if not items:
            print("⚠️ لا توجد نتائج Twitter")
            return None
        
        # البحث عن بيانات الـ profile
        profile = None
        tweets = []
        
        for item in items:
            if item.get("__typename") == "User" or item.get("type") == "user":
                profile = item
            elif item.get("__typename") == "Tweet" or item.get("type") == "tweet":
                tweets.append(item)
        
        if not profile:
            # جرب الطريقة البديلة
            profile = items[0] if items else {}
        
        followers = profile.get("followers_count") or profile.get("followersCount") or profile.get("followers") or 0
        
        # حساب معدل التفاعل
        total_engagement = 0
        for tweet in tweets[:20]:
            likes = tweet.get("favorite_count") or tweet.get("likes") or 0
            retweets = tweet.get("retweet_count") or tweet.get("retweets") or 0
            replies = tweet.get("reply_count") or tweet.get("replies") or 0
            total_engagement += likes + retweets + replies
        
        avg_engagement = 0
        if followers > 0 and len(tweets) > 0:
            avg_interactions = total_engagement / len(tweets[:20])
            avg_engagement = round((avg_interactions / followers) * 100, 2)
        
        return {
            "platform": "twitter",
            "username": profile.get("screen_name") or profile.get("username") or username,
            "full_name": profile.get("name") or profile.get("fullName"),
            "bio": profile.get("description") or profile.get("bio"),
            "followers": followers,
            "following": profile.get("friends_count") or profile.get("followingCount") or profile.get("following") or 0,
            "tweets_count": profile.get("statuses_count") or profile.get("tweetsCount") or 0,
            "is_verified": profile.get("verified") or profile.get("isVerified") or False,
            "profile_pic": profile.get("profile_image_url_https") or profile.get("profileImageUrl"),
            "website": profile.get("url"),
            "location": profile.get("location"),
            "created_at": profile.get("created_at"),
            "engagement_rate": avg_engagement,
            "latest_tweets": [
                {
                    "text": (t.get("full_text") or t.get("text") or "")[:280],
                    "likes": t.get("favorite_count") or t.get("likes") or 0,
                    "retweets": t.get("retweet_count") or t.get("retweets") or 0,
                    "replies": t.get("reply_count") or t.get("replies") or 0,
                    "timestamp": t.get("created_at"),
                }
                for t in tweets[:6]
            ],
        }
        
    except Exception as e:
        print(f"⚠️ خطأ في جلب نتائج Twitter: {str(e)}")
        return None


# ===================== Social Media Analysis Prompt =====================

SOCIAL_MEDIA_PROMPT = """
أنت محلل سوشال ميديا متخصص. ستحصل على بيانات حساب من منصة اجتماعية.

## مهمتك:
تحليل أداء الحساب وتقديم توصيات عملية.

## معايير التقييم:

### Instagram:
- engagement_rate > 3% = ممتاز
- engagement_rate 1-3% = جيد
- engagement_rate < 1% = ضعيف
- followers > 10K = حساب كبير
- followers 1K-10K = حساب متوسط
- followers < 1K = حساب صغير

### Twitter:
- engagement_rate > 1% = ممتاز
- engagement_rate 0.5-1% = جيد
- engagement_rate < 0.5% = ضعيف

## أرجع JSON:
{
  "analysis_summary_ar": "ملخص مخصص يذكر اسم الحساب والأرقام الفعلية والتقييم",
  "digital_presence_score": 0.75,
  "account_health": "ممتاز/جيد/متوسط/ضعيف",
  "strengths": ["نقطة قوة محددة 1", "نقطة قوة محددة 2"],
  "weaknesses": ["نقطة ضعف محددة 1", "نقطة ضعف محددة 2"],
  "recommendations_ar": ["توصية عملية محددة 1", "توصية عملية محددة 2"],
  "content_tips": ["نصيحة محتوى 1", "نصيحة محتوى 2"]
}

## تعليمات:
- اذكر الأرقام الفعلية (المتابعين، التفاعل)
- قارن بمعايير المنصة
- قدم توصيات عملية قابلة للتنفيذ
"""


# ===================== Social Media Endpoints =====================

@app.post("/analyze-social")
def analyze_social(req: AnalyzeRequest):
    """تحليل حساب سوشال ميديا"""
    
    url = req.url.strip()
    url_info = detect_url_type(url)
    
    print(f"📱 تحليل سوشال ميديا: {url_info['type']}")
    
    # =============== Instagram ===============
    if url_info["type"] == "instagram":
        username = url_info.get("username")
        if not username:
            raise HTTPException(status_code=400, detail="لم يتم العثور على اسم المستخدم")
        
        profile_data = fetch_instagram_profile(username)
        
        if not profile_data:
            raise HTTPException(status_code=404, detail=f"لم يتم العثور على حساب @{username}")
        
        # تحليل الحساب
        analysis = call_llm_analysis(profile_data, SOCIAL_MEDIA_PROMPT)
        
        return {
            "type": "instagram",
            "profile": profile_data,
            "analysis": analysis,
        }
    
    # =============== Twitter ===============
    elif url_info["type"] == "twitter":
        username = url_info.get("username")
        if not username:
            raise HTTPException(status_code=400, detail="لم يتم العثور على اسم المستخدم")
        
        profile_data = fetch_twitter_profile(username)
        
        if not profile_data:
            raise HTTPException(status_code=404, detail=f"لم يتم العثور على حساب @{username}")
        
        # تحليل الحساب
        analysis = call_llm_analysis(profile_data, SOCIAL_MEDIA_PROMPT)
        
        return {
            "type": "twitter",
            "profile": profile_data,
            "analysis": analysis,
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"نوع الرابط غير مدعوم: {url_info['type']}")


@app.post("/analyze-multi-social")
def analyze_multi_social(req: AnalyzeRequest):
    """تحليل جميع حسابات السوشال ميديا لموقع"""
    
    url = req.url.strip()
    
    # أولاً نجلب بيانات الاتصال من الموقع
    contacts = get_contacts_from_local(url)
    if not contacts:
        try:
            contacts = fetch_contacts_from_apify(url)
        except:
            raise HTTPException(status_code=404, detail="لم يتم العثور على بيانات الموقع")
    
    socials = contacts.get("socials", {})
    
    results = {
        "source_url": url,
        "platforms": {},
        "summary": {},
    }
    
    total_followers = 0
    platforms_found = 0
    
    # =============== Instagram ===============
    instagram_links = socials.get("instagram", [])
    if instagram_links:
        username = extract_instagram_username(instagram_links[0])
        if username:
            print(f"📸 جاري تحليل Instagram: @{username}")
            ig_data = fetch_instagram_profile(username)
            if ig_data:
                ig_analysis = call_llm_analysis(ig_data, SOCIAL_MEDIA_PROMPT)
                results["platforms"]["instagram"] = {
                    "profile": ig_data,
                    "analysis": ig_analysis,
                }
                total_followers += ig_data.get("followers", 0)
                platforms_found += 1
    
    # =============== Twitter ===============
    twitter_links = socials.get("x_twitter", [])
    if twitter_links:
        username = extract_twitter_username(twitter_links[0])
        if username:
            print(f"🐦 جاري تحليل Twitter: @{username}")
            tw_data = fetch_twitter_profile(username)
            if tw_data:
                tw_analysis = call_llm_analysis(tw_data, SOCIAL_MEDIA_PROMPT)
                results["platforms"]["twitter"] = {
                    "profile": tw_data,
                    "analysis": tw_analysis,
                }
                total_followers += tw_data.get("followers", 0)
                platforms_found += 1
    
    # =============== الملخص ===============
    results["summary"] = {
        "total_followers": total_followers,
        "platforms_analyzed": platforms_found,
        "platforms_found": list(results["platforms"].keys()),
    }
    
    return results