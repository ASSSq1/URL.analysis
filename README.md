<div align="center">

# Digital Analysis

### أداة تحليل الحضور الرقمي للأنشطة التجارية

![Version](https://img.shields.io/badge/version-3.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

</div>

---

## 📋 نظرة عامة

**Digital Analysis** هي أداة متكاملة لتحليل الحضور الرقمي للأنشطة التجارية في السعودية والخليج. تقوم الأداة بجمع وتحليل البيانات من مصادر متعددة وتقديم تقارير شاملة مع توصيات عملية.

### 🎯 المشكلة التي نحلها

أصحاب الأنشطة التجارية لا يعرفون:
- هل حضورهم الرقمي قوي أم ضعيف؟
- ماذا يقول العملاء عنهم؟
- كيف يقارنون بالمنافسين؟
- ما الخطوات العملية لتحسين وضعهم؟

### ✅ الحل

أداة واحدة تجمع كل البيانات وتحللها وتقدم:
- **درجة الحضور الرقمي** (0-100%)
- **تحليل المراجعات** مع Sentiment Analysis
- **بيانات السوشال ميديا** المفصّلة
- **توصيات عملية** مخصصة

---

## 🚀 الميزات

### ✅ الميزات الحالية (v3.0)

| الميزة | الوصف |
|--------|-------|
| 🌐 **تحليل المواقع** | جلب معلومات التواصل وحسابات السوشال ميديا |
| 📍 **Google Business Profile** | التقييم، المراجعات، تحليل Sentiment |
| 📸 **Instagram Analytics** | المتابعين، المنشورات، معدل التفاعل |
| 🐦 **Twitter/X Analytics** | المتابعين، التغريدات، معدل التفاعل |
| 🔍 **اكتشاف تلقائي** | يتعرف على نوع الرابط ويحلله تلقائياً |
| 📊 **تحليل Sentiment** | تصنيف المراجعات (إيجابي/محايد/سلبي) |
| 💡 **توصيات مخصصة** | توصيات عملية بناءً على البيانات الفعلية |

### 🔜 الميزات القادمة

- [ ] 📄 PDF Report Generator
- [ ] 💰 حاسبة الخسارة بالريال
- [ ] 🏆 مقارنة المنافسين
- [ ] 🎵 TikTok Analytics
- [ ] 📺 YouTube Analytics
- [ ] 📧 WhatsApp Bot

---

## 🛠️ التثبيت

### المتطلبات

- Python 3.10+
- حساب OpenAI API
- حساب Apify

### الخطوات

```bash
# 1. استنساخ المشروع
git clone https://github.com/your-repo/28-digital-analysis.git
cd 28-digital-analysis

# 2. إنشاء بيئة افتراضية
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# أو
.venv\Scripts\activate  # Windows

# 3. تثبيت المتطلبات
pip install fastapi uvicorn python-dotenv openai requests pydantic

# 4. إعداد ملف البيئة
cp .env.example .env
# عدّل الملف وأضف مفاتيح API
```

### ملف `.env`

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
APIFY_API_TOKEN=apify_api_xxxxxxxxxxxxx
```

### Apify Actors المطلوبة

فعّل هذه الـ Actors في حسابك على Apify:

| Actor | الغرض |
|-------|-------|
| `vdrmota/contact-info-scraper` | جلب معلومات التواصل |
| `compass/crawler-google-places` | Google Maps + Reviews |
| `apify/instagram-profile-scraper` | بيانات Instagram |
| `quacker/twitter-scraper` | بيانات Twitter |

---

## ▶️ التشغيل

```bash
# تشغيل السيرفر
uvicorn api:app --reload

# السيرفر يعمل على
# http://127.0.0.1:8000
```

افتح `index.html` في المتصفح للواجهة.

---

## 📖 API Documentation

### Base URL
```
http://127.0.0.1:8000
```

### Endpoints

#### 1. تحليل رابط
```http
POST /analyze-url
Content-Type: application/json

{
  "url": "https://www.example.com"
}
```

**الروابط المدعومة:**
- مواقع عادية: `https://jarir.com`
- Google Maps: `https://google.com/maps/place/...`
- Instagram: `https://instagram.com/username`
- Twitter: `https://twitter.com/username`

**Response للموقع:**
```json
{
  "type": "website",
  "contacts": {
    "normalized_domain": "example.com",
    "emails": [{"email": "info@example.com"}],
    "phones": [{"phone": "+966xxxxxxxx"}],
    "socials": {
      "instagram": ["https://instagram.com/example"],
      "twitter": ["https://twitter.com/example"]
    }
  },
  "google_maps": {
    "name": "اسم النشاط",
    "rating": 4.5,
    "reviews_count": 150,
    "reviews": [...]
  },
  "reviews_analysis": {
    "sentiment": {
      "positive_percentage": 75,
      "neutral_percentage": 15,
      "negative_percentage": 10
    },
    "topics": [...],
    "strengths": [...],
    "weaknesses": [...]
  },
  "social_profiles": {
    "instagram": {
      "followers": 15000,
      "posts_count": 234,
      "engagement_rate": 2.5
    }
  },
  "analysis": {
    "analysis_summary_ar": "ملخص التحليل...",
    "digital_presence_score": 0.72,
    "issues": ["مشكلة 1", "مشكلة 2"],
    "recommendations_ar": ["توصية 1", "توصية 2"]
  }
}
```

#### 2. تحليل نشاط تجاري بالاسم
```http
POST /analyze-business
Content-Type: application/json

{
  "url": "مكتبة جرير الرياض"
}
```

#### 3. فحص صحة السيرفر
```http
GET /health
```

---

## 🏗️ البنية التقنية

```
28-digital-analysis/
├── api.py              # FastAPI Backend
├── index.html          # Frontend (HTML + CSS + JS)
├── .env                # Environment Variables
├── .env.example        # Example Environment File
├── README.md           # Documentation
├── normalized_output.json  # Local Cache (optional)
└── requirements.txt    # Python Dependencies
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI + Python |
| **Frontend** | HTML + CSS + Vanilla JS |
| **AI/LLM** | OpenAI GPT-4 |
| **Data Scraping** | Apify Actors |
| **Styling** | Custom CSS (Navy + White Theme) |
| **Font** | IBM Plex Sans Arabic |

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│   FastAPI   │────▶│   Apify     │
│   Input     │     │   Backend   │     │   Actors    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   OpenAI    │
                   │   GPT-4     │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Analysis  │
                   │   Results   │
                   └─────────────┘
```

---

## 📊 معايير التقييم

### Digital Presence Score

| النطاق | التصنيف |
|--------|---------|
| 80-100% | ممتاز |
| 60-79% | جيد |
| 40-59% | متوسط |
| 0-39% | يحتاج تحسين |

### Instagram Engagement Rate

| النسبة | التصنيف |
|--------|---------|
| > 3% | ممتاز |
| 1-3% | جيد |
| < 1% | ضعيف |

### Twitter Engagement Rate

| النسبة | التصنيف |
|--------|---------|
| > 1% | ممتاز |
| 0.5-1% | جيد |
| < 0.5% | ضعيف |

---

## 🐛 المشاكل المعروفة

1. **بعض الروابط** قد لا يُستخرج منها اسم النشاط بشكل صحيح
2. **Apify Rate Limits** قد تؤثر على السرعة
3. **بعض حسابات Instagram/Twitter** الخاصة لا يمكن جلب بياناتها

---

## 🤝 المساهمة

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 الرخصة

MIT License - انظر ملف [LICENSE](LICENSE) للتفاصيل.

---


<div align="center">



</div>
