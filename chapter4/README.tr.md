# Bölüm 4 · Araçlar

> Araçlar bir Agent'ın elleridir. Araç sınıflandırması ve genel tasarım ilkelerini, MCP protokolünü ve araç seçimi zorluklarını, üç tür aracı (algı, yürütme, işbirliği) ve olay güdümlü asenkron Agent'ları ele alır.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter4.tr.md)

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| [perception-tools](perception-tools/) | ✅ | Web araması, çok modlu anlama, dosya sistemi işlemleri ve kamuya açık veri kaynaklarına erişim yetenekleri sunan kapsamlı bir algı aracı seti inşa eder. Çoğu özellik ücretsiz, açık API'lere dayanır (DuckDuckGo, Open-Meteo, Yahoo Finance, OpenStreetMap vb.) ve API anahtarı gerektirmez. |
| [multimodal-agent](multimodal-agent/) | ✅ | Çok modlu işleme: yerel çok modlu, metne çıkarım ve araç tabanlı analizi karşılaştırır. |
| [execution-tools](execution-tools/) | ✅ | Dosya işlemleri, bir kod yorumlayıcı, sanal terminal ve harici sistem entegrasyonu dahil, güvenlik mekanizmalarına sahip bir yürütme aracı seti uygular. İkincil bir LLM onay mekanizmasıyla tehlikeli işlemleri önler, karmaşık çıktıları otomatik özetler ve kod üzerinde sözdizimi doğrulaması yapar. |
| [collaboration-tools](collaboration-tools/) | ✅ | Tarayıcı otomasyonu (browser-use çerçevesi), İnsan-Döngüde (Human-in-the-Loop), çok kanallı bildirimler (E-posta, Telegram, Slack, Discord) ve zamanlayıcı yönetimi dahil kapsamlı işbirliği yetenekleri sunar. Hassas işlemler için yönetici onayını ve zamanlanmış görev dağıtımını destekler. |
| [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | FastAPI ile inşa edilmiş modern bir olay güdümlü Agent; varsayılan olarak ilk üç MCP sunucusundaki tüm araçları entegre eder. Temiz MCP araç yüklemesi için yerel bir asenkron mimari kullanır ve HTTP API üzerinden çok kaynaklı olayları (Web, Anlık Mesajlaşma, GitHub, Zamanlayıcılar vb.) alır. Otomatik API dokümantasyonu (Swagger UI) ve arka plan izleme yetenekleri sunar. |
| [active-tool-selection](active-tool-selection/) | ✅ | Agent'ın önceden tanımlanmış bir araç kümesini pasif olarak kabul etmek yerine, görev gereksinimlerine göre en uygun araç kombinasyonunu aktif olarak seçmesini sağlayan akıllı bir araç seçim mekanizması uygular. |
| [active-tool-discovery](active-tool-discovery/) | ✅ | İki paradigmayı karşılaştırır: "120+ araç şemasının tümünü enjekte etmek" ile "aktif, istendiğinde keşif." İkincisi, sistem isteminde yalnızca birkaç temel araç ve bir `discover_tools` meta-aracını tutar; bir araç kütüphanesinden en ilgili 3-5 uzman aracı getirmek için gömme benzerliğini kullanır. Bu, token tasarrufu sağlar ve modelin aşırı uzun bir listeden yanlış araç seçmesini veya yanlış kullanmasını önler. |
| [async-agent](async-agent/) | ✅ | Tek iş parçacıklı bir asyncio modeline dayalı, olay güdümlü asenkron bir Agent çerçevesinin (Flux) çekirdeğini uygular: bir gelen kutusu olay kuyruğu görevleri aciliyete göre (kesme/anında/kuyruk) dağıtır, asenkron araçların paralel yürütülmesini destekler, yürütme sırasında mevcut turun kesilmesine izin verir ve simüle edilmiş uzun süreli görevler için iptal ve durum sorgulama sağlar. Karar verme gerçek bir LLM (fonksiyon çağırma) tarafından yapılır. |

> Ayrıca, `chapter4/docker-compose.yml` ve `chapter4/DOCKER_DEPLOYMENT.md`, yukarıdaki MCP araç sunucularını konteynerleştirme ve dağıtma için bir referans çözüm sunar.

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
