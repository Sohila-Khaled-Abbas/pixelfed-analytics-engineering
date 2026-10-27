"""Egypt-focused market context for synthetic PixelFed data.

Only aggregate public reference data is used. Individual accounts, names, activity,
emails, and profile content remain fictional; no real social accounts are imported.
"""

from __future__ import annotations

import json
import random
import re
from typing import Any

# CAPMAS population estimates by governorate, dated 2024-01-01.
# Population is used as a geography sampling prior, not as a social-media usage rate.
_GOVERNORATE_ROWS = """
Cairo|القاهرة|cairo|Cairo|10299821|100.0|30.0444|31.2357|Greater Cairo
Alexandria|الإسكندرية|alexandria|Alexandria|5573808|98.0|31.2001|29.9187|Mediterranean coast
Port Said|بورسعيد|port-said|Port Said|793976|100.0|31.2653|32.3019|Canal
Suez|السويس|suez|Suez|797045|100.0|29.9668|32.5498|Canal
Damietta|دمياط|damietta|Damietta|1626063|40.5|31.4175|31.8144|Nile Delta
Dakahlia|الدقهلية|dakahlia|Mansoura|7086788|30.2|31.0409|31.3785|Nile Delta
Sharqia|الشرقية|sharqia|Zagazig|7961136|26.8|30.5877|31.5020|Nile Delta
Qalyubia|القليوبية|qalyubia|Banha|6175627|43.1|30.4667|31.1833|Greater Cairo
Kafr El-Sheikh|كفر الشيخ|kafr-el-sheikh|Kafr El-Sheikh|3740624|24.2|31.1107|30.9388|Nile Delta
Gharbia|الغربية|gharbia|Tanta|5468353|30.6|30.7865|31.0004|Nile Delta
Menoufia|المنوفية|menoufia|Shibin El-Kom|4767510|21.9|30.5526|31.0090|Nile Delta
Beheira|البحيرة|beheira|Damanhur|6927724|20.7|31.0341|30.4682|Nile Delta
Ismailia|الإسماعيلية|ismailia|Ismailia|1464224|47.0|30.5965|32.2715|Canal
Giza|الجيزة|giza|Giza|9578680|59.6|30.0131|31.2089|Greater Cairo
Beni Suef|بني سويف|beni-suef|Beni Suef|3624142|25.4|29.0661|31.0994|Upper Egypt
Fayoum|الفيوم|fayoum|Fayoum|4115608|22.8|29.3084|30.8428|Upper Egypt
Minya|المنيا|minya|Minya|6398400|19.1|28.1099|30.7503|Upper Egypt
Assiut|أسيوط|assiut|Assiut|5112926|27.6|27.1809|31.1837|Upper Egypt
Sohag|سوهاج|sohag|Sohag|5783044|21.4|26.5591|31.6957|Upper Egypt
Qena|قنا|qena|Qena|3674412|18.4|26.1551|32.7160|Upper Egypt
Aswan|أسوان|aswan|Aswan|1670122|46.1|24.0889|32.8998|Upper Egypt
Luxor|الأقصر|luxor|Luxor|1412746|42.8|25.6872|32.6396|Upper Egypt
Red Sea|البحر الأحمر|red-sea|Hurghada|406195|96.9|27.2579|33.8116|Red Sea and frontier
New Valley|الوادي الجديد|new-valley|Kharga|268834|50.8|25.4390|30.5586|Red Sea and frontier
Matrouh|مطروح|matrouh|Marsa Matruh|557193|66.1|31.3543|27.2373|Mediterranean coast
North Sinai|شمال سيناء|north-sinai|Arish|512110|61.0|31.1316|33.7984|Sinai
South Sinai|جنوب سيناء|south-sinai|El Tor|117388|56.2|28.2417|33.6222|Sinai
"""

# Additional public place names; unverified fine-grained coordinates are deliberately NULL.
_EXTRA_PLACE_ROWS = """
New Cairo|Cairo
Maadi|Cairo
Zamalek|Cairo
Heliopolis|Cairo
Nasr City|Cairo
Downtown Cairo|Cairo
Garden City|Cairo
Abbassia|Cairo
Shubra|Cairo
Ain Shams|Cairo
Mokattam|Cairo
Old Cairo|Cairo
Korba|Cairo
Fifth Settlement|Cairo
Roxy|Cairo
Fustat|Cairo
Dokki|Giza
Mohandessin|Giza
Haram|Giza
Faisal|Giza
6th of October City|Giza
Sheikh Zayed City|Giza
Imbaba|Giza
Boulak El-Dakrour|Giza
Montaza|Alexandria
Sidi Gaber|Alexandria
Raml Station|Alexandria
Stanley|Alexandria
Miami|Alexandria
Agami|Alexandria
Abu Qir|Alexandria
Borg El Arab|Alexandria
New Damietta|Damietta
Ras El Bar|Damietta
Faraskur|Damietta
Ezbet El-Borg|Damietta
Port Fouad|Port Said
Mit Ghamr|Dakahlia
10th of Ramadan City|Sharqia
Shubra El-Kheima|Qalyubia
Desouk|Kafr El-Sheikh
El Mahalla El-Kubra|Gharbia
Ashmoun|Menoufia
Kafr El-Dawwar|Beheira
Fayed|Ismailia
Ain Sokhna|Suez
Nasser|Beni Suef
Tunis Village|Fayoum
Mallawi|Minya
Dairut|Assiut
Akhmim|Sohag
Nag Hammadi|Qena
Abu Simbel|Aswan
Karnak|Luxor
Hurghada Marina|Red Sea
Marsa Alam|Red Sea
Dakhla Oasis|New Valley
Siwa Oasis|Matrouh
Sallum|Matrouh
Arish Coast|North Sinai
Sharm El-Sheikh|South Sinai
Dahab|South Sinai
Nuweiba|South Sinai
Saint Catherine|South Sinai
Kom Ombo|Aswan
Edfu|Aswan
Esna|Luxor
Armant|Luxor
Deshna|Qena
Abu Tig|Assiut
Talakh|Dakahlia
Kafr Saad|Damietta
New Salhia|Sharqia
"""

