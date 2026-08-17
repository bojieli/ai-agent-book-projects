# Bölüm 9 · Agent'ın Sürekli Evrimi

> İşletim yörüngelerini; bilgiyi, talimatları, programları ve parametreleri doğrulanabilir ve geri alınabilir bir döngüde güncelleyen güvenilir öğrenme sinyallerine dönüştürür.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter9.tr.md)

## Deneyler nasıl okunur

Metin, kontrol akışını açıklamak için kısa mekanizma skeleton'ları kullanır; deney dizininde tam SDK adaptörleri, günlükler, testler ve kabul kanıtı bulunur. Her dosyayı satır satır okumanız gerekmez.

- **Starter:** Hedef, en kısa komut ve kabul koşullarıyla başlayın; önce [trajectory-verifier](trajectory-verifier/);
- **Builder:** Giriş noktasını, ana döngüyü, durum/mesaj şemasını, araçları ve doğrulayıcıyı izleyin.
- **Maintainer:** Son olarak testleri, kanıt manifestlerini, hata işlemeyi, rollback yollarını ve sağlayıcı adaptörlerini okuyun.

İlk okumada kimlik bilgisi yükleme, sunum katmanı ve sağlayıcı uyumluluğunu atlayıp sayıları yeniden üretirken dönün.

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| [trajectory-verifier](trajectory-verifier/) (9-1) | ✅ | Ortam sonuçlarını, süreç kurallarını ve dil rubric'lerini kanıta dayalı yörünge teşhisinde birleştirir. |
| [gaia-experience](gaia-experience/) (9-2) | ✅ | Başarılı, kısmen başarılı ve başarısız yörüngeleri karşılaştırarak görevler arası deneyim belgeleri üretir. |
| [prompt-auto-optimization](prompt-auto-optimization/) (9-3) | ✅ | Başarısız yörüngelerden en küçük prompt düzeltmesini üretir ve sınır ile koruma kümeleri üzerinden yayını denetler. |
| **Metin deneyi** (9-4) | 🚧 | Kullanıcı geri bildiriminden gereksinim açıklama ve Spec onaylama Skill'ini üç kollu A/B tasarımı ve yayın kapılarıyla geliştirir. |
| [browser-use-rpa](browser-use-rpa/) (9-5) | ✅ | Tarayıcı yörüngelerini durum koşullu iş akışlarına derler; sıfırlama ve yeniden oynatmayla doğrular. |
| [self-modifying-agent](self-modifying-agent/) (9-6) | ✅ | Yinelenen arızalardan kod düzeltmesi üretir; regresyon, canary yayın ve rollback kapılarından geçirir. |
| [harness-safety-gate](harness-safety-gate/) (9-7) | ✅ | Kullanıcı düzeltmelerinden yüksek riskli işlemler için doğrulanabilir bir onay kapısı geliştirir. |
| [hermes-self-evolution](hermes-self-evolution/) (9-8) | 📖 | Hermes'e kitabın tamamını ve kendi kaynağını verir; bir iyileştirme seçip kendini değiştirir ve her Reviewer reddini kabul edilene kadar yeni bir öğrenme turuna dönüştürür. |
| [self-evolution-eval](self-evolution-eval/) (9-9) | ✅ | Öğrenme, aktarım, kural değişimi ve korumayı kapsayan uzun vadeli üç kollu değerlendirmeyi 3 seed × 14 sıralı görevle yürütür. |

## Tamamlayıcı Örnekler

| Proje | İlişki |
| --- | --- |
| [prompt-distillation](../chapter8/prompt-distillation/) (8-8) | Prompt damıtma ve parametreli öğrenme için Bölüm 8'e ait çapraz bölüm projesi. |
| [self-evolving-tools](self-evolving-tools/) | Deneyimi programlara yazmak için Alita tarzı araç keşfi, paketleme ve yeniden kullanım örneği. |
| [ai-style-skill](ai-style-skill/) | Ana örneği Bölüm 2'de yer alan tamamlayıcı yazma Skill'i örneği. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
