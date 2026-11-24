# Online Temel İSG Eğitimi (Az Tehlikeli, 8 ders saati) — ders senaryosu yazım kılavuzu

Çıktı: `lessons/az8_<kod>.json` (örn. `lessons/az8_g1.json`). Örnek biçim: `lessons/az8_g1_ornek.json` (yalnızca biçim örneği, kısa).
Doğrulama: `python3 tools/lesson_check.py lessons/az8_<kod>.json` HATASIZ geçmeli. Git commit/push YAPMA.

## Üst alanlar
```json
{"code": "az8_g1", "course": "Temel İSG Eğitimi · Az Tehlikeli", "section": "1. Bölüm · Genel Konular",
 "title": "<ders başlığı>", "voice": {"lang": "tr-TR", "voice": "tr-TR-Chirp3-HD-Charon", "gender": "MALE"}, "scenes": [...]}
```
section: 1. Bölüm · Genel Konular (g), 2. Bölüm · Sağlık Konuları (s), 3. Bölüm · Teknik Konular (t), 4. Bölüm · Faaliyete Özgü Konular (o).

## Süre (en önemli kural)
Ders videosu, LMS'deki süreyi doldurmalı. Seslendirme ≈ 2,02 kelime/sn. `steps` içindeki toplam kelime:
- g*, o*: 1350 sn → en az **2810** kelime (en çok ~3000)
- s*: 1080 sn → en az **2250** kelime (en çok ~2450)
- t*: 900 sn → en az **1875** kelime (en çok ~2050)
Doldurma/tekrar/boş laf YOK: süreyi gerçek içerik, örnek olaylar, "işyerinizde bunu nasıl görürsünüz" soruları ve uygulama ipuçlarıyla doldur.

## Sahne türleri (her sahne: `type`, `kicker` (kısa üst etiket), `title`, `steps` = seslendirme parçaları)
Her adımda görsel bir öğe belirir; adım metni o öğeyi anlatır. Adım: 1–4 cümle, 15–70 kelime.
- `cover`: photo (zorunlu), title, subtitle. Ders açılışı. steps 1–2.
- `split`: photo (önerilir; sağda), title (≤64 kr, 2 satır), bullets 2–5 (≤92 kr). steps = bullets+1 (ilk adım giriş, sonra her madde). Fazla adım olursa son hal ekranda kalır.
- `photo`: tam ekran photo (zorunlu), title (≤46), bullets 0–3 (≤62 kr, tek satır). steps = bullets+1.
- `fact`: tam ekran koyu photo (zorunlu), value (≤10 kr, büyük sayı/ifade, örn "3 iş günü", "%80"), title (≤120), text (≤160, 2. adımda belirir). steps ≥2.
- `stats`: items 2–4 {value ≤6 kr, unit, label}. title ≤46. steps = items+1.
- `cards`: tam 3 items {photo, tag (opsiyonel kısa), title ≤26, text ≤110}. title ≤46. steps = items+1.
- `roles`: tam 3 items {photo (yuvarlak kırpılır, kişi/yüz değil nesne/ortam olabilir), title ≤26, text ≤110}. steps = items+1.
- `process`: 3–5 items {title ≤24, text ≤80} numaralı akış. title ≤46. steps = items+1.
- `dodont`: tam 2 items {photo, ok: true/false, title ≤26, text ≤110} Doğru/Yanlış karşılaştırması. title ≤46. steps = 3.
- `check`: photo (önerilir), title, bullets 2–5 (≤92) özet. steps = bullets+1.

## Ders akışı (her ders)
1. cover (selamlama, dersin neden önemli olduğu, kısa)
2. "Bu derste neler öğreneceğiz" (split veya process)
3. İçerik bölümleri: tür çeşitliliği kullan, aynı türü art arda 2'den fazla kullanma. Sahne başına ortalama 40–75 sn.
4. En az 2 **örnek olay** (kısa hikâye: ofis, mağaza, depo, kafe, okul gibi az tehlikeli işyerlerinden; ne oldu, ne yapılmalıydı) — photo/dodont ile.
5. Ara özet (check) yaklaşık ortada, kapanış özeti (check) en sonda.
6. Kapanış cümlesi: "Dersin sonunda birkaç kısa soru sizi bekliyor..." gibi.
Toplam ~22–40 sahne. Sahnelerin en az %65'i fotoğraflı olsun (photo/cover/fact/split+photo/cards/roles/dodont).

## Dil ve üslup
- Türkçe, "siz" hitabı, sıcak, sohbet havasında, bir eğitmen konuşur gibi; kısa cümleler; soru sorup cevaplayan anlatım.
- Kısaltmaları olduğu gibi yaz (İSG, NACE, SGK, KKD, OSGB...); seslendirme motoru doğru okur. Sayılar rakamla yazılabilir.
- Madde/başlık metinleri ekranda görünür: kısa, net, noktasız.
- Ekranda görünen metin ile anlatım uyumlu olsun.

## Doğruluk (kritik)
- İçerik 6331 sayılı Kanun ve ilgili yönetmeliklere %100 uygun olmalı. **Çalışanların İSG Eğitimleri Yönetmeliği: RG 02.04.2026 / 33212 (yeni)**; 2013 tarihli yönetmelik yürürlükten kalktı — ondan alıntı yapma.
  - Az tehlikeli: temel eğitim en az 8 ders saati, 3 yılda bir tekrar (en az 8 saat); tehlikeli 12 saat / 2 yıl; çok tehlikeli 16 saat / her yıl.
  - İşe başlama eğitimi: işe başlamadan önce, en az 2 ders saati, yüz yüze. Temel eğitim işe başladıktan sonra 3 ay içinde.
  - Eğitim süresi çalışma süresinden sayılır; maliyeti çalışana yansıtılamaz.
- Emin olmadığın her sayı, süre, oran, madde numarası için WebSearch/WebFetch ile resmi kaynaktan (mevzuat.gov.tr, resmigazete.gov.tr, csgb.gov.tr, saglik.gov.tr, SGK) doğrula. Doğrulayamazsan sayı vermeden genel ifade kullan. Uydurma yok.
- Kanun madde numarası vermek zorunda değilsin; veriyorsan doğru olsun.
- Dersin sonunda sorulan sorular `/home/claude/src/v1core/app/modules/lms/data/az8.json` içinde (`lessons[].q`, doğru cevap `a` indeksi). Dersin **mutlaka** bu soruların doğru cevaplarını açıkça anlatması gerekir.

## Fotoğraflar
- Orshot araçları: `mcp__Orshot__orshot_search_stock_media` ile ara (İngilizce anahtar kelime daha iyi sonuç verir), gerekiyorsa `mcp__Orshot__orshot_use_stock_media` ile kalıcı URL al. ToolSearch ile şemaları yükle: `select:mcp__Orshot__orshot_search_stock_media,mcp__Orshot__orshot_use_stock_media`.
- Kullanılacak URL biçimi: `https://images.unsplash.com/photo-<id>?w=2400` (cards/roles/dodont öğeleri için `?w=1200`). Başka kaynak kullanma.
- Konuyla doğrudan ilgili, yatay, kaliteli fotoğraflar seç. Tanınmış kişi, marka logosu belirgin, kan/yaralanma/şiddet içeren fotoğraf YOK. "Yanlış" örneklerde de grafik olmayan, temsilî görsel seç.
- Aynı fotoğrafı bir ders içinde en çok 2 kez, art arda olmayacak şekilde kullan.
- Fotoğraf aramasını verimli yap: ders başına 10–20 arama yeterli.