# Arabic/English phrases are deliberately varied by content theme and language.
# They are illustrative synthetic content, not sampled from real users or scraped posts.
_TOPIC_ROWS = """
Egyptian food and cafés|الأكل المصري والمقاهي|أكل_مصري|egyptianfood|egyptianfood|بشارك صور الأكل والتفاصيل اليومية من أماكن مصرية.|Sharing food photography and everyday café finds in Egypt.|لقطة من {place} النهارده، وتفاصيل الأكل كانت تستاهل الصورة.~من السوق للمطبخ، حكايات صغيرة من يوم عادي.~صورة لكل اللي بيحبوا الأكل البلدي والتفاصيل البسيطة.~ريحة الخبز والقهوة في الصبح ليها حكاية تانية.|A small food diary from {place}, inspired by everyday Egyptian kitchens.~Local flavours, familiar streets, and the details behind a good meal.~A café stop in {place} turned into today's photo story.~Food photography is my way to remember everyday places.
Street and architecture photography|تصوير الشارع والعمارة|تصوير_شارع|streetphotographyegypt|streetphotoegypt|مهتم/ة بتفاصيل الشوارع والعمارة والحياة اليومية.|Documenting street life, architecture, and small details around Egypt.|تفاصيل صغيرة في شارع {place} ممكن تعدّي من غير ما ناخد بالنا.~النور والظل في الشارع النهارده كانوا أحلى من أي تعديل.~من مشوار عادي في {place} طلعت بالصورة دي.~بحاول أوثّق شكل المدينة وهي عايشة يومها الطبيعي.|Everyday street details from {place}, photographed without staging the scene.~The light in this Egyptian street did most of the work today.~A regular walk through {place} became a small photo story.~Architecture, shade, and ordinary city life in one frame.
Crafts and handmade work|الحرف والشغل اليدوي|شغل_يدوي|egyptiancrafts|egyptiancrafts|بوثّق الشغل اليدوي والحرف والتفاصيل اللي ورا كل قطعة.|Sharing handmade work, workshop details, and local craft stories.|تفاصيل من الشغل اليدوي في الورشة النهارده.~كل قطعة وراها وقت ومجهود وتفاصيل صغيرة.~من دمياط، لقطة للتفاصيل اللي بتفرق في الشغل.~لسه في مراحل شغل كتير قبل ما القطعة تخلص.|A behind-the-scenes look at handmade work in an Egyptian workshop.~Small details, patient work, and a finished piece taking shape.~Sharing the process behind local craft, not just the final result.~A workshop day in {place}, one step at a time.
Local business and creative studios|المشروعات المحلية والاستوديوهات|مشروعات_محلية|egyptiansmallbusiness|egyptsmallbusiness|بشارك كواليس الشغل والتصوير للمشروعات المحلية.|Visual stories from small businesses, makers, and local creative studios.|من كواليس يوم شغل طويل في {place}.~وراء كل صورة ترتيب وتجربة ومحاولات كتير.~تفاصيل بسيطة من مشروع محلي بنحاول نطوره كل يوم.~النهارده كان يوم تصوير منتجات وتجهيزات جديدة.|Behind the scenes of a small creative business in {place}.~A workday of product photos, small adjustments, and learning by doing.~Local businesses have stories beyond the final product shot.~A quick look at today's setup before the next batch.
Culture and heritage|الثقافة والتراث|تراث_مصري|egyptianheritage|egyptianheritage|مهتم/ة بالحكايات المحلية والعمارة والتراث المصري.|Collecting stories about Egyptian places, architecture, and local heritage.|تفصيلة قديمة في {place} ولسه محتفظة بروح المكان.~كل شارع قديم له حكاية تستاهل تتوثق.~زيارة سريعة خلتني أبص للمكان بشكل مختلف.~بحب أصوّر التفاصيل اللي بتربطنا بذاكرة المكان.|A heritage detail in {place} that still carries the character of the place.~Old streets hold layers of stories worth documenting carefully.~A short visit to an Egyptian landmark turned into a photo note.~Keeping a visual record of local architecture and everyday history.
Nature, river, and coast|الطبيعة والنيل والساحل|طبيعة_مصر|egyptnature|egyptnature|صور للطبيعة والنيل والساحل واللحظات الهادية.|Photographing the Nile, coastlines, gardens, and quiet outdoor moments.|الهوا على الكورنيش النهارده كان محتاج صورة.~من مشوار هادي جنب النيل قبل ما الدنيا تزحم.~ألوان السما فوق {place} مختلفة كل مرة.~لقطة بسيطة من يوم على البحر من غير تجهيزات.|A quiet moment by the Nile, photographed on an ordinary day.~Coastal light around {place} changes more than I expected.~A simple outdoor frame from Egypt, with no heavy editing.~A short walk, a little breeze, and a view worth remembering.
Art, illustration, and design|الفن والرسم والتصميم|فن_وتصميم|egyptianartists|egyptianartists|مساحة للتجارب الفنية والرسم والألوان والتصميم.|Exploring illustration, colour, visual design, and creative process.|تجربة ألوان جديدة من الاسكتش لحد النسخة دي.~لسه شغال/ة على التفاصيل، وأي ملاحظات مرحب بيها.~الفكرة بدأت برسمة صغيرة وكبرت واحدة واحدة.~بحاول أخلي التصميم بسيط وواضح من غير زحمة.|A work in progress from the sketchbook, with a new colour direction.~The idea started small and changed through a few iterations.~Testing a simpler composition before calling this version finished.~A little design experiment from today's studio time.
Learning and technology|التعلم والتكنولوجيا|تعلم_وتكنولوجيا|egypttechcommunity|egypttech|بشارك ملاحظات عن التعلم والتكنولوجيا والشغل الإبداعي.|Sharing learning notes, creative technology, and open-web projects.|ملاحظة صغيرة من اللي اتعلمته النهارده وحبيت أوثقها.~تجربة جديدة، والنتيجة محتاجة شوية تحسين كمان.~بحاول أشرح الفكرة من خلال مثال عملي بدل الكلام النظري.~خطوة صغيرة في مشروع أكبر، بس التقدم هو المهم.|A practical learning note from today's project work.~Trying a new approach and documenting what worked and what did not.~A small step in a longer project, shared for anyone learning too.~A short technical experiment with room for another iteration.
Travel and local discoveries|الرحلات واكتشاف الأماكن|اكتشاف_أماكن|discoveregypt|discoveregypt|ملاحظات وصور من رحلات قصيرة وأماكن محلية.|Photo notes from day trips, local discoveries, and less familiar places.|زيارة سريعة لـ{place} وطلعت منها بالصور دي.~مش لازم الرحلة تكون بعيدة عشان نكتشف حاجة جديدة.~مكان جديد في القائمة، ووقت كفاية للتمشية والتصوير.~تفاصيل من الطريق كانت أحلى من الخطة نفسها.|A short visit to {place} turned into a handful of photo notes.~You do not have to travel far to notice something new.~A local discovery, with time to walk around and take a few frames.~Some of the best details were between the planned stops.
"""

