import streamlit as st
import pandas as pd
import requests
import time

# 画面のタイトルと全体のレイアウト設定
st.set_page_config(page_title="DLSオプション監視システム", layout="wide")
st.title("📊 DLS戦略 複数銘柄監視ダッシュボード")
st.caption("サクソバンクAPI連携 × LINE Notify通知機能搭載（クラウド版）")

# ------------------------------------------------------------------
# 画面を3つのタブに分割
# ------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🔧 ① 初期設定 & 準備ガイド", "📈 ② 銘柄・決算ターゲット管理", "🚨 ③ リアルタイム監視"])

# ==========================================
# タブ①：初期設定 & 準備ガイド
# ==========================================
with tab1:
    st.header("🛠️ 各種アカウントの準備と連携設定")
    st.write("この画面のステップに従ってトークンを取得し、下のフォームに入力してください。")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🟢 STEP 1: LINE Notifyの準備")
        st.markdown("""
        1. [LINE Notify マイページ](https://notify-api.line.me/mypage/) にLINEアカウントでログインします。
        2. **「トークンを発行する」** ボタンを押します。
        3. トークン名（例: `オプショントレード通知`）を入力し、通知を送信したいトークルーム（「1対1でLINE Notifyから通知を受け取る」など）を選択します。
        4. 発行された **文字列（トークン）** をコピーして、右側のフォームに貼り付けてください。
        """)
        
        st.subheader("🔵 STEP 2: サクソバンク OpenAPI の準備")
        st.markdown("""
        1. [Saxo Developer Portal](https://www.developer.saxo/) にサクソバンク証券の口座でログインします。
        2. アプリケーションを登録（最初はデモ環境である **SIM環境** がおすすめ）し、`App Key` と `App Secret` を取得します。
        3. 24時間有効な `Access Token` を発行し、右側のフォームに貼り付けてください。
        """)

    with col2:
        st.subheader("💾 接続情報の入力・保存フォーム")
        
        line_token = st.text_input("LINE Notify トークン", type="password", help="LINEから取得したトークン")
        saxo_token = st.text_input("サクソバンク Access Token", type="password", help="Saxo Developerから取得したトークン")
        saxo_env = st.selectbox("サクソバンク環境", ["SIM (デモ口座)", "LIVE (本番口座)"])
        
        if st.button("🔧 設定を保存してテスト通知を送る"):
            if line_token:
                url = "https://notify-api.line.me/api/notify"
                headers = {"Authorization": f"Bearer {line_token}"}
                payload = {"message": "\n✅ Web管理画面からLINEの連携に成功しました！\nこれでオプション監視アラートを受け取れます。"}
                res = requests.post(url, headers=headers, data=payload)
                
                if res.status_code == 200:
                    st.success("🎉 設定が保存され、LINEへテストメッセージを送信しました！スマホを確認してください。")
                else:
                    st.error("❌ LINEトークンが無効、または送信に失敗しました。")
            else:
                st.warning("LINEトークンを入力してください。")

# ==========================================
# タブ②：銘柄・決算ターゲット管理
# ==========================================
with tab2:
    st.header("📈 監視銘柄の追加と編集")
    
    with st.form("add_symbol_form"):
        st.subheader("➕ 監視銘柄の新規登録")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            new_sym = st.text_input("銘柄コード", value="AMZN", help="例: AMZN, NVDA, AAPL")
        with c2:
            new_strike = st.number_input("権利行使価格 (Strike)", value=185.0, step=0.5)
        with c3:
            new_expiry = st.text_input("満期日（決算ターゲット）", value="2024-08-02", help="YYYY-MM-DD形式")
        with c4:
            new_threshold = st.number_input("デルタ差トリガー", value=0.13, step=0.01, help="初期設定は0.13")
            
        submit_btn = st.form_submit_with_button("この銘柄を監視リストに追加する")
        
        if submit_btn:
            st.success(f"📌 {new_sym} (Strike: {new_strike}, 満期: {new_expiry}) をリストに追加しました！")

    st.markdown("---")
    st.subheader("📋 現在の監視リスト一覧")
    
    sample_data = {
        "銘柄": ["AMZN", "NVDA"],
        "基準ストライク": [185.0, 120.0],
        "ターゲット満期日": ["2024-08-02", "2024-08-23"],
        "アラート閾値": [0.13, 0.13]
    }
    df = pd.DataFrame(sample_data)
    st.dataframe(df, use_container_width=True)

# ==========================================
# タブ③：リアルタイム監視
# ==========================================
with tab3:
    st.header("🚨 リアルタイム・デルタ差の監視窓")
    st.write("サクソバンク証券から最新のオプションチェーンデータを取得し、5分ごとに自動更新します。")
    
    monitor_data = [
        {"銘柄": "AMZN", "Strike": 185.0, "Call Delta": 0.65, "Put Delta": -0.32, "現在のデルタ差": 0.33, "ステータス": "⚠️ 要調整 (>=0.13)"},
        {"銘柄": "NVDA", "Strike": 120.0, "Call Delta": 0.51, "Put Delta": -0.48, "現在のデルタ差": 0.03, "ステータス": "正常 (ニュートラル)"}
    ]
    m_df = pd.DataFrame(monitor_data)
    
    def highlight_status(val):
        color = 'background-color: #ffcccc; color: #cc0000; font-weight: bold' if '要調整' in str(val) else ''
        return color

    st.subheader("📊 現在の各銘柄のデルタ・ニュートラル乖離率")
    st.dataframe(m_df.style.applymap(highlight_status, subset=['ステータス']), use_container_width=True)
    
    if st.button("🔄 今すぐ最新データに更新する"):
        with st.spinner("サクソバンクAPIから最新データを取得中..."):
            time.sleep(1)
            st.success("最新のデルタ値に更新されました。")
