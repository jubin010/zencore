"""
TTS 模块 - 语音合成播放
支持远程 API (studio.mosi.cn) 和本地 MOSS-TTS-Nano 服务
使用 ffplay 播放音频
"""

import base64
import subprocess
import os


def speak(text: str, config: dict = None):
    if not text or not config or not config.get("enabled", False):
        return

    backend = config.get("backend", "remote")

    if backend == "local":
        _speak_local(text, config)
    else:
        _speak_remote(text, config)


def _speak_local(text: str, config: dict):
    try:
        import requests
        response = requests.post(
            "http://localhost:18083/api/generate",
            files={
                "text": (None, text),
                "demo_id": (None, config.get("demo_id", "demo-1")),
            },
            timeout=60
        )
        if response.status_code != 200:
            return
        result = response.json()
        audio_b64 = result.get("audio_base64", "")
        if not audio_b64:
            return

        tmp_wav = "/tmp/temp_tts.wav"
        with open(tmp_wav, "wb") as f:
            f.write(base64.b64decode(audio_b64))

        speed = config.get("speed", 1.0)
        if speed != 1.0:
            cmd = ["/usr/bin/ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-af", f"atempo={speed}", tmp_wav]
        else:
            cmd = ["/usr/bin/ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp_wav]
        subprocess.run(cmd, capture_output=True, timeout=120)
        os.unlink(tmp_wav)
    except:
        pass


def _speak_remote(text: str, config: dict):
    api_key = config.get("api_key", "")
    if api_key == "YOUR_API_KEY_HERE":
        return

    try:
        import requests
        response = requests.post(
            config["api_url"],
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "moss-tts",
                "text": text,
                "voice_id": config.get("voice_id", "2001257729754140672"),
                "expected_duration_sec": 3.2,
                "meta_info": True,
                "sampling_params": {
                    "max_new_tokens": 20000,
                    "temperature": 1.7,
                    "top_p": 0.8,
                    "top_k": 25
                }
            },
            timeout=30
        )
        audio_b64 = response.json().get("audio_data", "")
        if not audio_b64:
            return

        tmp_wav = "/tmp/temp_tts.wav"
        with open(tmp_wav, "wb") as f:
            f.write(base64.b64decode(audio_b64))

        speed = config.get("speed", 1.0)
        if speed != 1.0:
            cmd = ["/usr/bin/ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-af", f"atempo={speed}", tmp_wav]
        else:
            cmd = ["/usr/bin/ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp_wav]
        subprocess.run(cmd, capture_output=True, timeout=60)
        os.unlink(tmp_wav)
    except:
        pass