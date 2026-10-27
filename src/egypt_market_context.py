"""Egypt-focused market context for the synthetic PixelFed source replica.

This layer creates fictional account and content records around public, aggregate
Egyptian reference data. It does not import real people, social accounts, emails,
device identifiers, or private activity. Population counts are geography weights,
not estimates of social-platform adoption by governorate.
"""

from __future__ import annotations

import json
import random
import re
from typing import Any

# CAPMAS, Population Estimates by Governorate (Urban/Rural), 2024-01-01.
# Population totals are the corresponding CAPMAS 2024 estimates by governorate.
# Urban shares are rounded published percentages. See docs/modeling/egypt-market-context.md.
GOVERNORATES: tuple[dict[str, Any], ...] = (
    {"en": "Cairo", "ar": "القاهرة", "slug": "cairo", "capital": "Cairo", "population": 10299821, "urban_pct": 100.0, "lat": 30.0444, "lon": 31.2357, "region": "Greater Cairo"},
    {"en": "Alexandria", "ar": "الإسكندرية", "slug": "alexandria", "capital": "Alexandria", "population": 5573808, "urban_pct": 98.0, "lat": 31.2001, "lon": 29.9187, "region": "Alexandria and Mediterranean coast"},
    {"en": "Port Said", "ar": "بورسعيد", "slug": "port-said", "capital": "Port Said", "population": 793976, "urban_pct": 100.0, "lat": 31.2653, "lon": 32.3019, "region": "Canal"},
    {"en": "Suez", "ar": "السويس", "slug": "suez", "capital": "Suez", "population": 797045, "urban_pct": 100.0, "lat": 29.9668, "lon": 32.5498, "region": "Canal"},
    {"en": "Damietta", "ar": "دمياط", "slug": "damietta", "capital": "Damietta", "population": 1626063, "urban_pct": 40.5, "lat": 31.4175, "lon": 31.8144, "region": "Nile Delta"},
    {"en": "Dakahlia", "ar": "الدقهلية", "slug": "dakahlia", "capital": "Mansoura", "population": 7086788, "urban_pct": 30.2, "lat": 31.0409, "lon": 31.3785, "region": "Nile Delta"},
    {"en": "Sharqia", "ar": "الشرقية", "slug": "sharqia", "capital": "Zagazig", "population": 7961136, "urban_pct": 26.8, "lat": 30.5877, "lon": 31.5020, "region": "Nile Delta"},
    {"en": "Qalyubia", "ar": "القليوبية", "slug": "qalyubia", "capital": "Banha", "population": 6175627, "urban_pct": 43.1, "lat": 30.4667, "lon": 31.1833, "region": "Greater Cairo"},
    {"en": "Kafr El-Sheikh", "ar": "كفر الشيخ", "slug": "kafr-el-sheikh", "capital": "Kafr El-Sheikh", "population": 3740624, "urban_pct": 24.2, "lat": 31.1107, "lon": 30.9388, "region": "Nile Delta"},
    {"en": "Gharbia", "ar": "الغربية", "slug": "gharbia", "capital": "Tanta", "population": 5468353, "urban_pct": 30.6, "lat": 30.7865, "lon": 31.0004, "region": "Nile Delta"},
    {"en": "Menoufia", "ar": "المنوفية", "slug": "menoufia", "capital": "Shibin El-Kom", "population": 4767510, "urban_pct": 21.9, "lat": 30.5526, "lon": 31.0090, "region": "Nile Delta"},
    {"en": "Beheira", "ar": "البحيرة", "slug": "beheira", "capital": "Damanhur", "population": 6927724, "urban_pct": 20.7, "lat": 31.0341, "lon": 30.4682, "region": "Nile Delta"},
    {"en": "Ismailia", "ar": "الإسماعيلية", "slug": "ismailia", "capital": "Ismailia", "population": 1464224, "urban_pct": 47.0, "lat": 30.5965, "lon": 32.2715, "region": "Canal"},
    {"en": "Giza", "ar": "الجيزة", "slug": "giza", "capital": "Giza", "population": 9578680, "urban_pct": 59.6, "lat": 30.0131, "lon": 31.2089, "region": "Greater Cairo"},
    {"en": "Beni Suef", "ar": "بني سويف", "slug": "beni-suef", "capital": "Beni Suef", "population": 3624142, "urban_pct": 25.4, "lat": 29.0661, "lon": 31.0994, "region": "Upper Egypt"},
    {"en": "Fayoum", "ar": "الفيوم", "slug": "fayoum", "capital": "Fayoum", "population": 4115608, "urban_pct": 22.8, "lat": 29.3084, "lon": 30.8428, "region": "Upper Egypt"},
    {"en": "Minya", "ar": "المنيا", "slug": "minya", "capital": "Minya", "population": 6398400, "urban_pct": 19.1, "lat": 28.1099, "lon": 30.7503, "region": "Upper Egypt"},
    {"en": "Assiut", "ar": "أسيوط", "slug": "assiut", "capital": "Assiut", "population": 5112926, "urban_pct": 27.6, "lat": 27.1809, "lon": 31.1837, "region": "Upper Egypt"},
    {"en": "Sohag", "ar": "سوهاج", "slug": "sohag", "capital": "Sohag", "population": 5783044, "urban_pct": 21.4, "lat": 26.5591, "lon": 31.6957, "region": "Upper Egypt"},
    {"en": "Qena", "ar": "قنا", "slug": "qena", "capital": "Qena", "population": 3674412, "urban_pct": 18.4, "lat": 26.1551, "lon": 32.7160, "region": "Upper Egypt"},
    {"en": "Aswan", "ar": "أسوان", "slug": "aswan", "capital": "Aswan", "population": 1670122, "urban_pct": 46.1, "lat": 24.0889, "lon": 32.8998, "region": "Upper Egypt"},
    {"en": "Luxor", "ar": "الأقصر", "slug": "luxor", "capital": "Luxor", "population": 1412746, "urban_pct": 42.8, "lat": 25.6872, "lon": 32.6396, "region": "Upper Egypt"},
    {"en": "Red Sea", "ar": "البحر الأحمر", "slug": "red-sea", "capital": "Hurghada", "population": 406195, "urban_pct": 96.9, "lat": 27.2579, "lon": 33.8116, "region": "Red Sea and frontier"},
    {"en": "New Valley", "ar": "الوادي الجديد", "slug": "new-valley", "capital": "Kharga", "population": 268834, "urban_pct": 50.8, "lat": 25.4390, "lon": 30.5586, "region": "Red Sea and frontier"},
    {"en": "Matrouh", "ar": "مطروح", "slug": "matrouh", "capital": "Marsa Matruh", "population": 557193, "urban_pct": 66.1, "lat": 31.3543, "lon": 27.2373, "region": "Alexandria and Mediterranean coast"},
    {"en": "North Sinai", "ar": "شمال سيناء", "slug": "north-sinai", "capital": "Arish", "population": 512110, "urban_pct": 61.0, "lat": 31.1316, "lon": 33.7984, "region": "Sinai"},
    {"en": "South Sinai", "ar": "جنوب سيناء", "slug": "south-sinai", "capital": "El Tor", "population": 117388, "urban_pct": 56.2, "lat": 28.2417, "lon": 33.6222, "region": "Sinai"},
)

