# Bölüm 10 · Çoklu Ajan İşbirliği

> Kolektif zeka bireysel zekayı aşabilir. Çoklu Ajan sınıflandırma çerçevesi, ne zaman gerçekten tek bir Agent'tan üstün olduğu, paylaşılan ve paylaşılmayan context ile işbirliği, başarısızlık modları ve ortaya çıkan "Agent Toplumu."

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter10.tr.md)

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| `use-computer-while-calling/` | 📖 | Bir Telefon Görüşmesi Ajanı ve bir Bilgisayar Kullanım Ajanı ile ikili ajan işbirliği mimarisi uygular. İki ajan bir koordinatör olmadan WebSocket üzerinden doğrudan iletişim kurar. Telefon Ajanı sesli etkileşimi yönetirken Bilgisayar Ajanı tarayıcı otomasyonu gerçekleştirir; hem ses hem web işlemi gerektiren karmaşık görevleri tamamlamak için paralel çalışırlar. |
| [staged-system-prompt](staged-system-prompt/) | ✅ | Aynı Coding Agent, bir görevin farklı yürütme aşamalarında (gereksinim netleştirme → kod uygulama → kod incelemesi) farklı sistem istemleri ve araç kümeleri yükler. Bu, tek bir konuşma içinde farklı roller oynamasına ve farklı davranışlar sergilemesine izin verirken, diyalog geçmişi ve görev durumu aşamalar arasında sürekli paylaşılır. İnceleme başarısız olursa, uygulama aşamasına geri dönebilir. |
| [multi-role-transfer](multi-role-transfer/) | ✅ | Paylaşılan bir context altında zincirleme handoff'u gösterir: tek bir oturum, her biri kendi sistem istemine ve özel araç kümesine sahip birden çok uzman rol ajanı içerir. Bir `transfer_to_agent` aracı kullanılarak, bir ajan görev ilerlemesine göre başka bir role ne zaman geçileceğine özerk olarak karar verir. Aynı diyalog geçmişini paylaştıkları için, handoff sırasında tam context doğal olarak korunur. |
| [book-translation](book-translation/) | ✅ | Uzun belge çevirisini sözlük/çeviri/redaksiyon için uzman ajanlara ayrıştırmak üzere orkestratör modunu kullanır. Manager yalnızca görevleri, planları, çağrı kayıtlarını ve dosya indekslerini saklar; tam çevrilmiş metin diske yazılır, context'i kabaca sabit tutar. Bunu tekli ajan yaklaşımıyla karşılaştırır; context patlamasının nasıl kontrol edileceğini ve paylaşılan bir sözlükle kitap genelinde tutarlılığın nasıl sağlanacağını göstermek için gerçek token sayılarını kullanır. |
| [parallel-web-research](parallel-web-research/) | ✅ | Merkezi koordinasyonlu, birden çok homojen ajanın paralel aramasını gösterir: ana koordinatör aynı anda N alt ajan başlatır, her biri bir kaynağa erişip yanıt arar. Biri hedefe ulaştığında, diğerleri zarifçe durur. Mesaj veri yolu, paralel dağıtım, gerçek zamanlı izleme, basamaklı sonlandırma ve yarış durumu (race condition) işleme, gerçekçi biçimde uygulanır (gerçek bir tarayıcı yerine kontrol edilebilir simüle bilgi kaynakları kullanılarak). |
| [voice-werewolf](voice-werewolf/) | ✅ | "Paylaşılmayan context" altında bilgi erişim kontrolünü göstermek için çoklu ajan bir kurt adam oyunu kullanır: her oyuncu, kesinlikle izole edilmiş özel bir context'e sahip bağımsız bir LLM ajanıdır. Kod güdümlü deterministik bir hakem, hangi bilginin hangi oyuncunun context'ine iletileceğine karar verir, denetim için kaydeder ve oyun sonunda izolasyon doğruluğunu otomatik olarak doğrular. Ses isteğe bağlı bir zenginleştirmedir. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
