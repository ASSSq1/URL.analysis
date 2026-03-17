# Changelog

جميع التغييرات الملحوظة في هذا المشروع موثقة في هذا الملف.

---

## [3.0.0] - 2026-03-18

### ✨ Added
- **Instagram Analytics**: جلب بيانات حسابات Instagram (متابعين، منشورات، معدل التفاعل)
- **Twitter/X Analytics**: جلب بيانات حسابات Twitter (متابعين، تغريدات، معدل التفاعل)
- **Auto Social Fetch**: جلب بيانات السوشال تلقائياً عند تحليل موقع
- **Social Stats Cards**: بطاقات عرض إحصائيات السوشال ميديا
- **Engagement Rate Calculator**: حساب معدل التفاعل لكل منصة
- **New Endpoints**: `/analyze-social`, `/analyze-multi-social`

### 🔧 Changed
- تحسين Prompts لتكون أكثر تخصيصاً وتذكر الأرقام الفعلية
- تحسين واجهة المستخدم لعرض بيانات السوشال

---

## [2.0.0] - 2026-03-17

### ✨ Added
- **Google Business Profile**: تكامل كامل مع Google Maps
- **Reviews Scraping**: جلب المراجعات التفصيلية
- **Sentiment Analysis**: تحليل مشاعر المراجعات (إيجابي/محايد/سلبي)
- **Topic Extraction**: استخراج المواضيع الأكثر ذكراً
- **Strengths & Weaknesses**: نقاط القوة والضعف من المراجعات
- **URL Type Detection**: اكتشاف تلقائي لنوع الرابط

### 🔧 Changed
- تحسين استخراج اسم النشاط من الروابط
- إضافة قائمة الكلمات المستثناة (ar, en, home, etc.)
- تحسين البحث في Google Maps بإضافة "السعودية"

### 🐛 Fixed
- إصلاح مشكلة `JSONDecodeError` عند الملف المحلي فارغ
- إصلاح مشكلة البحث الخاطئ في Maps

---

## [1.0.0] - 2026-03-16

### ✨ Added
- **Initial Release**
- **Contact Scraper**: جلب معلومات التواصل من المواقع
- **Social Links**: استخراج روابط السوشال ميديا
- **Basic Analysis**: تحليل أساسي للحضور الرقمي
- **Modern UI**: واجهة عصرية بتصميم Navy + White
- **Arabic Support**: دعم كامل للغة العربية

---

## الإصدارات القادمة

### [4.0.0] - Planned
- [ ] PDF Report Generator
- [ ] Revenue Loss Calculator (بالريال)
- [ ] Competitor Analysis
- [ ] TikTok Analytics
- [ ] YouTube Analytics

### [5.0.0] - Future
- [ ] WhatsApp Bot Integration
- [ ] Weekly Monitoring & Alerts
- [ ] White-Label Reports
- [ ] Multi-language Support