# Additional named places in the relevant governorate. Coordinates are left NULL when
# this curated starter catalogue does not have a verified representative point.
EXTRA_PLACES: tuple[tuple[str, str], ...] = (
    ("New Cairo", "Cairo"), ("Maadi", "Cairo"), ("Zamalek", "Cairo"), ("Heliopolis", "Cairo"),
    ("Nasr City", "Cairo"), ("Downtown Cairo", "Cairo"), ("Garden City", "Cairo"),
    ("Abbassia", "Cairo"), ("Shubra", "Cairo"), ("Ain Shams", "Cairo"), ("Mokattam", "Cairo"),
    ("Old Cairo", "Cairo"), ("Korba", "Cairo"), ("Fifth Settlement", "Cairo"), ("Roxy", "Cairo"),
    ("Fustat", "Cairo"), ("Dokki", "Giza"), ("Mohandessin", "Giza"), ("Haram", "Giza"),
    ("Faisal", "Giza"), ("6th of October City", "Giza"), ("Sheikh Zayed City", "Giza"),
    ("Imbaba", "Giza"), ("Boulak El-Dakrour", "Giza"), ("Montaza", "Alexandria"),
    ("Sidi Gaber", "Alexandria"), ("Raml Station", "Alexandria"), ("Stanley", "Alexandria"),
    ("Miami", "Alexandria"), ("Agami", "Alexandria"), ("Abu Qir", "Alexandria"),
    ("Borg El Arab", "Alexandria"), ("New Damietta", "Damietta"), ("Ras El Bar", "Damietta"),
    ("Faraskur", "Damietta"), ("Ezbet El-Borg", "Damietta"), ("Port Fouad", "Port Said"),
    ("Mit Ghamr", "Dakahlia"), ("10th of Ramadan City", "Sharqia"),
    ("Shubra El-Kheima", "Qalyubia"), ("Desouk", "Kafr El-Sheikh"),
    ("El Mahalla El-Kubra", "Gharbia"), ("Ashmoun", "Menoufia"), ("Kafr El-Dawwar", "Beheira"),
    ("Fayed", "Ismailia"), ("Ain Sokhna", "Suez"), ("Nasser", "Beni Suef"),
    ("Tunis Village", "Fayoum"), ("Mallawi", "Minya"), ("Dairut", "Assiut"),
    ("Akhmim", "Sohag"), ("Nag Hammadi", "Qena"), ("Abu Simbel", "Aswan"),
    ("Karnak", "Luxor"), ("Hurghada Marina", "Red Sea"), ("Marsa Alam", "Red Sea"),
    ("Dakhla Oasis", "New Valley"), ("Siwa Oasis", "Matrouh"), ("Sallum", "Matrouh"),
    ("Arish Coast", "North Sinai"), ("Sharm El-Sheikh", "South Sinai"), ("Dahab", "South Sinai"),
    ("Nuweiba", "South Sinai"), ("Saint Catherine", "South Sinai"), ("Kom Ombo", "Aswan"),
    ("Edfu", "Aswan"), ("Esna", "Luxor"), ("Armant", "Luxor"), ("Deshna", "Qena"),
    ("Abu Tig", "Assiut"), ("Talakh", "Dakahlia"), ("Kafr Saad", "Damietta"),
    ("New Salhia", "Sharqia"),
)

