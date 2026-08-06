# Bölüm 3 · Kullanıcı Belleği ve Bilgi Tabanları

> Agent'ların oturumlar arası kullanıcıları hatırlamasını ve harici bilgiye erişmesini sağlar. Kullanıcı bellek sistemlerini, temel RAG boru hatlarını ve düz metnin ötesindeki bilgi organizasyonu ve erişimini (yapılandırılmış indeksler, bilgi grafikleri vb.) kapsar.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter3.tr.md)

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| [user-memory](user-memory/) | ✅ | Uzun süreli bir kullanıcı bellek sistemi inşa eder; Agent'ın kullanıcı tercihlerini ve geçmiş etkileşimleri hatırlayıp kişiselleştirilmiş hizmet sunmasını sağlar. |
| [mem0](mem0/) · [memobase](memobase/) | ✅ | İki açık kaynak bellek çerçevesi mem0 ve Memobase'in her birini kullanarak bir kullanıcı belleği sürümü uygular; Deney 3-2 "Bellek Stratejisi Karşılaştırması" için karşılaştırmalı bir uygulama görevi görür, farklı bellek çözümleri arasında çıkarım biçimlerinin ve yanıt kalitesinin yatay karşılaştırmasını kolaylaştırır. |
| [log-sanitization](log-sanitization/) | ✅ | Yerel bir Ollama modeli kullanarak loglardaki sırları ve PII'yi tespit edip maskeleyen ve hata ayıklama değerini koruyan akıllı log sanitizasyonu. |
| [user-memory-evaluation](user-memory-evaluation/) | ✅ | Kullanıcı bellek sistemlerinin doğruluğunu, ilgililiğini ve etkinliğini sistematik olarak değerlendirir; birden çok test senaryosu ve değerlendirme metriği içerir. |
| [dense-embedding](dense-embedding/) | ✅ | Bir vektör benzerliği arama servisi inşa eder; ANNOY (ağaç tabanlı) ve HNSW (grafik tabanlı) yaklaşık en yakın komşu indeks algoritmalarını karşılaştırır. Farklı indeksleme stratejilerinin performans, bellek kullanımı ve güncelleme yeteneği açısından ödünleşimlerini gösterir. |
| [sparse-embedding](sparse-embedding/) | ✅ | BM25 algoritmasına dayalı bir seyrek vektör arama motorunu sıfırdan uygular. Arama motorunun iç işleyişini anlamak için zengin günlükleme ve görselleştirme arayüzleri sunar; terim frekansı ağırlık hesaplaması ve ters indeks ilkeleri dahil. |
| [retrieval-pipeline](retrieval-pipeline/) | ✅ | Yoğun erişim, seyrek erişim ve sinirsel yeniden sıralamayı birleştiren eksiksiz bir erişim boru hattı inşa eder. Özenle tasarlanmış test senaryolarıyla hibrit erişimin farklı senaryolardaki tamamlayıcı avantajlarını sistematik olarak gösterir. |
| [structured-index](structured-index/) | ✅ | İki yapılandırılmış indeksleme yöntemini—RAPTOR (özyinelemeli soyutlama ağacı) ve GraphRAG (bilgi grafiği)—uygular ve karşılaştırır. |
| [agentic-rag](agentic-rag/) | ✅ | Geleneksel Ajan-Olmayan RAG ile Agentic RAG arasındaki performans farklarını karşılaştırır. Bir Agent'ın ReAct örüntüsünü kullanarak yinelemeli bilgi erişimine öncülük etmesinin, karmaşık yargısal soru-cevaplarda yanıt kalitesini nasıl önemli ölçüde artırdığını gösterir. |
| [agentic-rag-for-user-memory](agentic-rag-for-user-memory/) | ✅ | Agentic RAG çerçevesini kullanıcı konuşma geçmişini yönetmek için uygular. Oturumlar arası bellek erişimini ele almak için çok turlu yinelemeli arama yeteneklerinden yararlanır; temel hatırlama ve oturumlar arası erişim yeteneklerini mümkün kılar. |
| [contextual-retrieval](contextual-retrieval/) | ✅ | Anthropic tarafından önerilen bağlamsal erişim tekniğini uygular. Metin parçaları için temel context içeren önek özetleri üreterek geleneksel parçalama yöntemlerinin bağlam kaybı sorununu giderir, erişim başarısızlık oranlarını %49-67 azaltır. |
| [contextual-retrieval-for-user-memory](contextual-retrieval-for-user-memory/) | ✅ | Bağlamsal erişim tekniklerini kullanıcı belleği oluşturmaya uygular. Gelişmiş JSON Kartlarını Bağlamsal RAG ile birleştirerek daha üst düzey proaktif hizmet yetenekleri sağlayan iki katmanlı bir bellek yapısı oluşturur. |
| [structured-knowledge-extraction](structured-knowledge-extraction/) | ✅ | Yargısal emsalleri örnek alarak üç aşamalı bir boru hattı uygular: "Aşağıdan yukarı faktör keşfi → Dava prototip kümeleme → Konuşma tabanlı danışman Agent". Önceden tanımlanmış katı alanlar olmadan, LLM çok sayıda davadan faktörleri özerk olarak keşfeder ve bunları modüler bir şemaya (temel faktörler + suça özgü genişleme faktörleri) özetler. Davalar daha sonra birkaç prototipe kümelenir ve her faktörün her prototip için önemi hesaplanır. Agent yeni dava gerçeklerini en benzer prototiple eşleştirir, faktör önemine göre eksik bilgiyi sorar ve kanıta dayalı tavsiye sunar (yasal sorumluluk reddiyle birlikte). |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
