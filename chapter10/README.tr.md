# Bölüm 10 · Çoklu Ajan İşbirliği

> Kolektif zeka bireysel zekayı aşabilir. Çoklu Ajan sınıflandırma çerçevesi, ne zaman gerçekten tek bir Agent'tan üstün olduğu, paylaşılan ve paylaşılmayan context ile işbirliği, başarısızlık modları ve ortaya çıkan "Agent Toplumu."

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter10.tr.md)

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| `use-computer-while-calling/` | 📖 | `7d70007…` commit'ine sabitlenmiş harici [TalkAct](https://github.com/19PINE-AI/TalkAct): fast/slow ajanlar gerçekten eşzamanlı çalışır ve süreç içi `SharedState` karatahtası (rolling digest, transcript/action log) ile çift yönlü metin kuyruklarını paylaşır. Bu sürüm bir WebSocket köprüsü değildir. Checkout depoya dahil değildir; tam clone komutu ve benchmark girişi ana README ekindedir. |
| [autonomous-phone-registration](autonomous-phone-registration/) | 🚧 | Playwright gerçek bir formu gözlemler ve gerçek bir LLM `initiate_phone_call_agent` çağrısını özerk olarak seçer. Açık onay gerektiren Twilio/yerel ses yolu doğrulama, yeniden sorma, eşzamanlı soru/doldurma, maskelenmiş izler ve isteğe bağlı gönderimi destekler. Mevcut kanıt yalnızca betik yanıtlarla tarayıcı/LLM/eşzamanlılığı doğrular; PSTN ve insan sesi `not_run` olduğundan canlı kabul tamamlanmamıştır. |
| [staged-system-prompt](staged-system-prompt/) | ✅ | Aynı Coding Agent, bir görevin farklı yürütme aşamalarında (gereksinim netleştirme → kod uygulama → kod incelemesi) farklı sistem istemleri ve araç kümeleri yükler. Bu, tek bir konuşma içinde farklı roller oynamasına ve farklı davranışlar sergilemesine izin verirken, diyalog geçmişi ve görev durumu aşamalar arasında sürekli paylaşılır. İnceleme başarısız olursa, uygulama aşamasına geri dönebilir. |
| [multi-role-transfer](multi-role-transfer/) | ✅ | Paylaşılan bir context altında zincirleme handoff'u gösterir: tek bir oturum, her biri kendi sistem istemine ve özel araç kümesine sahip birden çok uzman rol ajanı içerir. Bir `transfer_to_agent` aracı kullanılarak, bir ajan görev ilerlemesine göre başka bir role ne zaman geçileceğine özerk olarak karar verir. Aynı diyalog geçmişini paylaştıkları için, handoff sırasında tam context doğal olarak korunur. |
| [book-translation](book-translation/) | 🚧 | Dört rollü Manager ile tek ajan kontrolü için gerçek modelle küçük bir örnek çalışma vardır. Tam kabul için metinde istenen yoğun görsel/kod içeren teknik kitap ve eksiksiz kalite, verimlilik, token ve kaynak karşılaştırması hâlâ gereklidir. |
| [parallel-web-research](parallel-web-research/) | ✅ | N bağımsız Playwright tarayıcı oturumu on gerçek üniversite sitesini arar; gerçek bir LLM kaynak gösterilebilir kanıtı çıkarır. Kayıtlı kabul; izleme, timeout/error yalıtımı, tek uzlaşma, basamaklı sonlandırma onayları, kaynak temizliği ve ölçülen 3.142× aynı-site paralel hızlanmasını kapsar. |
| \`generative_agents/\` | 📖 | Stanford'un “AI Kasabası” üretken Agent deneyidir; harici \`joonspk-research/generative_agents\` deposundan klonlanır ve Deney 10-7'yi destekler. |
| 10-8 | [voice-werewolf](voice-werewolf/) | 🚧 | Yalnızca kendi koltuğunun bağlamını gören, araç çağıran ve oyuna yalnız sentezlenmiş ses ile gerçek OpenRouter audio ASR üzerinden giren gerçek LLM kullanıcı simülatörü eklendi. Sıkı yeniden doğrulama, bozuk dökümü çekimserlik sayan iki erken çalıştırmayı reddetti; sağlam v2 E2E, izolasyon, kural kazananı ve üç döngüyü geçti, ancak köylü kâhini yanlış çıkardığı için strateji başarısız oldu. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Devam Ediyor** | Uygulama veya gerekli kabul kanıtı eksiktir; çalıştırılabilir kod bulunması tam kabul anlamına gelmez |