TOPICS: tuple[dict[str, Any], ...] = (
    {"en": "Egyptian food and cafés", "ar": "الأكل المصري والمقاهي", "tag_ar": "أكل_مصري", "tag_en": "egyptianfood", "slug": "egyptianfood", "bio_ar": "بشارك صور الأكل والتفاصيل اليومية من أماكن مصرية.", "bio_en": "Sharing food photography and everyday café finds in Egypt.", "captions_ar": ("لقطة من {place} النهارده، وتفاصيل الأكل كانت تستاهل الصورة.", "من السوق للمطبخ، حكايات صغيرة من يوم عادي.", "صورة لكل اللي بيحبوا الأكل البلدي والتفاصيل البسيطة.", "ريحة الخبز والقهوة في الصبح ليها حكاية تانية."), "captions_en": ("A small food diary from {place}, inspired by everyday Egyptian kitchens.", "Local flavours, familiar streets, and the details behind a good meal.", "A café stop in {place} turned into today's photo story.", "Food photography is my way to remember the everyday places.")},
    {"en": "Street and architecture photography", "ar": "تصوير الشارع والعمارة", "tag_ar": "تصوير_شارع", "tag_en": "streetphotographyegypt", "slug": "streetphotoegypt", "bio_ar": "مهتمة/مهتم بتفاصيل الشوارع والعمارة والحياة اليومية.", "bio_en": "Documenting street life, architecture, and small details around Egypt.", "captions_ar": ("تفاصيل صغيرة في شارع {place} ممكن تعدّي من غير ما ناخد بالنا.", "النور والظل في الشارع النهارده كانوا أحلى من أي تعديل.", "من مشوار عادي في {place} طلعت بالصورة دي.", "بحاول أوثّق شكل المدينة وهي عايشة يومها الطبيعي."), "captions_en": ("Everyday street details from {place}, photographed without staging the scene.", "The light in this Egyptian street did most of the work today.", "A regular walk through {place} became a small photo story.", "Architecture, shade, and ordinary city life in one frame.")},
    {"en": "Crafts and handmade work", "ar": "الحرف والشغل اليدوي", "tag_ar": "شغل_يدوي", "tag_en": "egyptiancrafts", "slug": "egyptiancrafts", "bio_ar": "بوثّق الشغل اليدوي والحرف والتفاصيل اللي ورا كل قطعة.", "bio_en": "Sharing handmade work, workshop details, and local craft stories.", "captions_ar": ("تفاصيل من الشغل اليدوي في الورشة النهارده.", "كل قطعة وراها وقت ومجهود وتفاصيل صغيرة.", "من دمياط، لقطة للتفاصيل اللي بتفرق في الشغل.", "لسه في مراحل شغل كتير قبل ما القطعة تخلص."), "captions_en": ("A behind-the-scenes look at handmade work in an Egyptian workshop.", "Small details, patient work, and a finished piece taking shape.", "Sharing the process behind local craft, not just the final result.", "A workshop day in {place}, one step at a time.")},
    {"en": "Local business and creative studios", "ar": "المشروعات المحلية والاستوديوهات", "tag_ar": "مشروعات_محلية", "tag_en": "egyptiansmallbusiness", "slug": "egyptsmallbusiness", "bio_ar": "بشارك كواليس الشغل والتصوير للمشروعات المحلية.", "bio_en": "Visual stories from small businesses, makers, and local creative studios.", "captions_ar": ("من كواليس يوم شغل طويل في {place}.", "وراء كل صورة ترتيب وتجربة ومحاولات كتير.", "تفاصيل بسيطة من مشروع محلي بنحاول نطوره كل يوم.", "النهارده كان يوم تصوير منتجات وتجهيزات جديدة."), "captions_en": ("Behind the scenes of a small creative business in {place}.", "A workday of product photos, small adjustments, and learning by doing.", "Local businesses have stories beyond the final product shot.", "A quick look at today's setup before the next batch.")},
    {"en": "Culture and heritage", "ar": "الثقافة والتراث", "tag_ar": "تراث_مصري", "tag_en": "egyptianheritage", "slug": "egyptianheritage", "bio_ar": "مهتم/ة بالحكايات المحلية والعمارة والتراث المصري.", "bio_en": "Collecting stories about Egyptian places, architecture, and local heritage.", "captions_ar": ("تفصيلة قديمة في {place} ولسه محتفظة بروح المكان.", "كل شارع قديم له حكاية تستاهل تتوثق.", "زيارة سريعة خلتني أبص للمكان بشكل مختلف.", "بحب أصوّر التفاصيل اللي بتربطنا بذاكرة المكان."), "captions_en": ("A heritage detail in {place} that still carries the character of the place.", "Old streets hold layers of stories worth documenting carefully.", "A short visit to an Egyptian landmark turned into a photo note.", "Keeping a visual record of local architecture and everyday history.")},
    {"en": "Nature, river, and coast", "ar": "الطبيعة والنيل والساحل", "tag_ar": "طبيعة_مصر", "tag_en": "egyptnature", "slug": "egyptnature", "bio_ar": "صور للطبيعة والنيل والساحل واللحظات الهادية.", "bio_en": "Photographing the Nile, coastlines, gardens, and quiet outdoor moments.", "captions_ar": ("الهوا على الكورنيش النهارده كان محتاج صورة.", "من مشوار هادي جنب النيل قبل ما الدنيا تزحم.", "ألوان السما فوق {place} مختلفة كل مرة.", "لقطة بسيطة من يوم على البحر من غير تجهيزات."), "captions_en": ("A quiet moment by the Nile, photographed on an ordinary day.", "Coastal light around {place} changes more than I expected.", "A simple outdoor frame from Egypt, with no heavy editing.", "A short walk, a little breeze, and a view worth remembering.")},
    {"en": "Art, illustration, and design", "ar": "الفن والرسم والتصميم", "tag_ar": "فن_وتصميم", "tag_en": "egyptianartists", "slug": "egyptianartists", "bio_ar": "مساحة للتجارب الفنية والرسم والألوان والتصميم.", "bio_en": "Exploring illustration, colour, visual design, and creative process.", "captions_ar": ("تجربة ألوان جديدة من الاسكتش لحد النسخة دي.", "لسه شغال/ة على التفاصيل، وأي ملاحظات مرحب بيها.", "الفكرة بدأت برسمة صغيرة وكبرت واحدة واحدة.", "بحاول أخلي التصميم بسيط وواضح من غير زحمة."), "captions_en": ("A work in progress from the sketchbook, with a new colour direction.", "The idea started small and changed through a few iterations.", "Testing a simpler composition before calling this version finished.", "A little design experiment from today's studio time.")},
    {"en": "Learning and technology", "ar": "التعلم والتكنولوجيا", "tag_ar": "تعلم_وتكنولوجيا", "tag_en": "egypttechcommunity", "slug": "egypttech", "bio_ar": "بشارك ملاحظات عن التعلم والتكنولوجيا والشغل الإبداعي.", "bio_en": "Sharing learning notes, creative technology, and open-web projects.", "captions_ar": ("ملاحظة صغيرة من اللي اتعلمته النهارده وحبيت أوثقها.", "تجربة جديدة، والنتيجة محتاجة شوية تحسين كمان.", "بحاول أشرح الفكرة من خلال مثال عملي بدل الكلام النظري.", "خطوة صغيرة في مشروع أكبر، بس التقدم هو المهم."), "captions_en": ("A practical learning note from today's project work.", "Trying a new approach and documenting what worked and what did not.", "A small step in a longer project, shared for anyone learning too.", "A short technical experiment with room for another iteration.")},
    {"en": "Travel and local discoveries", "ar": "الرحلات واكتشاف الأماكن", "tag_ar": "اكتشاف_أماكن", "tag_en": "discoveregypt", "slug": "discoveregypt", "bio_ar": "ملاحظات وصور من رحلات قصيرة وأماكن محلية.", "bio_en": "Photo notes from day trips, local discoveries, and less familiar places.", "captions_ar": ("زيارة سريعة لـ{place} وطلعت منها بالصور دي.", "مش لازم الرحلة تكون بعيدة عشان نكتشف حاجة جديدة.", "مكان جديد في القائمة، ووقت كفاية للتمشية والتصوير.", "تفاصيل من الطريق كانت أحلى من الخطة نفسها."), "captions_en": ("A short visit to {place} turned into a handful of photo notes.", "You do not have to travel far to notice something new.", "A local discovery, with time to walk around and take a few frames.", "Some of the best details were between the planned stops.")},
)

