import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- Sayfa Ayarları ---
st.set_page_config(
    page_title="Altın/Gümüş Takip",
    page_icon="💰",
    layout="centered"
)

# --- Sabit Varlıklarınız ---
VARLIK_ALTIN_GR = 17.1666
VARLIK_GUMUS_GR = 1000.0  # 1 Kg

# --- Veri Çekme Fonksiyonu (Selenium) ---
@st.cache_data(ttl=120)  # Verileri 2 dakikada bir güncelle
def verileri_getir_hakanaltin():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Arayüzsüz mod
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Tarayıcıyı Başlat
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        # Cloud ortamı için alternatif başlatma
        driver = webdriver.Chrome(options=chrome_options)

    fiyatlar = {"has_altin": 0.0, "gumus": 0.0}

    try:
        driver.get("[https://www.hakanaltin.com/](https://www.hakanaltin.com/)")
        
        # Sitenin yüklenmesini bekle (Dinamik içerik)
        wait = WebDriverWait(driver, 15)
        # Tablonun görünür olmasını bekle
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Tüm tablo satırlarını al
        satirlar = driver.find_elements(By.TAG_NAME, "tr")
        
        for satir in satirlar:
            metin = satir.text.upper()
            
            # HAS ALTIN Fiyatını Bul (Genelde 'HAS' veya 'HAS ALTIN' yazar)
            if "HAS" in metin and "ALTIN" in metin:
                try:
                    # Satırın hücrelerini al
                    hucreler = satir.find_elements(By.TAG_NAME, "td")
                    # Genellikle 2. sütun Alış, 3. sütun Satış'tır. Biz Alış'ı (Bozdurma) alalım.
                    if len(hucreler) >= 3:
                        fiyat_text = hucreler.[2]text  # Alış Sütunu
                        fiyatlar["has_altin"] = text_to_float(fiyat_text)
                except:
                    continue

            # GÜMÜŞ Fiyatını Bul
            # HakanAltin'da 'GUMUS' veya 'KULCE GUMUS' olabilir.
            # Öncelik Has Gümüş (Gr)
            if "GUMUS" in metin and fiyatlar["gumus"] == 0.0:
                try:
                    hucreler = satir.find_elements(By.TAG_NAME, "td")
                    if len(hucreler) >= 3:
                        fiyat_text = hucreler.[2]text
                        ham_fiyat = text_to_float(fiyat_text)
                        
                        # Fiyat kontrolü: Eğer fiyat 1000 TL üzerindeyse Kg fiyatıdır, değilse Gr fiyatıdır.
                        if ham_fiyat > 5000: # Kg fiyatı tahmini eşik
                            fiyatlar["gumus"] = ham_fiyat / 1000.0 # Gr fiyatına çevir
                        else:
                            fiyatlar["gumus"] = ham_fiyat
                except:
                    continue
                    
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {str(e)}")
        return None
    finally:
        driver.quit()
    
    return fiyatlar

def text_to_float(text):
    """ '2.450,50' formatını float'a çevirir """
    try:
        temiz = text.replace('.', '').replace(',', '.')
        # Sadece sayı ve nokta kalsın
        filtreli = ''.join(c for c in temiz if c.isdigit() or c == '.')
        return float(filtreli)
    except:
        return 0.0

# --- Arayüz ---
st.title("Hakan Altın Varlık Takip 🏦")
st.markdown("*Veriler hakanaltin.com üzerinden anlık çekilmektedir.*")

# Yan Menü - Maliyet Girişi
st.sidebar.header("⚙️ Ayarlar")
maliyet = st.sidebar.number_input(
    "Toplam Ana Paranız (TL)",
    min_value=0.0,
    value=0.0,
    step=1000.0,
    help="Altın ve gümüşleri alırken cebinizden çıkan toplam parayı buraya yazın."
)

if st.button("Fiyatları Güncelle 🔄"):
    with st.spinner('HakanAltin.com sitesine bağlanılıyor...'):
        piyasa = verileri_getir_hakanaltin()

    if piyasa and piyasa["has_altin"] > 0:
        # Hesaplamalar
        toplam_altin_tl = piyasa["has_altin"] * VARLIK_ALTIN_GR
        toplam_gumus_tl = piyasa["gumus"] * VARLIK_GUMUS_GR
        toplam_varlik = toplam_altin_tl + toplam_gumus_tl
        
        # --- Sonuç Ekranı ---
        
        # 1. Kartlar: Birim Fiyatlar
        col1, col2 = st.columns(2)
        col1.metric("Has Altın (Gr)", f"{piyasa['has_altin']:,.2f} TL")
        col2.metric("Gümüş (Gr)", f"{piyasa['gumus']:,.2f} TL")
        
        st.divider()
        
        # 2. Varlık Detayı
        st.subheader("📦 Varlıklarınızın Değeri")
        c1, c2 = st.columns(2)
        c1.info(f"**Altın ({VARLIK_ALTIN_GR} gr):**\n\n{toplam_altin_tl:,.2f} TL")
        c2.info(f"**Gümüş ({int(VARLIK_GUMUS_GR)} gr):**\n\n{toplam_gumus_tl:,.2f} TL")
        
        st.divider()
        
        # 3. Ana Toplam ve Kar/Zarar
        st.subheader("💰 Toplam Portföy Durumu")
        
        # Büyük Toplam Göstergesi
        st.metric(
            label="Toplam Nakit Değeri", 
            value=f"{toplam_varlik:,.2f} TL"
        )
        
        # Kar Zarar Hesaplaması (Maliyet girildiyse)
        if maliyet > 0:
            kar_zarar_tl = toplam_varlik - maliyet
            kar_zarar_yuzde = (kar_zarar_tl / maliyet) * 100
            
            if kar_zarar_tl > 0:
                st.success(f"🎉 KAR: {kar_zarar_tl:,.2f} TL (%{kar_zarar_yuzde:.2f})")
            elif kar_zarar_tl < 0:
                st.error(f"🔻 ZARAR: {kar_zarar_tl:,.2f} TL (%{kar_zarar_yuzde:.2f})")
            else:
                st.warning("Durum: Başa Baş")
        else:
            st.caption("⚠️ Net kar/zarar hesabı için lütfen sol menüden maliyetinizi girin.")
            
    else:
        st.warning("Fiyatlar çekilemedi. Site yanıt vermiyor olabilir, lütfen tekrar deneyin.")