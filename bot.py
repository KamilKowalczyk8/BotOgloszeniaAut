import requests
from bs4 import BeautifulSoup
import time

# dane
TOKEN = "8142987363:AAGHaUreIkX3Q3p7_NwB7vx16pTA0VINMb8"
CHAT_ID = "7868036921"

OTOMOTO_URL = "https://www.otomoto.pl/osobowe/seat/leon/seg-city-car--seg-compact--seg-mini/od-2017?search%5Bfilter_enum_damaged%5D=0&search%5Bfilter_enum_fuel_type%5D=petrol&search%5Bfilter_enum_gearbox%5D=manual&search%5Bfilter_enum_generation%5D=gen-iii-2012&search%5Bfilter_float_engine_power%3Afrom%5D=140&search%5Bfilter_float_price%3Afrom%5D=50000&search%5Bfilter_float_price%3Ato%5D=65000&search%5Border%5D=relevance_web&search%5Badvanced_search_expanded%5D=true"

# Filtry 
INCLUDE_KEYWORDS = ["FR", "Facelift"]          
EXCLUDE_KEYWORDS = ["uszkodzony", "anglik"]    

seen_ads = set()
last_sent_messages = []


def ad_passes_filters(title: str):
    title_lower = title.lower()

    if not any(kw.lower() in title_lower for kw in INCLUDE_KEYWORDS):
        return False
    if any(kw.lower() in title_lower for kw in EXCLUDE_KEYWORDS):
        return False
    return True


def get_otomoto_ads():
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(OTOMOTO_URL, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    ads = []
    for listing in soup.select("article"):
        title_tag = listing.select_one("h1, h2, h3, h4")
        link = listing.find("a", href=True)
        location_tag = listing.select_one(".offer-item__location, .ooa-1wbpr6o")

        if title_tag and link:
            title = title_tag.text.strip()
            url = link['href']
            location = location_tag.text.strip() if location_tag else ""

            if url not in seen_ads and ad_passes_filters(title):
                seen_ads.add(url)
                ads.append({
                    "title": title,
                    "url": url,
                    "location": location
                })

    return ads


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        message_id = r.json()["result"]["message_id"]
        last_sent_messages.append(message_id)
        print(f"Wysłano wiadomość (ID: {message_id})")

        if len(last_sent_messages) > 15:
            old_message_id = last_sent_messages.pop(0)
            delete_telegram_message(old_message_id)
    else:
        print("Błąd przy wysyłaniu wiadomości:", r.text)


def delete_telegram_message(message_id):
    url = f"https://api.telegram.org/bot{TOKEN}/deleteMessage"
    payload = {
        "chat_id": CHAT_ID,
        "message_id": message_id
    }
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        print(f"Usunięto wiadomość (ID: {message_id})")
    else:
        print(f"Nie udało się usunąć wiadomości (ID: {message_id}):", r.text)



while True:
    new_ads = get_otomoto_ads()
    for ad in new_ads:
        message = f"🆕 Nowe ogłoszenie:\n{ad['title']}\n📍 {ad['location']}\n🔗 {ad['url']}"
        send_telegram_message(message)
    time.sleep(600)