AR_FIRST = (("مريم", "Mariam"), ("نور", "Nour"), ("أحمد", "Ahmed"), ("محمد", "Mohamed"), ("يوسف", "Youssef"), ("عمر", "Omar"), ("سارة", "Sara"), ("محمود", "Mahmoud"), ("آية", "Aya"), ("ملك", "Malak"), ("علي", "Ali"), ("مصطفى", "Mostafa"), ("منة", "Menna"), ("سلمى", "Salma"), ("ياسمين", "Yasmin"), ("فاطمة", "Fatma"), ("عبدالرحمن", "Abdelrahman"), ("كريم", "Karim"), ("دينا", "Dina"), ("ريم", "Reem"), ("هنا", "Hana"), ("ندى", "Nada"), ("زياد", "Ziad"), ("أميرة", "Amira"), ("يحيى", "Yehia"), ("ليلى", "Laila"), ("مروان", "Marwan"), ("عائشة", "Aisha"), ("إسراء", "Esraa"), ("حسن", "Hassan"), ("داليا", "Dalia"), ("رحمة", "Rahma"), ("أسماء", "Asmaa"), ("شريف", "Sherif"), ("إيمان", "Iman"), ("عمرو", "Amr"), ("سيف", "Seif"), ("رنا", "Rana"), ("حبيبة", "Habiba"), ("طارق", "Tarek"))
AR_LAST = (("حسن", "Hassan"), ("السيد", "ElSayed"), ("محمود", "Mahmoud"), ("علي", "Ali"), ("إبراهيم", "Ibrahim"), ("سالم", "Salem"), ("عثمان", "Othman"), ("خليل", "Khalil"), ("مراد", "Mourad"), ("حمدي", "Hamdy"), ("فؤاد", "Fouad"), ("رشاد", "Rashad"), ("سمير", "Samir"), ("مصطفى", "Mostafa"), ("ناجي", "Nagy"), ("سعيد", "Saeed"), ("جمال", "Gamal"), ("عوض", "Awad"), ("الشافعي", "ElShafei"), ("كمال", "Kamal"), ("صبري", "Sabry"), ("زكي", "Zaki"), ("النجار", "ElNaggar"), ("الحداد", "ElHaddad"), ("عادل", "Adel"), ("طه", "Taha"), ("مرسي", "Morsi"), ("فهمي", "Fahmy"), ("الرفاعي", "ElRefai"), ("عبدالله", "Abdallah"), ("حسين", "Hussein"), ("منصور", "Mansour"))

