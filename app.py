import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import urllib.parse

# 1. Sivun asetukset
st.set_page_config(page_title="Earnings Schedule", page_icon="📅")

# --- APUFUNKTIOT ---

def create_google_calendar_url(ticker, event_date):
    """Luo Google Kalenteri -linkin"""
    if isinstance(event_date, (pd.Timestamp, datetime)):
        start_dt = event_date.replace(hour=9, minute=0, second=0)
    else:
        start_dt = datetime.combine(event_date, datetime.min.time()).replace(hour=9)

    end_dt = start_dt + timedelta(hours=1)
    fmt = "%Y%m%dT%H%M%S"
    dates_str = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
    
    params = {
        "action": "TEMPLATE",
        "text": f"Earnings Call: {ticker}",
        "dates": dates_str,
        "details": f"Check investor relations page for {ticker}.\nData source: Yahoo Finance.",
        "location": "Online / Helsinki"
    }
    return "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(params)

# TÄMÄ ON UUSI OSA: Välimuisti ja naamiointi
@st.cache_data(ttl=3600) # Muistaa tiedot 1 tunnin ajan (vähentää virheitä)
def get_stock_data(ticker_symbol):
    """Hakee datan Yahoolta käyttäen 'selain-naamiota'"""
    try:
        # Luodaan sessio, joka näyttää Chrome-selaimelta
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        })
        
        # Annetaan sessio yfinancelle (jos tuettu) tai käytetään perushakua
        stock = yf.Ticker(ticker_symbol, session=session)
        cal = stock.calendar
        
        # Käsitellään data
        dates_found = []
        if cal is not None and not cal.empty:
            if isinstance(cal, dict):
                if 'Earnings Date' in cal:
                    dates = cal['Earnings Date']
                    for d in dates:
                        dates_found.append(("Earnings Call", d))
                elif 'Earnings High' in cal:
                        dates_found.append(("Estimated Earnings", cal.get('Earnings Date', [])))
            else:
                transposed = cal.T
                if "Earnings Date" in transposed.columns:
                    vals = transposed["Earnings Date"].values
                    for v in vals:
                        dates_found.append(("Earnings Call", v))
                elif 0 in cal.columns:
                    vals = cal.iloc[0]
                    dates_found.append(("Earnings Call", vals))
        return dates_found
    except Exception as e:
        # Jos tulee virhe, palautetaan tieto virheestä
        return f"ERROR: {str(e)}"

# --- SIVUN KÄYTTÖLIITTYMÄ ---

st.title("📅 Earnings Schedule")
st.write("Enter a stock ticker to see upcoming earnings dates.")

col1, col2 = st.columns([2, 1])

with col1:
    ticker_input = st.text_input("Ticker symbol (e.g. NVDA, KESKOB.HE)", value="").upper()

if ticker_input:
    # Käytetään uutta välimuistillista hakua
    with st.spinner(f"Searching data for {ticker_input}..."):
        result = get_stock_data(ticker_input)
        
        # Tarkistetaan onko tulos virhe vai dataa
        if isinstance(result, str) and "ERROR" in result:
            st.error("Yahoo Finance is blocking requests temporarily (Rate Limit).")
            st.warning("Try again in a few minutes or try a different ticker.")
        elif result:
            st.success(f"Events found for: {ticker_input}")
            for event_name, date_obj in result:
                display_date = pd.to_datetime(date_obj).strftime("%Y-%m-%d")
                with st.container(border=True):
                    c1, c2 = st.columns([3, 2])
                    with c1:
                        st.subheader(f"{display_date}")
                        st.caption(f"{event_name}")
                    with c2:
                        url = create_google_calendar_url(ticker_input, pd.to_datetime(date_obj))
                        st.link_button("📅 Add to Calendar", url)
        else:
            st.warning("No upcoming events found (or data not available).")
            st.info("Tip: For Helsinki stocks, use .HE suffix (e.g. QTCOM.HE)")
