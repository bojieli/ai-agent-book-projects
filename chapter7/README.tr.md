# Bölüm 7 · Model Eğitim Sonrası

> Pre-training, SFT ve RL üç aşamasının kapsamlı bir görünümü. SFT mi RL mi ne zaman seçilir, RLHF, algoritma karşılaştırması, veri ve ortamlar; modellere araç çağırma öğretme ve örnek verimliliğini artırma konusundaki sınır keşifleri.

← [Ana README'ye dön](../README.tr.md) · 📖 [Bölüm metnini oku](../book-tr/chapter7.tr.md)

## Eşlik Eden Projeler

| Proje | Tür | Açıklama |
| --- | :--: | --- |
| [learning-from-experience](../chapter1/learning-from-experience/) (7-1, 7-2) | ✅ | Deneyimden öğrenmek için aynı hazine avı ortamında Q-learning ve LLM Agent çalıştırır. |
| [prompt-distillation](../chapter8/prompt-distillation/) (7-8) | ✅ | Öğretmen örneklerini öğrenci prompt'una damıtır ve kalite ile maliyeti karşılaştırır. |
| [AdaptThink](AdaptThink/) | 📖 | Muhakeme modellerine, problem zorluğuna göre muhakeme modunu (Thinking vs NoThinking) uyarlanabilir şekilde seçmeyi öğretir. Kısıtlı optimizasyon ve önem örneklemesi yoluyla, doğruluğu artırırken muhakeme maliyetlerini önemli ölçüde azaltır (%45-69). DeepSeek-R1-Distill-Qwen modeline dayanır, DAPO algoritmasıyla eğitilir. |
| [retool](retool/) | 📖 | Büyük dil modellerinin matematiksel muhakeme yeteneğini artırmak için çok turlu diyalog ve bir kod sandbox'ı kullanır. SFT ve RL'den oluşan iki aşamalı bir eğitim süreciyle model, matematik problemlerini çözmeye yardımcı olmak için bir kod yürütme ortamını kullanmayı öğrenir. Qwen2.5-32B-Instruct'a dayanır, AIME 2024 veri kümesinde DAPO algoritması ve SandboxFusion sandbox'ı kullanılarak eğitilir. |
| `AWorld/` · [AWorld-train](AWorld-train/) | 📖 | AWorld çerçevesine dayalı olarak somutlaşmış (embodied) ajanları eğitir; ajanların sanal bir ortamda karmaşık görevleri yerine getirmesini ve deneyimden öğrenmesini sağlar. |
| `SFTvsRL/` | 📖 | Denetimli İnce Ayar (SFT) ve Pekiştirmeli Öğrenmenin (RL) farklı görevlerdeki etkinliğini sistematik olarak karşılaştırır; her iki yöntemin güçlü yanlarını, zayıf yanlarını ve uygun uygulama senaryolarını analiz eder. |
| [premature-completion-dpo](premature-completion-dpo/) (7-17) | ✅ | GPU üzerinde erken tamamlama bad case için DPO düzeltmesi. |
| [curly-quote-sft](curly-quote-sft/) (7-18) | ✅ | Denetimli kapsam duyarlı Çince kıvrımlı tırnak SFT'si: 10 belge türü ve 9 programlama dilinde 1024/256/256 train/holdout/sınır örneği; Qwen3-8B exact 96,9%/97,7%, korunan alan 100%. |
| [exact-copy-sft](exact-copy-sft/) (7-19) | ✅ | Denetimli byte-exact özel dize kopyalama SFT'si: 1024/256/256 örnek; Qwen3-8B holdout 78,9%, sınır 80,1%, Qwen3/Qwen2.5/Mistral tokenizer denetimiyle. |
| `verl/` | 📖 | verl, büyük dil modellerinin RLHF eğitimi için özel olarak tasarlanmış verimli bir pekiştirmeli öğrenme çerçevesidir; PPO, GRPO ve DAPO gibi çeşitli algoritmaları destekler. |
| [Intuitor](Intuitor/) | ✅ | Modellerin sezgisel muhakeme yeteneğini eğitir; ayrıntılı düşünce zincirleri gerektirmeden hızlı, makul kararlar vermelerini sağlar. |
| [MultilingualReasoning](MultilingualReasoning/) | ✅ | Modellerin çok dilli ortamlardaki muhakeme yeteneğini eğitir; diller arası görevlerdeki performansı artırır. |
| [cot-distillation](cot-distillation/) | ✅ | Claude gibi öncü modellerden OpenRouter aracılığıyla CoT trajectory'leri damıtır, bunları kural tabanlı doğrulayıcılarla süzer ve Deney 7-9 için SFT verisi üretir. |
| [SpatialReasoning](SpatialReasoning/) | 📖 | Konum, yön ve mesafe gibi uzamsal ilişkileri içeren problemleri ele almak için modellerin uzamsal muhakeme yeteneğini eğitmeye odaklanır. |
| [SimpleVLA-RL](SimpleVLA-RL/) | 📖 | Görsel, dil ve eylemi pekiştirmeli öğrenme eğitiminde birleştirir; modellerin görsel girdiyi anlamasını ve karşılık gelen eylemleri yürütmesini sağlar. |
| [RLVP](RLVP/) | 📖 | Sonucu ödüllendirip hatalı yolu cezalandıran RLVP sonradan eğitim araştırmasıdır; tam eğitim ve değerlendirme kodu harici \`19PINE-AI/rlvp\` deposundan klonlanır. |
| [continued-pretraining](continued-pretraining/) | ✅ | Hedef alandaki model performansını artırmak için alana özgü veriler üzerinde sürekli ön eğitim yapar. |
| [MiniMind-pretrain](MiniMind-pretrain/) | 📖 | Tam ön eğitim sürecini ve temel teknikleri anlamak için küçük bir dil modelini sıfırdan ön eğitir. |
| [sesame](sesame/) | ✅ | Dizi modelleme görevleri için eğitim ve değerlendirme yöntemlerine odaklanır. |
| [orpheus](orpheus/) | ✅ | Müzik üretimi ve anlama için modeller eğitir. |
| `tinker-cookbook/` | 📖 | Model eğitimi için çeşitli pratik ipuçları ve en iyi uygulamaları bir araya toplar. |

## Proje Türleri

| İkon | Tür | Anlamı |
| :--: | --- | --- |
| ✅ | **Bağımsız** | Bu depoda tam kod, API Key yapılandırıldıktan sonra çalışır |
| 📖 | **Yeniden Üretim Rehberi** | `git clone` ile **harici depolara** bağımlı ayrıntılı belge |
| 🚧 | **Tasarım Belgesi** | Yalnızca mimari/uygulama planı, çalıştırılabilir kod henüz hazır değil |
