
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_ebay_avg_price(keyword):
    url = f"https://www.ebay.com/sch/i.html?_nkw={keyword.replace(' ', '+')}&_sop=12&LH_Sold=1&LH_Complete=1"
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, "lxml")
        prices = []
        links = []
        for item in soup.select(".s-item"):
            price_tag = item.select_one(".s-item__price")
            link_tag = item.select_one(".s-item__link")
            if price_tag and link_tag:
                match = re.search(r'\$([\d,.]+)', price_tag.text)
                if match:
                    prices.append(float(match.group(1).replace(",", "")))
                    links.append(link_tag["href"])
        if prices:
            avg_price = round(sum(prices) / len(prices), 2)
            return avg_price, links[0]
        else:
            return None, None
    except:
        return None, None

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
    except:
        return []

def compile_data(keyword):
    ali_data = get_aliexpress_products(keyword)
    ebay_avg_price, ebay_sample_link = get_ebay_avg_price(keyword)
    results = []
    for title, ali_price, rating, orders, ali_url in ali_data:
        if ebay_avg_price and ali_price:
            ebay_fee = (ebay_avg_price * 0.13) + 0.30
            profit = round(ebay_avg_price - ali_price - ebay_fee, 2)
            if profit > 0:
                results.append({
                    "Keyword": keyword,
                    "Product Title": title,
                    "AliExpress Price": ali_price,
                    "eBay Avg Price": ebay_avg_price,
                    "Estimated Profit": profit,
                    "Orders": orders,
                    "Rating": rating,
                    "AliExpress URL": ali_url,
                    "eBay Sample URL": ebay_sample_link
                })
        time.sleep(0.5)
    return results

st.title("AliExpress to eBay Profit Tracker")

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
        st.download_button("Download CSV", data=csv, file_name="ebay_tracker_results.csv", mime="text/csv")
    else:
        st.warning("No profitable products found or search failed.")