_GENERIC_TAG_ROWS = """
مصر|egypt
القاهرة|cairo
الإسكندرية|alexandria
دمياط|damietta
النيل|nile
البحر_المتوسط|mediterranean
البحر_الأحمر|red-sea
رمضان|ramadan
عيد|eid
تصوير_منتجات|product-photography
تصوير_طعام|food-photography
تصوير_معماري|architecture-photography
صناعة_مصرية|made-in-egypt
تصميم_مصري|egyptian-design
التراث_المصري|egyptian-heritage-tag
شوارع_مصر|egypt-streets
حياة_يومية|daily-life
مشروعات_صغيرة|small-projects
مصممين_مستقلين|independent-designers
فن_مصري|egyptian-art
تصوير_طبيعة|nature-photography
صور_اليوم|photo-of-the-day
مذكرات_بصرية|visual-journal
رحلة_قصيرة|short-trip
حكايات_مصرية|egyptian-stories
إسكندرية|eskendereya
دمياطي|damyati
قاهرة|cairo-life
مبدعين|creatives
مساحة_إبداع|creative-space
"""

_FIRST_NAMES = """
مريم|Mariam
نور|Nour
أحمد|Ahmed
محمد|Mohamed
يوسف|Youssef
عمر|Omar
سارة|Sara
محمود|Mahmoud
آية|Aya
ملك|Malak
علي|Ali
مصطفى|Mostafa
منة|Menna
سلمى|Salma
ياسمين|Yasmin
فاطمة|Fatma
عبدالرحمن|Abdelrahman
كريم|Karim
دينا|Dina
ريم|Reem
هنا|Hana
ندى|Nada
زياد|Ziad
أميرة|Amira
يحيى|Yehia
ليلى|Laila
مروان|Marwan
عائشة|Aisha
إسراء|Esraa
حسن|Hassan
داليا|Dalia
رحمة|Rahma
أسماء|Asmaa
شريف|Sherif
إيمان|Iman
عمرو|Amr
سيف|Seif
رنا|Rana
حبيبة|Habiba
طارق|Tarek
"""

_LAST_NAMES = """
حسن|Hassan
السيد|ElSayed
محمود|Mahmoud
علي|Ali
إبراهيم|Ibrahim
سالم|Salem
عثمان|Othman
خليل|Khalil
مراد|Mourad
حمدي|Hamdy
فؤاد|Fouad
رشاد|Rashad
سمير|Samir
مصطفى|Mostafa
ناجي|Nagy
سعيد|Saeed
جمال|Gamal
عوض|Awad
الشافعي|ElShafei
كمال|Kamal
صبري|Sabry
زكي|Zaki
النجار|ElNaggar
الحداد|ElHaddad
عادل|Adel
طه|Taha
مرسي|Morsi
فهمي|Fahmy
الرفاعي|ElRefai
عبدالله|Abdallah
حسين|Hussein
منصور|Mansour
"""

_COMMENTS_AR = """
الصورة طالعة حلوة جدًا، خصوصًا التفاصيل اللي في الخلفية.
المكان ده له طابع مميز فعلًا.
حبيت الألوان وطريقة التصوير.
التفاصيل الصغيرة هي اللي بتخلي الصورة مختلفة.
المشهد ده فكّرني بمشوار قديم.
مستنيين صور أكتر من المكان ده.
الشغل اليدوي واضح فيه وقت ومجهود.
لقطة بسيطة بس فيها حكاية.
حلو إنك وثّقت التفاصيل دي.
المرة الجاية جرّب التصوير وقت الغروب.
المكان يستاهل زيارة فعلًا.
التكوين والألوان راكبين على بعض بشكل جميل.
"""

_COMMENTS_EN = """
The details in the background make this frame work.
I like how this captures an ordinary moment.
The colour and composition feel balanced.
This looks like a place worth exploring.
Thanks for sharing a little context with the photo.
The handmade details are easy to appreciate here.
A simple frame with a strong sense of place.
Would love to see more from this series.
The light in this one is especially good.
This reminds me to notice everyday places.
The process behind this is just as interesting as the result.
A lovely local discovery.
"""

