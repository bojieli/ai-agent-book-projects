# Bölüm 9 · Çok Modluluk ve Gerçek Zamanlı Etkileşim

> Algı ve eylemi metinden sese, GUI'ye ve fiziksel dünyaya genişletir. Üç ses paradigması (aşamalı zincir/uçtan uca tam modlu/tam çift yönlü), akış tabanlı ses algısı ve sentezi, Computer Use ve robot manipülasyonu.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter9.tr.md)

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| [live-audio](live-audio/) | ✅ | Konuşmadan metne, AI diyaloğu ve metinden konuşmayı entegre eden gerçek zamanlı bir sesli sohbet demosu. Birden çok AI hizmet sağlayıcısını destekler (OpenAI, OpenRouter, ARK, Siliconflow), düşük gecikmeli bir konuşma deneyimi sunar. |
| `browser-use/` | 📖 | Harici `browser-use/browser-use` `ec9277c…` commit'ine sabitlenmiştir; visual CLI (`use_vision=True`) Google'da San Francisco hava durumunu arar ve action/screenshot yörüngesini saklar. |
| `claude-quickstarts/computer-use-demo/` | 📖 | Harici `anthropics/claude-quickstarts` `9bcc95e…` commit'ine sabitlenmiştir; hedef tüm quickstarts değil, container içindeki Ubuntu desktop＋Claude agent loop Computer Use demosudur. |
| [phone-agent](phone-agent/) | 🚧 | Resmî `pine-voice` SDK direct/ReAct yolları uygulanmıştır; ancak yetkili ve onay vermiş bir E.164 hedefi yoktur. Preflight arama/transcript olmadığını kaydeder; test double kabul sayılmaz. |
| [end-to-end-speech](end-to-end-speech/) | ✅ | Sabit revision'lı MiniCPM-o 4.5 tek RTX PRO 6000 üzerinde gerçekten yerel çalıştırıldı; end-to-end ve self-cascade 3/4 elde etti, tamamlayıcı anlamsal/paralinguistik hatalar ile gerçek 24kHz ses ve kabul kanıtı saklandı. |
| [streaming-speech](streaming-speech/) | ✅ | Akış tabanlı ses algısının temel ödünleşimini gösterir: sürekli sesi giderek uzayan segmentlere ayırır ve ASR'ye besler. Alınan her segment, erken metin çıktısı için son derece düşük ilk parça gecikmesi sağlamak üzere bir "mevcut kısmi tanıma sonucu" üretir. Bedeli, cümlenin ikinci yarısının bağlamından yoksun olan erken parçaların hatalı olabilmesi, ses biriktikçe kademeli olarak yakınsamasıdır. Bu, "tanımadan önce tüm cümleyi bekleme"nin yüksek doğruluk/yüksek gecikmeli yaklaşımıyla tezat oluşturur. |
| [controllable-tts](controllable-tts/) | 🚧 | Gerçek Fish Audio S1 4×3×2 referans kütüphanesi ve A/B/C medya yapısal kapıları geçer; nitel dinleme çalışması ve “insana yakın” değerlendirme eksiktir. |
| [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | Harici XLeRobot `3d14695…`, keyboard/Xbox/Joy-Con/VR teleoperation. Yalnız source/non-actuating preflight vardır; yetkili dört-mod donanım ve pick/place/wipe kanıtı yoktur. |
| [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Harici XLeRobot `3d14695…`＋RoboCrew; tam `gemini-robotics-er-1.5-preview`, angle annotation ve forward/left/right tools. Yetkili robot navigation çalışması yoktur. |
| [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | Harici `lerobot-sim2real` `87d6c1d…`, beş aşamalı RGB→PPO→SO-100 pipeline. Makinede ManiSkill/NVIDIA ve yetkili fiziksel robot çalışması yoktur. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Devam Ediyor** | Uygulama vardır; ancak gerekli canlı çalıştırma, yetki, donanım veya metin kabul kanıtı eksiktir |
