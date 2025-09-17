from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# === Kullanıcı girişi ve yardımcılar ===
def _normalize_tr(s: str) -> str:
    return (
        s.lower()
         .replace("ç", "c").replace("ğ", "g").replace("ı", "i")
         .replace("ö", "o").replace("ş", "s").replace("ü", "u")
         .strip()
    )


# --- Yardımcılar: sadece görünür dropdown'u bul ve şehir seç ---
def _get_visible_dropdown(driver):
    lists = driver.find_elements(By.CSS_SELECTOR, ".SelectBox__airport__list")
    for lst in lists:
        if lst.is_displayed():
            return lst
    return None

# Aktif input'un kendi dropdown'unu (aynı SelectBox kapsayıcısı içindeki) bul
def _get_visible_dropdown_for(driver, input_el):
    try:
        # En yakın SelectBox kapsayıcısını bul
        box = input_el.find_element(By.XPATH, "ancestor::div[contains(@class,'SelectBox')][1]")
        lists = box.find_elements(By.CSS_SELECTOR, ".SelectBox__airport__list")
        for lst in lists:
            if lst.is_displayed():
                return lst
    except Exception:
        pass
    # Fallback: global görünür dropdown
    return _get_visible_dropdown(driver)

def _select_top_suggestion(driver, wait, input_el=None) -> bool:
    """Görünür dropdown içindeki EN ÜSTTEKİ öneriyi seçer; önce input'a en yakın dropdown'u dener."""
    lst = _get_visible_dropdown_for(driver, input_el) if input_el is not None else _get_visible_dropdown(driver)
    if not lst:
        return False
    items = [it for it in lst.find_elements(By.CSS_SELECTOR, ".SelectBox__airport__item") if it.is_displayed()]
    if not items:
        return False
    first = items[0]
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", first)
        driver.execute_script("arguments[0].click();", first)
        return True
    except Exception:
        if input_el is not None:
            try:
                input_el.send_keys(Keys.ARROW_DOWN)
                input_el.send_keys(Keys.ENTER)
                return True
            except Exception:
                return False
        return False

def _click_city_from_visible_list(driver, wait, city_text: str, input_el=None) -> bool:
    """
    Görünür listedeki ilk uygun item'i seçer.
    Eşleştirme önceliği:
      1) Kullanıcı girişi 3 harfli IATA koduysa -> data-port-code tam eşleşme (örn: ESB)
      2) Şehir adı metin eşleşmesi (normalize edilerek, içerir)
    """
    lst = _get_visible_dropdown_for(driver, input_el) if input_el is not None else _get_visible_dropdown(driver)
    if not lst:
        return False

    items = lst.find_elements(By.CSS_SELECTOR, ".SelectBox__airport__item")
    if not items:
        return False

    # 1) IATA port kodu denemesi
    code = (city_text or "").strip().upper()
    if len(code) == 3 and code.isalpha():
        for it in items:
            try:
                port_code = it.get_attribute("data-port-code") or ""
                if port_code.upper() == code:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", it)
                    wait.until(EC.element_to_be_clickable(it))
                    driver.execute_script("arguments[0].click();", it)
                    return True
            except Exception:
                continue

    # 2) Şehir adına göre eşleşme
    wanted = _normalize_tr(city_text or "")
    for it in items:
        try:
            city_el = it.find_element(By.CSS_SELECTOR, ".SelectBox__airport__city")
            city_txt = _normalize_tr(city_el.text)
            if wanted and wanted in city_txt:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", it)
                wait.until(EC.element_to_be_clickable(it))
                driver.execute_script("arguments[0].click();", it)
                return True
        except Exception:
            continue

    return False


# Kullanıcıdan değer al
USER_FROM = input("Nereden (ör. İstanbul): ")
USER_TO = input("Nereye (ör. Antalya): ")
USER_DAY = int(input("Eylül ayında gün seç (ör. 16 ile 20 arası): "))
if USER_DAY < 1 or USER_DAY > 30:
    raise ValueError("Geçerli bir gün giriniz (1-30).")

# 1) Driver aç
driver = webdriver.Chrome()
driver.get("https://www.flypgs.com/kalkis-varis-bilgilerimiz")

wait = WebDriverWait(driver, 10)

# 2) Nereden inputunu bul ve tıkla
from_input = wait.until(EC.element_to_be_clickable((By.ID, "fromWhere")))
from_input.click()

from_input.send_keys(Keys.COMMAND, 'a')
from_input.send_keys(Keys.CONTROL, 'a')
from_input.send_keys(Keys.BACK_SPACE)

# 3) İstediğin şehri yaz (örnek: "İstanbul")
from_input.send_keys(USER_FROM)
time.sleep(2)  # seçeneklerin çıkması için kısa bekle

