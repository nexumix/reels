# Online Temel İSG Eğitimi — TEHLİKELİ / ÇOK TEHLİKELİ — ders senaryosu yazım kılavuzu

Bu kılavuz `lessons/SPEC.md`'nin (az tehlikeli) üzerine yazılır: sahne türleri, sınırlar, fotoğraf kuralları, dil/üslup, doğruluk kuralları AYNEN geçerlidir. ÖNCE `lessons/SPEC.md` dosyasını oku; biçim örneği için `lessons/az8_g1.json`'a bak. Aşağıdakiler farklıdır:

## Çıktı
- Ders: `lessons/tc_<kod>.json` (örn. `lessons/tc_g3.json`). Doğrulama: `python3 tools/lesson_check.py lessons/tc_<kod>.json` HATASIZ geçmeli.
- Sorular: `/home/claude/work/tcq/<kod>.json` → `[{"q": "...", "o": ["A","B","C","D"], "a": <doğru şık indeksi 0-3>}, ...]` TAM 3 soru, 4'er şık, tek doğru, ders içinde açıkça anlatılan bilgiden. Şık uzunlukları dengeli olsun (doğru şık hep en uzun olmasın), doğru şık yerleri karışık olsun.
- Git commit/push YAPMA.

## Üst alanlar
`"code": "tc_<kod>"`, `"course": "Temel İSG Eğitimi · Tehlikeli ve Çok Tehlikeli"`, section: `1. Bölüm · Genel Konular` (g), `2. Bölüm · Sağlık Konuları` (s), `3. Bölüm · Teknik Konular` (t). voice az8 ile aynı. cover kicker: "1. Bölüm · Ders 3" gibi (kod numarası).

## Süre
Her ders 1350 sn (yarım ders saati değil; 22,5 dk video). `steps` toplam kelime **en az 2810, en çok ~3000**.

## Kitle ve örnekler
- Kitle: TEHLİKELİ ve ÇOK TEHLİKELİ sınıftaki işyerlerinin çalışanları: inşaat ve yapı işleri, metal ve makine imalatı, kaynak atölyeleri, fabrika/üretim hatları, depo-lojistik ve forklift, kimya/boya, gıda üretimi, plastik, mobilya-ahşap, otomotiv servis, temizlik ve bakım, enerji/elektrik bakım işleri.
- Örnek olaylar bu işyerlerinden olsun (ofis/mağaza değil). Gerçekçi ama grafik olmayan anlatım; kişi adı uydurulabilir (Ahmet usta, vardiya amiri Selin gibi), firma adı yok.
- Tehlikeli/çok tehlikeli sınıfa özgü kurallar: temel eğitim tehlikelide en az 12 ders saati ve 2 yılda bir, çok tehlikelide en az 16 ders saati ve yılda bir; 4. başlık (işe ve işyerine özgü riskler) bu sınıflarda YÜZ YÜZE verilir (bu online eğitimde 4. başlık yoktur; derste "işyerinize özgü riskleri yüz yüze eğitimde uzmanınızla konuşacaksınız" diye bağlantı kurulabilir). Tehlikeli/çok tehlikeli işlerde mesleki eğitim belgesi zorunluluğu (Tehlikeli ve Çok Tehlikeli Sınıfta Yer Alan İşlerde Çalıştırılacakların Mesleki Eğitimlerine Dair Yönetmelik) ve MYK belgesi zorunlu meslekler gibi konular ilgili derslerde geçebilir; sayı/tarih vermeden önce doğrula.
- az8 derslerini KOPYALAMA; kendi özgün metnini yaz (aynı konu olsa bile derinlik ve örnekler farklı).

## Ders akışı
SPEC.md ile aynı (cover, yol haritası, içerik, en az 2 örnek olay, ara özet, kapanış özeti, "dersin sonunda kısa sorular" kapanışı). ~28–38 sahne, en az %65 fotoğraflı.
