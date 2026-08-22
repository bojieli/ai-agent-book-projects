# Bölüm 9 · Agent'ın Kendi Kendine Evrimi

> Ağırlıkları değiştirmeden büyüme. Üç öğrenme paradigması, deneyimden öğrenme ve "araç kullanıcısından" "araç yaratıcısına" giden yolculuk; Agent'ların "akıllı"dan "usta"ya ilerlemesini sağlar.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter9.tr.md)

## Deneyler nasıl okunur

Metin, kontrol akışını açıklamak için kısa mekanizma skeleton'ları kullanır; deney dizininde tam SDK adaptörleri, günlükler, testler ve kabul kanıtı bulunur. Her dosyayı satır satır okumanız gerekmez.

- **Starter:** Hedef, en kısa komut ve kabul koşullarıyla başlayın; önce [trajectory-verifier](trajectory-verifier/);
- **Builder:** Giriş noktasını, ana döngüyü, durum/mesaj şemasını, araçları ve doğrulayıcıyı izleyin.
- **Maintainer:** Son olarak testleri, kanıt manifestlerini, hata işlemeyi, rollback yollarını ve sağlayıcı adaptörlerini okuyun.

İlk okumada kimlik bilgisi yükleme, sunum katmanı ve sağlayıcı uyumluluğunu atlayıp sayıları yeniden üretirken dönün.

## Eşlik Eden Projeler

| Deney | Proje | Tür | Açıklama |
| :--: | --- | :--: | --- |
| 9-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | Deney 9-1: ortam sonuçlarını, süreç kurallarını ve dil rubriklerini, müşteri hizmetleri izlencelerine ilişkin kanıta dayalı tanılarda birleştirir. |
| 9-2 | [gaia-experience](gaia-experience/) | ✅ | AWorld çerçevesi ve GAIA kıstasına dayalı olarak eksiksiz bir "öğren-uygula" döngüsü uygular. Ajan, başarılı görev izlencelerini otomatik olarak yapılandırılmış deneyimlere özetler ve bunları yeni görevlerde getirip uygulayarak kendi kendine evrim gerçekleştirir. |
| 9-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | İnsan geri bildirimine dayalı otomatik sistem istemi öğrenimi: tau-bench tarzı havayolu müşteri hizmetleri "aşırı aktarma" sorununu örnek alarak, bir Coding Agent sistem istem dosyasını okur, sorunlu kuralları belirler, kesin değişiklikler üretir ve istem dosyasını gerçekten yeniden yazar. Ardından değişiklikleri yeniden değerlendirir, "geri bildirim → yeniden yazma → doğrulama" döngüsü oluşturur. |
| 9-4 | Metin içi deney | 🚧 | Deney 9-4: kullanıcı geri bildiriminden "gereksinim netleştirme + Spec onayı" Skill'i geliştirir; metin üç kollu A/B tasarımını, metrikleri ve yayın kapılarını verir, eşlik eden uygulama henüz eklenmemiştir. |
| 9-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | Tarayıcı otomasyonu için bir iş akışı kayıt sistemi uygular; tekrarlanan işlem dizilerini otomatik olarak parametreli araçlara kapsüller. Pahalı LLM çıkarımından kesin otomatik yürütmeye geçerek 3-5 kat hız artışı sağlar. |
| 9-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | Deney 9-6: yinelenen hatalar yeniden deneme/devre kesici kod yamalarını tetikler; ardından regresyon testleri, canary yayını ve geri alma gelir. |
| 9-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | Yüksek riskli işlemler için onay kapısı. |
| 9-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Deney 9-8: Hermes'e kitabın tamamını ve kendi kaynağını verir; bir iyileştirme seçip kendini değiştirir ve her Reviewer reddini kabul edilene kadar yeni bir öğrenme turuna dönüştürür. |
| 9-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | Deney 9-9: öğrenme, aktarım, kural değişimi ve korumayı kapsayan uzun vadeli üç kollu değerlendirme; 3 seed × 14 sıralı görev boyunca 126 gerçek çağrının kanıtını saklar. |

Yukarıdaki tüm deneyler API Key gerektirmeyen çevrimdışı giriş noktaları ve birim testleri sunar; gerçek model veya tarayıcı gerektiren genişletme yolları her projenin README dosyasında belgelenmiştir.

## Tamamlayıcı Örnekler

| Deney | Proje | İlişki |
| :--: | --- | --- |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | Prompt damıtma ve parametreli öğrenmenin bölümler arası projesi; eğitim yöntemi 8. bölüme aittir |
| — | [self-evolving-tools](self-evolving-tools/) | Alita tarzı araç keşfi, kapsülleme ve yeniden kullanım — "deneyimi programa yazmanın" tamamlayıcı örneği |
| — | [ai-style-skill](ai-style-skill/) | Yazım geri bildirimini doğrulanabilir Skill'e dönüştürür; bölüm, kıvrımlı tırnak Skill'ini denetlenmiş sentetik veri ve sonradan eğitimle ilişkilendirir, exact-copy tokenizer/Harness hatalarını ayırır. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
