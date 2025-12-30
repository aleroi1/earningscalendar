import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

st.set_page_config(page_title="Tuloskalenteri", page_icon="📅")

def create_google_calendar_url(ticker, event_date):
    """Luo URL-linkin Google Kalenteriin"""
    # Varmistetaan että on datetime
    if isinstance(event_date, (pd.Timestamp, datetime)):
        start_dt = event_date.replace(hour=9, minute=0, second=0)
    else:
        start_dt = datetime.combine(event_date, datetime.min.time()).replace(hour=9)

    end_dt = start_dt + timedelta(hours=1)
    
    # Google vaatii ajan muodossa YYYYMMDDTHHMMSSZ
    fmt = "%Y%m%dT%H%M%S"
    dates_str = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
    
    params = {
        "action": "TEMPLATE",
        "text": f"Tulosjulkistus: {ticker}",
        "dates": dates_str,
        "details": f"Muista tarkistaa {ticker} sijoittajasivut.\nLähde: yfinance.",
        "location": "Helsinki"
    }
    
    base_url = "https://calendar.google.com/calendar/render?"
    return base_url + urllib.parse.urlencode(params)

# --- SIVUN ULKOASU ---

st.title("📈 Oma Tuloskalenteri")
st.write("Kirjoita osakkeen tikkeri nähdäksesi tulevat tapahtumat.")

col1, col2 = st.columns([2, 1])

with col1:
    ticker_input = st.text_input("Tikkeri (esim. NVDA, NDA-FI.HE, KESKOB.HE)", value="").upper()

if ticker_input:
    with st.spinner(f"Haetaan tietoja yhtiölle {ticker_input}..."):
        try:
            stock = yf.Ticker(ticker_input)
            cal = stock.calendar
            dates_found = []
            
            # Logiikka datan kaivamiseen eri muodoista
            if cal is not None and not cal.empty:
                if isinstance(cal, dict):
                    if 'Earnings Date' in cal:
                        dates = cal['Earnings Date']
                        for d in dates:
                            dates_found.append(("Tulosjulkistus", d))
                    elif 'Earnings High' in cal:
                         dates_found.append(("Arvioitu tulos", cal.get('Earnings Date', [])))
                else:
                    transposed = cal.T
                    if "Earnings Date" in transposed.columns:
                        vals = transposed["Earnings Date"].values
                        for v in vals:
                            dates_found.append(("Tulosjulkistus", v))
                    elif 0 in cal.columns:
                        vals = cal.iloc[0]
                        dates_found.append(("Tulosjulkistus", vals))

            if dates_found:
                st.success(f"Löydettiin tapahtumia: {ticker_input}")
                for event_name, date_obj in dates_found:
                    display_date = pd.to_datetime(date_obj).strftime("%d.%m.%Y")
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.subheader(f"{display_date}")
                            st.caption(f"{event_name}")
                        with c2:
                            url = create_google_calendar_url(ticker_input, pd.to_datetime(date_obj))
                            st.link_button("📅 Kalenteriin", url)
            else:
                st.warning("Ei tulevia kalenteritapahtumia tiedossa.")
                st.info("Vinkki: Suomiosakkeissa muista pääte .HE (esim. QTCOM.HE)")

        except Exception as e:
            st.error(f"Virhe: {e}")