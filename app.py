import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # 🔥 轉型為 Chrome 核心
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import re
import requests
import pandas as pd
import os

st.set_page_config(page_title="屏基看診提醒雲端版", page_icon="🏥", layout="centered")

# ==========================================
# ⚙️ 核心配置
# ==========================================
SHEET_ID = "1_cvylqVa37FcEunXNBO-iH0QxBRLlzfBMp7-F2xHeao"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

LINE_ACCESS_TOKEN = "wG5i0FGWHF7/MRfxdKmdeid/K0+uQ4b8bL/Ha6SehuMJxH4dzCcC3XLExvqV47HXamB/GG8kiNXfaWuqAxbBQpQEZ+BN+Yt5e+3DICdN7jCKmuU85r6CJVOWULCrAkfKD19E0eWznT+5v3tVPb29ugdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "U78abd5b466c9df853475809a7597419f"

@st.cache_data(ttl=5)
def load_doctor_data():
    try:
        xl = pd.ExcelFile(EXCEL_URL)
        df = xl.parse("工作表2") if "工作表2" in xl.sheet_names else xl.parse(1)
        df = df.iloc[:, :3] 
        df.columns = ["科別", "診間", "醫師姓名"]
        df = df.dropna(subset=["醫師姓名"])
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"無法讀取雲端資料。錯誤: {e}")
        return None

df_doc = load_doctor_data()

def send_line_push(msg):
    if not LINE_ACCESS_TOKEN or LINE_ACCESS_TOKEN.startswith("YOUR_"): return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    payload = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": msg}]}
    try: requests.post(url, headers=headers, json=payload)
    except: pass

st.title("🏥 屏基看診進度智慧提醒 (手機雲端版)")

if df_doc is not None:
    st.write("✨ 雲端試算表同步成功！")
    
    all_departments = sorted(list(df_doc["科別"].unique()))
    col1, col2 = st.columns(2)
    with col1:
        selected_dept = st.selectbox("1. 選擇看診大科別", all_departments)
    
    filtered_df = df_doc[df_doc["科別"] == selected_dept].copy()
    filtered_df["顯示名稱"] = filtered_df["診間"] + " - " + filtered_df["醫師姓名"]
    doc_options = sorted(list(filtered_df["顯示名稱"].unique()))
    
    with col2:
        selected_doc_info = st.selectbox("2. 選擇看診醫師", doc_options)
    
    with st.form("control_form"):
        col3, col4 = st.columns(2)
        with col3:
            my_number = st.number_input("3. 您的掛號號碼", min_value=1, value=17, step=1)
        with col4:
            buffer_count = st.slider("4. 前幾號收到提醒", min_value=1, max_value=5, value=2)
            
        submit_btn = st.form_submit_button("🚀 開始雲端背景監控")

    # ==========================================
    # 🚀 核心監控 (雲端環境高相容進化版)
    # ==========================================
    if submit_btn:
        target_doctor = selected_doc_info.split(" - ")[1]
        target_trigger = my_number - buffer_count
        st.info(f"🔄 雲端監控已啟動！目標：【{selected_dept} - {target_doctor} 醫師】，提醒線：【{target_trigger} 號】。")
        
        status_area = st.empty()
        
        # 🛡️ 【雲端 Chrome 參數極致優化】
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 雲端環境必須強制無頭模式
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")  # 🔥 Linux 雲端環境必備防崩潰參數
        chrome_options.add_argument("--disable-dev-shm-usage")  # 🔥 防止記憶體不足爆掉
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 🎯 偵測目前是家裡 Windows 還是 Streamlit 雲端 Linux，自動切換驅動路徑
        if os.path.exists("/usr/bin/chromium-browser"):
            chrome_options.binary_location = "/usr/bin/chromium-browser"
            
        url = "https://www.ptch.org.tw/index.php/shw_seqForm"
        driver = None
        
        try:
            while True:
                if driver is None:
                    try:
                        # 自動對齊 Chrome/Chromium 驅動
                        service = Service(ChromeDriverManager().install())
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                    except Exception as init_err:
                        status_area.error(f"雲端瀏覽器初始化失敗，5秒後重試... 錯誤: {init_err}")
                        time.sleep(5)
                        continue

                try:
                    driver.get(url)
                    time.sleep(5) 
                    
                    # 模擬選單切換
                    try:
                        dropdown_element = driver.find_element(By.TAG_NAME, "select")
                        dropdown = Select(dropdown_element)
                        dropdown.select_by_visible_text(selected_dept)
                        time.sleep(2.5)
                    except Exception as select_err:
                        pass
                    
                    rows = driver.find_elements(By.TAG_NAME, "tr")
                    found = False
                    current_number = None
                    
                    search_doctor = "陳柏" if "陳柏" in target_doctor else target_doctor
                    target_doc_clean = search_doctor.replace(" ", "")
                    
                    for row in rows:
                        row_raw_text = row.get_attribute("textContent")
                        if not row_raw_text: continue
                        row_text = "".join(row_raw_text.split())
                        
                        if target_doc_clean in row_text:
                            found = True
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if cells:
                                last_cell_text = cells[-1].get_attribute("textContent").strip()
                                num_match = re.search(r'\d+', last_cell_text)
                                if num_match:
                                    current_number = int(num_match.group())
                            break 
                    
                    if current_number is not None:
                        status_area.metric(
                            label=f"🔄 雲端檢查時間：{time.strftime('%H:%M:%S')}", 
                            value=f"【{target_doctor} 醫師】當前叫號：{current_number} 號",
                            delta=f"距離您的號碼還有 {my_number - current_number} 號"
                        )
                        
                        if current_number >= target_trigger:
                            if current_number < my_number:
                                line_msg = f"🏥【屏基看診提醒】\n\n您選取的【{target_doctor} 醫師】目前叫號已達 {current_number} 號（已過提醒線 {target_trigger} 號）！\n您的號碼是【{my_number} 號】，請立刻出發前往診間！"
                            else:
                                line_msg = f"🚨【屏基看診緊急通知：可能已過號】\n\n雲端偵測到叫號瞬間暴跳！【{target_doctor} 醫師】目前叫號已達 {current_number} 號（您的號碼是 {my_number} 號）！請火速前往診間確認！"
                            
                            send_line_push(line_msg)
                            
                            # 雲端版移除本機音效播放以提升相容性，完全保留強大的 LINE 通知與氣球特效
                            st.balloons()
                            st.error(line_msg)
                            try: driver.quit()
                            except: pass
                            st.stop()
                            
                    elif not found:
                        status_area.warning(f"⏳ 檢查時間：{time.strftime('%H:%M:%S')} | 屏基網頁上目前找不到【{target_doctor} 醫師】的看診進度。")
                    
                    time.sleep(10)

                except Exception as loop_err:
                    try: driver.quit()
                    except: pass
                    driver = None  
                    time.sleep(5)

        except Exception as e:
            st.error(f"雲端執行發生嚴重錯誤: {e}")
        finally:
            if driver:
                try: driver.quit()
                except: pass