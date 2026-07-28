# Bölüm 9 · Çok Modluluk ve Gerçek Zamanlı Etkileşim

> Algı ve eylemi metinden sese, GUI'ye ve fiziksel dünyaya genişletir. Üç ses paradigması (aşamalı zincir/uçtan uca tam modlu/tam çift yönlü), akış tabanlı ses algısı ve sentezi, Computer Use ve robot manipülasyonu.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter9.tr.md)

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| [live-audio](live-audio/) | ✅ | Konuşmadan metne, AI diyaloğu ve metinden konuşmayı entegre eden gerçek zamanlı bir sesli sohbet demosu. Birden çok AI hizmet sağlayıcısını destekler (OpenAI, OpenRouter, ARK, Siliconflow), düşük gecikmeli bir konuşma deneyimi sunar. |
| `browser-use/` | 📖 | Browser-Use, LLM'lerin karmaşık görevleri tamamlamak için bir tarayıcıyı kontrol etmesini sağlayan güçlü bir tarayıcı otomasyon çerçevesidir. Form doldurma, web gezinme ve veri çıkarımı gibi senaryoları destekler; GUI otomasyonunun (Computer Use) tipik bir uygulaması olarak hizmet eder. |
| `claude-quickstarts/` | 📖 | Çeşitli kullanım senaryolarını kapsayan Claude API için hızlı başlangıç örnekleri ve en iyi uygulamalar. |
| [phone-agent](phone-agent/) | ✅ | "Kullanıcı adına telefon görüşmeleriyle dış dünyayla etkileşim kuran" bir sesli ajanı gösterir: üst katman standart bir ReAct ajanıdır. Doğal dil görevi aldığında aramanın sayısını ve amacını özerk olarak belirler, tüm konuşmayı tamamlamak için bir `make_phone_call` aracını (bir telefon API soyutlamasına dayalı) çağırır, yapılandırılmış arama günlüğünü okur, gerektiğinde başka bir arama yaparak takip soruları sorar ve sonunda kullanıcıya rapor verir. |
| [end-to-end-speech](end-to-end-speech/) | ✅ | Step-Audio R1'in uçtan uca ses düşüncesine ("dinle→düşün→konuş") karşılık gelir; gecikmeyi ve paralinguistik kaybı ASR→LLM→TTS zincirleme yaklaşımıyla karşılaştırır. |
| [streaming-speech](streaming-speech/) | ✅ | Akış tabanlı ses algısının temel ödünleşimini gösterir: sürekli sesi giderek uzayan segmentlere ayırır ve ASR'ye besler. Alınan her segment, erken metin çıktısı için son derece düşük ilk parça gecikmesi sağlamak üzere bir "mevcut kısmi tanıma sonucu" üretir. Bedeli, cümlenin ikinci yarısının bağlamından yoksun olan erken parçaların hatalı olabilmesi, ses biriktikçe kademeli olarak yakınsamasıdır. Bu, "tanımadan önce tüm cümleyi bekleme"nin yüksek doğruluk/yüksek gecikmeli yaklaşımıyla tezat oluşturur. |
| [controllable-tts](controllable-tts/) | ✅ | Ana LLM'in çıktısı kontrol tokenleri taşır (duygu/konuşma hızı/stil/duraklama/kahkaha). Yürütme katmanı bu tokenleri ayrıştırır, bunları bir referans konuşma kütüphanesindeki karşılık gelen stil profillerine eşler, ardından konuşmayı sentezler. Bu, "nerede duraklanacağı ve hangi tonun kullanılacağı" kararlarını LLM'e devreder, aynı metnin farklı stil ve duygularla sentezlenmesine olanak tanır. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
