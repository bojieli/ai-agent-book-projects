# Bölüm 6 · Etkileşim: Gözlem ve Eylem Uzaylarının Genişletilmesi

> Algı ve eylemi metinden sese, GUI'ye ve fiziksel dünyaya genişletir. Üç ses paradigması (aşamalı zincir/uçtan uca tam modlu/tam çift yönlü), akış tabanlı ses algısı ve sentezi, Computer Use ve robot manipülasyonu.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter6.tr.md)

## Deneyler nasıl okunur

Metin, kontrol akışını açıklamak için kısa mekanizma skeleton'ları kullanır; deney dizininde tam SDK adaptörleri, günlükler, testler ve kabul kanıtı bulunur. Her dosyayı satır satır okumanız gerekmez.

- **Starter:** Hedef, en kısa komut ve kabul koşullarıyla başlayın; önce [live-audio](live-audio/);
- **Builder:** Giriş noktasını, ana döngüyü, durum/mesaj şemasını, araçları ve doğrulayıcıyı izleyin.
- **Maintainer:** Son olarak testleri, kanıt manifestlerini, hata işlemeyi, rollback yollarını ve sağlayıcı adaptörlerini okuyun.

İlk okumada kimlik bilgisi yükleme, sunum katmanı ve sağlayıcı uyumluluğunu atlayıp sayıları yeniden üretirken dönün.

## Eşlik Eden Projeler

| Deney | Proje | Tür | Açıklama |
| :--: | --- | :--: | --- |
| 6-1 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | FastAPI ile inşa edilmiş modern bir olay güdümlü Agent; varsayılan olarak ilk üç MCP sunucusundaki tüm araçları entegre eder. Temiz MCP araç yüklemesi için yerel bir asenkron mimari kullanır ve HTTP API üzerinden çok kaynaklı olayları (Web, Anlık Mesajlaşma, GitHub, Zamanlayıcılar vb.) alır. Otomatik API dokümantasyonu (Swagger UI) ve arka plan izleme yetenekleri sunar. |
| 6-2 | [async-agent](async-agent/) | ✅ | Tek iş parçacıklı bir asyncio modeline dayalı, olay güdümlü asenkron bir Agent çerçevesinin (Flux) çekirdeğini uygular: bir gelen kutusu olay kuyruğu görevleri aciliyete göre (kesme/anında/kuyruk) dağıtır, asenkron araçların paralel yürütülmesini destekler, yürütme sırasında mevcut turun kesilmesine izin verir ve simüle edilmiş uzun süreli görevler için iptal ve durum sorgulama sağlar. Karar verme gerçek bir LLM (fonksiyon çağırma) tarafından yapılır. |
| 6-3 | [live-audio](live-audio/) | ✅ | Konuşmadan metne, AI diyaloğu ve metinden konuşmayı entegre eden gerçek zamanlı bir sesli sohbet demosu. Birden çok AI hizmet sağlayıcısını destekler (OpenAI, OpenRouter, ARK, Siliconflow), düşük gecikmeli bir konuşma deneyimi sunar. |
| Add-on | [phone-agent](phone-agent/) | 🚧 | Resmî `pine-voice` SDK direct/ReAct yolları uygulanmıştır; ancak yetkili ve onay vermiş bir E.164 hedefi yoktur. Preflight arama/transcript olmadığını kaydeder; test double kabul sayılmaz. |
| 6-4 | [streaming-speech](streaming-speech/) | ✅ | Akış tabanlı ses algısının temel ödünleşimini gösterir: sürekli sesi giderek uzayan segmentlere ayırır ve ASR'ye besler. Alınan her segment, erken metin çıktısı için son derece düşük ilk parça gecikmesi sağlamak üzere bir "mevcut kısmi tanıma sonucu" üretir. Bedeli, cümlenin ikinci yarısının bağlamından yoksun olan erken parçaların hatalı olabilmesi, ses biriktikçe kademeli olarak yakınsamasıdır. Bu, "tanımadan önce tüm cümleyi bekleme"nin yüksek doğruluk/yüksek gecikmeli yaklaşımıyla tezat oluşturur. |
| 6-5 | [end-to-end-speech](end-to-end-speech/) | ✅ | Sabit revision'lı MiniCPM-o 4.5 tek RTX PRO 6000 üzerinde gerçekten yerel çalıştırıldı; end-to-end ve self-cascade 3/4 elde etti, tamamlayıcı anlamsal/paralinguistik hatalar ile gerçek 24kHz ses ve kabul kanıtı saklandı. |
| 6-6 | [controllable-tts](controllable-tts/) | 🚧 | Gerçek Fish Audio S1 4×3×2 referans kütüphanesi ve A/B/C medya yapısal kapıları geçer; nitel dinleme çalışması ve “insana yakın” değerlendirme eksiktir. |
| 6-7 | `claude-quickstarts/computer-use-demo/` | 📖 | Harici `anthropics/claude-quickstarts` `9bcc95e…` commit'ine sabitlenmiştir; hedef tüm quickstarts değil, container içindeki Ubuntu desktop＋Claude agent loop Computer Use demosudur. |
| 6-8 | `browser-use/` | 📖 | Harici `browser-use/browser-use` `ec9277c…` commit'ine sabitlenmiştir; visual CLI (`use_vision=True`) Google'da San Francisco hava durumunu arar ve action/screenshot yörüngesini saklar. |
| 6-9 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | Gerçek XLeRobot teleoperasyonu ile aynı masa toplama görevi: kırmızı bardağı tepsiye, sarı kâğıdı çöp kutusuna koyup durumu yeniden doğrulama. |
| 6-10 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Simülatörde aynı görevin ideal kontrol üst sınırını ölçer; gerçek robotun çalıştırıldığı anlamına gelmez. |
| 6-11 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Gemini Robotics-ER 1.5 ile gerçek XLeRobot'u aynı masa toplama görevinde otonom olarak kontrol eder. |
| 6-12 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Simülatörde aynı görev için açık çevrim, adım adım kontrol ve öngörülü kapalı çevrim stratejilerini karşılaştırır. |
| 6-13 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | Arka planı, nesne görünümünü, ışığı ve görsel gürültüyü değiştirerek aynı görevde RGB ortamlar arası testi yapar. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Devam Ediyor** | Uygulama vardır; ancak gerekli canlı çalıştırma, yetki, donanım veya metin kabul kanıtı eksiktir |
