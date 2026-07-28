# Bölüm 5 · Coding Agent ve Kod Üretimi

> Kod, "yeni araçlar yaratabilen bir araçtır" ve genel amaçlı bir Agent'ın meta-yeteneğidir. Bu en güçlü genel aracın eksiksiz uygulamasını göstermek için üretim seviyesinde bir Coding Agent'ı örnek alır.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter5.tr.md)

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| [coding-agent](coding-agent/) | ✅ | Claude üzerine inşa edilmiş, komut satırı bağımlılığı olmadan tamamen saf Python ile uygulanmış üretim seviyesinde bir AI kodlama asistanı. Dosya işlemleri, arama, shell işlemleri ve proje yönetimini kapsayan 17 tam uygulanmış araç içerir. ripgrep'in işlevselliğiyle tamamen uyumlu saf bir Python Grep aracı içerir. |
| [code-for-math](code-for-math/) | ✅ | Aynı yarışma matematik problemleri kümesinde, aynı modeli kullanarak "saf düşünce zinciri" ile "kod destekli" modları karşılaştırır. İkinci modda problemler Python'a (sympy/numpy/scipy) formelleştirilir ve bir alt süreç sandbox'ında fonksiyon çağırma yoluyla yürütülür; hataya açık zihinsel hesaplamanın yerini kesin hesaplama alır, bu da doğruluğu önemli ölçüde artırır. |
| [code-for-logic](code-for-logic/) | ✅ | "Şövalyeler ve Serseriler" mantık bulmacalarını Kısıt Karşılama Problemlerine (CSP) dönüştürür. Agent, değişkenleri ve çift koşullu kısıtları tanımlamak için `python-constraint` kullanır, ardından çözücüyü çağırır. Bir dizi Şövalye-Serseri bulmacasında saf doğal dil muhakemesi ile kod destekli modların doğruluğunu karşılaştırır. |
| [small-model-codified-rules](small-model-codified-rules/) | ✅ | τ-bench havayolu müşteri hizmetleri senaryosuna dayalı kontrollü bir deney: karmaşık iş politikaları (iade kuralları) doğal dil promptlarından koda/araçlara taşındıktan sonra, küçük bir modelin görev başarı oranı ve politika uyumu çarpıcı biçimde iyileşir. Araç içi kod doğrulaması, modelin hatalı inançlarını gerçek zamanlı olarak yakalayabilir. |
| [paper-to-ppt](paper-to-ppt/) | ✅ | "PPT yapmayı" bir kod üretimi problemi olarak yeniden çerçeveler: Proposer, Slidev (Markdown+HTML) kodu yazar, Reviewer her sayfayı bir PNG'ye render eder ve yerleşim sorunlarını kontrol etmek için bir Görsel LLM kullanır, yapılandırılmış geri bildirime dayalı olarak revizyonları yineler. Bu ikili ajan iş bölümü, önemli ölçüde daha düşük bir zirve context boyutuyla sonuçlanır. |
| [paper-to-video](paper-to-video/) | ✅ | "Makale → PPT" üzerine inşa edilerek, her slayt için günlük dilde anlatım senaryoları üretir, TTS ile ses sentezler, ardından her slaytın ekran görüntüsünü sesiyle sayfa sayfa senkronize etmek için ffmpeg kullanarak anlatımlı bir açıklama videosu oluşturur. |
| [video-edit](video-edit/) | ✅ | Çok sahneli bir video ve doğal dil isteği verildiğinde, Agent hedef sahnenin zaman sınırlarını belirlemek için "iki adımlı Görsel konumlandırma" süreci (kabadan inceye kare çıkarma ve okuma) kullanır. Segmenti kestikten sonra Reviewer, doğrulama için ortaya çıkan klipten anahtar kareler çıkarır, sonuç tatmin edici değilse yineler. |
| [adaptive-log-parser](adaptive-log-parser/) | ✅ | Kendi kendine evrimleşen bir günlük ayrıştırma sistemi: ayrıştırılamayan yeni bir biçimle karşılaştığında hata vermez. Bunun yerine, başarısız örneği ve hata mesajını bir `parse` fonksiyonu üretmesi için bir kod üretim Agent'ına besler. Otomatik test geçtikten sonra fonksiyon sıcak güncellenir ve ayrıştırma motoruna kaydedilir; tüm süreç boyunca insan müdahalesi gerekmez. |
| [log-diagnosis](log-diagnosis/) | ✅ | Bir teşhis Agent'ı üretim iz günlüklerini, mimari belgelerini ve PRD'leri okur. Sorunları ve kök nedenleri otomatik olarak bulur, yapılandırılmış raporlar ve regresyon test senaryoları üretir, gerçek yürütme doğrulaması için bir tekrar oynatma çerçevesi kullanır ve MCP entegrasyonu üzerinden GitHub'da (simüle edilmiş) Issue'lar oluşturur. |
| [dynamic-form](dynamic-form/) | ✅ | Eksik bir istekle karşılaştığında Agent tek tek soru sormaz. Bunun yerine, kullanıcının eksik tüm bilgiyi tek seferde doldurmasına izin veren, basamaklı mantığa sahip kendi kendine yeten bir HTML formu dinamik olarak üretir. Ön uç, form verisini JSON'a toplayıp Agent'a geri döndürerek görevin devam etmesini sağlar. |
| [erp-agent](erp-agent/) | ✅ | Çince doğal dil sorgularını veritabanı yürütmesi için SQL'e çevirir, ortaya çıkan tabloyu doğrudan sunar. Çekirdek, artifact örüntüsüdür: LLM yalnızca SQL artifact'ını üretir, veriyi kendisi taşımaz; bu, token tasarrufu sağlar ve elle hesaplama hatalarını önler. On binlerce satırlık sonuç kümeleri bile anında döndürülebilir. |
| [conversational-ui](conversational-ui/) | ✅ | Kullanıcılar doğal dilde UI özelleştirme istekleri (renk/font/metin/yerleşim) önerir. Agent, React ön uç kaynak kodunu özerk olarak bulup değiştirir. Vite'ın Hot Module Replacement (HMR) özelliğinden yararlanarak değişiklikler anında etkili olur, çok turlu yinelemeli özelleştirmeyi destekler. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
