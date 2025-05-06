import requests

def translate_text(text, target_lang):
    """
    Translate text using LibreTranslate API
    """
    try:
        url = "https://libretranslate.de/translate"
        data = {
            "q": text,
            "source": "auto",
            "target": target_lang
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json()["translatedText"]
        return text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def get_supported_languages():
    """
    Get list of supported languages from LibreTranslate
    """
    try:
        url = "https://libretranslate.de/languages"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error getting languages: {e}")
        return []