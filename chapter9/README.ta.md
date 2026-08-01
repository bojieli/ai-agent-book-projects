# அத்தியாயம் 9 · பல்முக மற்றும் நிகழ்நேர இடைவினை

> உணர்தல் மற்றும் செயலை உரையிலிருந்து குரல், GUI மற்றும் இயற்கை உலகத்திற்கு விரிவுபடுத்துகிறது. குரலின் மூன்று முன்னுதாரணங்கள் (அடுக்கப்பட்ட / இறுதி-முதல்-இறுதி முழு-வடிவ / முழு-இருவழி), ஸ்ட்ரீமிங் குரல் உணர்தல் மற்றும் தொகுப்பு, Computer Use மற்றும் ரோபோ செயல்பாடு ஆகியவற்றை உள்ளடக்கியது.

← [முக்கிய README க்குத் திரும்பு](../docs/ta/README.md) · 📖 [அத்தியாய உரையைப் படி](../book-ta/chapter9.ta.md)

## துணை திட்டங்கள்

| சோதனை | Project | Type | Description |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | நிகழ்நேர குரல் அரட்டை டெமோ, பேச்சு-முதல்-உரை, AI உரையாடல் மற்றும் உரை-முதல்-பேச்சு செயல்பாடுகளை ஒருங்கிணைக்கிறது. பல AI சேவை வழங்குநர்களை (OpenAI, OpenRouter, ARK, Siliconflow) ஆதரித்து, குறைந்த தாமத உரையாடல் அனுபவத்தை வழங்குகிறது. |
| 9-2 | [phone-agent](phone-agent/) | 🚧 | அதிகாரப்பூர்வ `pine-voice` SDK direct/ReAct பாதைகள் உள்ளன; ஆனால் ஒப்புதல் பெற்ற E.164 இலக்கு இல்லை. Preflight dial/transcript இல்லை என்று பதிவு செய்கிறது; test double acceptance அல்ல. |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | ஸ்ட்ரீமிங் குரல் உணர்தலின் முக்கிய பரிமாற்றத்தை விளக்குகிறது: தொடர்ச்சியான ஆடியோவை அதிகரிக்கும் நீளத் தொகுதிகளாகப் பிரித்து ASR-க்கு ஊட்டி, ஒவ்வொரு சிறு பகுதி கிடைத்தவுடன் "தற்போதைய பகுதி அங்கீகார முடிவை" உருவாக்கி, மிகக் குறைந்த முதல்-பாக்கெட் தாமதத்துடன் (first-packet latency) உரையை விரைவில் வெளியிடுகிறது; இதன் விலை, பின்னர் வரும் வாக்கியச் சூழல் இல்லாததால் ஆரம்பத் தொகுதிகள் தவறாக இருக்கலாம், ஆடியோ குவியும்போது படிப்படியாக ஒருங்கமைகிறது—"முழு வாக்கியம் வரும் வரை காத்திருந்து அங்கீகரித்தல்" என்ற உயர் துல்லியம்/உயர் தாமத அணுகுமுறைக்கு மாறானதாக உள்ளது. |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | நிலைநிறுத்தப்பட்ட revision கொண்ட MiniCPM-o 4.5 ஒரு RTX PRO 6000-இல் உண்மையாக உள்ளூரில் இயக்கப்பட்டது; end-to-end மற்றும் self-cascade இரண்டும் 3/4, மேலும் உண்மையான 24kHz ஒலி வெளியீடும் ஏற்றுக்கொள்ளல் சான்றும் சேமிக்கப்பட்டன. |
| 9-5 | [controllable-tts](controllable-tts/) | 🚧 | Real Fish Audio S1 4×3×2 reference library மற்றும் A/B/C media structure gates கடக்கின்றன; qualitative listening study மற்றும் “near-human” மதிப்பீடு இன்னும் இல்லை. |
| 9-6 | `claude-quickstarts/computer-use-demo/` | 📖 | வெளிப்புற `anthropics/claude-quickstarts` `9bcc95e…`-இல் pin செய்யப்பட்டது; புத்தகத்தில் கேட்கப்பட்ட இலக்கு Ubuntu desktop＋Claude agent loop கொண்ட containerized Computer Use demo ஆகும். |
| 9-7 | `browser-use/` | 📖 | வெளிப்புற `browser-use/browser-use` `ec9277c…`-இல் pin செய்யப்பட்டது; `use_vision=True` visual CLI Google-ல் San Francisco weather தேடி action/screenshot trajectory-ஐ வைத்திருக்க வேண்டும். |
| 9-8 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | வெளிப்புற XLeRobot `3d14695…` keyboard/Xbox/Joy-Con/VR teleoperation. Source/non-actuating preflight மட்டும்; அனுமதியுள்ள 4-mode hardware மற்றும் pick/place/wipe evidence இல்லை. |
| 9-9 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | வெளிப்புற XLeRobot `3d14695…`＋RoboCrew; சரியாக `gemini-robotics-er-1.5-preview`, angle annotation, forward/left/right tools. அனுமதியுள்ள robot navigation evidence இல்லை. |
| 9-10 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | வெளிப்புற `lerobot-sim2real` `87d6c1d…` ஐந்து-stage RGB→PPO→SO-100 pipeline. ManiSkill/NVIDIA மற்றும் அனுமதியுள்ள physical run இல்லை. |

## திட்ட வகைகள்

| சின்னம் | வகை | பொருள் |
| :--: | --- | --- |
| ✅ | **தனித்து இயங்கும்** | முழு குறியீடு இந்த களஞ்சியத்தில், API Key உள்ளமைத்தவுடன் இயங்கும் |
| 📖 | **மறு உருவாக்க வழிகாட்டி** | **வெளிப்புற களஞ்சியங்களை** `git clone` செய்ய வேண்டிய விரிவான ஆவணம் |
| 🚧 | **செயலில் உள்ளது** | Implementation உள்ளது; ஆனால் தேவையான live run, authorization, hardware அல்லது manuscript acceptance evidence முழுமையில்லை |