_CAPTION_FOLLOWUPS_AR = (
    "والتفاصيل الصغيرة هي اللي لفتت نظري.",
    "صورة عادية من يوم عادي، بس حبيت أوثقها.",
    "حاولت أسيب الألوان قريبة من شكلها الطبيعي.",
    "لسه في تفاصيل كتير تستحق التصوير.",
    "من غير تجهيزات كبيرة، مجرد لحظة عابرة.",
    "كل زيارة للمكان بتكشف تفصيلة جديدة.",
    "الصورة جزء من مذكرات بصرية للمكان.",
    "التعديل كان بسيط عشان يفضل إحساس اللحظة واضح.",
)
_CAPTION_FOLLOWUPS_EN = (
    "The smaller details are what caught my attention.",
    "An ordinary moment from an ordinary day, worth keeping.",
    "I tried to keep the colours close to what I saw.",
    "There are still more details here worth photographing.",
    "No elaborate setup, just a passing moment.",
    "Every visit seems to reveal another detail.",
    "One more page in a visual diary of the place.",
    "I kept the edit light to preserve the feel of the moment.",
)
_COMMENT_FOLLOWUPS_AR = (
    "الإضاءة هنا فارقة فعلًا.",
    "والألوان طالعة طبيعية.",
    "حبيت إن التعديل مش مبالغ فيه.",
    "التفاصيل الصغيرة بتضيف كتير.",
    "الصورة فيها إحساس واضح بالمكان.",
    "اختيار زاوية التصوير موفق.",
    "اللقطة دي تستاهل تتحط في مجموعة.",
    "مستني أشوف باقي السلسلة.",
    "المشهد عادي، بس متصور باهتمام.",
    "الظل والنور عاملين توازن حلو.",
    "واضح إن فيه اهتمام بالتفاصيل.",
    "دي من الصور اللي تخليك تلاحظ المكان تاني.",
    "التكوين بسيط ومش مزدحم.",
    "حلو إنك شاركت كواليس الشغل.",
    "وقت التصوير غيّر شكل الألوان.",
    "فيه حكاية صغيرة وراء الصورة.",
)
_COMMENT_FOLLOWUPS_EN = (
    "The light makes a real difference here.",
    "The colours still feel natural.",
    "I like that the edit is not overdone.",
    "The smaller details add a lot.",
    "This frame has a strong sense of place.",
    "The camera angle works well.",
    "I could see this fitting into a photo series.",
    "Looking forward to seeing the rest of the series.",
    "An everyday scene, captured with care.",
    "The balance of light and shadow is lovely.",
    "It is clear that the details were considered.",
    "This makes me want to notice familiar places again.",
    "The composition feels simple rather than crowded.",
    "Thanks for sharing the process, not only the result.",
    "The time of day really changes the colours.",
    "There is a small story behind this frame.",
)
_REPORT_REASONS_AR = {
    "spam": "محتوى مزعج أو متكرر",
    "abusive": "محتوى مسيء",
    "copyright": "حقوق الملكية",
    "impersonation": "انتحال الهوية",
    "other": "سبب آخر يحتاج إلى مراجعة",
}
_REPORT_REASONS_EN = {
    "spam": "spam or repetitive content",
    "abusive": "abusive content",
    "copyright": "a copyright concern",
    "impersonation": "a possible impersonation",
    "other": "another issue requiring review",
}
_MODERATION_NOTES_AR = (
    "تم ربط البلاغ بالمنشور المشار إليه؛ يلزم فحص المحتوى والسياق قبل اتخاذ قرار.",
    "يرجى مراجعة وصف البلاغ مع المنشور الأصلي قبل إغلاق الحالة.",
    "لا يُفترض وجود مخالفة من نوع البلاغ وحده؛ يلزم التحقق من السياق.",
    "ملاحظة للمراجعة: الحفاظ على سجل القرار وأي إجراء يتم اتخاذه.",
    "يرجى التأكد من أن الحالة مرتبطة بالمحتوى الصحيح قبل التصعيد.",
)
_MODERATION_NOTES_EN = (
    "The report is linked to the referenced post; review the content and context before deciding.",
    "Review the report details alongside the original post before closing the case.",
    "The report type alone does not establish a violation; check the context.",
    "Review note: preserve the decision trail and document any action taken.",
    "Confirm that the case points to the correct content before escalation.",
)
_SUPPORT_REQUESTS_AR = (
    "عندي مشكلة في رفع صورة من الموبايل، وعايز أعرف الخطوات المناسبة.",
    "محتاج مساعدة في إعدادات الخصوصية وإخفاء الموقع من الملف الشخصي.",
    "أبلغ عن مشكلة في عرض الصور بعد تحديث الصفحة.",
    "ممكن توضيح طريقة الإبلاغ عن محتوى مخالف لإرشادات المجتمع؟",
    "واجهت مشكلة في تغيير اللغة بين العربية والإنجليزية.",
    "أحتاج مساعدة في الوصول إلى إعدادات وصف الصور لتحسين إمكانية الوصول.",
    "فيه مشكلة في ظهور إشعارات التعليقات عندي.",
    "عايز أعرف إزاي أراجع الأجهزة المسجلة على الحساب.",
)
_SUPPORT_REQUESTS_EN = (
    "I need help uploading a photo from my phone.",
    "Could you explain the privacy setting that hides my profile location?",
    "Images are not displaying after I refresh the page.",
    "How do I report content that may violate the community guidelines?",
    "I am having trouble switching between Arabic and English.",
    "I need help finding image-description settings for accessibility.",
    "Comment notifications do not seem to be appearing on my account.",
    "How can I review the devices associated with my account?",
)
_SUPPORT_RESPONSES_AR = (
    "يرجى تجربة الخطوات مرة أخرى وتسجيل نص رسالة الخطأ إن استمرت المشكلة.",
    "يمكنك مراجعة إعدادات الملف الشخصي والتأكد من إيقاف مشاركة الموقع.",
    "تم تسجيل البلاغ للمراجعة، وسنحتاج إلى تفاصيل إضافية إذا تكررت المشكلة.",
    "جرّب تحديث الصفحة بعد التأكد من الاتصال، ثم أرسل وصفًا للنتيجة.",
    "راجع مركز المساعدة التجريبي، ولا تشارك كلمة المرور أو رموز التحقق.",
)
_SUPPORT_RESPONSES_EN = (
    "Please try the steps again and note the exact error if the issue continues.",
    "Review your profile settings and confirm location sharing is turned off.",
    "The request is recorded for review; more details may be needed if it repeats.",
    "Refresh after checking the connection, then share what you observe.",
    "Use the demo help guidance; never share a password or verification code.",
)
_NEWS_ITEMS = (
    {
        "category": "community",
        "slug": "community-photo-walk",
        "title_ar": "مبادرة توثيق الأماكن اليومية",
        "title_en": "Documenting everyday places",
        "summary_ar": "دعوة تجريبية لمشاركة صور توثق تفاصيل الأماكن والحياة اليومية.",
        "summary_en": "A fictional community prompt for documenting places and everyday life.",
        "body_ar": "هذا إعلان تجريبي داخل مجموعة بيانات تعليمية. شاركوا صورًا أصلية من دون كشف معلومات شخصية أو مواقع خاصة.",
        "body_en": "This is a demo announcement inside an educational dataset. Share original photos without exposing personal details or private locations.",
    },
    {
        "category": "accessibility",
        "slug": "image-description-guide",
        "title_ar": "إرشادات وصف الصور",
        "title_en": "A practical image-description guide",
        "summary_ar": "تذكير تجريبي بإضافة وصف يساعد الآخرين على فهم محتوى الصورة.",
        "summary_en": "A demo reminder to add descriptions that explain the image to other people.",
        "body_ar": "الوصف الجيد يذكر العناصر المهمة والسياق المرئي، ويبتعد عن التخمين بشأن هوية الأشخاص أو معلومات غير ظاهرة.",
        "body_en": "A useful description names important visible elements and context without guessing people's identities or information not shown.",
    },
    {
        "category": "privacy",
        "slug": "location-privacy",
        "title_ar": "راجع إعدادات مشاركة الموقع",
        "title_en": "Review location-sharing settings",
        "summary_ar": "الموقع الجغرافي اختياري؛ لا تضف عنوان المنزل أو موقعًا خاصًا دون حاجة.",
        "summary_en": "Geotagging is optional; avoid publishing a home address or private location unnecessarily.",
        "body_ar": "تستخدم هذه المجموعة بيانات اصطناعية. توضح الرسالة أهمية الإفصاح الاختياري عن الموقع، ولا تطلب بيانات موقع حقيقية.",
        "body_en": "This dataset is synthetic. The notice illustrates optional location disclosure and does not ask users to provide a real location.",
    },
    {
        "category": "community",
        "slug": "local-creative-work",
        "title_ar": "مساحة للمبدعين والمشروعات المحلية",
        "title_en": "A space for local creators",
        "summary_ar": "مثال تجريبي لمشاركة مراحل العمل اليدوي والتصميم والتصوير.",
        "summary_en": "A fictional prompt about sharing craft, design, and photography process.",
        "body_ar": "يمكن أن تشمل القصص المصورة مراحل العمل والأدوات والنتيجة النهائية، مع توضيح أن الأمثلة في هذا المشروع مولدة.",
        "body_en": "Visual stories can show process, tools, and outcomes. Examples in this project are generated and are not real business endorsements.",
    },
)
_PAGE_ITEMS = (
    {
        "slug": "community-guidelines",
        "title_ar": "إرشادات المجتمع",
        "title_en": "Community guidelines",
        "body_ar": "احترم الآخرين، وتجنب نشر معلومات شخصية أو محتوى لا تملك حق مشاركته. أبلغ عن المخاوف مع توضيح السياق.",
        "body_en": "Respect other people, avoid sharing personal information or content you do not have rights to share, and include context when reporting concerns.",
    },
    {
        "slug": "privacy-and-location",
        "title_ar": "الخصوصية ومشاركة الموقع",
        "title_en": "Privacy and location sharing",
        "body_ar": "الموقع والنبذة والموقع الإلكتروني حقول اختيارية. لا يستنتج هذا التطبيق موقع الشخص من نشاطه أو من عنوان الشبكة.",
        "body_en": "Location, biography, and website are optional. This demo does not infer a person's location from activity or network addresses.",
    },
    {
        "slug": "accessibility",
        "title_ar": "إمكانية الوصول ووصف الصور",
        "title_en": "Accessibility and image descriptions",
        "body_ar": "اكتب وصفًا واضحًا للعناصر المهمة في الصورة. لا تخمّن هوية الأشخاص أو معلومات لا تظهر في الصورة.",
        "body_en": "Write clear descriptions of important visible elements. Do not guess people's identities or information that is not shown.",
    },
    {
        "slug": "about-demo",
        "title_ar": "حول النسخة التجريبية",
        "title_en": "About this demo",
        "body_ar": "هذه بيئة تعليمية ببيانات اصطناعية لأغراض هندسة التحليلات. لا تمثل سجلات مستخدمين حقيقيين أو مؤشرات أداء منصة فعلية.",
        "body_en": "This is an educational analytics-engineering demo with synthetic data. It does not represent real user records or actual platform performance.",
    },
)

