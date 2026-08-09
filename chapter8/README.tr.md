# Bölüm 8 · Agent'ın Kendi Kendine Evrimi

> Ağırlıkları değiştirmeden büyüme. Üç öğrenme paradigması, deneyimden öğrenme ve "araç kullanıcısından" "araç yaratıcısına" giden yolculuk; Agent'ların "akıllı"dan "usta"ya ilerlemesini sağlar.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter8.tr.md)

## Eşlik Eden Projeler

| Deney | Proje | Tür | Açıklama |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | Ortam sonuçlarını, süreç kurallarını ve dilsel ölçütleri birleştirerek müşteri hizmetleri yörüngeleri için kanıta dayalı teşhisler üretir. |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | Başarılı, kısmen başarılı ve başarısız yörüngeleri karşılaştırarak yörüngeler arası Markdown deneyim belgeleri oluşturur. |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Başarısız yörüngelerden asgari istem yamaları üretir; yayına almayı bir sınır kümesi ve bir koruma kümesiyle denetler. |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | Tarayıcı yörüngelerini durum yüklemleri olan iş akışlarına derler ve bunları sıfırlayıp yeniden oynatarak doğrular. |
| 8-5 | [self-modifying-agent](self-modifying-agent/) | ✅ | Tekrarlanan başarısızlıklar yeniden deneme/devre kesici kod yamalarını tetikler; gerileme testleri, kademeli dağıtım ve geri alma ile güvence sağlanır. |
| 8-6 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Deney 8-6: Hermes'e kitabın tamamını ve kendi kaynağını verir; bir iyileştirme seçip kendini değiştirir ve her Reviewer reddini kabul edilene kadar yeni bir öğrenme turuna dönüştürür. |
| 8-7 | [self-evolution-eval](self-evolution-eval/) | ✅ | Deney 8-7: öğrenme, aktarım, kural değişimi ve korumayı kapsayan uzun vadeli üç kollu değerlendirme; 3 seed × 14 sıralı görev boyunca 126 gerçek çağrının kanıtını saklar. |
| 8-8 | [harness-safety-gate](harness-safety-gate/) | ✅ | Yüksek riskli işlemler için onay kapısı (8-8). |
| 8-9 | [ai-style-skill](ai-style-skill/) | ✅ | Yazım geri bildirimini doğrulanabilir Skill'e dönüştürür (8-9); bölüm, kıvrımlı tırnak Skill'ini denetlenmiş sentetik veri ve sonradan eğitimle ilişkilendirir, exact-copy tokenizer/Harness hatalarını ayırır. |

## Ek Örnekler

| Deney | Proje | İlişki |
| :--: | --- | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | Bölümler arası proje: istem damıtma ve parametreli öğrenme; eğitim yöntemi Bölüm 7'ye aittir |
| — | [self-evolving-tools](self-evolving-tools/) | Alita tarzı araç keşfi, kapsülleme ve yeniden kullanım — deneyimi "programlara yazma" fikrinin tamamlayıcı bir örneği |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