COMMENTS_AR = (
    "الصورة طالعة حلوة جدًا، خصوصًا التفاصيل اللي في الخلفية.",
    "المكان ده له طابع مميز فعلًا.",
    "حبيت الألوان وطريقة التصوير.",
    "التفاصيل الصغيرة هي اللي بتخلي الصورة مختلفة.",
    "المشهد ده فكّرني بمشوار قديم.",
    "مستنيين صور أكتر من المكان ده.",
    "الشغل اليدوي واضح فيه وقت ومجهود.",
    "لقطة بسيطة بس فيها حكاية.",
    "حلو إنك وثّقت التفاصيل دي.",
    "المرة الجاية جرّب التصوير وقت الغروب.",
    "المكان يستاهل زيارة فعلًا.",
    "التكوين والألوان راكبين على بعض بشكل جميل.",
)
COMMENTS_EN = (
    "The details in the background make this frame work.",
    "I like how this captures an ordinary moment.",
    "The colour and composition feel balanced.",
    "This looks like a place worth exploring.",
    "Thanks for sharing a little context with the photo.",
    "The handmade details are easy to appreciate here.",
    "A simple frame with a strong sense of place.",
    "Would love to see more from this series.",
    "The light in this one is especially good.",
    "This reminds me to notice everyday places.",
    "The process behind this is just as interesting as the result.",
    "A lovely local discovery.",
)

CATEGORIES = (
    ("تصوير الشارع | Street photography", "street-photography"),
    ("أكل ومقاهي | Food & cafés", "food-cafes"),
    ("حرف يدوية | Handmade crafts", "handmade-crafts"),
    ("فن وتصميم | Art & design", "art-design"),
    ("أماكن وتراث | Places & heritage", "places-heritage"),
    ("طبيعة وساحل | Nature & coast", "nature-coast"),
    ("مشروعات محلية | Local businesses", "local-businesses"),
    ("تعلم وتكنولوجيا | Learning & technology", "learning-technology"),
    ("رحلات واكتشافات | Trips & discoveries", "trips-discoveries"),
)

def _slug(value: str) -> str:
    text = value.lower().replace("el-", "").replace("el ", "")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "egypt-place"


def _put(row: dict[str, Any], key: str, value: Any) -> None:
    if key in row:
        row[key] = value


def _governorate_by_population(rng: random.Random) -> dict[str, Any]:
    return rng.choices(GOVERNORATES, weights=[g["population"] for g in GOVERNORATES], k=1)[0]


