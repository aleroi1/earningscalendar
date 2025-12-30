import streamlit as st
import pandas as pd
from yahooquery import Ticker
from datetime import datetime, timedelta
import urllib.parse

# 1. Sivun asetukset
st.set_page_config(page_title="Earnings Schedule", page_icon="📅")

# --- APUFUNKTIOT ---

def create_google_calendar_url(ticker, event_date):
    """Luo Google Kalenteri -linkin"""
    # Varmistetaan aikamuoto
    if isinstance(event_date, (pd.Timestamp, datetime)):
        start_dt = event_date.replace(hour=9, minute=0, second=0)
    else:
        # Jos data on pelkkä päivämäärä ilman kelloa
        start_dt = datetime.combine(event_date, datetime.min.time()).replace(hour=9)

    end_dt = start_dt + timedelta(hours=1)
    fmt = "%Y%m%dT%H%M%S"
    dates_str = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
    
    params = {
        "action": "TEMPLATE",
        "text": f"Earnings Call: {ticker}",
        "dates": dates_str,
        "details": f"Check investor relations page for {ticker}.\nData source: Yahoo Finance via Yahooquery.",
        "location": "Online / Helsinki"
    }
    return "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(params)

@st.cache_data(ttl=3600)
def get_earnings_data(symbol):
    """Hakee tiedot yahooquery-kirjastolla"""
    try:
        # Yahooquery on usein luotettavampi pilvessä
        t = Ticker(symbol)
        
        # Haetaan kalenteritiedot
        # calendar_events palauttaa yleensä DataFramen tai sanakirjan
        cal = t.calendar_events
        
        if isinstance(cal, dict):
            # Joskus palauttaa virheen sanakirjana
            if symbol in cal and isinstance(cal[symbol], str):
                return None
            # Joskus data on suoraan avaimen takana
            df = cal.get(symbol)
        else:
            df = cal

        if isinstance(df, pd.DataFrame) and not df.empty:
             return df
        return None

    except Exception as e:
        st.error(f"Tekninen virhe haussa: {e}")
        return None

# --- SIVUN KÄYTTÖLIITTYMÄ ---

st.title("📅 Earnings Schedule")
st.caption("Powered by YahooQuery")

col1, col2 = st.columns([2, 1])

with col1:
    ticker_input = st.text_input("Ticker symbol (e.g. NVDA, KESKOB.HE)", value="").upper()

if ticker_input:
    with st.spinner(f"Fetching data for {ticker_input}..."):
        df = get_earnings_data(ticker_input)
        
        if df is not None:
            # Tarkistetaan löytyykö Earnings Date -saraketta
            if 'earnings_date' in df.columns:
                st.success(f"Events found for: {ticker_input}")
                
                # Järjestetään päivämäärät
                dates = df['earnings_date'].sort_values().values
                
                for date_val in dates:
                    # Muutetaan pandas timestamp oikeaan muotoon
                    d_obj = pd.to_datetime(date_val)
                    
                    # Ohitetaan menneet tapahtumat (valinnainen, nyt näytetään kaikki tulevat)
                    if d_obj > datetime.now() - timedelta(days=1):
                        display_date = d_obj.strftime("%Y-%m-%d %H:%M")
                        
                        with st.container(border=True):
                            c1, c2 = st.columns([3, 2])
                            with c1:
                                st.subheader(display_date)
                                st.caption("Earnings Call / Release")
                            with c2:
                                url = create_google_calendar_url(ticker_input, d_obj)
                                st.link_button("📅 Add to Calendar", url)
            else:
                 st.warning("Data found, but no earnings dates listed.")
        else:
            st.warning("No data found. Yahoo might be blocking requests or ticker is wrong.")
            st.info("Try adding .HE for Finnish stocks (e.g. FORTUM.HE)")
