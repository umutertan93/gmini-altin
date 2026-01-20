import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import shutil

# --- Sayfa Ayarları ---
st.set_page_config(page_title="Altın/Gümüş Takip", page_icon="💎")

# --- Sabit Varlıklarınız ---
VARLIK_ALTIN_GR = 17.1666
VARLIK_GUMUS_GR = 1000.0

@st.cache_data(ttl=120)
def verileri_getir_hakanaltin():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Streamlit Cloud üzerinde Chromium genelde bu yoldadır
    # Eğer sistemde chromium varsa yolunu options'a ekle
    chromium_path = shutil.which("chromium")
    if chromium_path:
        chrome_options.binary_location = chromium_path

    driver = None
    try:
        # ChromeType.CHROMIUM belirterek sürüm uyumsuzluğunu önlüyoruz
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get("[https://www.hakanaltin.com/](https://www.hakanaltin.com/)")
        
        # Tablonun yüklenmesini bekle
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        fiyatlar = {"has_altin": 0.0, "gumus": 0.0}
        satirlar = driver.find_elements(By.TAG_NAME, "tr")
        
        for satir in satirlar:
            metin = satir.text.upper()
            if "HAS" in metin and "ALTIN" in metin:
                try:
                    hucreler = satir.find_elements(By.TAG_NAME, "td")
                    if len(hucreler) >= 3:
                        fiyatlar["has_altin"] = text_to_float(hucreler.[1]text)
                except: continue
            
            if "GUMUS" in metin and fiyatlar["gumus"] == 0.0:
                try:
                    hucreler = satir.find_elements(By.TAG_NAME, "td")
                    if len(hucreler) >= 3:
                        ham = text_to_float(hucreler.[1]text)
                        fiyatlar["gumus"] = ham / 1000.0 if ham > 5000 else ham
                except: continue
                
        return fiyatlar

    except Exception as e:
        st.error(f"Hata Oluştu: {str(e)}")
        return None
    finally:
        if driver:
            driver.quit()

def text_to_float(text):
    try:
        temiz = text.replace('.', '').replace(',', '.')
        filtreli = ''.join(c for c in temiz if c.isdigit() or c == '.')
        return float(filtreli)
    except: return 0.0

# --- Arayüz ---
st.title("Hakan Altın Portföy 🏦")

if st.button("Fiyatları Getir 🔄"):
    with st.spinner('Veriler çekiliyor...'):
        piyasa = verileri_getir_hakanaltin()
        
    if piyasa and piyasa["has_altin"] > 0:
        t_altin = piyasa["has_altin"] * VARLIK_ALTIN_GR
        t_gumus = piyasa["gumus"] * VARLIK_GUMUS_GR
        toplam = t_altin + t_gumus
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Has Altın", f"{piyasa['has_altin']:,.2f} TL")
        c2.metric("Gümüş", f"{piyasa['gumus']:,.2f} TL")
        c3.metric("Toplam Varlık", f"{toplam:,.2f} TL")
        
        st.success(f"Portföyünüz: {VARLIK_ALTIN_GR} gr Altın + {int(VARLIK_GUMUS_GR)} gr Gümüş")
