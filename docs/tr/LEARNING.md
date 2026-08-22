# Öğrenme Önerileri

← [Ana README'ye dön](README.md)

## Temel Kavram: Agent = LLM + Bağlam + Araçlar

Bu kitabın temel formülü **Agent = LLM + Bağlam + Araçlar**'dır. Bölüm 1 aynı Agent'ı üç düzeyde açıklar: uygulama düzeyi bu formüldür, sezgisel düzey «beyin + gözler + eller ve ayaklar»dır, akademik düzey ise politika (Policy), gözlem uzayı (Observation Space) ve eylem uzayı (Action Space) ile eşleşir.

| Bileşen | Benzetme | Görevi |
| :--: | :--: | --- |
| 🧠 **LLM** | Beyin | Anlama, muhakeme ve karar verme yeteneklerini sağlar |
| 👁️ **Bağlam (Context)** | Gözler | Agent'ın her karar noktasında görebildiği her şey: sistem istemi, araç tanımları, kullanıcı mesajları, model yanıtları, araç çalıştırma sonuçları |
| 🤲 **Araçlar (Tools)** | Eller ve ayaklar | Ortamı algılar, eylemleri yürütür, dış dünyayla etkileşir |

Üretim ortamı için Bölüm 1 aynı sistemi **Agent = Model + Harness** olarak yeniden yazar; burada **Harness = bağlam yönetimi + araç arayüzleri + kısıtlar + doğrulama + düzeltme**. Bu son üç madde, çalışan bir demo ile güvenilir bir ürün arasındaki farkın ta kendisidir.

## Öğrenme Yolu

Giriş bölümünün çizdiği genel yapı şudur: **Bölüm 1–6 bir Agent inşa etmenin eksiksiz yöntemini kurar; Bölüm 7–10 ise değerlendirme, eğitim sonrası, sürekli evrim ve çoklu Agent işbirliği olmak üzere dört yönden yetenek artışını tartışır.** Her bölüme bir temel içgörü eşlik eder:

| Kısım | Böl. | Kapsam | Temel içgörü |
| --- | :--: | --- | --- |
| **İnşa** | 1 | Üç unsur, ReAct döngüsü, orkestrasyon kalıpları (iş akışı ile özerklik), Harness mühendisliği | Çalışan bir demo ile güvenilir bir ürün arasındaki fark modelde değil, Harness'tadır |
| | 2 | API mesaj yapısı, KV Cache, prompt mühendisliği ve prompt injection savunması, Agent Skills, Agent durum çubuğu, bağlam sıkıştırma | Kitabın en önemli bölümü; bağlam yetenek tavanını belirler ve önek ne kadar kararlıysa önbellek isabeti o kadar yüksek olur |
| | 3 | Kullanıcı belleği için dört kademeli strateji, RAG yığını, bilginin düzenlenmesi ve erişimi, Agentic RAG, çok kipli bellek | Bağlamı tek bir oturumdan, oturumlar arasında biriken bilgiye genişletir |
| | 4 | Beş araç kategorisi (algı / yürütme / işbirliği / olay tetikleme / kullanıcı iletişimi), MCP, genel tasarım ilkeleri, etkin araç keşfi | Algı araçları bilgi hacmini, yürütme araçları riski denetler; araç tasarımı genelleştirilmiş olmalıdır |
| | 5 | Coding Agent artı dosya sistemi, OpenClaw mimarisi, meta-yetenek olarak kodun altı yönü | Kod yalnızca program yazmak değildir; çalışma zamanında yeni araçlar yaratan meta-yetenektir |
| | 6 | İki eksen, kiplik × zamanlama: asenkron ve olay güdümlü, ses, Computer Use, robot manipülasyonu | Dört etkileşim türü aynı sistem ilkellerini paylaşır: uyandırma, güvenli noktalar, iptal, kesme, hızlı/yavaş yol ayrımı |
| **Geliştirme** | 7 | Değerlendirme ortamları, metrik sistemi, veri kümesi tasarımı, LLM-as-a-Judge, istatistiksel anlamlılık, gözlemlenebilirlik, simülasyon ortamları | Değerlendirme olmadan «tasarımın getirdiği iyileşme» ile «rastgele dalgalanma» ayırt edilemez |
| | 8 | Dört aşamalı panorama, mid-training / SFT / RL, ödül tasarımı, çok turlu kredi ataması, damıtma | SFT ezberler, RL genelleştirir; veri ve ortamlar algoritmalardan daha önemlidir |
| | 9 | Öğrenme sinyalleri (ortam sonuçları / süreç kuralları / LLM Rubric), dört güncelleme taşıyıcısı — bilgi, talimat, program, parametre — artı kademeli yayın ve geri alma | Güncelleme taşıyıcısı, yeteneğin nasıl ifade edildiğine ve nasıl doğrulandığına bağlıdır |
| | 10 | Sınıflandırma çerçevesi (paylaşılan ya da yalıtılmış bağlam × eşler arası / yönetici / merkezsiz), A2A protokolü, altı başarısızlık kipi, Agent toplumu | Çoklu Agent'taki her tasarım kararının tekil Agent'ın üç unsurunda bir karşılığı vardır |

## Metin ile deneylerin görev paylaşımı

Kitap tek bir SDK için adım adım bir öğretici değildir. Metindeki kısa pseudocode ve skeleton'lar yalnızca «durum nasıl akar, hangi adımda durulabilir, doğrulamaya hangi sinyaller katılır» sorularını yanıtlar; bölüm deneyleri ise tam uygulama, model/ortam adaptörleri, testler, günlükler ve kanıt sunar. Bir deneyi okurken her dosyanın her satırını anlamanız gerekmez; tek bir deneyin somut API kullanımını genel bir mimari sanmayın.

Aşağıdaki üç katmanda okumanız önerilir; karmaşık bir bölümde tek bir proje çalıştırmak yerine aynı katmandan birkaç mekanizma deneyi seçin:

| Katman | Önce oku | Şimdilik atla | Yanıtladığı soru |
| :--: | --- | --- | --- |
| **Starter** | Proje README'si: amaç, minimum komut ve kabul koşulları; metindeki karşılık gelen skeleton | kimlik bilgileri, UI, sağlayıcı adaptörleri ve uzun ham günlükler | Bu deney hangi mekanizmayı kanıtlamayı amaçlıyor? |
| **Builder** | giriş noktası, çekirdek döngü, durum/mesaj şeması, araçlar ve doğrulayıcı | mekanizmayla ilgisiz uyumluluk/dağıtım katmanları | Hangi değişken davranışı değiştirdi? |
| **Maintainer** | testler, hata işleme, kanıt biçimi, manifest/hash ve geri alma yolu | deneyi değiştirirken gereken üçüncü taraf ayrıntıları | Sonuç yeniden üretilebilir mi ve hatalar dürüstçe kaydedilmiş mi? |

Her bölümün README'si kendi Starter giriş noktasını belirtir. Önerilen ilk küme şudur: böl. 1 `context`, böl. 2 `context-compression`, böl. 3 `user-memory`, böl. 4 `execution-tools`, böl. 5 `coding-agent`, böl. 6 `live-audio`, böl. 7 `tau2-bench-eval`, böl. 8 `cot-distillation`, böl. 9 `trajectory-verifier`, böl. 10 `parallel-web-research`. Her dizinin Code map'i Run first, Core behavior, Verifier ve ilk okumada atlanabilecek kısımları işaretler.

## Zorluk Seviyeleri

| Seviye | Böl. | Kimin için uygun |
| --- | :--: | --- |
| 🟢 Başlangıç | 1–2 | Yeni başlayanlar; Python temelleri ve LLM kullanma deneyimi yeterli |
| 🔵 Orta | 3–4 | Biraz programlama altyapısı; erişim sistemleri ve araç entegrasyonunu kapsar |
| 🟣 İleri | 5–6 | Güçlü programlama becerileri ve karmaşık sistem tasarımı; böl. 6 için HTTP/WebSocket bilgisi önerilir |
| 🟡 Mühendislik | 7 | Değerlendirme altyapısı ve istatistik yöntemleri — ağırlıklı mühendislik, az matematik |
| 🔴 Uzman | 8 | Kitapta makine öğrenmesi ve model eğitimi deneyimi gerektiren tek bölüm |
| 🟠 Uygulama | 9–10 | Önceki her şeyi birleştirerek sürekli evrim döngüleri ve çoklu Agent sistemleri kurar |

Metindeki deneylerin ve soruların ayrıca yıldız derecesi vardır: ★ giriş düzeyi, tüm okurlara uygun; ★★ orta düzey, bir miktar mühendislik pratiği gerektirir; ★★★ ileri düzey, genellikle açık uçlu problemler veya karmaşık sistem tasarımı içerir.

## Pratik Öneriler

| # | Öneri | Açıklama |
| :--: | --- | --- |
| 1 | 🛠️ **Uygulamalı pratik** | Her proje bağımsız çalıştırılabilecek şekilde tasarlanmıştır; kodu kendiniz çalıştırıp değiştirin |
| 2 | 📚 **Kitapla birleştirin** | Teori ile pratiğin birleşimini anlamak için [`book-tr/`](../../book-tr/) (Türkçe) veya [`book/`](../../book/) (Çince orijinal) dizinlerindeki ilgili bölümleri okuyun |
| 3 | 🔬 **Deneysel karşılaştırma** | Pek çok proje ablasyon çalışmaları ve karşılaştırmalı deneyler içerir; karşılaştırma yoluyla anlayışınızı derinleştirin |
| 4 | 🪜 **Kademeli öğrenme** | Basit projelerle başlayın ve giderek karmaşık sistemlere inin |
| 5 | 🔌 **Protokollere odaklanın** | Bölüm 4'teki MCP araç projeleri, ölçeklenebilir Agent'lar kurmanın anahtarı olan standartlaştırılmış araç protokollerini gösterir |
