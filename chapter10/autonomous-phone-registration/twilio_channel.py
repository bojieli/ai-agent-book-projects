"""Real PSTN transport for the Experiment 10-3 Phone Agent.

Twilio places one outbound call. Its speech ``Gather`` provides ASR and ``Say``
provides TTS; the call stays open while the Phone and Computer Agents work.
"""

from __future__ import annotations

import asyncio
import os
from typing import List


class TwilioPhoneChannel:
    def __init__(self):
        required = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER",
                    "PHONE_USER_NUMBER", "TWILIO_WEBHOOK_BASE_URL"]
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError(f"Twilio PSTN 缺少环境变量：{', '.join(missing)}")
        self.sid = os.environ["TWILIO_ACCOUNT_SID"]
        self.token = os.environ["TWILIO_AUTH_TOKEN"]
        self.from_number = os.environ["TWILIO_FROM_NUMBER"]
        self.to_number = os.environ["PHONE_USER_NUMBER"]
        self.base_url = os.environ["TWILIO_WEBHOOK_BASE_URL"].rstrip("/")
        self.port = int(os.getenv("TWILIO_LOCAL_PORT", "8765"))
        self.language = os.getenv("TWILIO_LANGUAGE", "zh-CN")
        self.voice = os.getenv("TWILIO_VOICE", "Google.zh-CN-Standard-A")
        self._pending: List[str] = []
        self._answers: asyncio.Queue[str] = asyncio.Queue()
        self._closing = False
        self._server = None
        self._server_task = None
        self.call_sid = None
        self.asr_count = 0
        self.tts_prompt_count = 0
        self.call_status = "not_started"
        self._client = None
        self.closed = False

    async def start(self):
        from fastapi import FastAPI, Request, Response
        from twilio.request_validator import RequestValidator
        from twilio.rest import Client
        from twilio.twiml.voice_response import Gather, VoiceResponse
        import uvicorn

        app = FastAPI()
        validator = RequestValidator(self.token)

        async def verified(request: Request, form) -> bool:
            signature = request.headers.get("X-Twilio-Signature", "")
            public_url = self.base_url + request.url.path
            return validator.validate(public_url, dict(form), signature)

        @app.post("/voice")
        async def voice(request: Request):
            form = await request.form()
            if not await verified(request, form):
                return Response("invalid signature", status_code=403)
            response = VoiceResponse()
            if self._closing:
                for text in self._pending:
                    response.say(text, language=self.language, voice=self.voice)
                    self.tts_prompt_count += 1
                self._pending.clear()
                response.hangup()
            elif self._pending:
                text = " ".join(self._pending)
                self._pending.clear()
                self.tts_prompt_count += 1
                gather = Gather(
                    input="speech",
                    action=f"{self.base_url}/gather",
                    method="POST",
                    language=self.language,
                    speech_timeout="auto",
                    timeout=8,
                )
                gather.say(text, language=self.language, voice=self.voice)
                response.append(gather)
                response.redirect(f"{self.base_url}/voice", method="POST")
            else:
                response.pause(length=1)
                response.redirect(f"{self.base_url}/voice", method="POST")
            return Response(str(response), media_type="application/xml")

        @app.post("/gather")
        async def gather_result(request: Request):
            form = await request.form()
            if not await verified(request, form):
                return Response("invalid signature", status_code=403)
            transcript = str(form.get("SpeechResult", "")).strip()
            if transcript:
                await self._answers.put(transcript)
                self.asr_count += 1
            response = VoiceResponse()
            response.redirect(f"{self.base_url}/voice", method="POST")
            return Response(str(response), media_type="application/xml")

        config = uvicorn.Config(app, host="0.0.0.0", port=self.port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(self._server.serve())
        while not self._server.started:
            await asyncio.sleep(0.05)

        client = Client(self.sid, self.token)
        self._client = client
        call = await asyncio.to_thread(
            client.calls.create,
            to=self.to_number,
            from_=self.from_number,
            url=f"{self.base_url}/voice",
            method="POST",
        )
        self.call_sid = call.sid
        self.call_status = call.status or "queued"
        print(f"  [PSTN] outbound call initiated; call SID suffix={call.sid[-6:]}")

    async def say(self, text: str) -> None:
        self._pending.append(text)

    async def listen(self, *, timeout: float = 45.0) -> str:
        text = await asyncio.wait_for(self._answers.get(), timeout)
        print(f"  [Twilio ASR] 用户：{text}")
        return text

    async def close(self):
        if self.closed:
            return
        self._closing = True
        try:
            # Let the current Gather redirect once so the final queued Say + Hangup is served.
            await asyncio.sleep(2)
            if self._server:
                self._server.should_exit = True
            if self._server_task:
                await self._server_task
            if self._client and self.call_sid:
                try:
                    call = await asyncio.to_thread(self._client.calls(self.call_sid).fetch)
                    self.call_status = call.status
                except Exception as exc:
                    self.call_status = f"status_check_failed:{type(exc).__name__}"
        finally:
            self.closed = True
