import streamlit as st
import pandas as pd
import requests
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_aliexpress_products(keyword):
    url = f"https://gpsfront.aliexpress.com/gps/search?keyword={keyword.replace(' ', '%20')}&page=1&sort=orignalPriceDown"
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return []
        data = response.json()
        items = data.get("results", [])
        results = []
        for item in items[:20]:
            title = item.get("title", "").strip()
            price = float(item.get("appSalePrice", "0").replace("$", "").strip())
            rating = item.get("averageStar", "N/A")
            orders = item.get("tradeDesc", "N/A")
            url = "https:" + item.get("productDetailUrl", "")
            results.append((title, price, rating, orders, url))
        return results
    except Exception as e:
        return []

def compile_data(keyword):
    ali_data = get_aliexpress_products(keyword)
    results = []
    for title, ali_price, rating, orders, ali_url in ali_data:
        results.append({
            "Keyword": keyword,
            "Product Title": title,
            "AliExpress Price": ali_price,
            "Rating": rating,
            "Orders": orders,
            "AliExpress URL": ali_url
        })
        time.sleep(0.2)
    return results

st.title("AliExpress Product Tracker")

mode = st.radio("Choose mode:", ["Single keyword", "Multiple keywords"])
if mode == "Single keyword":
    keyword = st.text_input("Enter a product keyword:")
    keywords = [keyword] if keyword else []
else:
    default_keywords = "pet grooming,car phone holder,tactical flashlight,usb charger,resistance bands,posture corrector"
    text = st.text_area("Enter keywords (comma-separated):", value=default_keywords)
    keywords = [k.strip() for k in text.split(",") if k.strip()]

if st.button("Run Tracker"):
    all_data = []
    for kw in keywords:
        with st.spinner(f"Processing '{kw}'..."):
            data = compile_data(kw)
            all_data.extend(data)
    if all_data:
        df = pd.DataFrame(all_data)
        st.success("Done!")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="aliexpress_results.csv", mime="text/csv")
    else:
        st.warning("No products found or API blocked. Try again later.")
