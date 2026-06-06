"""
TTS (Text-to-Speech) — macOS built-in 'say' komutu kullanır.
Ek kurulum gerektirmez, Türkçe ve İngilizce destekler.
Alp Ünlü tarafından yapılmıştır — @alppunlu

Geliştirmeler:
- Ses konfigürasyonu (app_config'den)
- Ses hızı kontrolü (-r parametresi)
- Artan metin sınırı (1000 karaktere)
- Daha iyi hata yönetimi
"""

import subprocess
import threading


SPEECH_RATE = 150  # Sözcük/dakika (normal: 150-180, hızlı: 200+, yavaş: 100-150)
MAX_TEXT_LENGTH = 1000  # Maksimum metin uzunluğu

_VOICE_CACHE = None  # Ses cache'i


def get_available_voices() -> list:
    """macOS'taki mevcut sesleri listeler."""
    try:
        result = subprocess.run(["say", "-v", "?"],
                                capture_output=True, text=True)
        voices = []
        for line in result.stdout.splitlines():
            if line.strip():
                voices.append(line.split()[0])
        return voices
    except Exception:
        return []


def _get_voice() -> str:
    """app_config'den dinamik olarak sesi yükler."""
    global _VOICE_CACHE
    
    if _VOICE_CACHE:
        return _VOICE_CACHE
    
    available = get_available_voices()
    
    try:
        from app_config import get_app_config_value
        voice = get_app_config_value("voice", None)
        # Config'deki ses sistemde mevcutsa kullan
        if voice and voice in available:
            _VOICE_CACHE = voice
            return voice
    except Exception:
        pass
    
    # Fallback: Türkçe sesi sırasıyla dene
    for v in ["Yelda", "Zoe", "Samantha"]:
        if v in available:
            _VOICE_CACHE = v
            return v
    
    # En son çare: ilk bulduğu ses
    default = available[0] if available else "Samantha"
    _VOICE_CACHE = default
    return default


def speak_text(text: str, on_done=None, blocking: bool = False, rate: int = None, volume: float = 1.0):
    """
    Metni sesli olarak okur.
    
    Args:
        text: Okunacak metin
        on_done: okuma bitince çağrılacak fonksiyon (opsiyonel)
        blocking: True ise bitene kadar bekler
        rate: Sözcük/dakika cinsinden hız (örn. 100 = yavaş, 180 = normal, 250 = hızlı)
        volume: Ses seviyesi (0.0-1.0, varsayılan: 1.0)
    """
    if not text or not text.strip():
        if on_done:
            on_done()
        return

    # Çok uzun metinleri kısalt (TTS için)
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH] + "..."

    def _run():
        try:
            voice = _get_voice()
            cmd = ["say", "-v", voice]
            
            # Ses hızı ekle
            if rate and rate > 0:
                cmd.extend(["-r", str(rate)])
            elif SPEECH_RATE > 0:
                cmd.extend(["-r", str(SPEECH_RATE)])
            
            cmd.append(text)
            subprocess.run(cmd, check=False)
            
        except FileNotFoundError:
            print("[TTS] 'say' komutu bulunamadı")
        except Exception as e:
            print(f"[TTS] Hata: {e}")
        
        if on_done:
            on_done()

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


def set_voice(voice_name: str) -> bool:
    """Dinamik olarak ses değiştirir."""
    global _VOICE_CACHE
    available = get_available_voices()
    if voice_name in available:
        _VOICE_CACHE = voice_name
        return True
    return False


def set_speech_rate(rate: int) -> bool:
    """Dinamik olarak konuşma hızını değiştirir."""
    global SPEECH_RATE
    if 50 <= rate <= 400:  # Makul aralık
        SPEECH_RATE = rate
        return True
    return False


def get_voice_info() -> dict:
    """Mevcut ses ayarlarını döndürür."""
    return {
        "current_voice": _get_voice(),
        "available_voices": get_available_voices(),
        "speech_rate": SPEECH_RATE,
        "max_text_length": MAX_TEXT_LENGTH
    }
