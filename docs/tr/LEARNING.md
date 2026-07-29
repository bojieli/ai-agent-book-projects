# Öğrenme Önerileri

← [Ana README'ye dön](README.md)


### Temel Kavram: Agent = Model + Bağlam + Araçlar

Bu kitabın temel çerçevesi **Agent = Model + Bağlam + Araçlar**'dır. Bu üç bileşen, bir ajanın akıllı davranışını gerçekleştirmek için birlikte çalışır:

- **Model**: Ajanın beyni; anlama, muhakeme ve karar verme yeteneklerini sağlar.
- **Bağlam (Context)**: Ajanın işletim sistemi; sistem talimatlarını, diyalog geçmişini, muhakeme süreçlerini, araç etkileşim kayıtlarını vb. içerir.
- **Araçlar (Tools)**: Ajanın elleri; ortamı algılamasını, eylemleri yürütmesini ve dış dünyayla etkileşim kurmasını sağlar.

### Öğrenme Yolu

Öğrenme yolu, kitabın tamamına bölüm bölüm karşılık gelir ve üç temel direk etrafında katman katman açılır:

- **Bölüm 1 · Temeller**: Ajan sistemleri için eksiksiz bir bilişsel çerçeve kurun—RL'deki ajan tanımını anlayın, geleneksel RL ile LLM+RL paradigmaları arasındaki örnek verimliliği farklarını karşılaştırın, "ajan olarak model" yeni paradigmasını kavrayın ve **Agent = Model + Bağlam + Araçlar** temel çerçevesine hakim olun. **Temel İçgörü**: Ön bilginin önemi algoritmaları ve ortamları aşar.

- **Bölüm 2–3 · Bağlam**: Bağlam, ajanın işletim sistemidir. Bölüm 2, sistem istemlerini, KV Cache dostu tasarımı, bağlam sıkıştırmayı ve prompt mühendisliği ablasyonunu kapsar. Bölüm 3, kullanıcı belleğini, yoğun/seyrek/hibrit erişimi, Agentic RAG'ı, bağlam duyarlı erişimi ve yapılandırılmış bilgi çıkarımını kapsar. **Temel İçgörü**: Tam bağlam; sistem talimatlarını, diyalog geçmişini, muhakeme süreçlerini, araç etkileşim kayıtlarını, kullanıcı belleğini ve harici bilgiyi içerir.

- **Bölüm 4–5 · Araçlar**: Araçlar, ajanın dünyayla etkileşim kurmasının köprüsüdür. Bölüm 4, üç tür MCP aracını (algı/yürütme/işbirliği), olay tetiklemesini ve asenkron mimariyi kapsar. Bölüm 5, üretim seviyesinde bir Coding Agent'ın tam uygulamasına iner. **Temel İçgörü**: Araç tasarımı genelleştirilmiş olmalıdır (bir kod yorumlayıcı bir hesap makinesinden daha iyidir); kod, yeni araçlar yaratan meta-yetenektir.

- **Bölüm 6–7 · Model**: Zekayı nasıl ölçer ve büyütürüz. Bölüm 6, Terminal-Bench, SWE-bench, GAIA, OSWorld ve Tau2-Bench gibi değerlendirme kıstaslarını kapsar. Bölüm 7, SFT, RL, RLHF ve örnek verimliliği gibi eğitim sonrası teknikleri kapsar. **Temel İçgörü**: Bağımsız bir doğrulama sinyali, "modele tekrar düşünmesini sormaktan" daha güvenilirdir; "ajan olarak model", RL yoluyla araç çağrılarını yerel bir yeteneğe içselleştirir.

- **Bölüm 8 · Kendi Kendine Evrim**: Ajanların, ağırlıkları değiştirmeden deneyimden büyümesini sağlayın—deneyim öğrenimi, iş akışlarını araçlara dışsallaştırma, promptları ve gözlemleri parametrelere damıtma. **Temel İçgörü**: Deneyimden öğrenme, bir ajanın "akıllı" olmaktan "usta" olmaya geçmesinin anahtarıdır.

- **Bölüm 9–10 · Genişleme ve İşbirliği**: Bölüm 9, algı ve eylemi metinden sese, GUI'ye ve fiziksel dünyaya genişletir. Bölüm 10, karmaşık görevleri ele almak için çoklu ajan iş bölümünü kullanır. **Temel İçgörü**: Çoklu ajan sistemindeki her tasarım kararı, tekil bir ajanın üç unsurunda karşılığını bulabilir.

### Zorluk Seviyeleri

- **Başlangıç** (Bölüm 1–2): Yeni başlayanlara uygun, temel kavramları anlama.
- **Orta** (Bölüm 3–4): Biraz programlama altyapısı gerektirir, sistem entegrasyonunu içerir.
- **İleri** (Bölüm 5–6): Güçlü programlama becerileri gerektirir, karmaşık sistem tasarımını içerir.
- **Uzman** (Bölüm 7–8): Derin öğrenme ve eğitim/kendi kendine evrim deneyimi gerektirir.
- **Uygulama** (Bölüm 9–10): Önceki bilgilerin pratik uygulamalar inşa etmek için kapsamlı kullanımı.

### Pratik Öneriler

1.  **Uygulamalı Pratik**: Her proje bağımsız çalıştırılabilecek şekilde tasarlanmıştır. Kodu kendiniz çalıştırıp değiştirmeniz önerilir.
2.  **Kitapla Birleştirin**: Teori ve pratiğin birleşimini anlamak için bu deponun [`book-tr/`](../../book-tr/) dizinindeki (Türkçe) ya da [`book/`](../../book/) dizinindeki (Çince orijinal) ilgili bölümlerini okuyun.
3.  **Deneysel Karşılaştırma**: Pek çok proje ablasyon çalışmaları ve karşılaştırmalı deneyler içerir. Karşılaştırma yoluyla anlayışınızı derinleştirin.
4.  **Kademeli Öğrenme**: Basit projelerle başlayın ve giderek karmaşık sistemlere inin.
5.  **Protokollere Odaklanın**: Bölüm 4'teki MCP sunucu projesi, ölçeklenebilir ajanlar inşa etmenin anahtarı olan standartlaştırılmış araç protokollerini gösterir.