def _tag_catalog(count: int) -> list[dict[str, str]]:
    catalog: list[dict[str, str]] = []
    for topic in TOPICS:
        catalog.append({"name": topic["tag_ar"], "slug": topic["slug"], "topic": topic["en"]})
        catalog.append({"name": topic["tag_en"], "slug": f"{topic['slug']}-en", "topic": topic["en"]})
    generic = (
        ("مصر", "egypt"), ("القاهرة", "cairo"), ("الإسكندرية", "alexandria"),
        ("دمياط", "damietta"), ("النيل", "nile"), ("البحر_المتوسط", "mediterranean"),
        ("البحر_الأحمر", "red-sea"), ("رمضان", "ramadan"), ("عيد", "eid"),
        ("تصوير_منتجات", "product-photography"), ("تصوير_طعام", "food-photography"),
        ("تصوير_معماري", "architecture-photography"), ("صناعة_مصرية", "made-in-egypt"),
        ("تصميم_مصري", "egyptian-design"), ("التراث_المصري", "egyptian-heritage"),
        ("شوارع_مصر", "egypt-streets"), ("حياة_يومية", "daily-life"),
        ("مشروعات_صغيرة", "small-projects"), ("مصممين_مستقلين", "independent-designers"),
        ("فن_مصري", "egyptian-art"), ("تصوير_طبيعة", "nature-photography"),
        ("صور_اليوم", "photo-of-the-day"), ("مذكرات_بصرية", "visual-journal"),
        ("رحلة_قصيرة", "short-trip"), ("حكايات_مصرية", "egyptian-stories"),
        ("إسكندرية", "eskendereya"), ("دمياطي", "damyati"), ("قاهرة", "cairo-life"),
        ("مبدعين", "creatives"), ("مساحة_إبداع", "creative-space"),
    )
    catalog.extend({"name": name, "slug": slug, "topic": TOPICS[index % len(TOPICS)]["en"]} for index, (name, slug) in enumerate(generic))
    # A long tail of general creative topics adds variety without synthesizing people or URLs.
    for tag in ("photography", "streetphotography", "portrait", "landscape", "nature", "architecture", "travel", "food", "coffee", "art", "illustration", "filmphotography", "design", "music", "books", "gardening", "history", "urbanism", "nightphotography", "blackandwhite", "minimalism", "fashion", "handmade", "craft", "cycling", "running", "learning", "technology", "programming", "datascience", "museum", "weekend", "sunset", "sunrise", "citylife", "ocean", "desert", "plants", "flowers", "streetart", "documentary", "makers", "ceramics", "watercolor", "sketchbook", "visualstorytelling", "publictransport", "homemade", "workspace", "openweb", "localhistory", "smallbusiness", "foodphotography", "community", "opensource", "privacy", "accessibility", "publicspace", "slowtravel", "portraitphotography", "mobilephotography", "productdesign", "arabiccalligraphy", "egyptianculture", "craftsmanship"):
        catalog.append({"name": tag, "slug": tag, "topic": TOPICS[len(catalog) % len(TOPICS)]["en"]})
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in catalog:
        if item["slug"] in seen:
            continue
        seen.add(item["slug"])
        result.append(item)
    while len(result) < count:
        index = len(result)
        result.append({"name": f"creative_topic_{index + 1}", "slug": f"creative-topic-{index + 1}", "topic": TOPICS[index % len(TOPICS)]["en"]})
    return result[:count]