_CATEGORY_ROWS = """
تصوير الشارع / Street photography|street-photography
أكل ومقاهي / Food & cafes|food-cafes
حرف يدوية / Handmade crafts|handmade-crafts
فن وتصميم / Art & design|art-design
أماكن وتراث / Places & heritage|places-heritage
طبيعة وساحل / Nature & coast|nature-coast
مشروعات محلية / Local businesses|local-businesses
تعلم وتكنولوجيا / Learning & technology|learning-technology
رحلات واكتشافات / Trips & discoveries|trips-discoveries
"""

_GLOBAL_TAGS = (
    "photography streetphotography portrait landscape nature architecture travel food coffee art "
    "illustration filmphotography design music books gardening history urbanism nightphotography "
    "blackandwhite minimalism fashion handmade craft cycling running learning technology programming "
    "datascience museum weekend sunset sunrise citylife ocean desert plants flowers streetart "
    "documentary makers ceramics watercolor sketchbook visualstorytelling publictransport homemade "
    "workspace openweb localhistory smallbusiness community opensource privacy accessibility "
    "publicspace slowtravel portraitphotography mobilephotography productdesign arabiccalligraphy "
    "egyptianculture craftsmanship photographywalk visualdiary foodstyling digitalcreator"
).split()


def _parse_rows(raw: str) -> list[list[str]]:
    return [line.split("|") for line in raw.strip().splitlines() if line.strip()]


GOVERNORATES: tuple[dict[str, Any], ...] = tuple(
    {
        "en": row[0],
        "ar": row[1],
        "slug": row[2],
        "capital": row[3],
        "population": int(row[4]),
        "urban_pct": float(row[5]),
        "lat": float(row[6]),
        "lon": float(row[7]),
        "region": row[8],
    }
    for row in _parse_rows(_GOVERNORATE_ROWS)
)
TOPICS: tuple[dict[str, Any], ...] = tuple(
    {
        "en": row[0],
        "ar": row[1],
        "tag_ar": row[2],
        "tag_en": row[3],
        "slug": row[4],
        "bio_ar": row[5],
        "bio_en": row[6],
        "captions_ar": tuple(row[7].split("~")),
        "captions_en": tuple(row[8].split("~")),
    }
    for row in _parse_rows(_TOPIC_ROWS)
)
AR_FIRST = tuple(tuple(row) for row in _parse_rows(_FIRST_NAMES))
AR_LAST = tuple(tuple(row) for row in _parse_rows(_LAST_NAMES))
COMMENTS_AR = tuple(line for line in _COMMENTS_AR.strip().splitlines() if line.strip())
COMMENTS_EN = tuple(line for line in _COMMENTS_EN.strip().splitlines() if line.strip())
CATEGORIES = tuple(tuple(row) for row in _parse_rows(_CATEGORY_ROWS))


