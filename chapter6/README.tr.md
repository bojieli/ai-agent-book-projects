# Bölüm 6 · Agent Değerlendirmesi

> Agent performansını karşılaştırılabilir sinyallere dönüştürür. Değerlendirme ortamlarını, veri kümesi tasarımını, metrik sistemlerini, istatistiksel anlamlılığı, gözlemlenebilirliği, değerlendirme odaklı seçimi ve üretim seviyesinde dahili değerlendirme ile simülasyon ortamlarını kapsar.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter6.tr.md)

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| `terminal-bench/` | 📖 | Terminal-Bench, gerçek terminal ortamlarında AI Agent performansını test etmek için bir kıstastır. Kod derlemekten model eğitmeye ve sunucu kurmaya kadar, Agent'ların gerçek uçtan uca görevleri nasıl ele aldığını değerlendirir. ~100 görevlik bir veri kümesi ve çeşitli Agent uygulamalarını destekleyen bir yürütme çerçevesi içerir. |
| `SWE-bench/` | 📖 | SWE-bench, büyük dil modellerinin gerçek GitHub issue'larını çözme yeteneğini değerlendirmek için bir kıstastır. Bir kod tabanı ve issue açıklaması verildiğinde model, sorunu çözen bir yama üretmelidir. SWE-bench, SWE-bench Lite, SWE-bench Verified ve SWE-bench Multimodal dahil birden çok sürüm içerir. |
| `GAIA/` | 📖 | GAIA, yeni nesil LLM'leri (araç genişletmeli, verimli promptlamalı, arama erişimli vb.) değerlendirmeyi amaçlar. Farklı derecelerde araç kullanımı ve özerklik gerektiren, belirsiz olmayan yanıtlara sahip 450'den fazla önemsiz olmayan soru içerir. 3 zorluk seviyesine ayrılmıştır. |
| `OSWorld/` | 📖 | Ajanların dosya yönetimi, uygulama işletme ve sistem yapılandırması dahil, eksiksiz bir işletim sistemi ortamı içinde karmaşık görevleri yerine getirme yeteneğini değerlendirir. |
| `android_world/` (6-2, 6-12) | 📖 | Ajan performansını bir Android mobil ortamında değerlendirir; uygulama gezinme, UI etkileşimi ve görev tamamlama yeteneklerini kapsar. |
| `tau2-bench/` (6-1) | 📖 | Bir ajanın hesaplama, arama ve veri işleme gibi senaryolar dahil, karmaşık muhakeme için araç kullanma yeteneğini değerlendirmeye odaklanır. |
| `tau2-bench/` (6-2) | 📖 | Derecelendirilmiş τ²-bench görevlerini elle tamamlar ve yörüngeleri kaydeder. |
| [user-memory-evaluation](../chapter3/user-memory-evaluation/) (6-3) | ✅ | Dört seviyeli rubric'i kanıt ve halüsinasyon vetosuyla 180 yapılandırılmış değerlendirmede çalıştırır. |
| [user-memory-system-evaluation](user-memory-system-evaluation/) (6-4) | ✅ | Tam maliyet muhasebesiyle üç sistem üzerinde 60 vakayı çalıştırır. |
| [user-memory-policy-eval](user-memory-policy-eval/) (6-5) | ✅ | JSON, Markdown ve Python benzeri bellek gösterimlerinde 11 hatalı yörünge öneki vakasını gerçek OpenRouter çağrıları ve belirlenimci politika kontrolleriyle çalıştırır. |
| [user-memory-system-evaluation](user-memory-system-evaluation/) (6-11) | ✅ | Tam 4×3×2×60 matrisinde 1.440/1.440 gerçek yörüngeyi hata veya fiyatlandırılmamış kullanım olmadan korur; erişim/görev metrikleri, etkileşim analizi ve bağımsız doğrulama tamamlanmıştır. |
| [openvla-robotwin2-eval](openvla-robotwin2-eval/) (6-13) | ✅ | Tek GPU'lu resmi çalışma kol başına 256 episode tamamladı; chunk 1 0/256, chunk 25 26/256 aldı ve 512 rollout hash'i saklandı. |
| [elo-leaderboard](elo-leaderboard/) (6-7) | ✅ | ELO derecelendirme sistemine dayalı bir ajan performansı liderlik tablosu uygular; ikili karşılaştırmalarla farklı ajanların göreli yeteneklerini değerlendirir. |
| [model-action-threshold](model-action-threshold/) (6-8) | ✅ | Aynı tarafsız Coding Harness altında GPT-5.6-sol ile Claude Sonnet 5'in keşiften ilk düzenlemeye geçiş eşiğini karşılaştırır; 18/18 hücre API hatası olmadan tamamlanmış, [manifest](model-action-threshold/results/exp6-7-action-threshold-20260731-v1/manifest.json) ise yürütme izleriyle özetleri doğrulanabilir hash'lerle bağlamıştır. |
| [model-benchmark](model-benchmark/) (6-10) | 🚧 | Birden çok OpenAI uyumlu LLM API sağlayıcısının yatay bir kıstasını yapar. İlk Token Süresini (TTFT) hassas biçimde ölçmek için bir akış arayüzü kullanır, eşzamanlılık altında uçtan uca gecikme yüzdeliklerini (p50/p95), verimi ve başarı oranını hesaplar. Tek bir komut, model seçiminin yalnızca bir liderlik tablosuna bakmaktan ibaret olmadığını, çok yönlü bir ödünleşim olduğunu gösteren çok boyutlu bir karşılaştırma tablosu üretir. |
| [agent-cost-analysis](agent-cost-analysis/) (6-9) | ✅ | Tipik çok turlu bir ajan görevi (müşteri hizmetleri iadesi) için tam zincir maliyet analizi yapar: her LLM çağrısı için girdi/çıktı/önbellek token'larını, gecikmeyi ve maliyeti kaydetmek için özel hafif bir izleme sistemi kullanır, "hangi adımın en pahalı olduğunu" belirlemek için toplar, ardından KV-cache dostu tasarım ve context sıkıştırmadan elde edilen gerçek tasarrufları nicelleştirmek için A/B testi kullanır. |
| [tts-quality-eval](tts-quality-eval/) (6-6) | ✅ | Aynı zorlu metin kümesini çeşitli TTS yapılandırmalarıyla (farklı model/ses/hız) sentezler, ardından her boyutu (netlik, doğallık vb.) bir Rubric'e göre puanlamak için çok modlu bir LLM-as-a-Judge kullanır, sonuçları yeniden üretilebilir bir yapılandırma karşılaştırma tablosunda toplar. |
| [android-world](android-world/) (6-12) | 📖 | AndroidWorld üzerinde T3A Agent değerlendirmesi ve başarısızlık analizi için başlangıç raporu; kıstasın kaynak kodu yerine Deney 6-12'nin uygulama notlarını içerir. |
| [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | Sentetik DHIS2 tarzı özet veriler üzerinde bir halk sağlığı raporlama Agent'ının araç çağrılarını, hesaplama doğruluğunu, kanıt kullanımını ve dayanaksız iddialarını nesnel olarak değerlendirir. |

> `chapter6/android-world/` (tire ile yazılan) kıstas kodu değil, bilakis kitabın android_world üzerindeki T3A Agent başarısızlık vakaları hakkındaki analiz notlarıdır (`t3a*.md`); referans okuma materyali olarak kullanılabilir.

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
