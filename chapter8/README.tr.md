# Bölüm 8 · Agent'ın Kendi Kendine Evrimi

> Ağırlıkları değiştirmeden büyüme. Üç öğrenme paradigması, deneyimden öğrenme ve "araç kullanıcısından" "araç yaratıcısına" giden yolculuk; Agent'ların "akıllı"dan "usta"ya ilerlemesini sağlar.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter8.tr.md)

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| [gaia-experience](gaia-experience/) | ✅ | AWorld çerçevesi ve GAIA kıstasına dayalı olarak eksiksiz bir "öğren-uygula" döngüsü uygular. Ajan, başarılı görev izlencelerini otomatik olarak yapılandırılmış deneyimlere özetler ve bunları yeni görevlerde getirip uygulayarak kendi kendine evrim gerçekleştirir. |
| [browser-use-rpa](browser-use-rpa/) | ✅ | Tarayıcı otomasyonu için bir iş akışı kayıt sistemi uygular; tekrarlanan işlem dizilerini otomatik olarak parametreli araçlara kapsüller. Pahalı LLM çıkarımından kesin otomatik yürütmeye geçerek 3-5 kat hız artışı sağlar. |
| [prompt-distillation](prompt-distillation/) | ✅ | Karmaşık promptların etkinliğini model parametrelerine damıtır; çıkarım sırasında prompt uzunluğunu azaltır ve bağlamsal deneyimi parametreli bilgiye dönüştürür. |
| [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | İnsan geri bildirimine dayalı otomatik sistem istemi öğrenimi: tau-bench tarzı havayolu müşteri hizmetleri "aşırı aktarma" sorununu örnek alarak, bir Coding Agent sistem istem dosyasını okur, sorunlu kuralları belirler, kesin değişiklikler üretir ve istem dosyasını gerçekten yeniden yazar. Ardından değişiklikleri yeniden değerlendirir, "geri bildirim → yeniden yazma → doğrulama" döngüsü oluşturur. |
| [self-evolving-tools](self-evolving-tools/) | ✅ | Alita tarzı bir "minimal ön tanım, maksimum kendi kendine evrim" yaklaşımı: ajanın önceden inşa edilmiş alana özgü aracı yoktur, yalnızca beş genel meta-araç vardır. Yapamayacağı bir görevle karşılaştığında, açık kaynak kütüphaneler/API'ler için web'de arama yapar, dokümantasyon okur, bir sandbox'ta test eder, uygulanabilir çözümleri yeni araçlar olarak kapsüller, yeniden kullanım için araç kütüphanesinde saklar ve tüm süreç boyunca halüsinasyon kontrolüne vurgu yapar. |
| [self-evolution-eval](self-evolution-eval/) | ✅ | Bir ajanın "kendi kendine evrim" yeteneğini (araçları kendi başına keşfetme, yaratma ve yeniden kullanma) değerlendirmek için tasarlanmış özel bir veri kümesi ve doğrulama metodolojisi: 20 alanlar arası görev (araç isimlerine ipucu vermeden) + dört katmanlı hiyerarşik doğrulama harness'i + kontrol edilebilir bir referans ajan. "Sonuç doğru mu" kontrolünün ötesine geçerek keşif, yaratma ve yeniden kullanımın kalitesini değerlendirir. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