def apply_egypt_market_context(generator: Any) -> dict[str, Any]:
    """Localize profiles, content, place references, and topics for an Egypt-focused scenario."""
    rng = random.Random(generator.seed + 604_271)
    data = generator.datasets
    users = data.get("users", [])
    profiles = data.get("profiles", [])
    statuses = data.get("statuses", [])
    local_count = min(len(users), len(profiles))
    profile_market: dict[Any, dict[str, Any]] = {}
    profile_language: dict[Any, str] = {}
    profile_governorate: dict[Any, dict[str, Any] | None] = {}
    profile_by_id = {row.get("id"): row for row in profiles}
    user_by_id = {row.get("id"): row for row in users}

    # The upstream schema replica defines local accounts first and federated profiles after.
    for index, profile in enumerate(profiles):
        local = index < local_count
        if local:
            governorate = _governorate_by_population(rng)
            language = rng.choices(["ar", "en"], weights=[0.78, 0.22], k=1)[0]
            first_ar, first_en = AR_FIRST[(index * 7 + rng.randrange(len(AR_FIRST))) % len(AR_FIRST)]
            last_ar, last_en = AR_LAST[(index * 11 + rng.randrange(len(AR_LAST))) % len(AR_LAST)]
            name = f"{first_ar} {last_ar}" if language == "ar" else f"{first_en} {last_en}"
            username = f"{_slug(first_en)}_{_slug(last_en)}_{profile.get('id')}"
            user = users[index]
            _put(user, "profile_id", profile.get("id"))
            _put(user, "name", name)
            _put(user, "username", username)
            _put(user, "email", f"{username}@example.test")
            _put(user, "language", language)
            _put(profile, "user_id", user.get("id"))
            _put(profile, "domain", None)
            _put(profile, "name", name)
            _put(profile, "username", username)
            profile_language[profile.get("id")] = language
            profile_governorate[profile.get("id")] = governorate
            profile_market[profile.get("id")] = {"local": True, "governorate": governorate, "language": language}
        else:
            language = "en" if rng.random() < 0.8 else "ar"
            profile_language[profile.get("id")] = language
            profile_governorate[profile.get("id")] = None
            profile_market[profile.get("id")] = {"local": False, "governorate": None, "language": language}

    # Derive a stable, small creator cohort from observed generated post counts.
    post_counts: dict[Any, int] = {}
    for post in statuses:
        pid = post.get("profile_id")
        post_counts[pid] = post_counts.get(pid, 0) + 1
    ranked = sorted(profile_market, key=lambda pid: (-post_counts.get(pid, 0), str(pid)))
    creator_ids = set(ranked[: max(1, round(len(ranked) * 0.10))]) if ranked else set()

    # Build 100 distinct place names without inventing exact coordinates for every locality.
    gov_by_name = {row["en"]: row for row in GOVERNORATES}
    place_specs: list[tuple[str, dict[str, Any], float | None, float | None]] = [
        (gov["capital"], gov, gov["lat"], gov["lon"]) for gov in GOVERNORATES
    ]
    for place_name, gov_name in EXTRA_PLACES:
        governorate = gov_by_name[gov_name]
        place_specs.append((place_name, governorate, None, None))
    places = data.get("places", [])
    for index, row in enumerate(places):
        name, governorate, latitude, longitude = place_specs[index % len(place_specs)]
        _put(row, "name", name)
        _put(row, "country", "Egypt")
        _put(row, "slug", f"eg-{_slug(name)}-{index + 1:03d}")
        _put(row, "aliases", json.dumps([governorate["en"], governorate["ar"], governorate["region"]], ensure_ascii=False, separators=(",", ":")))
        _put(row, "lat", latitude)
        _put(row, "long", longitude)
    capital_place_id = {
        governorate["en"]: places[index].get("id")
        for index, governorate in enumerate(GOVERNORATES)
        if index < len(places)
    }

    # Natural absence is modelled deliberately: an undisclosed location is not inferred,
    # bios are optional, and websites are more common for visible creators.
    for profile in profiles:
        pid = profile.get("id")
        market = profile_market.get(pid, {})
        governorate = profile_governorate.get(pid)
        language = profile_language.get(pid, "en")
        topic = rng.choice(TOPICS)
        if market.get("local") and governorate:
            location_text = governorate["capital"] if governorate["capital"] == governorate["en"] else f"{governorate['capital']}, {governorate['en']}"
            location_text = f"{location_text}, Egypt" if rng.random() < 0.64 else None
            _put(profile, "location", location_text)
        else:
            _put(profile, "location", rng.choice(("Berlin, Germany", "Amman, Jordan", "London, United Kingdom", "Tunis, Tunisia", "Nairobi, Kenya")) if rng.random() < 0.55 else None)
        if rng.random() < (0.78 if pid in creator_ids else 0.67):
            bio = topic["bio_ar"] if language == "ar" else topic["bio_en"]
            _put(profile, "bio", bio)
        else:
            _put(profile, "bio", None)
        _put(profile, "website", f"https://portfolio-{profile.get('id')}.example.test" if pid in creator_ids and rng.random() < 0.45 else None)
        _put(profile, "profile_layout", rng.choices(["grid", "masonry"], weights=[0.70, 0.30], k=1)[0])
        _put(profile, "post_layout", "masonry" if pid in creator_ids else "grid")

    hashtag_rows = data.get("hashtags", [])
    tag_catalog = _tag_catalog(len(hashtag_rows))
    tag_by_id: dict[Any, dict[str, str]] = {}
    for index, row in enumerate(hashtag_rows):
        item = tag_catalog[index]
        tag_item = dict(item)
        if any(previous.get("slug") == item["slug"] for previous in tag_by_id.values()):
            tag_item["slug"] = f"{item['slug']}-{index + 1}"
        _put(row, "name", tag_item["name"])
        _put(row, "slug", tag_item["slug"])
        _put(row, "is_nsfw", 0)
        _put(row, "is_banned", 0)
        tag_by_id[row.get("id")] = tag_item

    bridge_by_status: dict[Any, list[dict[str, Any]]] = {}
    for bridge in data.get("status_hashtags", []):
        bridge_by_status.setdefault(bridge.get("status_id"), []).append(bridge)
    topic_by_name = {topic["en"]: topic for topic in TOPICS}
    for post in statuses:
        pid = post.get("profile_id")
        market = profile_market.get(pid, {})
        governorate = profile_governorate.get(pid)
        language = profile_language.get(pid, "en")
        linked = bridge_by_status.get(post.get("id"), [])
        linked_tags = [tag_by_id[item.get("hashtag_id")] for item in linked if item.get("hashtag_id") in tag_by_id]
        if linked_tags:
            selected_topic = topic_by_name.get(linked_tags[0]["topic"], TOPICS[0])
        else:
            selected_topic = rng.choice(TOPICS)
        if governorate:
            place_label = governorate["capital"] if language == "en" else governorate["ar"]
        else:
            place_label = "the community" if language == "en" else "المجتمع"
        templates = selected_topic["captions_ar"] if language == "ar" else selected_topic["captions_en"]
        caption = rng.choice(templates).format(place=place_label)
        _put(post, "caption", caption)
        _put(post, "rendered", caption)
        _put(post, "language", language)
        _put(post, "local", int(bool(market.get("local"))))
        place_id = capital_place_id.get(governorate["en"]) if governorate and market.get("local") else None
        _put(post, "place_id", place_id if rng.random() < 0.38 else None)
        embedded_tags = [tag_by_id[item.get("hashtag_id")]["name"] for item in linked if item.get("hashtag_id") in tag_by_id]
        _put(post, "entities", json.dumps({"hashtags": embedded_tags, "mentions": []}, ensure_ascii=False, separators=(",", ":")))

    # Keep media descriptions aligned to the caption before the raw-quality profile runs.
    post_by_id = {post.get("id"): post for post in statuses}
    for media in data.get("media", []):
        post = post_by_id.get(media.get("status_id"))
        if post:
            _put(media, "caption", post.get("caption"))

    for comment in data.get("comments", []):
        actor_language = profile_language.get(comment.get("profile_id"), "en")
        templates = COMMENTS_AR if actor_language == "ar" else COMMENTS_EN
        comment_text = rng.choice(templates)
        _put(comment, "comment", comment_text)
        _put(comment, "rendered", comment_text)

    for collection in data.get("collections", []):
        market = profile_market.get(collection.get("profile_id"), {})
        language = market.get("language", "en")
        collection_topic = rng.choice(TOPICS)
        title = collection_topic["ar"] if language == "ar" else collection_topic["en"]
        description = (
            f"مجموعة صور عن {collection_topic['ar']} وأماكن من الحياة اليومية."
            if language == "ar"
            else f"A collection of visual notes about {collection_topic['en'].lower()} and everyday life in Egypt."
        )
        _put(collection, "title", title)
        _put(collection, "description", description)

    categories = data.get("discover_categories", [])
    for index, category in enumerate(categories):
        name, slug = CATEGORIES[index % len(CATEGORIES)]
        suffix = f"-{index + 1}" if index >= len(CATEGORIES) else ""
        _put(category, "name", name if not suffix else f"{name} {index + 1}")
        _put(category, "slug", f"{slug}{suffix}")
        _put(category, "active", int(rng.random() < 0.94))
        _put(category, "order", index + 1)
        _put(category, "local_only", int(index % 3 == 0))
        _put(category, "public_only", 1)
        _put(category, "photos_only", int(index % 3 != 1))

    for notification in data.get("notifications", []):
        language = profile_language.get(notification.get("profile_id"), "en")
        actor = profile_by_id.get(notification.get("actor_id"), {})
        actor_name = actor.get("name") or ("حد" if language == "ar" else "A profile")
        action = str(notification.get("action") or "")
        if language == "ar":
            message = {
                "like": f"{actor_name} عمل إعجاب على أحد منشوراتك.",
                "comment": f"{actor_name} علّق على أحد منشوراتك.",
                "follow": f"{actor_name} بدأ يتابعك.",
            }.get(action, "عندك إشعار جديد.")
        else:
            message = {
                "like": f"{actor_name} liked one of your posts.",
                "comment": f"{actor_name} commented on one of your posts.",
                "follow": f"{actor_name} started following you.",
            }.get(action, "You have a new notification.")
        _put(notification, "message", message)
        _put(notification, "rendered", message)

    for story in data.get("stories", []):
        language = profile_language.get(story.get("profile_id"), "en")
        story_text = "لحظة من اليوم تستحق التوثيق." if language == "ar" else "A small moment from the day worth remembering."
        _put(story, "story", json.dumps({"synthetic": True, "caption": story_text, "format": story.get("type")}, ensure_ascii=False, separators=(",", ":")))

    # Check the population reference table is well formed; this is not a claim about
    # who uses PixelFed or how creators are distributed in actual Egypt.
    expected = {governorate["en"] for governorate in GOVERNORATES}
    errors: list[str] = []
    actual_local = sum(bool(item.get("local")) for item in profile_market.values())
    if len(GOVERNORATES) != 27:
        errors.append("Expected all 27 Egyptian governorates in the reference table")
    if any(governorate["population"] <= 0 for governorate in GOVERNORATES):
        errors.append("Governorate population counts must be positive")
    if len(places) >= len(GOVERNORATES):
        actual_places = {str(row.get("country")) for row in places}
        if actual_places != {"Egypt"}:
            errors.append("The Egyptian market place catalogue must contain only Egypt records")
    return {
        "applied": True,
        "synthetic_only": True,
        "market": "Egypt",
        "local_profiles": actual_local,
        "federated_profiles": max(0, len(profiles) - local_count),
        "governorate_reference_count": len(GOVERNORATES),
        "reference_date": "2024-01-01",
        "checks": {"passed": not errors, "errors": errors},
        "source_reference": {
            "population": "CAPMAS governorate estimates, 2024-01-01",
            "digital_context": "DataReportal Digital 2026: Egypt; October 2025 data",
            "internet_adoption": "World Bank WDI indicator IT.NET.USER.ZS, 2024 value",
        },
        "assumptions_not_observed_facts": {
            "local_governorate_weights": "Population-proportional sample weights, not measured social-platform audience shares",
            "local_language_mix": {"ar": 0.78, "en": 0.22},
            "profile_location_disclosure": "64% local profile location disclosure assumption",
            "bio_presence": "67%-78% depending on creator cohort, modelling assumption",
            "website_presence": "Reserved .test URLs only; visible creators are more likely to have one",
            "engagement_distribution": "Existing synthetic event counts are not calibrated to actual platform telemetry",
        },
        "privacy_policy": "No real social accounts, emails, phone numbers, IP addresses, or private records imported",
        "checks_passed": not errors,
    }
