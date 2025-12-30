import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. ASETUKSET
st.set_page_config(page_title="Earnings Schedule", page_icon="📅")

# --- TÄRKEÄÄ: LIITÄ API-AVAIMESI TÄHÄN ---
# Korvaa teksti 'SINUN_AVAIN_TÄHÄN' sillä koodilla jonka sait Alpha Vantagelta.
# Esimerkiksi: API_KEY = "A1B2C3D4E5"
API_KEY = "WL4169NK8EZMS49Z"

def create_google_calendar_url(ticker, event_date, event_type):
    """Luo Google Kalenteri -linkin"""
    date_str = event_date.replace("-", "")
    # Oletetaan tapahtuman kestävän aamulla 09-10
    start_time = f"{date_str}T090000"
    end_time = f"{date_str}T100000"
    
    details = f"Official earnings release for {ticker}. Data source: Alpha Vantage."
    text = f"{ticker} - {event_type}"
    
    base = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    return f"{base}&text={text}&dates={start_time}/{end_time}&details={details}"

@st.cache_data(ttl=3600)
def get_alpha_vantage_data(symbol):
    """Hakee datan Alpha Vantagesta"""
    if API_KEY == "SINUN_AVAIN_TÄHÄN":
        return "NO_KEY"
        
    url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={symbol}&apikey={API_KEY}"
    
    try:
        r = requests.get(url)
        data = r.json()
        
        # Alpha Vantage palauttaa tyhjän {} tai virheen jos symboli on väärä
        if "quarterlyEarnings" in data:
            return data["quarterlyEarnings"]
        elif "Note" in data:
            # Alpha Vantagen ilmaisversiossa on rajoitus (n. 25 hakua päivässä)
            return "LIMIT"
        else:
            return None
    except:
        return None

# --- UI ---

st.title("📅 Earnings Schedule")
st.caption("Powered by Alpha Vantage")

if API_KEY == "SINUN_AVAIN_TÄHÄN":
    st.error("⚠️ API-avain puuttuu!")
    st.write("Avaa `app.py` tiedosto ja liitä Alpha Vantage -avaimesi riville 12.")
else:
    col1, col2 = st.columns([2, 1])
    with col1:
        # Huom: Alpha Vantagessa USA-osakkeet ilman päätettä (NVDA)
        # Eurooppalaiset usein .HEL, .TRT (eikä .HE). Kokeile eri muotoja.
        ticker_input = st.text_input("Ticker symbol (e.g. IBM, NVDA)", value="").upper()

    if ticker_input:
        with st.spinner(f"Checking Alpha Vantage for {ticker_input}..."):
            earnings_list = get_alpha_vantage_data(ticker_input)
            
            if earnings_list == "NO_KEY":
                st.error("Muista tallentaa API-avaimesi koodiin!")
            elif earnings_list == "LIMIT":
                st.warning("Daily API limit reached. Alpha Vantage free tier allows ~25 requests/day.")
            elif earnings_list:
                st.success(f"Found earnings data for {ticker_input}")
                
                # Otetaan 4 seuraavaa/viimeisintä havaintoa
                upcoming = earnings_list[:4]
                
                for item in upcoming:
                    rep_date = item.get('fiscalDateEnding', 'N/A')
                    report_date = item.get('reportedDate', 'N/A')
                    
                    # Jos reportedDate on tiedossa, käytetään sitä, muuten arvio
                    display_date = report_date if report_date != 'None' else f"~{rep_date} (Est)"
                    
                    # Ohitetaan vanhat (jos haluat vain tulevat)
                    # Tässä näytetään viimeisimmät raportoidut selkeyden vuoksi
                    
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 2])
                        with c1:
                            st.subheader(display_date)
                            st.text(f"Fiscal End: {rep_date}")
                        with c2:
                            if report_date != 'None':
                                url = create_google_calendar_url(ticker_input, report_date, "Earnings Report")
                                st.link_button("📅 Add to Cal", url)
                            else:
                                st.write("(Date not confirmed)")
            else:
                st.warning("No data found. Check ticker symbol.")
                st.info("Alpha Vantage uses different suffixes. Try 'IBM' or 'DAI.DEX' for Germany.")
