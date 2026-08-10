# Bölüm 2 · Bağlam Mühendisliği

> Context, Agent yeteneklerinin üst sınırını belirler. LLM API'lerinin context yapısına, KV Cache dostu tasarıma, prompt mühendisliğine, dinamik promptlara ve Agent Skills'e, durum çubuğu meta-bilgisine ve context sıkıştırma stratejilerine iner.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter2.tr.md)

## Deneyler nasıl okunur

Metin, kontrol akışını açıklamak için kısa mekanizma skeleton'ları kullanır; deney dizininde tam SDK adaptörleri, günlükler, testler ve kabul kanıtı bulunur. Her dosyayı satır satır okumanız gerekmez.

- **Starter:** Hedef, en kısa komut ve kabul koşullarıyla başlayın; önce [context-compression](context-compression/);
- **Builder:** Giriş noktasını, ana döngüyü, durum/mesaj şemasını, araçları ve doğrulayıcıyı izleyin.
- **Maintainer:** Son olarak testleri, kanıt manifestlerini, hata işlemeyi, rollback yollarını ve sağlayıcı adaptörlerini okuyun.

İlk okumada kimlik bilgisi yükleme, sunum katmanı ve sağlayıcı uyumluluğunu atlayıp sayıları yeniden üretirken dönün.

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| [local_llm_serving](local_llm_serving/) | ✅ | En iyi arka ucu (vLLM veya Ollama) otomatik seçen platformlar arası yerel LLM dağıtım çözümü. İyi sistem tasarımıyla 0,6B'lik küçük bir modelin bile mükemmel araç çağırma yeteneği gösterebildiğini kanıtlar. Düşünce sürecinin gerçek zamanlı gösterimi için akış (streaming) yanıtları destekler. |
| [attention_visualization](attention_visualization/) | ✅ | Bir LLM'in tam girdi/çıktı token dizisini ve dikkat ağırlığı dağılımını görselleştirir; modelin context'i nasıl işlediğine, muhakeme yaptığına ve araç çağırdığına derinlemesine bir bakış sunar. |
| [kv-cache](kv-cache/) | ✅ | Farklı context yönetimi modlarının KV Cache üzerindeki etkisini araştırır, yaygın hata örüntülerinin önbellek verimliliğini nasıl bozduğunu gösterir. Uygun context tasarımının gecikme ve maliyeti nasıl önemli ölçüde azaltabileceğini deneylerle gösterir. |
| [context-compression](context-compression/) | ✅ | Özetleme, anahtar bilgi çıkarımı ve anlamsal sıkıştırma dahil birden çok context sıkıştırma stratejisini uygular ve karşılaştırır. Agent yeteneklerini korurken token kullanımını azaltır. |
| [prompt-engineering](prompt-engineering/) | ✅ | Tau-Bench çerçevesini genişleterek, sistematik ablasyon deneyleriyle farklı prompt mühendisliği faktörlerinin Agent performansı üzerindeki etkisini nicelleştirir. Ton, talimat organizasyonu ve araç açıklamaları gibi faktörlerin görev tamamlama oranlarını nasıl etkilediğini gösterir. |
| [system-hint](system-hint/) | ✅ | System Hint'lerin (sistem ipuçlarının) Agent davranışı üzerindeki etkisini inceler, sistem istemlerini optimize ederek performansın nasıl artırılabileceğini araştırır. |
| [prompt-injection](prompt-injection/) | ✅ | 3 saldırı senaryosu (doğrudan enjeksiyon, dolaylı enjeksiyon, bellek enjeksiyonu) × 4 savunma yapılandırması (savunmasız, prompt sertleştirme, kaynak etiketleme, birleşik savunma) içeren kontrollü bir deney kurar. Saldırı başarı oranlarını hesaplamak için deterministik kurallar kullanır, katmanlı savunmaların enjeksiyon başarı oranlarını nasıl önemli ölçüde azalttığını görsel olarak gösterir. |
| [agent-skills-ppt](agent-skills-ppt/) | ✅ | Agent Skills'in "kademeli açığa çıkarma" (progressive disclosure) kavramını yeniden üretir: Agent başlangıçta yalnızca ince bir Skill dizini görür. Görevin `pptx` Skill'ini gerektirdiğini belirledikten sonra ancak tam iş akışını, ayrıntılı dokümantasyonu ve paketlenmiş betikleri kademeli olarak yükler; sonunda python-pptx kullanarak gerçek bir `.pptx` dosyası üretir. |
| **Metin deneyi** | 🚧 | Kişisel örneklerden hafif bir yazma Skill'i oluşturmayı; tetikleme koşullarını, kuralları, örnekleri, kapsamı ve yinelemeli bakımı ele almayı dener. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
