# Bölüm 10 · Çoklu Ajan İşbirliği

> Kolektif zeka bireysel zekayı aşabilir. Çoklu Ajan sınıflandırma çerçevesi, ne zaman gerçekten tek bir Agent'tan üstün olduğu, paylaşılan ve paylaşılmayan context ile işbirliği, başarısızlık modları ve ortaya çıkan "Agent Toplumu."

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter10.tr.md)

## Deneyler nasıl okunur

Metin, kontrol akışını açıklamak için kısa mekanizma skeleton'ları kullanır; deney dizininde tam SDK adaptörleri, günlükler, testler ve kabul kanıtı bulunur. Her dosyayı satır satır okumanız gerekmez.

- **Starter:** Hedef, en kısa komut ve kabul koşullarıyla başlayın; önce [parallel-web-research](parallel-web-research/);
- **Builder:** Giriş noktasını, ana döngüyü, durum/mesaj şemasını, araçları ve doğrulayıcıyı izleyin.
- **Maintainer:** Son olarak testleri, kanıt manifestlerini, hata işlemeyi, rollback yollarını ve sağlayıcı adaptörlerini okuyun.

İlk okumada kimlik bilgisi yükleme, sunum katmanı ve sağlayıcı uyumluluğunu atlayıp sayıları yeniden üretirken dönün.

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| 10-1 | [multi-role-transfer](multi-role-transfer/) | ✅ | Paylaşılan context altında zincirleme handoff'u gösterir: tek bir oturumda uzman roller, ayrı sistem istemleri ve araç kümeleriyle çalışır; `transfer_to_agent` ile geçiş kararı görev ilerlemesine göre verilir. |
| 10-2 | [book-translation](book-translation/) | 🚧 | Dört rollü Manager ile tek ajan kontrolünü kitap çevirisinde karşılaştırır. |
| 10-3 | `use-computer-while-calling/` + [autonomous-phone-registration](autonomous-phone-registration/) | 📖 / 🚧 | Sabit TalkAct fast/slow paralel işbirliği temelini ve gerçek LLM'in formu inceleyip Phone Agent'ı özerk başlattığı, doğrulama/yeniden sorma ve eşzamanlı soru-doldurma akışını birleştirir. |
| 10-4 | [parallel-web-research](parallel-web-research/) | ✅ | N bağımsız Playwright oturumu on gerçek üniversite sitesini arar; mesaj bus'ı, hata yalıtımı, kademeli sonlandırma ve ölçülen hızlanmayı doğrular. |
| 10-5 | \`generative_agents/\` | 📖 | Stanford'un “AI Kasabası” üretken Agent deneyidir; harici \`joonspk-research/generative_agents\` deposundan klonlanır ve Deney 10-5'i destekler. |
| 10-6 | [voice-werewolf](voice-werewolf/) | 🚧 | Gerçek LLM kullanıcı simülatörünü ses sentezi ve OpenRouter ASR sınırıyla oyuna dahil eder; bilgi izolasyonu, kurallar ve üç döngü doğrulanır, ancak strateji değerlendirmesi başarısızdır. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Devam Ediyor** | Uygulama veya gerekli kabul kanıtı eksiktir; çalıştırılabilir kod bulunması tam kabul anlamına gelmez |
