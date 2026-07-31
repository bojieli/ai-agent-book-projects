# Experiment 7-6 checkpoint-free voice-SFT training report

## Result

Status: **passed**. The package retains two immutable executed Unsloth notebooks, 358 step-level loss rows, four notebook-embedded WAV outputs, and two raw direct-audio Voxtral judgments.

| Track | Steps | First loss | Final loss | First-20 mean | Last-20 mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| Orpheus | 298 | 5.1138 | 4.4980 | 4.8349 | 4.4181 |
| Sesame | 60 | 4.8070 | 4.7306 | 5.0374 | 4.8061 |

## Direct-audio observations

The Orpheus WAV received transcript accuracy 5/5 and naturalness 4/5. The judge reported audible paralinguistic activity=True (laughter, confidence 0.95).
For Sesame's same-text B/C pair, the judge reported voice similarity 5/5 and style similarity 5/5.

## Negative finding: the mechanism labels are reversed

The executable book sources and immutable upstream notebooks do not support the manuscript's Orpheus=reference-audio consistency / Sesame=paralinguistic-tag mapping. The retained Orpheus path serializes SNAC tokens and demonstrates a <giggle> text tag, while the Sesame path supplies prior audio in CSM conversation context for speaker/style conditioning and contains no <laugh>/<sigh> tag protocol. This contradiction is reported rather than converted into a positive result.

## Provenance boundary

The executed notebooks are public upstream reference runs at one immutable Git commit. They are not represented as author-local runs. Author-local adapters and outputs were not retained; checkpoints remain intentionally undistributed and are not acceptance artifacts.
The reproduction contract freezes notebook blobs, model/data/codec revisions and weight objects, all book source hashes, commands, and the remaining CUDA-environment limits.