def _slug(value: str) -> str:
    text = value.lower().replace("el-", "").replace("el ", "")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "egypt-place"


def _put(row: dict[str, Any], key: str, value: Any) -> None:
    if key in row:
        row[key] = value


def _null_summary(rows: list[dict[str, Any]], column: str) -> dict[str, Any]:
    total = len(rows)
    null_count = sum(row.get(column) is None for row in rows)
    return {
        "row_count": total,
        "null_count": null_count,
        "null_rate": round(null_count / total, 4) if total else None,
    }


def _governorate_by_population(rng: random.Random) -> dict[str, Any]:
    # Population anchors the sample; a documented urban propensity prior lightly
    # favours places where creators and local businesses are easier to discover.
    weights = [
        governorate["population"] * (0.65 + 0.35 * governorate["urban_pct"] / 100)
        for governorate in GOVERNORATES
    ]
    return rng.choices(GOVERNORATES, weights=weights, k=1)[0]


def _tag_catalog(count: int) -> list[dict[str, str]]:
    catalog: list[dict[str, str]] = []
    for topic in TOPICS:
        catalog.append({"name": topic["tag_ar"], "slug": topic["slug"], "topic": topic["en"]})
        catalog.append({"name": topic["tag_en"], "slug": f"{topic['slug']}-en", "topic": topic["en"]})
    for index, row in enumerate(_parse_rows(_GENERIC_TAG_ROWS)):
        catalog.append(
            {"name": row[0], "slug": row[1], "topic": TOPICS[index % len(TOPICS)]["en"]}
        )
    for index, tag in enumerate(_GLOBAL_TAGS):
        catalog.append(
            {"name": tag, "slug": tag, "topic": TOPICS[index % len(TOPICS)]["en"]}
        )

    result: list[dict[str, str]] = []
    seen_names: set[str] = set()
    seen_slugs: set[str] = set()
    for item in catalog:
        if item["name"] in seen_names or item["slug"] in seen_slugs:
            continue
        seen_names.add(item["name"])
        seen_slugs.add(item["slug"])
        result.append(item)
    while len(result) < count:
        index = len(result) + 1
        result.append(
            {
                "name": f"creative_topic_{index}",
                "slug": f"creative-topic-{index}",
                "topic": TOPICS[index % len(TOPICS)]["en"],
            }
        )
    return result[:count]


