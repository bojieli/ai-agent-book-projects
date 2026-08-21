# Bölüm 1 · Agent Temelleri

> "Ajan Olarak Model" yeni paradigmasından başlayarak **Agent = LLM + Context + Tools** temel formülünü kurar ve Harness mühendisliğini tanıtır—modelin ötesindeki tüm mühendislik yetenekleri gerçek rekabet avantajıdır.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter1.tr.md)

## Deneyler nasıl okunur

Metin, kontrol akışını açıklamak için kısa mekanizma skeleton'ları kullanır; deney dizininde tam SDK adaptörleri, günlükler, testler ve kabul kanıtı bulunur. Her dosyayı satır satır okumanız gerekmez.

- **Starter:** Hedef, en kısa komut ve kabul koşullarıyla başlayın; önce [context](context/);
- **Builder:** Giriş noktasını, ana döngüyü, durum/mesaj şemasını, araçları ve doğrulayıcıyı izleyin.
- **Maintainer:** Son olarak testleri, kanıt manifestlerini, hata işlemeyi, rollback yollarını ve sağlayıcı adaptörlerini okuyun.

İlk okumada kimlik bilgisi yükleme, sunum katmanı ve sağlayıcı uyumluluğunu atlayıp sayıları yeniden üretirken dönün.

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| [learning-from-experience](learning-from-experience/) | ✅ | Geleneksel pekiştirmeli öğrenmeyi (Q-learning) LLM tabanlı bağlam içi öğrenmeyle karşılaştırır, Shunyu Yao'nun "The Second Half" blog yazısındaki temel içgörüleri yeniden üretir. Bir hazine avı oyunu üzerinden LLM'lerin geleneksel RL'yi 250-400 kat örnek verimliliğiyle nasıl geçebildiğini gösterir. |
| [web-search-agent](web-search-agent/) | ✅ | Temel derin arama yeteneklerine sahip, çok turlu arama ve bilgi entegrasyonu yapabilen bir Agent uygular. |
| [search-codegen](search-codegen/) | ✅ | Temel derin arama ve kod sandbox yeteneklerine sahip bir Agent inşa eder; karmaşık analiz için web araması ve kod yürütme gibi araçları kullanır. |
| [image-gen-workflow](image-gen-workflow/) | ✅ | Somut/geniş iki istek türü × workflow (kimi-k3 yeniden yazımı + Tongyi Wanxiang) ile yerli (Gemini / GPT-Image 2) çift rotanın gerçek karşılaştırması: somut isteklerde yerli rota daha sadık (poster metni yeniden yazım düğümü tarafından negatif prompt'a atıldı), geniş isteklerde yeniden yazımın sahne somutlaştırması hayal gücü katıyor, ama GPT-Image 2 kendi başına görüş üretebiliyor—uyarlama katmanının model tarafından içselleştirildiğinin ampirik kanıtı. |
| [context](context/) | ✅ | Sistematik ablasyon deneyleriyle çeşitli Agent context bileşenlerinin önemini gösterir. Birden çok LLM sağlayıcısını destekler (SiliconFlow Qwen, ByteDance Doubao, Moonshot Kimi), farklı context modlarını yapılandırıp Agent davranışındaki değişimleri gözlemlemeye olanak tanır. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