# 4) Görünür listeyi bekle ve en üstteki öneriyi seç
wait.until(lambda d: _get_visible_dropdown(d) is not None)
picked_from = _select_top_suggestion(driver, wait, from_input)
if not picked_from:
    # Son bir kez DOM ile dene
    time.sleep(0.4)
    _select_top_suggestion(driver, wait, from_input)
time.sleep(3)
print("Nereden kısmına seçim yapıldı ✅")
# (sonrasında 'nereye' kısmına da aynı şekilde geçebilirsin)
# 5) 'Nereye' inputunu bul ve tıkla
to_input = wait.until(EC.element_to_be_clickable((By.ID, "toWhere")))
to_input.click()

# Input'u tamamen temizle (Mac/Win olası kombinasyonları)
to_input.send_keys(Keys.COMMAND, 'a')
to_input.send_keys(Keys.CONTROL, 'a')
to_input.send_keys(Keys.BACK_SPACE)

# 6) Şehir yaz (örnek: "Antalya")
to_input.send_keys(USER_TO)

# 7) Görünür listeyi bekle ve kullanıcı girdisine göre seç, bulunamazsa en üsttekini seç
wait.until(lambda d: _get_visible_dropdown_for(d, to_input) is not None)
# Önce tam eşleşme (IATA veya şehir adı)
clicked_to = _click_city_from_visible_list(driver, wait, USER_TO, input_el=to_input)
if not clicked_to:
    # Bulunamazsa en üstteki öneriye bas
    picked_to = _select_top_suggestion(driver, wait, to_input)
    if not picked_to:
        time.sleep(0.4)
        _select_top_suggestion(driver, wait, to_input)

time.sleep(1)
print("Nereye kısmına seçim yapıldı ✅")

# 8) Tarih alanını aç ve ilgili günü tıkla (Eylül ayı, 2025 varsayımıyla)
date_input = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "input.js-dai-date-input.active.flatpickr-input[readonly]"))
)
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_input)
driver.execute_script("arguments[0].click();", date_input)
# İlgili günü bul ve tıkla (Eylül ayı, 2025 varsayımıyla)
target_label = f"Eylül {USER_DAY}, 2025"
day_selector = f".flatpickr-calendar.open .flatpickr-day[aria-label='{target_label}']:not(.prevMonthDay):not(.nextMonthDay):not(.flatpickr-disabled)"
selected_day = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, day_selector))
)
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", selected_day)
driver.execute_script("arguments[0].click();", selected_day)
time.sleep(0.3)
print(f"Tarih seçildi: {target_label} ✅")

# 10) 'Uçuş Ara' butonuna tıkla
search_button = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-dai-submit-button"))
)
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_button)
driver.execute_script("arguments[0].click();", search_button)
time.sleep(2)

# 11) Arama sonuçlarından kalkış bilgilerini topla (tarifeli/tahmini/gerçek)
import json

# Birden fazla uçuş olabilir; her birini ayrı dict olarak saklayacağız
flights = []

# Sonuçların geldiğini bekle: her uçuş kartında bu liste var
result_lists = wait.until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.FlightInfo__item__content__list"))
)

for ul in result_lists:
    data = {}
    try:
        items_li = ul.find_elements(By.CSS_SELECTOR, "li")
        for li in items_li:
            try:
                title_el = li.find_element(By.CSS_SELECTOR, ".FlightInfo__item__content__list__title")
                desc_el  = li.find_element(By.CSS_SELECTOR, ".FlightInfo__item__content__list__desc")
            except Exception:
                continue
            title = title_el.text.strip().lower()
            value = desc_el.text.strip()

            # Başlıkları anahtara çevir (Türkçe başlık -> anahtar)
            if "tarifeli kalkış" in title:
                key = "tarifeli_kalkis"
            elif "tahmini kalkış" in title:
                key = "tahmini_kalkis"
            elif "gerçek kalkış" in title:
                key = "gercek_kalkis"
            else:
                # Diğer başlıklar olursa güvenli bir anahtar oluştur
                key = title.replace(" ", "_").replace("ç", "c").replace("ğ", "g").replace("ı", "i").replace("ö", "o").replace("ş", "s").replace("ü", "u")
            data[key] = value
    except Exception:
        continue

    # Sadece en az bir alan toplandıysa ekle
    if data:
        flights.append(data)

# Bellekte tut: flights listesi
print("Toplanan uçuş verileri:")
for idx, fdata in enumerate(flights, 1):
    print(f"#{idx}: {fdata}")

# JSON olarak diske yaz
out_path = "ucus_sonuclari.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(flights, f, ensure_ascii=False, indent=2)
print(f"JSON kaydedildi: {out_path}")

print("Uçuş arama başlatıldı ✅")