def apply_egypt_market_context(generator: Any) -> dict[str, Any]:
    """Localize profiles, content, location tags, and topics for an Egypt-focused scenario."""
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

    # The schema replica defines local accounts first and federated profiles after.
    for index, profile in enumerate(profiles):
        local = index < local_count
        if local:
            governorate = _governorate_by_population(rng)
            language = rng.choices(["ar", "en"], weights=[0.78, 0.22], k=1)[0]
            first_ar, first_en = AR_FIRST[
                (index * 7 + rng.randrange(len(AR_FIRST))) % len(AR_FIRST)
            ]
            last_ar, last_en = AR_LAST[
                (index * 11 + rng.randrange(len(AR_LAST))) % len(AR_LAST)
            ]
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
            profile_market[profile.get("id")] = {
                "local": True,
                "governorate": governorate,
                "language": language,
            }
        else:
            language = "en" if rng.random() < 0.8 else "ar"
            profile_language[profile.get("id")] = language
            profile_governorate[profile.get("id")] = None
            profile_market[profile.get("id")] = {
                "local": False,
                "governorate": None,
                "language": language,
            }

    post_counts: dict[Any, int] = {}
    for post in statuses:
        pid = post.get("profile_id")
        post_counts[pid] = post_counts.get(pid, 0) + 1
    ranked = sorted(profile_market, key=lambda pid: (-post_counts.get(pid, 0), str(pid)))
    creator_ids = set(ranked[: max(1, round(len(ranked) * 0.10))]) if ranked else set()

    governorate_by_name = {row["en"]: row for row in GOVERNORATES}
    place_specs: list[tuple[str, dict[str, Any], float | None, float | None]] = [
        (gov["capital"], gov, gov["lat"], gov["lon"]) for gov in GOVERNORATES
    ]
    place_specs.extend(
        (name, governorate_by_name[gov_name], None, None)
        for name, gov_name in _parse_rows(_EXTRA_PLACE_ROWS)
    )
    places = data.get("places", [])
    places_by_governorate: dict[str, list[dict[str, Any]]] = {}
    for index, row in enumerate(places):
        name, governorate, latitude, longitude = place_specs[index % len(place_specs)]
        _put(row, "name", name)
        _put(row, "country", "Egypt")
        _put(row, "slug", f"eg-{_slug(name)}-{index + 1:03d}")
        _put(
            row,
            "aliases",
            json.dumps(
                [governorate["en"], governorate["ar"], governorate["region"]],
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        _put(row, "lat", latitude)
        _put(row, "long", longitude)
        places_by_governorate.setdefault(governorate["en"], []).append(
            {"id": row.get("id"), "name": name}
        )

    # Missing biography, website, and location values are expected profile states.
    profile_place_name: dict[Any, str] = {}
    profile_place_id: dict[Any, Any] = {}
    for profile in profiles:
        pid = profile.get("id")
        market = profile_market.get(pid, {})
        governorate = profile_governorate.get(pid)
        language = profile_language.get(pid, "en")
        topic = rng.choice(TOPICS)
        if market.get("local") and governorate:
            available_places = places_by_governorate.get(governorate["en"], [])
            selected_place = (
                rng.choice(available_places)
                if available_places
                else {"name": governorate["capital"], "id": None}
            )
            place_name = str(selected_place["name"])
            profile_place_name[pid] = place_name
            profile_place_id[pid] = selected_place.get("id")
            if place_name in {governorate["en"], governorate["capital"]}:
                location_text = f"{place_name}, Egypt"
            else:
                location_text = f"{place_name}, {governorate['en']}, Egypt"
            location = location_text if rng.random() < 0.64 else None
        else:
            location = (
                rng.choice(
                    ("Berlin, Germany", "Amman, Jordan", "London, United Kingdom", "Tunis, Tunisia", "Nairobi, Kenya")
                )
                if rng.random() < 0.55
                else None
            )
        _put(profile, "location", location)
        if rng.random() < (0.78 if pid in creator_ids else 0.67):
            _put(profile, "bio", topic["bio_ar"] if language == "ar" else topic["bio_en"])
        else:
            _put(profile, "bio", None)
        website = f"https://portfolio-{pid}.example.test" if pid in creator_ids and rng.random() < 0.45 else None
        _put(profile, "website", website)
        _put(profile, "profile_layout", rng.choices(["grid", "masonry"], weights=[0.70, 0.30], k=1)[0])
        _put(profile, "post_layout", "masonry" if pid in creator_ids else "grid")

    tag_by_id: dict[Any, dict[str, str]] = {}
    hashtag_rows = data.get("hashtags", [])
    tag_catalog = _tag_catalog(len(hashtag_rows))
    for index, row in enumerate(hashtag_rows):
        item = tag_catalog[index]
        _put(row, "name", item["name"])
        _put(row, "slug", item["slug"])
        _put(row, "is_nsfw", 0)
        _put(row, "is_banned", 0)
        tag_by_id[row.get("id")] = item

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
        linked_tags = [tag_by_id[row.get("hashtag_id")] for row in linked if row.get("hashtag_id") in tag_by_id]
        topic = topic_by_name.get(linked_tags[0]["topic"], TOPICS[0]) if linked_tags else rng.choice(TOPICS)
        place_label = (
            profile_place_name.get(pid, governorate["capital"])
            if language == "en"
            else governorate["ar"]
        ) if governorate else ("the community" if language == "en" else "المجتمع")
        templates = topic["captions_ar"] if language == "ar" else topic["captions_en"]
        caption = rng.choice(templates).format(place=place_label)
        if rng.random() < 0.42:
            caption += " " + rng.choice(
                _CAPTION_FOLLOWUPS_AR if language == "ar" else _CAPTION_FOLLOWUPS_EN
            )
        _put(post, "caption", caption)
        _put(post, "rendered", caption)
        _put(post, "language", language)
        _put(post, "local", int(bool(market.get("local"))))
        place_id = profile_place_id.get(pid) if governorate and market.get("local") else None
        _put(post, "place_id", place_id if rng.random() < 0.38 else None)
        embedded_tags = [
            tag_by_id[row.get("hashtag_id")]["name"]
            for row in linked
            if row.get("hashtag_id") in tag_by_id
        ]
        _put(
            post,
            "entities",
            json.dumps({"hashtags": embedded_tags, "mentions": []}, ensure_ascii=False, separators=(",", ":")),
        )

    post_by_id = {post.get("id"): post for post in statuses}
    for media in data.get("media", []):
        post = post_by_id.get(media.get("status_id"))
        if post:
            _put(media, "caption", post.get("caption"))

    for comment in data.get("comments", []):
        language = profile_language.get(comment.get("profile_id"), "en")
        if language == "ar":
            comment_text = rng.choice(COMMENTS_AR)
            if rng.random() < 0.58:
                comment_text += " " + rng.choice(_COMMENT_FOLLOWUPS_AR)
        else:
            comment_text = rng.choice(COMMENTS_EN)
            if rng.random() < 0.58:
                comment_text += " " + rng.choice(_COMMENT_FOLLOWUPS_EN)
        _put(comment, "comment", comment_text)
        _put(comment, "rendered", comment_text)

    for collection in data.get("collections", []):
        language = profile_market.get(collection.get("profile_id"), {}).get("language", "en")
        topic = rng.choice(TOPICS)
        title = topic["ar"] if language == "ar" else topic["en"]
        description = (
            f"مجموعة صور عن {topic['ar']} وأماكن من الحياة اليومية."
            if language == "ar"
            else f"A collection of visual notes about {topic['en'].lower()} and everyday life in Egypt."
        )
        _put(collection, "title", title)
        _put(collection, "description", description)

    for index, category in enumerate(data.get("discover_categories", [])):
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

    # Moderation records use reason-aware notes and the reporter's language.
    for report in data.get("reports", []):
        language = profile_language.get(report.get("profile_id"), "en")
        reason_key = str(report.get("type") or "other").strip().lower()
        if language == "ar":
            reason = _REPORT_REASONS_AR.get(reason_key, _REPORT_REASONS_AR["other"])
            message = f"بلاغ للمراجعة: {reason}. يرجى التحقق من المحتوى والسياق."
        else:
            reason = _REPORT_REASONS_EN.get(reason_key, _REPORT_REASONS_EN["other"])
            message = f"Review request: {reason}. Please check the content and context."
        _put(report, "message", message)

    for report_comment in data.get("report_comments", []):
        language = profile_language.get(report_comment.get("profile_id"), "en")
        note = rng.choice(_MODERATION_NOTES_AR if language == "ar" else _MODERATION_NOTES_EN)
        _put(report_comment, "comment", note)

    users_by_id = {row.get("id"): row for row in users}
    # Support tickets are localized. If there is no response timestamp, a blank response
    # is retained in raw data rather than implying that support replied.
    for contact in data.get("contacts", []):
        user = users_by_id.get(contact.get("user_id"), {})
        language = str(user.get("language") or "ar")
        requests = _SUPPORT_REQUESTS_AR if language == "ar" else _SUPPORT_REQUESTS_EN
        responses = _SUPPORT_RESPONSES_AR if language == "ar" else _SUPPORT_RESPONSES_EN
        _put(contact, "message", rng.choice(requests))
        response = rng.choice(responses) if contact.get("responded_at") is not None else ""
        _put(contact, "response", response)

    # These are demo newsroom/pages records, not claims that the real Pixelfed service
    # published Egyptian announcements. Link only to the reserved .test domain.
    for index, item in enumerate(data.get("newsroom", [])):
        language = str(rng.choices(["ar", "en"], weights=[0.78, 0.22], k=1)[0])
        content_item = _NEWS_ITEMS[index % len(_NEWS_ITEMS)]
        suffix = str(item.get("id") or index + 1)
        title = content_item["title_ar"] if language == "ar" else content_item["title_en"]
        summary = content_item["summary_ar"] if language == "ar" else content_item["summary_en"]
        body = content_item["body_ar"] if language == "ar" else content_item["body_en"]
        slug = f"demo-eg-{content_item['slug']}-{suffix}"
        _put(item, "category", content_item["category"])
        _put(item, "title", title)
        _put(item, "slug", slug)
        _put(item, "summary", summary)
        _put(item, "body", body)
        _put(item, "body_rendered", body)
        _put(
            item,
            "link",
            f"https://pixelfed.example.test/community/{slug}" if item.get("show_link") else None,
        )
        _put(item, "header_photo_url", None)

    for index, item in enumerate(data.get("pages", [])):
        language = str(rng.choices(["ar", "en"], weights=[0.78, 0.22], k=1)[0])
        page_item = _PAGE_ITEMS[index % len(_PAGE_ITEMS)]
        suffix = str(item.get("id") or index + 1)
        _put(item, "slug", f"demo-eg-{page_item['slug']}-{suffix}")
        _put(item, "title", page_item["title_ar"] if language == "ar" else page_item["title_en"])
        _put(item, "content", page_item["body_ar"] if language == "ar" else page_item["body_en"])
        _put(item, "template", "standard")

    # Use reserved documentation-only addresses in audit logs too; no routable IP
    # is required for a synthetic sample.
    for log_row in data.get("account_logs", []):
        row_id = int(log_row.get("id") or 0)
        _put(log_row, "ip_address", f"192.0.2.{row_id % 254 + 1}")
        _put(
            log_row,
            "metadata",
            json.dumps(
                {"synthetic": True, "market": "Egypt", "demo_record_id": row_id},
                separators=(",", ":"),
            ),
        )
        user = users_by_id.get(log_row.get("user_id"), {})
        language = str(user.get("language") or "ar")
        action = str(log_row.get("action") or "").lower()
        if language == "ar":
            message = {
                "login": "تم تسجيل حدث دخول تجريبي للحساب.",
                "password": "تم تسجيل حدث متعلق بإعدادات كلمة المرور.",
                "update": "تم تسجيل تحديث تجريبي لإعدادات الحساب.",
                "delete": "تم تسجيل حدث متعلق بحالة الحساب.",
            }
            _put(log_row, "message", next((value for key, value in message.items() if key in action), "تم تسجيل حدث في سجل الحساب التجريبي."))
        else:
            message = {
                "login": "A demo account sign-in event was recorded.",
                "password": "An account password-settings event was recorded.",
                "update": "A demo account-settings update was recorded.",
                "delete": "An account lifecycle event was recorded.",
            }
            _put(log_row, "message", next((value for key, value in message.items() if key in action), "A demo account event was recorded."))

    for story in data.get("stories", []):
        language = profile_language.get(story.get("profile_id"), "en")
        story_text = (
            "لحظة من اليوم تستحق التوثيق."
            if language == "ar"
            else "A small moment from the day worth remembering."
        )
        _put(
            story,
            "story",
            json.dumps(
                {"synthetic": True, "caption": story_text, "format": story.get("type")},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )

    errors: list[str] = []
    if len(GOVERNORATES) != 27:
        errors.append("Expected all 27 Egyptian governorates in the reference table")
    if any(gov["population"] <= 0 for gov in GOVERNORATES):
        errors.append("Governorate population counts must be positive")
    if len(places) >= len(GOVERNORATES) and {row.get("country") for row in places} != {"Egypt"}:
        errors.append("The Egyptian market place catalogue must contain only Egypt records")

    contacts = data.get("contacts", [])
    return {
        "applied": True,
        "synthetic_only": True,
        "market": "Egypt",
        "local_profiles": sum(bool(item.get("local")) for item in profile_market.values()),
        "federated_profiles": max(0, len(profiles) - local_count),
        "governorate_reference_count": len(GOVERNORATES),
        "reference_date": "2024-01-01",
        "checks": {"passed": not errors, "errors": errors},
        "checks_passed": not errors,
        "source_reference": {
            "population": "CAPMAS governorate estimates, 2024-01-01",
            "digital_context": "DataReportal Digital 2026: Egypt; October/end-2025 data",
            "internet_adoption": "World Bank WDI indicator IT.NET.USER.ZS, 2024 value",
        },
        "source_urls": {
            "population": "https://www.capmas.gov.eg/Admin/Pages%20Files/20245121324361-%20pop_new.pdf",
            "digital_context": "https://datareportal.com/reports/digital-2026-egypt",
            "internet_adoption": "https://data.worldbank.org/indicator/IT.NET.USER.ZS?locations=EG",
        },
        "reference_metrics_context_only": {
            "world_bank_internet_use_pct_2024": 75,
            "datareportal_internet_users_millions_october_2025": 98.2,
            "datareportal_social_media_user_identities_millions_october_2025": 51.6,
            "caveat": "Social-media user identities may not represent unique people. These values are not used to estimate platform account counts.",
        },
        "assumptions_not_observed_facts": {
            "local_governorate_weights": "Population multiplied by (0.65 + 0.35 * CAPMAS urban share); not measured platform audience shares",
            "urban_propensity_factor": 0.35,
            "local_language_mix": {"ar": 0.78, "en": 0.22},
            "profile_location_disclosure": "64% local location disclosure assumption",
            "bio_presence": "67%-78% depending on creator cohort, modelling assumption",
            "website_presence": "Reserved .test URLs; visible creators are more likely to list one",
            "engagement_distribution": "Synthetic event counts are not calibrated to actual platform telemetry",
        },
        "natural_missingness_before_raw_quality": {
            "profiles.bio": _null_summary(profiles, "bio"),
            "profiles.location": _null_summary(profiles, "location"),
            "profiles.website": _null_summary(profiles, "website"),
            "statuses.place_id": _null_summary(statuses, "place_id"),
            "users.email_verified_at": _null_summary(users, "email_verified_at"),
            "places.latitude": _null_summary(places, "lat"),
            "places.longitude": _null_summary(places, "long"),
            "contacts.response_blank_without_response_timestamp": sum(
                not str(row.get("response") or "").strip() and row.get("responded_at") is None
                for row in contacts
            ),
        },
        "privacy_policy": "No real social accounts, emails, phone numbers, IP addresses, or private records imported",
    }
