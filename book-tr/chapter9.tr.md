# Çok Modluluk ve Gerçek Zamanlı Etkileşim

Önceki bölümler Agent'ın metin dünyasındaki tasarımını ele aldı — context, araçlar ve kod aracılığıyla dijital sistemlerle etkileşim. Ancak Agent'ın etkileşime girdiği şeyler metin ve API'lerden ibaret değildir. Agent'ın kullanıcının sesli komutunu anlaması, ekranda doğru düğmeyi bulup tıklaması ya da bir robot kolunu bir nesneyi hassasça kavrayacak biçimde yönetmesi gerektiğinde, bambaşka bir alana girer: **çok modlu gerçek zamanlı etkileşim** — saf metin girdi-çıktısından **çok modlu algı ve gerçek zamanlı yanıta** genişleme, Agent'ın "diyalog kutusundan" çıkmasının kilit adımıdır. "Çok modluluk" dediğimiz şey, yalnızca metni değil, birden fazla bilgi biçimini — yazı, ses, görüntü, video, eylem — aynı anda işlemektir.

Önce bu bölümün sınırlarını çizelim. Statik görüntü ve doküman anlama — bir ekran görüntüsüne bakmak, bir grafiği okumak, bir PDF'i ayrıştırmak — önceki bölümlerdeki Agent pratiğine zaten birer algı aracı olarak doğal biçimde yerleşti: bugünün çok modlu büyük modelleri için bu tür "bir kez girdi, bir kez anlama" görevleri görece olgunlaşmıştır ve özel bir mimari tasarım gerektirmez. Bu bölüm başka bir problem sınıfına odaklanıyor: **gerçek zamanlılığın çok modlu problemi zorlaştırdığı** üç senaryo — sesli diyalog, GUI kullanımı ve robot kontrolü. Bu senaryolarda girdi sürekli akar, çıktı ise katı bir zaman bütçesi içinde verilmek zorundadır; mimari tasarım bu yüzden nitelik değiştirir. Sürekli görsel akışın (videonun) gerçek zamanlı anlaşılmasına gelince, bu satırların yazıldığı tarih itibarıyla Agent'lar açısından hâlâ açık bir problemdir — bu bölümün Computer Use kısmında tartışılan kare kare ekran görüntüsü sınırlılığı ile bölüm sonundaki düşünme soruları bu konuya geri dönecek. Bir sınır daha çizmek gerekiyor: çok modlu **üretim** (görüntü üretimi, video üretimi) bu kitabın çerçevesinde sıradan bir tool calling'den ibarettir (Bölüm 5'teki multimedya üretimi kısmında ele alındı); Agent onu harici bir araç olarak kullanır, bu bölümün çözmeye çalıştığı gerçek zamanlı etkileşim zorluklarını içermez ve bu nedenle bölümün ana hattının dışında kalır.

Sesli etkileşim, Computer Use ve robot kullanımı ilk bakışta bambaşka üç alana yayılıyor gibi görünür; ama işe girişilince takılınan yerlerin birbirine son derece benzediği fark edilir: hepsi aynı anda birden çok modaliteye ait bilgiyi işlemek zorundadır ve hepsi gecikmeye aşırı duyarlıdır. Sesli konuşmada iki saniyeyi aşan bir duraklama insanı huzursuz eder; robot kontrolünde milisaniye ölçeğindeki bir titreme çarpışmaya yol açabilir. Bu iki kısıt, üç senaryoyu birlikte aynı mimari yöne iter: **seri boru hattından** (fabrika üretim bandı gibi, bir halka bitmeden sonrakine devredilemez) **uçtan uca modele** (girdiden çıktıya doğrudan giden, aradaki devir teslim halkalarını ortadan kaldıran tek ve birleşik bir model) doğru.

Bu bölüm şu hat boyunca ilerliyor:

1. Önce "Ses Mimarisinin Üç Paradigması" ile bir koordinat sistemi kuruyoruz — kaskad (VAD-ASR-LLM-TTS boru hattı), uçtan uca tam modlu (Omni; tek model, ama hâlâ sırayla konuşma), full-duplex (Moshi, GPT-Live; dinlerken konuşma) — ve "VAD'nin tur varsayımından nasıl kurtulunur" ekseni boyunca her halkanın gecikmesini ve ödünleşimlerini sırayla açıyoruz; kaskad kısmında ayrıca VAD + ASR'nin yerine akışlı konuşma algısının nasıl konulacağı anlatılıyor.
2. Sonra düşünme mimarisinin "gerçek zamanlı yanıt" ile "derin düşünme" arasındaki çelişkiyi nasıl uzlaştırdığına bakıyoruz: hızlı ile yavaşın basitçe paralel çalıştırılmasından, arka plandaki reasoning modelinin "akıl hocası" rolünü üstlendiği ayrıştırma hattına (GPT-Live'ın devretmesi, Pine AI vb.), oradan da Step-Audio R1'in düşünmeyi tek bir modelin içine "içselleştirdiği" düşünürken konuşmaya.
3. Ardından daha insana benzeyen konuşma sentezinin yürütme katmanına getirdiği iyileştirmeleri tartışıyoruz.
4. Son olarak bakışı Computer Use'a (yapay zekânın bilgisayar ekranını bir insan gibi kullanması) ve robot kullanımına genişletip aynı gecikme ve çok modluluk problemlerinin bu iki senaryoda nasıl belirdiğini görüyoruz.

Bunların içinde, teoriye daha yakın duran ve senaryolar arasında taşınabilen iki noktayı özellikle vurgulamak gerekir: **düşünme mimarisi** (hızlı ve yavaş iki düşünme takımının nasıl iş birliği yaptığı) ve ondan türeyen **hızlı-yavaş arayüzü** (Latent Bridge; hızlı ve yavaş modeller arasında metin dışında başka ne aktarılabilir). Bunlar ses senaryosundan yola çıksa da yalnızca sese hizmet etmiyor — ilerideki Computer Use ve robot kısımlarında da "ne zaman yavaş bir akıl hocasına başvurmalı" sorusuyla karşılaşılacak; okurun bunlara ayrıca dikkat etmesinde yarar var.

## Ses: En Doğal İnsan-Makine Arayüzü

Ses, yalnızca metni sese çevirmek değildir. Konuşma yazmaktan yaklaşık dört kat hızlıdır ve elleri gözleri serbest bırakır; bu yüzden kullanıcı istediği anda araya girebildiği sürekli bir giriş-çıkış döngüsü oluşturur. Dikte konuşmayı metne çevirir; sesli Agent ise kullanıcıyla doğrudan iş birliği yapar. Her ikisi de daha önce tanıtılan whisper-coding çalışma biçimini destekler.

Bu bölüm iki yönü ele alır: kullanıcının Agent ile konuşması ve Agent'ın kullanıcı adına dış dünyayla konuşması. Ses modeli Agent'ın neleri yanıtlayacağını belirler; etkileşim mimarisi ise doğru duyma, zamanında yanıt verme, doğal biçimde söz devretme, onayları ve araç çağrılarını bir görüşme sırasında tamamlama becerisini belirler.

### Etkileşim zamanı: kaskaddan full-duplex'e

OpenAI'nin GPT-Live tanıtımı üç ses etkileşimi paradigması tanımlar: kaskad, sıra tabanlı ve full-duplex[^ch9-12]. Bunlar eskiden yeniye basit bir geçiş değil, gecikme, maliyet ve gözlemlenebilirlik arasında farklı ödünleşimlerdir:

| Paradigma | Temel yapı | Ana avantaj | Ana sınırlama |
| --- | --- | --- | --- |
| Kaskad | VAD → ASR → LLM → TTS | Modüller açık; değiştirmek ve hata ayıklamak kolay | Gecikme birikir, paralinguistik bilgi arayüzlerde kaybolur |
| Uçtan uca Omni | Tek model dinler, düşünür ve konuşur | Daha düşük gecikme; ton, duygu ve ortam sesi daha iyi korunur | Hâlâ sıra tabanlı; eğitim ve hata ayıklama daha pahalı |
| Full-duplex | Sürekli dinler, konuşur ve karar verir | Üst üste konuşma, doğal kesme ve kesintisiz akış | Eğitim, kontrol ve değerlendirme daha karmaşıktır |

Ortak hedef, insanların mutlaka sırayla konuşması ve VAD'nin kimin söz hakkına sahip olduğunu tahmin etmesi varsayımlarından kurtulmaktır. Kaskad ve Omni hâlâ etkileşimi turlara böler; full-duplex ise söz hakkını modelin sürekli verdiği bir karara dönüştürür.

[^ch9-12]: OpenAI, *Introducing GPT-Live*, 2026-07-08. https://openai.com/index/introducing-gpt-live/ Kaskad / sıra tabanlı / full-duplex sınıflandırması, yazının ChatGPT Voice'un üç kuşağına dair özetinden gelir; “uçtan uca omnimodal (Omni)” terimi “turn-based voice models” kategorisine karşılık gelir.

**Akış iptali:**

```python
while audio_is_arriving:
    partial = asr.push(audio_chunk)
    if endpoint_is_probable(partial):
        candidate = llm.start(partial)
        if later_audio_changes_meaning(partial):
            cancel(candidate)                 # speculative cancellation
        else:
            tts.enqueue_stable_segments(candidate)

on_final_transcript(text):
    commit_or_restart(text)
```

### Paradigma 1 · Kaskad boru hattı

Ticari sesli yardımcıların çoğu hâlâ seri bir boru hattı kullanır (Şekil 9-1): VAD konuşmanın bitip bitmediğine karar verir, ASR sesi metne çevirir, LLM isteği anlayıp yanıtı üretir ve TTS bunu seslendirir. Modülerlik her parçayı ayrı ayrı geliştirmeyi kolaylaştırır, fakat her sınır bekleme ekler.

![Şekil 9-1: Seri sesli Agent boru hattı](images/fig9-1.svg)

| Modül | Rol | Tipik darboğaz |
| --- | --- | --- |
| VAD | Konuşmanın bittiğine karar vermek | Sessizlik eşiği yanıtı geciktirir ve turları yanlış böler |
| ASR | Sesi metne çevirmek | Tanıma gecikmesi ve bağlam kaybı |
| LLM | Anlamak, akıl yürütmek ve üretmek | İlk token süresi; reasoning ek bekleme getirir |
| TTS | Metni konuşmaya çevirmek | İlk paket sentezi ve oynatma tamponu |

Reasoning içermeyen kısa bir yanıtta VAD, ASR, LLM ve TTS beklemeleri seri biçimde toplanır (Şekil 9-2); gerçek değerler girdi uzunluğu, model, donanım, ağ ve yüke bağlıdır. Üretim kuyruğu boşta geçen gecikmeyi daha da büyütür (Şekil 9-3).

![Şekil 9-2: Seri yanıt için gecikme şelalesi](images/fig9-2.svg)

![Şekil 9-3: Kuyruk gecikmesi eğrisi](images/fig9-3.svg)

> **Deney 9-1 ★: Geleneksel bir sesli Agent inşa etmek**
>
> Mikrofonu, Silero VAD'yi, yerel Whisper'ı, akışlı bir LLM'i ve Fish S1 TTS'yi WebSocket üzerinden bağlayarak kaskad temel hattını kurun. Saklanan gerçek tek turlu kanıt, medya ve model zincirinin uçtan uca çalıştığını gösterir; eşzamanlılık veya üretim yükü benchmark'ı değildir. Kod ve kabul kaydı: [chapter9/live-audio](../chapter9/live-audio/).

> **Ek: WebRTC ile “kullanıcıyı arayan” bir sesli Agent**
>
> Telefon Agent'ı için PSTN şart değildir. Tarayıcı WebRTC'si oturum açma, eksik bilgileri isteme, teyit için tekrarlama ve yapılandırılmış sonuç kaydetme döngüsünü yeniden üretir. Harici bir kuruluşla bağlantı gerektiğinde aynı tool sözleşmesi uygun bir PSTN/SIP sağlayıcısına bağlanabilir. Tam medya yolu, direct/ReAct karşılaştırması ve kabul kanıtı [chapter9/phone-agent](../chapter9/phone-agent/) içindedir. Proje tarihsel \`exp9-2\` çalıştırma kimliklerini korur, ancak artık metinde numaralı bir deney değildir.

#### Seriden akışlı algıya

Akışlı ASR kullanıcı konuşurken geçici bir transkript üretebilir; LLM konuşulabilir ilk cümleyi TTS'ye gönderebilir; TTS de ses parçaları döndürebilir. Bu, ASR, LLM ve TTS'yi baştan sona tamamen paralel yapmaz: kısmi transkript değişirse üretim iptal edilmeli, yeniden başlatılmalı veya düzeltilmelidir; yalnızca \`stream\` seçeneğini açmak yeterli değildir.

Sıradan streaming, VAD'nin sessizlik beklemesini de ortadan kaldırmaz. VAD + ASR ön ucu gecikme biriktirir, tereddüt/duygu/arka kanal tepkilerini ve ortam sesini kaybeder; isimler ve e-posta adresleri parçalar arasında bölünebilir. Gerçek streaming modelinin nedensel ya da parçalı bir kodlayıcıya ve artımlı kod çözmeye ihtiyacı vardır. Whisper kodlayıcısı tam ses parçasını beklediği için nedensel bir streaming modeli değildir. LLM tabanlı bir ses modeli sürekli sesten metin ve semantik olaylar çıkarabilir, ancak önek simülasyonu nedensel modelin gecikme garantisi değildir.

Metin belirteçlerine ek olarak \`speak_start/end\`, \`interrupt\`, \`emotion\`, \`laugh\`, \`sigh\` ve \`noise\` işaretleri konuşma sınırlarını, kesme niyetini, duyguyu, tereddüdü ve çevresel sesi taşıyabilir. Böylece her akustik olay düz metne sıkıştırılmaz.

[^ch9-11]: Tur kararını tanıyıcıya gömme ve geleceğe bakan etiketler sorununa ilişkin teşhis için bkz. Bojie Li ve Noah Shi, *The Trade-off Was in the Labels: Causal Supervision for Turn-Aware Streaming ASR*, 2026 (yayına hazırlanıyor).

> **Deney 9-2 ★: Qwen2-Audio ile akışlı konuşma algısını simüle etmek**
>
> Qwen2-Audio kendi başına bir streaming modeli değildir. Deney, artan ses önekleriyle sürekli algıyı simüle eder ve 600 ms VAD + Whisper ile karşılaştırır. Canonical run tüm yürütme ve provenance kapılarını geçti, ancak beklenen altı davranıştan yalnızca ikisini yeniden üretti: önek çağrıları 8,4–11,3 saniye sürdü, pause örneğinde \`silence\` kaçırıldı ve noise örneği \`cough/laughter\` olarak yanlış sınıflandırıldı. Bu mekanizma ve hata kiplerini sınayan negatif bir sonuçtur; 100–200 ms gerçek streaming algısının kanıtı değildir. Tam kayıt: [chapter9/streaming-speech](../chapter9/streaming-speech/).

### Paradigma 2 · Uçtan uca omnimodal modeller (Omni)

Streaming algı olsa bile kaskad dinleme, düşünme ve konuşmayı ayrık arayüzlerden geçirir; ses düz metne dönüştüğünde duygu, tonlama ve ortam sesi kaybolabilir. Omni bunları tek modelde yapar; eğitim, hata ayıklama ve bileşen değiştirme maliyeti daha yüksek olsa da gecikmeyi azaltır ve metin dışı sinyalleri korur (Şekil 9-4). Metnin görevi taşıdığı durumlarda öz-kaskad bir algılama hatasını düzeltebilir; yanıt konuşma hızına, duyguya veya ortama bağlıysa metin darboğazı kanıtı geri döndürülemez biçimde siler[^ch9-13].

Omni hâlâ sıra almayı varsayar ve genellikle VAD ya da anlamsal endpointing kullanır. Sayı dizisindeki kısa bir duraklama konuşmanın sonu sanılabilir; akışlı algı kararı iyileştirir ama turları kaldırmaz.

[^ch9-13]: Kaskad ile uçtan uca doğruluk avantajının ne zaman tersine döndüğünü ölçen çalışma için bkz. Li, Bojie ve Noah Shi, *The Cascade Gap: When and Why Self-Cascades Help Multimodal Agents*, 2026 (yayına hazırlanıyor).

![Şekil 9-4: Uçtan uca omnimodal konuşma modeli karşılaştırması](images/fig9-4.svg)

Gerçek zamanlı konuşma API'leri kaskad ile Omni arasında durur: model sesi doğal biçimde işler, ancak etkileşim kontrolü VAD, kesme ve asenkron tool çağrılarına dayanır. Yararlı karşılaştırma leaderboard değil, uçtan uca ve öz-kaskad yolların farklı görevlerde nasıl hata yaptığıdır.

> **Deney 9-3 ★★: MiniCPM-o 4.5'i yerel çalıştırmak — uçtan uca ve öz-kaskad**
>
> Tek bir yerel revizyonu sabitleyin, düşünme modunu kapatın ve sese doğrudan yanıtı aynı modelin öz-kaskadıyla (önce transkript, sonra metinden yanıt) karşılaştırın. Bu ölçüm ses bilgisinin korunmasını ölçer; daha sonraki “konuşurken düşünme” yeteneğini değil.
>
> | Görev türü | Uçtan uca | Öz-kaskad | Gözlem |
> | --- | ---: | ---: | --- |
> | Anlamsal aritmetik (2) | 1/2 | 2/2 | Öz-kaskad bir transkripsiyon hatasını düzeltti |
> | Paralinguistik konuşma hızı (2) | 2/2 | 1/2 | Düz metin hızlı/yavaş ayrımını sildi |
> | Toplam | 3/4 | 3/4 | Eşit toplam, birbirini tamamlayan hatalar |
>
> Örneklem küçüktür; hangi yolun genel olarak daha doğru veya hızlı olduğunu kanıtlamaz. Sürümler, ham çıktılar ve gerçek audio-to-audio kanıtı [chapter9/end-to-end-speech](../chapter9/end-to-end-speech/) içindedir.

Step-Audio 2 ham sesi işleyerek metin ve konuşma çıkaran uçtan uca yolu gösterir; duygu, konuşma hızı, tonlama ve ortam sesine odaklanır. Step-Audio R1 düşünmeyi ses modelinin içine alır ve “konuşurken düşünme” örneğini sağlar.

### Paradigma 3 · Full-duplex etkileşimli modeller

Omni “kullanıcı konuşur” ve “model konuşur” ayrımını korur, ancak simultane çeviri gibi görevler örtüşme ister. Full-duplex model sürekli dinler ve konuşur; devam etme, durma, araya girme veya tool çağırma kararını yinelemeli olarak verir. Kyutai'nin Moshi'si erken bir araştırma örneğidir. Thinking Machines Lab bu yaklaşımı **Interaction Model**[^ch9-14] olarak adlandırır: etkileşim VAD çevresinde dışarıdan kurulmaz, modelin içine yerleştirilir. GPT-Live bunu üretim ölçeğine taşır ve ön plandaki model sohbeti sürdürürken karmaşık işi arka plan reasoning modeline devreder.

[^ch9-14]: Thinking Machines Lab, “Interaction Models: A Scalable Approach to Human-AI Collaboration”, 2026-05. https://thinkingmachines.ai/blog/interaction-models/

Gelişim çizgisi şöyledir: kaskad sessizlik eşikleriyle turları tahmin eder; akışlı algı kararı anlamsal düzeye taşır; full-duplex ise sıra değişimini sürekli bir model kararına dönüştürür.

### Bilişsel zaman: gerçek zamanlı etkileşim ve derin düşünme

Ön plan modeli kullanıcı hâlâ hatta iken yanıt vermeli, arka plan modeli ise daha uzun düşünebilmelidir. Bunlar doğrusal bir ilerleme değil, üç tasarım ödünleşimidir:

| Tasarım | Ön plan | Arka plan | Ana risk |
| --- | --- | --- | --- |
| Hızlı dolgu, yavaş düzeltme | Anında yanıt | Yeniden düşünme ve tamamlama | Çelişki |
| Hızlı etkileşim, yavaş tavsiye | Sohbeti ve ifadeyi sürdürme | Tavsiye veya araç sonucu | Kısıtlı arayüz |
| Düşünme ve ifadenin birleşmesi | Konuşurken düşünme | Model durumunu paylaşma | Yüksek eğitim/değiştirme maliyeti |

İlk tasarım soruyu iki kez işleyebilir ve çelişebilir. İkincisi status bar üzerinden tavsiye verdiği için daha kararlı olsa da ön plan ara muhakemeyi göremez ve gerçekten konuşurken düşünemez. Üçüncüsü iki süreci birleştirir. Step-Audio R1'de MGRD düşünmeyi akustik özelliklere bağlar; MPS iki beyinli mimarisi planlama ile ifadeyi paralel üretir (Şekil 9-5 ve 9-6). Birleşik model daha doğaldır, ayrıştırılmış tasarım arka plan beynini değiştirmeyi kolaylaştırır; bunlar alternatif değil ödünleşimlerdir.

### Daha insana benzeyen konuşma sentezi

Geleneksel TTS'nin aşırı pürüzsüz olması ve az duraklaması makine kimliğini ele verir. Ana LLM metne \`THINKING\`, \`EMO:happy\` ve \`SPEED:0.8x\` gibi kontrol etiketleri ekleyebilir; TTS bunları duraklama, prozodi, hız, kahkaha ve iç çekmeye dönüştürür. Etiketleri anlayan bir TTS eğitilebilir veya farklı referans klipleriyle ses klonlama kullanılabilir.

> **Deney 9-4 ★★: Fish Audio ile kontrol belirteçli TTS**
>
> Fish Audio S1 kullanarak çok referanslı bir ses kütüphanesi oluşturun ve üç ayarı karşılaştırın: belirteçsiz, tek referanslı ve çok referanslı. Yürütme katmanı etiketlerden uygun duygu, konuşma hızı ve stili seçer. Dengeli üç kör dinlemede çok referanslı ayar en yüksek puanı aldı (insan müşteri hizmetleri benzerliği 4,67/5); ancak belirteçsiz kol tek referanslı kolu geçtiği için planlanan sıralama bütünüyle tekrarlanmadı. Küçük dinleme çalışması ifade kontrolünün yararlı olabileceğini gösterir, genel konuşma kalitesi sonucu değildir. 24 referanslı kütüphane, A/B/C medyası ve kabul kaydı: [chapter9/controllable-tts](../chapter9/controllable-tts/).
## Computer Use: GUI Otomasyonu Agent'ları

Buraya kadar okuyunca, bu bölümün sese ayırdığı yerin sonraki iki senaryodan belirgin biçimde fazla olduğu fark edilebilir — bu bilinçli bir tercihtir. Gerçek zamanlı çok modluluk çizgisinde ses, en uzun yolu almış ve referans çerçevesi olarak alınmaya en değer alandır: "seri boru hattının gecikmesi çok yüksek" sorunundan yola çıkıp uçtan uca modeller, full-duplex etkileşim ve düşünürken konuşma gibi bir dizi çözümden geçerek bugünkü görece olgunlaşmış noktaya ulaşmıştır; sorun → çözüm → son durum güzergâhının tamamı katedilmiştir. Bu yüzden onu enine boyuna anlattık. Sıradaki Computer Use ve robotik senaryolarını okurken bu güzergâhla karşılaştırın: her biri bu evrim çizgisinin neresine gelmiştir ve nerede takılı kalmıştır?

Bu üç senaryo görünüşte birbirinden çok farklıdır, ama aynı temel zorluklarla yüzleşir: gerçek zamanlı algı, düşük gecikmeli karar verme ve sürekli etkileşim. Şimdi bu teknik temaların görsel etkileşimde (Computer Use) ve fiziksel etkileşimde (robotik) nasıl yeniden ortaya çıktığına bakalım — önce bakış açısını işitsel modaliteden görsel modaliteye genişletelim: ya bir Agent yalnızca konuşmayı anlamakla kalmayıp ekranı da "görebilseydi" ve grafik arayüzü kullanabilseydi?

Computer Use (GUI otomasyonu Agent'ı olarak da anılır), yapay zekanın tıpkı bir insan gibi ekranı gözleyerek ve fare ile klavyeyi kullanarak yazılım çalıştırmasını sağlar — örneğin bilgi aramak için tarayıcı açmak, bir tablo yazılımına veri girmek veya sistem ayarlarında bir yapılandırmayı değiştirmek. Özünde bir **algılama-düşünme-eylem** döngüsü vardır (Şekil 9-7):

1. Agent o anki ekranın görüntüsünü alır
2. Çok modlu model ekran görüntüsünü ve görev talimatını alır, bir düşünme parçası ve somut bir eylem üretir
3. Yürütme katmanı bu eylemi gerçek ortamda uygular (fareyi hareket ettirmek, tıklamak, metin girmek vb.)
4. Arayüzün yanıt vermesini bekledikten sonra yeniden ekran görüntüsü alır ve döngünün bir sonraki turuna girer

**Computer Use güvenlik döngüsü:**

```python
observation = capture_screenshot_and_accessibility_tree()
proposal = model.decide(task, observation)
action = validate_schema_and_coordinates(proposal)

if action.is_irreversible and not user_or_policy_approval(action):
    stop("approval required")
else:
    execute_in_sandbox_or_scoped_session(action)
    new_observation = capture_after_settle()
    if not verify_goal_progress(new_observation, action):
        rollback_if_possible_or_replan()
```

![Şekil 9-7: Computer Use Agent'ının algılama-düşünme-eylem döngüsü](images/fig9-7.svg)


Bu döngüde üç kritik tasarım boyutu vardır: **action space** (eylem alanı — Agent'ın hangi işlemleri yürütebildiği), **görsel konumlandırma** (ekran görüntüsünde hedef öğenin nasıl bulunacağı) ve **model mimarisi** (ekran görüntüsünden doğru eylemin nasıl üretileceği).

### Action Space Tasarımı

Anthropic, eksiksiz bir etkileşim yeteneği oluşturan üç tür araç tanımlar (Şekil 9-8):


![Şekil 9-8: Computer Use action space'i](images/fig9-8.svg)


**GUI işlem aracı** (computer tool): Fare işlemleri arasında hareket ettirme (mouse_move), sol/sağ/orta tuş tıklaması, çift/üçlü tıklama, sürükleme (left_click_drag) ve daha ince taneli basma/bırakma (left_mouse_down/up) yer alır. Kaydırma (scroll) dört yönü destekler ve değiştirici tuşlarla birlikte kullanılabilir. Klavye işlemleri arasında karakter karakter yazma (type; gerçek klavye kullanımını taklit etmek için her karakter arasında 12 ms aralıkla), tuş kombinasyonları (key, örneğin Ctrl+C) ve tuşu basılı tutma (hold_key) bulunur. Algı eylemleri: ekran görüntüsü alma (screenshot), imleç konumunu okuma (cursor_position) ve bekleme (wait).

**Komut yürütme aracı** (bash tool): Kalıcı bir bash terminal oturumu sağlar, 120 saniyelik zaman aşımına sahiptir, komutun tamamlanıp tamamlanmadığını bir nöbetçi (sentinel) dizesiyle tespit eder ve çağrılar arasında ortam durumunu korur (örneğin cd ile bir dizine geçildikten sonra bir sonraki çağrı da aynı dizinde başlar).

**Dosya düzenleme aracı** (str_replace_editor): Dizi eşleştirmesi yoluyla güvenli düzenleme sağlar; görüntüleme, oluşturma, değiştirme, ekleme ve geri alma işlemlerini destekler. Dosyanın tamamının üzerine yazmaktan daha kesindir ve alakasız içeriği yanlışlıkla değiştirme olasılığı daha düşüktür.

> **Deney 9-5 ★: Computer Use'ı Çalıştırmak (Anthropic Referans Yolu veya Açık Model Yolu)**
>
> A yolu Anthropic Computer Use Demo'yu kullanır. Konteyner, tarayıcı, terminal ve diğer yaygın araçları içeren eksiksiz bir Ubuntu masaüstü ortamı sunar. Ön uç görevi alır; arka uç talimatları ve ekran görüntülerini Claude'a gönderir, ardından modelin döndürdüğü fare, klavye, terminal veya düzenleme eylemlerini yürütür. Bu yol, yerleşik `computer` aracı protokolünü anlamaya yöneliktir; her okuyucunun Anthropic API erişimine sahip olmasını gerektirmez.
>
> B yolu, kitabın [`chapter9/computer-use-open-model`](../chapter9/computer-use-open-model/) eşlikçi projesini kullanır. Varsayılan olarak browser-use'ı açık ağırlıklı Qwen3-VL 32B Instruct ile çalıştırır; OpenRouter barındırılan API'si kullanılabilir veya `OPEN_MODEL_BASE_URL`, kendi barındırdığınız vLLM/SGLang ya da başka bir uyumlu uç noktaya yönlendirilebilir. Uç nokta ekran görüntülerini kabul etmeli ve yerleşik JSON Schema'yı desteklemelidir; yalnızca normal JSON destekliyorsa schema-in-prompt uyumluluk modu açıkça etkinleştirilebilir.
>
> İki yol da aynı salt okunur görevi ve aynı kabul sözleşmesini kullanır: en fazla 25 adım, adım başına tek bir eylem ve model/uç nokta kimliğinin, ham sağlayıcı yanıtlarının, adım adım ekran görüntülerinin, eylem dizisinin, nihai yanıtın ve durma nedeninin saklanması. Farklı modeller ayrı deney kolları olarak raporlanmalıdır; açık model sonucu Claude yeniden üretimi gibi sunulmamalı, “konteyner başarıyla başladı” ifadesi görev tamamlandı sayılmamalıdır. Eylem aralıkları ve planlama kalitesi ölçülen sonuçlardır; 2–5 saniye olacağı veya diğer modellerden mutlaka üstün olacağı önceden varsayılmaz.
>

### Görsel Konumlandırma (Grounding)

Döngünün her turunda modelin ekran görüntüsü içinde hedef öğeyi doğru biçimde bulması gerekir — "Arama kutusu nerede?", "Gönder düğmesinin koordinatları ne?" İşte bu, görsel konumlandırma (Grounding) problemidir. Hâlihazırda başlıca **iki yaklaşım** vardır: birincisi konumlandırmayı bir **çoktan seçmeli soruya** dönüştürmek — önce arayüz öğelerini numaralandırarak işaretlemek, böylece modelin yalnızca birini seçmesi yeterli olur; ikincisi **saf koordinat tahmini** — modelin tıpkı bir insan gibi ekran görüntüsüne doğrudan "bakıp" koordinatı söylemesi. Çoktan seçmeli yaklaşımın da iki uygulama biçimi vardır: **saf görsel işaretleme** (orijinal Set-of-Mark; bir segmentasyon modeliyle piksel düzeyinde aday bölgeler çıkarılır) ve **yapısal öğe indeksleme** (DOM/Accessibility Tree; arayüzün kendi yapısı doğrudan okunur). Çoktan seçmeli yaklaşımın ortak avantajı, "ekran görüntüsünde düğmeyi bul ve koordinatını tahmin et" biçimindeki açık uçlu problemi "önceden işaretlenmiş öğelerden birini seç" biçimindeki kapalı uçlu bir probleme çevirmesidir — tıpkı sınavda çoktan seçmeli soruların boşluk doldurmaya göre daha kolay doğru yanıtlanması gibi, modelin "ekranın sol üst köşesinden yaklaşık 200 piksel sağdaki mavi düğmeye tıkla" demesi gerekmez, "[123]'e tıkla" demesi yeter.

**Set-of-Mark: görsel işaretleme yöntemi.**

Orijinal Set-of-Mark (SoM), 2023'te Microsoft Research tarafından, başlangıçta GPT-4V'nin görsel konumlandırma yeteneğini açığa çıkarmak amacıyla önerildi. **Saf görsel** bir yöntemdir: görüntü segmentasyon modelleri (SAM, SEEM vb.) ekran görüntüsünde aday bölgeleri otomatik olarak çıkarır, her bölgenin üzerine numaralı bir işaret bindirilir; modelin gördüğü şey numaralandırılmış bir görüntüdür ve yalnızca numarayı söylemesi yeterlidir, sistem bunu ilgili bölgenin merkez koordinatına çevirir. Sürecin tamamı DOM'a ya da herhangi bir arayüz iç yapısına ihtiyaç duymaz; bu nedenle yerel masaüstü yazılımları ve oyun arayüzleri için de aynı ölçüde geçerlidir — yeter ki segmentasyon modeli aday bölgeleri çıkarabilsin.

**Yapısal öğe indeksleme: SoM fikrinin Web üzerindeki yapısal uygulaması.**

Arayüzün kendisi yapısal bilgi sunabildiğinde işaretleme çok daha kesin yapılabilir. Modern web sayfaları, render edilmeden önce zaten eksiksiz bir öğe yapısı (DOM ağacı) ve semantik roller (hangisi düğme, hangisi giriş kutusu) tanımlar; erişilebilirlik arayüzü (Accessibility Tree) birçok masaüstü uygulaması için benzer bilgiyi sağlar. Bir segmentasyon modelinin piksellerden "hangi bölge düğme" diye tahmin yürütmesindense, doğrudan arayüzün kendisine "tıklanabilir hangi öğelerin var?" diye sormak daha iyidir. browser-use projesinin temsil ettiği Web Agent çözümleri tam olarak bunu yapar: etkileşimli öğeleri DOM'dan numaralandırarak listeler; bu, SoM fikrinin Web üzerindeki yapısal uygulaması sayılabilir (Şekil 9-9). Süreç dört adımdan oluşur:

1. Tarayıcının hata ayıklama arayüzü (CDP, Chrome DevTools Protocol) üzerinden sayfanın yapısal temsilini (DOM ağacı) ve erişilebilirlik bilgilerini elde etmek
2. Hangi öğelerin etkileşimli olduğunu otomatik olarak tespit etmek (düğmeler, giriş kutuları, bağlantılar vb.)
3. Her etkileşimli öğeye benzersiz bir ID atamak ve ekran görüntüsünde sınırlayıcı kutuları çizmek
4. Aynı anda, her ID'ye karşılık gelen öğeyi tanımlayan bir metin listesi üretmek

```text
Screenshot: [Görseldeki kilit öğeler [1], [2], [3], [4] gibi ID'lerle işaretlenmiştir]

Elements:
[1] <input type="text" placeholder="Search" aria-label="Search" />
[2] <button id="submit-btn" aria-label="Submit form" />
[3] <input type="text" placeholder="Enter your name" value="" />
[4] <a href="/docs" aria-label="Documentation" />
```

Modelin yalnızca bir ID numarası üretmesi yeterlidir; sistem otomatik olarak o öğenin merkez koordinatını kullanarak tıklamayı gerçekleştirir. Bu tür çözümler token tasarrufu sağlamaz (çünkü tüm işaretleme bilgisinin modele gönderilmesi gerekir), ama konumlandırması kesin ve kararlıdır; üstelik segmentasyon modelinin yol açabileceği atlanmış ve yanlış tespitleri de ortadan kaldırır.


![Şekil 9-9: Set-of-Mark ile yapısal öğe indeksleme (browser-use uygulaması)](images/fig9-9.svg)

**Saf koordinat tahmini.**

Üçüncü yol hiçbir işaretleme yapmaz, doğrudan modelin koordinat üretmesini ister. **SeeClick** ve Claude'un computer use'u bunun temsilcileridir: devasa miktarda GUI ekran görüntüsü ve öğe konumu eşleşmesinden oluşan veriyle görsel modeller eğitilir ve modelin doğal dil betimlemelerini (örneğin "gönder düğmesine tıkla") doğrudan ekran görüntüsündeki kesin koordinatlara eşlemeyi öğrenmesi sağlanır — tıpkı bir insan kullanıcı gibi, tıklanacak yeri saf görme yoluyla bulur.

Koordinat tahmini çözümlerinde modelin koordinatları kavrayışı, eğitim sırasında kullanılan çözünürlüğe yüksek oranda bağımlıdır (Şekil 9-10). Claude'un eğitiminde XGA (1024x768), WXGA (1280x800) ve FWXGA (1366x768) kullanılmıştır; girdi olarak verilen ekran görüntüsünün çözünürlüğü bunlarla uyuşmazsa modelin tahmin ettiği koordinatlar sistematik biçimde kayar — tıpkı küçük bir haritada ölçülen mesafeyi doğrudan büyük haritaya uygulamak gibi. Bu nedenle araç katmanında çift yönlü bir koordinat ölçekleme mekanizması gerekir ve hedef çözünürlük **en-boy oranına göre seçilmelidir**; aksi hâlde orantısız gerdirme görüntüyü bozar ve koordinat değerlendirmesini de saptırır. Örneğin gerçek ekran çözünürlüğü 2560×1440 (16:9) ise, Claude'un desteklediği üç seçenek arasından en-boy oranı 16:9'a en yakın olanı — FWXGA (1366×768) — seçilmelidir. Ekran görüntüsü orantılı biçimde 1366×768'e ölçeklenip modele verilir; model tıklama koordinatı olarak (683, 384) ürettiğinde bu değer ters yönde gerçek koordinata eşlenir: (683×2560/1366, 384×1440/768) ≈ (1280, 720). Buna karşılık 16:9'luk bir görüntü zorla 4:3'lük 1024×768'e gerdirilirse görüntü yatayda ezilir ve modelin tahmin ettiği koordinatlar sistematik olarak kayar.


![Şekil 9-10: Çözünürlük eşleştirme ve çift yönlü koordinat ölçekleme](images/fig9-10.svg)


Üç yol arasındaki seçim mantığı şöyle özetlenebilir: **yapısal bilgi elde edilebiliyorsa öncelikle DOM/Accessibility Tree indekslemesi kullanılmalıdır**; konumlandırması en kesin ve en kararlı olan budur. **Elde edilemiyorsa** (Photoshop gibi yerel masaüstü yazılımları, Canvas/WebGL ile render edilen arayüzler, oyunlar) **hem görsel işaretleme (orijinal SoM yolu) hem de koordinat tahmini kullanılabilir**. Görsel işaretleme konumlandırmayı çoktan seçmeli bir soruya dönüştürdüğü için, özel olarak eğitilmemiş genel amaçlı modellere daha dosttur; koordinat tahmini ise işaretleme adımını ortadan kaldırdığı için, GUI konumlandırma eğitimi almış modeller açısından daha doğrudandır. Küçük öğelerde ve yoğun arayüzlerde her ikisinin de doğruluğu hâlâ yetersizdir.

> **Deney 9-6 ★: browser-use ile Otomatik Tarayıcı İşlemleri**
>
> Tarayıcı otomasyon çerçevesi Playwright'ı çok modlu bir modelle birleştirerek doğal dille yönlendirilen tarayıcı işlemlerini gerçekleştirin. SoM görselleştirmesini etkinleştirin ve her karardan önce açıklamalı sınırlayıcı kutular içeren ekran görüntüsünü kaydedin. Model arayüzü OpenAI veya Anthropic ile sınırlı değildir; kitap, açık Qwen3-VL modeli için API yapılandırması sağlar ve diğer barındırılan hizmetler ya da kendi barındırdığınız çıkarım için genel bir OpenAI uyumlu base URL sunar.
>
> “Google'ı aç ve San Francisco hava durumunu sorgula” test görevi: Başlatma sonrasında ekran görüntüsü, numaralandırılmış etkileşimli öğelerle Google arama sayfasını gösterir. Model arama kutusunu seçer, “San Francisco weather today” yazar, aramayı gönderir ve sonuç sayfasından sıcaklık ile hava koşullarını çıkarır. Kabul sırasında yanıt ve iz bağımsız olarak doğrulanır; gerçek adım sayısı ve geçen süre olduğu gibi kaydedilir. “5 adım, yaklaşık 20 saniye” yalnızca belirli bir çalışmanın gözlem değeri olabilir; yürütme kaydı olmadan sabit sonuç sayılamaz.
>
> Kitapta saklanan resmi açık model çalışması, OpenRouter üzerindeki `qwen/qwen3-vl-32b-instruct` modelini kullandı. Model Google Search'ün 4. adımında CAPTCHA ile karşılaştığında başarılı olduğunu iddia etmedi; weather.com'a geçti ve 16. adımda San Francisco Today sayfasından 64°F, Sunny, hissedilen 62°F, en yüksek 74°F ve en düşük 55°F bilgilerini okudu. 16 API yanıtının tamamı istenen Qwen3-VL modelini bildirdi; 15 geçerli adım ekran görüntüsü ve salt okunur eylem izi bağımsız deterministik kabulden geçti. Bu sonuç açık model API yolunun çalıştığını kanıtlar; Anthropic'in yerleşik `computer` aracı kolunun yeniden üretildiği anlamına gelmez.

### Animasyon Görebilen, Ses Duyabilen Computer Use Agent'ı

Buraya kadar Computer Use'un algısı örtük bir varsayıma dayanıyordu: **ekran durağandır** — bir görüntü al, bir adım düşün, bir kez tıkla, sonra bir görüntü daha al. Oysa gerçek ekranlarda video oynar, göz açıp kapayıncaya kadar kaybolan bildirimler belirir, toplantılardaki insan sesleri duyulur. Her 3–5 saniyede bir gözünü açan ve hiç kulağı olmayan bir Agent, "iki kare arasında olup bitenleri" ne görebilir ne de duyabilir. Ekran kaydı izlemek, bir toplantıyı takip etmek, sesli bir uyarıyı dinlemek, bir anda gelip geçen bir iletişim kutusuna yetişmek — bu gündelik bilgisayar işlerinin tamamı bugünün Computer Use Agent'ı için neredeyse yasak bölgedir.

Burada asıl yeniden tasarlanması gereken şey "eylem arayüzü" değil, "**gözlem arayüzü**"dür[^ch9-9]. Temel fikir, **gözlemi** (sürekli, uyarlanabilir, çok modlu) **eylemden** (ayrık) ayrıştırmak ve ortam ile herhangi bir hazır Computer Use modeli arasına yerleşen, yeniden eğitim gerektirmeyen bir algı ara katmanı hâline getirmektir (buna Agent–bilgisayar gözlem arayüzü, AOI denebilir). Bu katmanın "ihtiyaç oldukça kapağı açılan" üç bileşeni vardır. Birincisi, **kareler arası anahtar kare yakalama**: önce son derece ucuz bir piksel kapısıyla neredeyse hiç değişmeyen kareler atlanır, ardından küçük bir model görüntüde anlamlı bir değişiklik olup olmadığına karar verir ve yalnızca değişiklik varken bir kare yakalanır; durağan görüntüde maliyet neredeyse sıfırdır. İkincisi, **ses seviyesiyle kapılanan konuşma transkripsiyonu**: yalnızca ses varken konuşma tanıma çağrılır ve Agent ilk kez "kulak sahibi olur". Üçüncüsü — ve en kritiği — **görüntüyü kalıcı metne dönüştürmek**: model, yakalanan kareyi tek bir cümleyle betimler ("Az önce çıkan bildirimde yayın tarihinin 28 Nisan'a alındığı yazıyor") ve **orijinal görsel daha sonra context'ten temizlense bile bu cümle bellekte kalır**, yani dinamik bilgi metin biçiminde ileriye taşınır.

Sezgiye aykırı bir bulgu şudur: asıl işe yarayan şey "hangi karelerin seçildiği" değil, "**karelerin uzun süre saklanabilecek metne dönüştürülmesi**"dir — çünkü metin, LLM Agent'larının en iyi işlediği modalitedir. 7B'den öncü ölçeğe uzanan sekiz model üzerinde bu ara katman, hiçbir yeniden eğitim gerektirmeden +17 ila +48 yüzde puanlık iyileşme sağladı; aradaki en büyük fark sesli görevlerde görüldü: bu algı katmanı eklendiğinde Agent, daha önce "duyulabilir ama üzerinde işlem yapılamaz" olan sesli görevleri tamamlayabildi. Ne var ki bu, her duruma uyan sabit bir yapılandırma değildir — bazı daha yeni modellerde çok fazla görsel token yüklemek akıl yürütmeyi sıkıştırıp performansı düşürebiliyor. Dolayısıyla bu bileşenler toptan açılmak yerine **model model seçilmelidir**. Bu, daha önceki Set-of-Mark ile koordinat tahmini arasındaki tercihle aynı derstir: algı çözümlerinin gümüş kurşunu yoktur, yapılandırma modelin huyuna göre ayarlanır.

[^ch9-9]: Kapılı anahtar kare, ihtiyaç hâlinde transkripsiyon ve kareleri kalıcı metne dönüştürme biçimindeki üç bileşenin eksiksiz mekanizması ve model bazlı ablation çalışması için bkz. Li, Bojie and Noah Shi. *Agent-Computer Observation Interfaces Enable Dynamic Computer Use.* arXiv:2606.29472, 2026.

### Mobil Taraf: Ekosistem Bariyerleri Teknolojiden Daha Zorlu

Computer Use mobil tarafa da yayılıyor. Mobil ile masaüstü arasında teknik açıdan gerçek farklar vardır: action space genellikle artık "fare koordinatı + klavye" değildir, sistemin erişilebilirlik servisi API'si (örneğin Android'in AccessibilityService'i) üzerinden arayüz öğeleri okunur, tıklama ve metin girişi gönderilir; etkileşim biçimi de fare imlecinden dokunma hareketlerine döner ve koordinatın anlamı buna bağlı olarak değişir — aynı (x, y) noktasının parmakla tek dokunuş mu, uzun basma mı, yoksa bir kaydırma hareketinin başlangıç noktası mı olduğunu belirlemek için ayrıca bir hareket türü gerekir. Bölüm 6'da tanıtılan AndroidWorld gibi mobil benchmark'lar, Agent'ın gerçek uygulamalarda görev tamamlama yeteneğini tam da böyle bir action space üzerinde değerlendirir.

Ama mobil tarafı asıl tıkayan şey çoğu zaman bu teknik farklar değil, ekosistem bariyerleridir. Bazı telefon üreticileri, tüketici sınıfı telefonlara yapay zeka asistanları entegre edip WeChat, Taobao, Alipay gibi gündelik uygulamaları otomatik olarak kullandırmayı denedi, ama kısa sürede platform kısıtlamalarına takıldı.

Bu durum Computer Use'un karşılaştığı kendine özgü bir zorluğu açığa çıkarır: **ekosistem bariyerleri**. Engellemenin temelindeki neden bir iş modeli çatışmasıdır. Geleneksel internet uygulamalarının çekirdek gelir mantığı **trafik ve dikkattir**: kullanıcı akışı kaydırırken reklam görür, ürün ararken öneri algoritmasının yönlendirmesine uyar, sayfaları gezerken anlık satın alma kararı verir. Agent kullanıcının yerine işlem yaptığında ise bu gelir zinciri tamamen baypas edilir: yapay zeka reklamlara bakmaz, anlık alışveriş yapmaz, doğrudan hedefe gidip görevi bitirir ve çıkar. Reklam ve trafikten para kazanan platformlar için Agent'ın her işlemi, iş modelinin temelini aşındırır.

Bu da Computer Use'un yalnızca CAPTCHA (doğrulama kodu) gibi teknik düzeydeki karşı önlemlerle değil, **yapısal bir çıkar çatışmasıyla** da karşı karşıya olduğu anlamına gelir. Bu çelişkiyi kısa vadede uzlaştırmak zordur ve Computer Use'un tüketici senaryolarında hayata geçmesini, salt teknik sorunlardan daha çetin bir engelle karşı karşıya bırakır.

### Gerçek Zamanlılık: Henüz Çözülmemiş Temel Zorluk

**OSWorld** (değerlendirme metodolojisi Bölüm 6'da ayrıntılı olarak anlatılıyor), yaygın kullanılan bir Computer Use değerlendirme benchmark'ıdır ve Agent'ın gerçek Ubuntu/Windows/macOS ortamlarında uygulamalar arası görevleri tamamlama yeteneğini ölçer. Erken dönem genel amaçlı modellerin bu benchmark'taki başarı oranı yalnızca %20 civarındaydı; sonraki özel modeller ve daha güçlü genel amaçlı modeller doğruluğu sürekli yukarı taşıdı ve bu satırların yazıldığı sırada kademeli olarak insan seviyesine yaklaştı. Ama doğruluk hiç de bitiş çizgisi değil — asıl darboğaz "doğru yapabiliyor mu" sorusundan "hızlı yapabiliyor mu" sorusuna kaydı.

**OSWorld-Human** verimlilik araştırması can sıkıcı bir gerçeği ortaya koyuyor: görev sonunda başarıyla tamamlansa bile, Agent'ın aynı görev için ihtiyaç duyduğu işlem adımı sayısı insandan belirgin biçimde fazla kalıyor; üstelik her adımın çıkarım gecikmesi görev ilerledikçe sürekli büyüyor — context uzadıkça model daha yavaş karar veriyor ve geç adımlar çoğu zaman erken adımlardan çok daha uzun sürüyor. Bir insanın onlarca saniyede bitirdiği bir doküman biçimlendirme işi, Agent'ın dakikalarını alabiliyor. **İnsan seviyesinde doğruluğa ulaşmak kullanışlılıkla aynı şey değildir; asıl darboğaz verimliliktir.**

Verimlilik sorununun kökeni ses senaryosundakine benzer: seri işleyen "ekran görüntüsü-düşünme-tıklama" döngüsünde her halka en uç noktasına kadar optimize edilse bile, adım adım biriken gecikme yine de kabul edilemez düzeyde kalır. Daha derindeki sorun şudur: bugünkü Computer Use "önceden düşünmeyi" hiç beceremiyor. Agent, mevcut eylemi yürütürken bir sonraki adımda ne yapacağını da öngörebilseydi — örneğin sayfa yüklenirken bir sonraki tıklamanın nereye yapılacağını çoktan kararlaştırabilseydi — düşünme ile yürütme zamanları üst üste bindirilebilir ve toplam gecikme büyük ölçüde düşürülebilirdi (bu, bu bölümün başındaki ses senaryosunda "düşünürken konuşma" ile Bölüm 4'teki "sürekli düşünme" tarzı asenkron Agent'ın talebinin aynısıdır; burada yalnızca "düşünürken işlem yapma"ya dönüşmüştür).

Ses alanından farklı olarak, Computer Use'un kendi gerçek zamanlılığı için — yani "ekran görüntüsü-düşünme-tıklama" döngüsünün kendisini hızlandırmak için — şu an sistematik bir çözüm yok; hâlâ kare kare ekran görüntüsüne dayalı ayrık bir döngüde takılı durumda. Ama bunu baypas eden bir fikir çoktan işler hâle geldi ve bu bölümde tekrar tekrar karşımıza çıkan hızlı-yavaş ayrıştırmasını kullanıyor: madem yavaş çalışan bilgisayar kullanma Agent'ını hızlandırmak zor, o hâlde **kullanıcıyı onu boş yere bekletmeyelim**. "Konuşma" ile "bilgisayarı kullanma" hızlı ve yavaş iki modele bölünüp eşzamanlı çalıştırılır[^ch9-10]: küçük bir model (hızlı) gerçek zamanlı sesli sohbeti üstlenir, öncü bir VLM (yavaş) tarayıcıda adım adım işlem yapar ve ikisi yalnızca son derece sade bir "düz metin sözleşmesi" üzerinden haberleşir. Yavaş Agent her işlemine, sürekli güncellenen tek cümlelik bir durum özeti ekler ("Formu dolduruyorum, doğum tarihine ihtiyacım var"); hızlı Agent buna dayanarak kullanıcıya gerçek zamanlı yanıt verir ve kullanıcının sözlü olarak verdiği yeni bilgileri yavaş Agent'a aktarır. Üstelik **durum özeti tamamlandığını teyit etmeden hızlı Agent asla "hallettim" diyemez**. Bu, tam olarak "bir yandan telefonda konuşurken bir yandan bilgisayarın kendi kendine işlem yapması" senaryosudur. Deneylerde bu ayrıştırma, sesli yanıtı "tek modelle hem işlem yapıp hem konuşma" yaklaşımına göre yaklaşık 15 kat hızlandırdı (medyan gecikme 0,58 saniyeye karşı 8,64 saniye) ve görev başarı oranı düşmedi; hızlı ile yavaş arasındaki o metin kanalı çekilip alındığında ise başarı oranı anında sıfıra çöktü — çünkü kullanıcının sözlü olarak verdiği kritik bilgi artık tarayıcıya ulaşamıyordu. Bu, daha önceki Latent Bridge ve ses senaryosundaki "düşünürken konuşma" ile aynı fikirdir: bir halka doğası gereği yavaşsa, hızlı olan başka bir halka kullanıcının bekleme süresini doldursun — üstelik o "düz metin sözleşmesi", özünde bu kitabın Bölüm 2'den beri anlattığı Agent durum çubuğundan başka bir şey değildir. Computer Use döngüsünün kendisini hızlandırmak muhtemelen hâlâ bir sonraki önemli araştırma yönü olacak, ama "hızlı-yavaş ayrıştırmasıyla 'yavaşlığı' saklamak" şimdiden kullanılabilir bir yanıttır.

[^ch9-10]: Ses-işlem hızlı-yavaş ayrıştırmasının ve "düz metin sözleşmesi"nin eksiksiz tasarımı için bkz. Li, Bojie and Noah Shi. *Talking While Acting: Real-Time Voice for Slow Computer-Use Agents.* 2026 (yayınlanacak).

## Robot Manipülasyonu: Gerçek Zamanlı Kontrolden Eğitim ve Genellemeye

> **Bu bölümdeki beş deney aynı görevi kullanır: kırmızı bardağı tepsiye koymak, sarı kâğıdı çöp kutusuna koymak, ardından masayı yeniden gözlemleyip durumu doğrulamak. Gerçek robot ve simülatör ayrı raporlanır; eylem anlamı ve başarı koşulları aynıdır.**
>
Sesli Agent'lar gecikmeyle işitsel modalitede, Computer Use ise görsel modalitede yüzleşir; Agent'ın fiziksel dünyadaki bir robotu kontrol etmesi gerektiğinde gecikme ve çok modluluk zorlukları daha da büyür — eylemlerin sonuçları geri alınamaz ve tek bir çarpışma nesneye ya da robotun kendisine zarar verebilir. Bu bölümde önce robotların iki katmanlı mimari ve action chunking ile gerçek zamanlı kontrol sorununu nasıl bastırdığına, ardından bugün karşılarındaki daha sert cevize — eğitim ve genellemeye — bakacağız: veri nereden gelecek, model görevler ve platformlar arasında nasıl aktarılacak?

### Darboğaz Donanım Değil, Algoritma

Robotlar genel amaçlı açık senaryolarda hâlâ yaygın olarak kullanılmıyor; peki darboğaz donanımda mı yoksa algoritmada mı? XLeRobot projesi güçlü bir karşı örnek sunuyor: maliyeti 1000 doları bulmayan çift kollu tekerlekli bir robot, insan tarafından VR başlığı üzerinden uzaktan kumanda edildiğinde (teleoperasyon) birçok ev işini şimdiden akıcı biçimde yapabiliyor. Becerikli el gerektiren daha karmaşık ev işlerini de Unitree'nin robotları insan teleoperasyonuyla akıcı biçimde tamamlayabiliyor. Teleoperasyon gecikmesi yaklaşık 100-200 ms; bu, fiziksel etkileşimin gerektirdiği tepki süresine yakın bir değer. Sensör çözünürlüğü, aktüatör hassasiyeti ve kontrol frekansı (robotun saniyede kaç kez eylem komutunu güncellediği; frekans düştükçe hareket daha az akıcı olur, titreme ya da hedef yörüngeden sapma olasılığı artar) bugünkü düşük maliyetli platformlarda pratik görevleri desteklemeye şimdiden yeterli.

Bu iddianın sınırını net çizmek gerekiyor: teleoperasyon karşı örneğinin asıl gösterdiği şey, "mevcut düşük maliyetli donanım artı insan zekâsının **ağırlıklı olarak görsel geri bildirime dayanan bu tür ev manipülasyon görevlerini** tamamlamaya yettiği"dir. Bu, donanımın her boyutta yeterli olduğu anlamına gelmez — dokunsal algılamanın yokluğu, becerikli ellerin güvenilirliği ve maliyeti bugün de herkesçe kabul edilen donanım eksiklikleridir; görev ince kuvvet kontrolüne ve dokunsal geri bildirime ağır biçimde bağımlı hâle geldiğinde donanım pekâlâ darboğaz olabilir. Dolayısıyla aşağıda söylenen "donanım darboğaz değil" ifadesi, bu bölümde tartışılan görev sınıfıyla sınırlıdır.

Bu tür görevler açısından bakıldığında asıl uçurum algoritma katmanındadır; sonraki iki alt bölüm bunu ayrı ayrı ele alıyor.

> **Deney 9-7 ★: XLeRobot teleoperasyonu ile masayı toplamak**
>
> **Amaç:** Gerçek bir XLeRobot'u uzaktan kullanarak aynı çok adımlı görevi tamamlamak ve masa durumunu doğrulamak.
>
> **İlke:** Birkaç yüz dolarlık kol, insan teleoperasyonu altında bu görevi yapabilir; bu görev için donanım gövdesi darboğaz değildir, farkı algı, planlama, kapalı çevrim kontrol ve hata kurtarma yaratır.
>
### İki Katmanlı Mimari: Planlama ile Kontrolün Ayrılması

Robotların karmaşık ev işlerini tamamlaması, iki farklı zaman ölçeğinde karar vermeyi gerektirir. Birinci katman, daha yavaş olan **uzun ufuklu planlamadır** (long-horizon planning): "mutfağı temizle" gibi üst düzey bir talimatı alt hedef dizisine ayırmak (tezgahı toplamak, bulaşık makinesini doldurmak, yüzeyleri silmek). Bu, ortamın semantiğini anlamayı, görev bağımlılıkları üzerine akıl yürütmeyi ve çok adımlı bir eylem planı kurmayı gerektirir — tıpkı insanın işe girişmeden önce "önce neyi, sonra neyi yapacağım" diye düşünmesi gibi. İkinci katman, daha hızlı olan **VLA kontrolüdür** (Vision-Language-Action, görsel-dil-eylem modeli): her somut işlemi yürütür ("lavaboya git", "bezi al", "tezgahı sil") ve o an gördüğü görüntüyle dil talimatına göre sürekli kontrol sinyali üreterek robotun hareketlerinin akıcı ve tutarlı olmasını sağlar.

Bu iki katmanlı mimari karmaşıklığı etkili biçimde ayırır: uzun ufuklu planlama "ne yapılacağından", VLA kontrolü ise "nasıl yapılacağından" sorumludur. Bu "üst düzeyde yavaş karar + alt düzeyde hızlı yürütme" biçimindeki iki katmanlı mimari, yukarıdaki ses senaryosunda anlatılan "hızlı-yavaş düşünme" ile yapısal olarak büyük benzerlik taşır — her ikisi de karmaşık düşünme ile gerçek zamanlı tepkiyi farklı modüllere ayrıştırır. Şunu hatırlatmak gerekir: buradaki "planlama / kontrol" ayrımı, hızlı-yavaş düşünmedeki "yavaş derin düşünme / hızlı gerçek zamanlı tepki" boyutunun ayrıştırılmasına karşılık gelir; üçüncü çözümdeki MPS'in "kurgulama beyni / ifade beyni" (Formulation Brain / Articulation Brain) biçimindeki "düşünme / ifade etme" ayrıştırmasına değil — ikincisi "düşünmek" ile "söylemek"i böler, birincisi ise "bütünü planlamak" ile "gerçek zamanlı yürütmek"i böler; bu iki "çift-X mimarisi"nin böldüğü boyutlar aynı değildir.

Bununla birlikte gerçek zamanlılık ortadan kalkmış olmaz, yalnızca VLA kontrol katmanına itilir ve orada **action chunking** (eylem parçalama; aşağıdaki "VLA Kontrolü" alt bölümüne bakınız) ile sindirilir: model tek bir çıkarımda gelecekteki kısa bir eylem dizisini üretir, kontrol iş parçacığı bunu yüksek frekansla oynatır ve tek çıkarımın gecikmesi dizinin tümünün yürütülme süresine yayılır. Ama burada kaçınılmaz bir denge vardır — parçalama, tepkiselliği pürüzsüzlükle takas eder: parça uzadıkça her çıkarımın gecikmesi daha ince yayılır ve hareket daha tutarlı olur, ama model bu süre boyunca yeni görüntüyü "göremez" ve ani değişikliklere (nesnenin yerinden alınması, birinin elini uzatıp önünü kesmesi) o kadar geç tepki verir. Gerçek zamanlılık ile pürüzsüzlük arasındaki bu tercih, iki katmanlı mimarinin ortadan kaldırmadığı, yalnızca yerini değiştirdiği bir gerilimdir.

Burada bu bölümün ana hattındaki bir dönüşü de belirtmek gerekiyor: robotik senaryosunda gerçek zamanlılık çelişkisi iki katmanlı ayrıştırma ve action chunking ile kısmen hafifletilmiş durumda; asıl çelişki artık **eğitim ve genellemeye** kaydı — yeterli gösterim verisi nasıl elde edilecek, model görevler ve platformlar arasında nasıl genelleyecek? Sonraki birkaç alt bölüm tam da bu yeni çelişki etrafında ilerliyor; bu aynı zamanda Bölüm 6'daki simülasyon ortamları ile Bölüm 7'deki pekiştirmeli öğrenme temalarının fiziksel dünyaya uzantısıdır.

Bu yeni çelişki esas olarak VLA kontrol katmanının üzerine biniyor. VLA'yı "VLM + eylem çıktısı" olarak düşünebilirsiniz: **VLM** (Vision-Language Model, görsel-dil modeli — görüntüyü ve metni aynı anda anlayabilen büyük model) "görmek"ten ve "düşünmek"ten sorumludur; VLA bunun üzerine bir de "iş yapmak" zorundadır ve asıl zorluk tam da bu "iş yapma" katmanındadır. Bugün VLA kontrol katmanı ağırlıklı olarak taklit yoluyla öğrenmeyle (davranış klonlama) eğitiliyor — çok sayıda insan gösteriminden doğrudan "ne görürsen onu yap" öğreniliyor (OpenVLA, RT-2, π₀ gibi modellerin hepsi bu kategoridedir); pekiştirmeli öğrenme ise son yıllarda bunun üzerine eklenen tamamlayıcı bir yöntemdir. Pekiştirmeli öğrenmeyle eğitilen VLA'lar tek bir görevde çok iyi performans gösterebilse de genelleme yetenekleri çoğu zaman yetersiz kalıyor: örneğin Bölüm 7'deki SimpleVLA-RL, LIBERO üzerinde çok yüksek tek görev sonuçları bildirse de bu sonuçlar her görev için ayrı ayrı yapılan RL eğitimlerinden geliyor; tüm görevlere zero-shot genelleyen tek bir birleşik modelden değil. Bu "her görev için bir eğitim" düzeni, her yeni görevde yeniden veri toplamak ve yeniden eğitmek anlamına geliyor.

Aşağıdaki iki alt bölüm sırasıyla uzun ufuklu planlama ile VLA kontrolünün somut teknik çözümlerini derinlemesine ele alıyor.

### Uzun Ufuklu Planlama: VLM'den Özel Bedenlenmiş Akıl Yürütme Modellerine

Genel amaçlı VLM'ler şimdiden fena olmayan bir bedenlenmiş akıl yürütme yeteneğine sahip. Google DeepMind'ın **Gemini Robotics-ER 1.5** modeli özellikle bedenlenmiş akıl yürütme (Embodied Reasoning, yani fiziksel dünyadaki nesnelerin konumunu, hareketini ve nedensel ilişkilerini anlamak) için optimize edilmiştir; 15 akademik benchmark üzerinde (Point-Bench, RefSpatial, RoboSpatial, BLINK vb.) ortalama %62,8 ile GPT-4o'yu (%60,6) ve Gemini 2.5 Pro'yu (%59,3) geride bırakır. Temel üstünlükleri arasında şunlar vardır: gelişmiş uzamsal kavrayış ve nesne konumlandırma, zamansal akıl yürütme ("bu bardağı devirirsem ne olur" gibi eylem-sonuç ilişkilerini öngörme), görev orkestrasyonu (üst düzey talimatları küçük adımlara ayırma); ayrıca düşünme (thinking) mekanizmasını ve tool calling'i yerleşik olarak destekler.[^ch9-2]

[^ch9-2]: Google DeepMind, "Gemini Robotics-ER 1.5". https://deepmind.google/models/gemini-robotics/gemini-robotics-er/

> **Deney 9-8 ★: Simülasyonda aynı görevin ideal kontrol üst sınırı**
>
> **Amaç:** Algılama ve eylem seçiminde hata yapmayan ideal denetleyiciyle aynı görevi çalıştırıp tekrarlanabilir üst sınır oluşturmak.
>
> **İlke:** Bu, kararların her zaman doğru olduğu durumun referansıdır; gerçek robotun çalıştırıldığı anlamına gelmez.
>

> **Deney 9-9 ★★: Gemini Robotics-ER 1.5 ile gerçek XLeRobot'u otonom kontrol etmek**
>
> **Amaç:** İnsanın yerine masayı gözleyen ve sınırlı pick, place, verify becerilerini çağıran bir Agent koymak; robotu, görevi ve başarı ölçütünü 9-7 ile aynı tutmak.
>
> **İlke:** Doğrudan karşılaştırma yeni bir mekanik sınırı değil; algı, planlama, zamanlama, kapalı çevrim ve hata kurtarma farkını gösterir.
>

### VLA Kontrolü: Gösterim Verisinden Çapraz Bedenlenme Genellemesine

İki katmanlı mimarinin yürütme katmanında RT-2, OpenVLA ve π₀ olmak üzere üç temsilci model VLA kontrolüne odaklanır — yani kamera görüntüsüne ve dil talimatına göre robotun eylemlerini gerçek zamanlı üretmeye (Şekil 9-11). Bu modeller eylem temsili bakımından iki ayrı yola ayrılır: ayrık eylem token'ları ile sürekli yörünge üretimi.


![Şekil 9-11: VLA mimarisi (Vision-Language-Action)](images/fig9-11.svg)


**RT-2 ve OpenVLA: ayrık eylem token'ı yolu.**

**RT-2** bu yolu açtı: doğrudan büyük ölçekli görsel-dil modelleri üzerinde fine-tuning yapar, robotun sürekli eylemlerini token'lara ayrıklaştırır ve tıpkı metin üretir gibi bunları tek tek otoregresif olarak çıkarır; böylece ön eğitimli modelin genelleme yeteneğinden yararlanarak yeni nesnelere ve yeni talimatlara zero-shot aktarımı iyileştirir. **OpenVLA** ise RT-2'nin eylem temsili şemasını sürdürdü; dil modeli ile görsel kodlayıcıyı tek bir mimaride birleştirir, girdi olarak görüntü ve yazılı talimat alır, çıktı olarak eylem token'ları üretir. Eğitim iki aşamalıdır: önce büyük ölçekli, platformlar arası Open X-Embodiment veri kümesinde (20'den fazla robot platformundaki gerçek manipülasyon gösterimlerini kapsar) ön eğitim yapılarak genel manipülasyon bilgisi öğrenilir ("kavrama", "yerleştirme" gibi eylem kalıpları farklı robotlar arasında ortaktır), ardından belirli bir platform için az miktarda veriyle fine-tuning yapılır. Eylem temsilleri özünde aynı olduğuna göre, ikisi arasındaki asıl fark açıklık ve mühendislik tercihlerindedir: RT-2 ve eğitim verisi Google'ın içindedir, OpenVLA ise tamamen açık kaynaktır — açık kaynak bir omurga model (Llama 2 artı görsel kodlayıcı) ile herkese açık bir veri kümesi, tüm topluluğa ilk kez bunun üzerine yeniden üretim ve iyileştirme yapma imkânı verdi.

**Action chunking: VLA alanında ortak kullanılan frekans telafisi tekniği.**

LLM çıkarımının gecikmesi olduğundan, VLA'nın kontrol frekansı geleneksel robot kontrolünün gerektirdiğinin çok altındadır (geleneksel robot kontrolü genellikle 50-1000 Hz kontrol frekansı ister, VLA'nın tek çıkarımı ise yalnızca 1-10 Hz dolayındadır — aradaki fark iki büyüklük mertebesine ulaşabilir). Orijinal OpenVLA bu sorunun tipik örneğidir: her çıkarımda yalnızca tek bir eylem üretir (yaklaşık 6 Hz'lik tek adımlı otoregresif tahmin) ve hareketlerinin takılması onun en çok eleştirilen eksiği olmuştur. **Action chunking** (eylem parçalama) tam da bu farkı kapatmak için doğmuş genel bir tekniktir — ilk kez ACT (Zhao ve ark., 2023) tarafından önerildi, sonra π₀ ve OpenVLA-OFT gibi modellerce yaygın olarak benimsendi: model her çıkarımda tek bir eylem değil, gelecekteki kısa bir zaman dilimine ait eylem dizisini bir seferde üretir (π₀'ın tipik yapılandırması örnek alınırsa, bir seferde yaklaşık 0,5-1 saniyelik bir eylem parçası, yani 50 Hz kontrol frekansında 25-50 eylem); kontrol iş parçacığı bunları yüksek frekansla sırayla yürütürken model arka planda bir sonraki partiyi asenkron olarak üretir. Modelin çıkarım süresi bu partinin yürütme süresinden kısa olduğu sürece robot sürekli ve akıcı hareket edebilir — tıpkı video ön belleğe alma gibi: sonraki içerik önceden yüklendiği için oynatma takılmaz.

**π₀: sürekli yörünge üretimi yolu.**

Eylem temsilindeki asıl ayrım RT-2 ile OpenVLA arasında değil, **ayrık token ile sürekli yörünge üretimi** arasındadır. **π₀** ikinci yolu temsil eder: ayrık eylem token'larını tek tek tahmin etmek yerine, flow matching (akış eşleme; difüzyon modelleriyle aynı kökten gelen sürekli bir üretim yöntemi) kullanarak rastgele gürültüden başlar, çok adımlı yinelemeli bir "gürültü giderme" süreciyle doğrudan pürüzsüz ve sürekli bir eylem yörüngesi üretir. Bu temsil, action chunking ile doğal biçimde birleşir ve becerikli manipülasyon gibi hareket hassasiyeti ile akıcılığın kritik olduğu görevlerde daha iyi sonuç verir. Bir benzetme yapmak gerekirse: ayrık token yolu bir menüden adım adım "5 derece sola", "3 santimetre ileri" seçmeye benzer; sürekli yörünge yolu ise ressamın önce tüm eğriyi kabaca çizip sonra fırça darbeleriyle son hâline getirmesine benzer.

### Sim2Real Transfer: Simülasyondan Gerçekliğe Uzanan Uçurum

Bölüm 6'daki simülasyon ortamları alt bölümü, sim-to-real gap'in (gerçeklik farkı) kaynağını ve domain randomization'ın (alan rastgeleleştirme) buna nasıl çözüm ürettiğini zaten açıklığa kavuşturmuştu; burada tekrar etmiyoruz — tek cümleyle özetlemek gerekirse: simülasyon gerçek fiziği, görüntüyü ve donanım özelliklerini tam olarak yeniden üretemediği için, eğitim sırasında bu parametreler geniş bir aralıkta rastgele karıştırılır ve politikanın her türlü değişime dayanıklı, genel bir temsil öğrenmesi zorlanır (Şekil 9-11). Aşağıda yalnızca bu ilkenin gerçek bir robot kolunda nasıl hayata geçtiğine bakacağız.


![Şekil 9-12: Sim2Real uçurumu ve Domain Randomization](images/fig9-12.svg)


Bu yolun çok sayıda başarılı örneği var: OpenAI'ın robot eliyle becerikli manipülasyonu (Dactyl projesi el içinde küp yeniden yönlendirmeyi gerçekleştirdi; devamındaki çalışma otomatik alan rastgeleleştirmesi (ADR) yardımıyla tek elle Rubik küpü çözmeyi başardı) ve ETH Zürih'in ANYmal'i (dört ayaklı robotun kar, moloz gibi karmaşık arazi koşullarında sağlam biçimde yürümesi) bunlar arasındadır.

Bu bölümde asıl tamamlanması gereken şey, domain randomization'ı gerçek bir makineye indirirken kaçınılmaz olan iki mühendislik halkasıdır. Birincisi **rastgeleleştirme aralığının kalibrasyonu**: aralık göz kararı belirlenemez; çok dar olursa gerçek değişimleri kapsamaz, çok geniş olursa eğitimi zorlaştırır ve "her şeye idare eder ama hiçbirinde iyi olmayan" alt optimal bir politika ortaya çıkar. Pratikte genellikle önce gerçek ortam verisinden kilit parametrelerin dağılımı **ölçümle kalibre edilir** (sürtünme katsayısının, motor tepki gecikmesinin gerçek dağılımı gibi) ve örnekleme bu aralıkta yapılır; simülasyonda eğitilen politika gerçek makinede belirgin biçimde puan kaybediyorsa rastgeleleştirme aralığı kademeli olarak genişletilir, ta ki sim-to-real gap kabul edilebilir bir düzeye inene kadar. İkincisi **görsel hizalamadır**: simülasyondaki ve gerçekteki kamera pozu (konum ve yönelim) hassas biçimde kalibre edilir (ortam hizalaması) ve gerçekte çekilmiş arka planlar simülasyon render'ına rastgele yerleştirilir (greenscreen arka plan değişimi); böylece simülasyon görüntüsü gerçek makinenin gördüğüne olabildiğince yaklaşır — bu iki adımı Deney 9-9 somut olarak gösterecek.

> **Deney 9-10 ★★: Simülatörde üç otonom döngüyü karşılaştırmak**
>
> **Amaç:** Aynı görev ve araçlarla açık çevrim, adım adım kontrol ve kısa ufuklu öngörü stratejisini karşılaştırmak.
>
> **İlke:** Adım kontrolü yerel hatadan kurtarır; dünya modeli tahmin gerçekle uyuştuğunda devam eder, ayrıştığında yeniden planlar. Son durum yeni gözlemle doğrulanır.
>

> **Deney 9-11 ★★★: Aynı görev için ortamlar arası RGB testi**
>
> **Amaç:** Arka planı, nesne görünümünü, ışığı ve görsel gürültüyü değiştirip simülasyonda öğrenilen politikanın yeni görüntülere uyumunu sınamak.
>
> **İlke:** Görsel çeşitlilik dayanıklılığı artırabilir, ancak gerçek robot kalibrasyonunun ve tam güvenlik döngüsünün yerini tutmaz.
>

### 2026 Güncellemesi: Akışkan Planlama ve Dünya Modelleri

Robotik bölümü “VLM bir plan yazar, VLA da uygular” cümlesinde bitmemeli. **“Masayı düzenle”** görevini düşünelim. Uzun ufuklu planlayıcı önce yarısı dolu bir fincanı, kâğıt parçalarını, üç kitabı, açık bir dizüstü bilgisayarı, çöp kutusunu ve bir saklama kutusunu içeren durum listesini çıkarır; ardından önkoşulları ve başarı kontrolleri olan komutlar üretir:

1. “Masaya git ve kenardan 30 cm uzakta dur.”
2. “İki kâğıt parçasını çöp kutusuna koy; hiç kâğıt kalmadığını doğrula.”
3. “Fincanı dik tutup tepsiye yerleştir; sıvı hareket ederse yavaşla.”
4. “Dizüstü bilgisayarı kapatıp arka sola taşı; güç kablosunu çekme.”
5. “Kitapları boyutlarına göre istifle ve kalemleri saklama kutusuna koy.”
6. “Kırılabilir ve elektriğe bağlı eşyalar kaldırıldıktan sonra masayı sil.”
7. “Geri çekil, yeniden gözlemle ve son durumu doğrula.”

Bu bir düzyazı paragrafı değil, bir bağımlılık grafiğidir. Kullanıcı “dizüstünü önce kaldır” derse sistem hedef önceliğini günceller. Fincan devrilirse robot güvenli bir noktada durur, `cup.orientation=fallen` ve `laptop.at_risk=true` gibi olguları kaydeder, eskimiş planın kuyruğunu geçersiz kılar ve yeniden planlar: dizüstünü koru, dökülen sıvıyı kontrol altına al, tekrar gözlemle, sonra yalnızca etkilenmeyen görevleri sürdür. Tamamlanmış eylemler tekrarlanmaz. Acil olaylar mevcut parçayı iptal eder; sıradan güncellemeler bir sonraki güvenli noktayı bekler.

### Akışkan yürütme

Planlama ile yürütme üst üste bindirilebilir. Güvenli bir önek hazır olur olmaz planlayıcı, kuyruğun geri kalanını planlamaya devam ederken eksiksiz bir komutu yürütücüye akıtır. Komut olayı eksiksiz ve denetlenebilir olmalıdır:

```text
{"type":"command.commit","seq":12,"command_id":"desk-02","command":"put paper in bin","preconditions":["paper.visible","bin.reachable"],"success":"paper_count=0","cancel_at":"before_grasp"}
```

Yürütücü `started`, `succeeded`, `cancelled` veya `failed` durumlarından birini bildirir. Planlayıcı bu gözlemlerle bağımlılıkları günceller; kuyruk eskimiş ya da doluysa backpressure uygular. Akışkan yürütme ilk güvenli eyleme kadar geçen süreyi kısaltır; eksik JSON’un veya doğrulanmamış model düşüncelerinin çalıştırılmasına izin vermez.

### Güncel VLA’lar neden kötü genelleme yapıyor?

OpenVLA tam anlamıyla yalnızca projector güncellenerek eğitilmiş değildir: özgün çalışma tam fine-tuning’in yanı sıra dondurulmuş vision encoder, yalnızca son katman ve LoRA varyantlarını da raporlar. Yine de temel eleştiri geçerlidir. Çok büyük bir metin/görüntü ön eğitim külliyatı, çok daha küçük bir robot veri kümesine dar bir uyarlama yoluyla bağlanır; düşük maliyetli uyarlama yeni davranışı çoğu zaman projector, LoRA modülleri veya action head üzerinde yoğunlaştırır. Behavior cloning “gözlem + talimat → action chunk” eşlemesini öğrenir, karşı-olgusal fiziksel sonuçları değil. Embodiment’e özgü eylem uzayları ve eskimiş action chunk’lar aktarımı daha da sınırlar. Dil backbone’u “fincan” kelimesini bilse de sürtünme, sıvı, temas ve güç kablosunun nasıl davranacağını bu yüzden bilmez.

**Eylem parçası öncelik kesmesi:**

```python
chunk = vla(current_observation, skill)
for action in chunk:
    low_level.execute(action)
    if safety_event() or observation_changed_significantly():
        low_level.stop()
        discard_remaining(chunk)
        reobserve_and_replan()
        break
```

### Dünya modelleri

Bir dünya modeli eyleme dönüştürülebilir bir geçiş öğrenir:

```text
durum + aday eylem -> tahmin edilen gelecek durum -> eylemi seç ve doğrula
```

Bu kavram yalnızca V-JEPA’dan ibaret değildir. Aile; latent predictive model’leri (V-JEPA 2), etkileşimli üretici modelleri (Genie 3 ve Cosmos), World-Action Model’leri (GeniWorld ve Robust-WAM), etiketsiz videodan latent action öğrenimini (LAWM-3D) ve model tabanlı RL’yi (Dreamer ve MuZero) kapsar. Değeri; büyük ölçekte gözlemden öğrenmek, eylemleri gerçekleştirmeden önce karşı-olgusal sonuçlarını sınamak, ortak dinamikleri embodiment’e özgü kontrolden ayırmak ve tahmin gerçeklikten saptığında yeniden planlamaktır.

2026 tarihli yeni preprint’ler ortak dinamik öncüllerini ve embodiment’e özgü head’leri (DyPES-VLA), dağılım dışı kapalı çevrim manipülasyon için görsel-eylem temsillerini (GeniWorld), insan videolarından 3B farkındalıklı latent action’ları (LAWM-3D), semantic foresight alignment’ı (Robust-WAM) ve eşzamansız gerçek zamanlı dağıtımı inceliyor. Bunlar umut verici araştırma sonuçlarıdır; genellemenin çözüldüğünü göstermezler.

## Bölüm Özeti

Üç senaryo yüzeyde birbirinden çok farklı görünüyor, ama gecikme ve çok modluluk biçimindeki iki engel hepsinin peşini hiç bırakmıyor. Ses; seri boru hattından uçtan uca ve full-duplex mimarilere, birbirinden ayrı hızlı-yavaş düşünmeden "düşünürken konuşma"ya uzanan bir evrim yolunu şimdiden katetti. Computer Use'un OSWorld gibi benchmark'lardaki doğruluğu insan seviyesine yaklaştı, ama işlem adımlarının insandan belirgin biçimde fazla olması ve adım sürelerinin görev ilerledikçe sürekli artması biçimindeki verimlilik farkının sistematik bir çözümü hâlâ yok. Robotikte ise ağırlıklı olarak görsel geri bildirime dayanan manipülasyon görevlerinde darboğaz donanımdan VLA kontrol katmanının görevler arası genelleme yeteneğine kaydı (dokunsal algılama, becerikli eller vb. hâlâ aşılamamış donanım eksiklikleridir). Bir sonraki bölüm bakış açısını birden fazla Agent arasındaki iş birliğine çevirecek; orası bambaşka bir boyutun zorluğudur.

## Düşünce Soruları

1. ★★ Sesli Agent'ların uçtan uca modeli ASR-LLM-TTS zincirini tek bir modelde birleştirir; gecikmeyi düşürür ama modülerliği kaybeder. Uçtan uca model bir halkada (örneğin konuşma tanımada) hata yaparsa, hata ayıklamak ve düzeltmek seri boru hattına göre çok daha zordur. Uçtan uca bir sesli Agent'ın gözlemlenebilirlik (observability) sistemini nasıl tasarlardınız?
2. ★ Step-Audio R1, MPS çift beyin mimarisiyle "düşünürken konuşma"yı gerçekleştiriyor. Ama insanlar "düşünürken konuşurken" sık sık iyi düşünülmemiş şeyler söyler, kendini düzeltir ya da dolgu sözcükleri kullanır. Agent'ın "düşünürken konuşması" insandaki bu özellikleri taklit etmeli mi?
3. ★★ SoM (Set-of-Mark) ve onun yapısal türevi (DOM öğe indeksleme), Computer Use'un görsel konumlandırmasını açık uçlu koordinat tahmininden kapalı uçlu ID seçimine dönüştürür; ama her ikisi de önce arayüz öğelerinin tespit edilip işaretlenmesini gerektirir — ister segmentasyon modeliyle ister DOM'la olsun. Arayüzde standart dışı kontroller veya dinamik olarak değişen öğeler varsa, işaretleme eksik ya da hatalı olabilir. Bu durumda koordinat tahminine geri dönmeli mi?
4. ★★ XLeRobot gibi bin dolar seviyesindeki robot platformları teleoperasyon verisi toplamayı ucuzlattı. Ama teleoperasyon verisinin kalitesi büyük ölçüde operatörün becerisine bağlıdır. Deneyimsiz bir operatörün sağladığı veri, VLA modelinin eğitimini nasıl etkiler? Veri toplama aşamasında düşük kaliteli veriyi otomatik olarak nasıl elerdiniz?
5. ★★★ Bu bölüm ses, Computer Use ve robotik olmak üzere üç etkileşim biçimini kapsadı. Bu üç biçimin ortak eğilimi, seri boru hattından uçtan uca modellere doğru evrilmek. Bu eğilim sürerse, beş yıl sonraki Agent etkileşim katmanı nasıl görünecek?
6. ★★★ Bugünkü Computer Use, "ekran görüntüsü → eylem → ekran görüntüsü" biçiminde ayrık bir döngüyle çalışıyor ve her gözlem tek bir durağan kareden ibaret. Oysa insanın ekran algısı süreklidir — animasyonun oynadığını görebilir, yükleme ilerlemesini izleyebilir, video içeriğini anlayabiliriz. Bu da bugünkü Computer Use'un zamansal görsel anlama gerektiren görevleri kesinlikle yapamayacağı anlamına geliyor. Sürekli görsel akış anlamayı destekleyecek biçimde algı katmanını nasıl yeniden tasarlarsınız?
7. ★★ DOM/Accessibility Tree öğe indekslemesi standart Web uygulamalarında belirgin sonuç veriyor, ama gitgide daha çok yazılım arayüzü (Canvas/WebGL render'ı, platformlar arası kendi çizen kontroller) erişilebilir yapısal bilgi sunmuyor ve geriye yalnızca görsel işaretleme ya da koordinat tahmini kalıyor. Sizce Computer Use saf görsel yola mı oynamalı, yoksa yapısal ve görsel iki yolu birden mi sürdürmeli? İki yolu birden sürdürmenin maliyeti ve getirisi nedir?
8. ★★ VLA modelleri action chunking (eylem parçalama) kullanıyor — metinde anlatıldığı gibi, π₀'ın tipik yapılandırması 50 Hz frekansta 25-50 gelecek eylemi bir seferde üretmektir — ve böylece çıkarım gecikmesini yürütme süresinin içine saklıyor. Ama yürütme sırasında ortam ani biçimde değişirse (örneğin nesne yerinden alınırsa), önceden üretilmiş eylem dizisi geçersizleşir. Action chunking'in verimlilik avantajı ile ortam değişimlerine tepki hızı arasında dengeyi nasıl kurarsınız?
9. ★★★ Bu bölümdeki üç senaryonun (ses, Computer Use, robotik) hepsi "algılama-düşünme-eylem" döngüsünün gecikme sorunuyla yüzleşiyor ve hepsi hızlı-yavaş düşünmenin paralelleştirilmesi yönünde evriliyor. Ses senaryosunda bu, "yanlış söylediysen sonra düzelt" biçiminde; Computer Use senaryosunda "önce tıkla sonra bak" biçiminde; robotik senaryosunda ise "bir adım at sonra bak" biçiminde ortaya çıkıyor. Hızlı düşünmeye dayanan bu eylemlerin geri döndürülemez sonuçlara yol açmamasını nasıl garanti edersiniz?
