import streamlit as st
import pandas as pd
import requests
import time

# 画面のタイトルと全体のレイアウト設定
st.set_page_config(page_title="DLSストラドル監視システム", layout="wide")
st.title("📊 DLS戦略 ストラドル専用監視ダッシュボード")
st.caption("サクソバンクAPI連携 × Discord通知機能搭載（絶対値デルタ監視版）")

# ------------------------------------------------------------------
# 画面を3つのタブに分割
# ------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🔧 ① 初期設定 & 準備ガイド", "📈 ② ストラドル銘柄管理", "🚨 ③ リアルタイム監視"])

# ==========================================
# タブ①：初期設定 & 準備ガイド
# ==========================================
with tab1:
    st.header("🛠️ 各種アカウントの準備と連携設定")
    st.write("この画面のステップに従って設定情報を取得し、下のフォームに入力してください。")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🟢 STEP 1: Discord Webhookの準備")
        st.markdown("""
        1. Discordで自分専用のサーバーを作成するか、既存のサーバーを開きます。
        2. 通知を受け取りたいチャンネルの **「⚙️ チャンネルの編集」**（歯車マーク）をクリックします。
        3. 左メニューの **「連携サービス」** を選び、**「ウェブフック」** をクリックします。
        4. **「新しいウェブフック」** を作成し、**「ウェブフックURLをコピー」** をクリックして右側のフォームに貼り付けてください。
        """)
        
        st.subheader("🔵 STEP 2: サクソバンク OpenAPI の準備")
        st.markdown("""
        1. [Saxo Developer Portal](https://www.developer.saxo/) にサクソバンク証券の口座でログインします。
        2. アプリケーションを登録（最初はデモ環境である **SIM環境** がおすすめ）し、`App Key` と `App Secret` を取得します。
        3. 24時間有効な `Access Token` を発行し、右側のフォームに貼り付けてください。
        """)
        
    with col2:
        st.subheader("💾 接続情報の入力・保存フォーム")
        discord_webhook = st.text_input("Discord Webhook URL", type="password", help="Discordから取得したウェブフックURL")
        saxo_token = st.text_input("サクソバンク Access Token", type="password", help="Saxo Developerから取得したトークン")
        saxo_env = st.selectbox("サクソバンク環境", ["SIM (デモ口座)", "LIVE (本番口座)"])
        
        if st.button("🔧 設定を保存してテスト通知を送る"):
            if discord_webhook:
                payload = {"content": "✅ **Web管理画面からDiscordの連携に成功しました！**\nストラドル監視アラートの準備が完了しました。"}
                try:
                    res = requests.post(discord_webhook, json=payload)
                    if res.status_code in [200, 204]:
                        st.success("🎉 設定が保存され、Discordへテストメッセージを送信しました！部屋を確認してください。")
                    else:
                        st.error(f"❌ Discordへの送信に失敗しました。URLが正しいか確認してください。")
                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {e}")
            else:
                st.warning("Discord Webhook URLを入力してください。")

# ==========================================
# タブ②：ストラドル銘柄管理
# ==========================================
with tab2:
    st.header("📈 ストラドルポジションの追加・編集")
    
    with st.form("add_symbol_form"):
        st.subheader("➕ 監視ポジションの新規登録")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            new_sym = st.text_input("対象銘柄コード", value="AMZN", help="例: AMZN, AAPL")
        with c2:
            new_strike = st.number_input("権利行使価格 (Strike)", value=240.0)
        with c3:
            new_expiry = st.text_input("満期日 (YYYY-MM-DD)", value="2026-07-31")
        with c4:
            new_threshold = st.number_input("デルタ乖離トリガー (絶対値)", value=0.05, min_value=0.01, step=0.01, help="目標デルタからの許容乖離幅（絶対値）")
            
        submit_btn = st.form_submit_button("このストラドルを監視リストに追加する")
        
        if submit_btn:
            st.success(f"📌 {new_sym} ストラドル (Strike: {new_strike}, 満期: {new_expiry}, 許容乖離: {new_threshold}) を監視リストに追加しました！")

    st.subheader("📋 現在のストラドル監視一覧")
    # ストラドル専用（Call/Put合計の合計デルタを監視するイメージ）
    monitor_data = {
        "銘柄": ["AMZN", "AAPL", "NVDA"],
        "権利行使価格": [240.0, 210.0, 120.0],
        "満期日": ["2026-07-31", "2026-08-21", "2026-07-24"],
        "現在ネットデルタ": [-0.02, 0.04, 0.12],   # Callデルタ + Putデルタ の合計値
        "目標デルタ": [0.00, 0.00, 0.00],         # 基本はデルタニュートラル(0)想定
        "現在のデルタ差(絶対値)": [0.02, 0.04, 0.12], # abs(現在 - 目標)
        "許容トリガー": [0.05, 0.05, 0.10],
        "ステータス": ["正常", "正常", "要調整"]    # NVDAは 0.12 > 0.10 なのでアラート
    }
    m_df = pd.DataFrame(monitor_data)
    
    def highlight_status(val):
        if val == "要調整":
            return "background-color: #ffcccc; color: #cc0000; font-weight: bold;"
        return ""
        
    st.dataframe(m_df.style.map(highlight_status, subset=['ステータス']), use_container_width=True)

# ==========================================
# タブ③：リアルタイム監視
# ==========================================
with tab3:
    st.header("🚨 リアルタイム・ストラドル監視")
    st.write("「自動監視をスタート」を押すと、サクソバンクから取得したネットデルタの変動を監視し、設定した乖離トリガー（絶対値）を超えた場合にアラートを飛ばします。")
    
    run_monitor = st.checkbox("🔄 自動監視をバックグラウンドで実行する")
    
    if run_monitor:
        st.info("⏰ 5秒ごとにサクソバンクAPIからデータを取得中... (シミュレーション実行中)")
        status_area = st.empty()
        
        # 擬似的な相場変動シミュレーション（絶対値での判定ロジックを模したもの）
        for i in range(3):
            if i == 1:
                status_area.warning("⚠️ NVDA ストラドルの合計デルタが目標値から接近して乖離しています...")
            elif i == 2:
                status_area.error("🚨 【アラート発令】NVDA ストラドルのデルタ乖離が設定値（0.10）を突破しました！")
                if discord_webhook:
                    payload = {
                        "content": "🚨 **【DLSストラドルアラート】**\n"
                                   "NVDA (Strike: 120, 満期: 07-24) のネットデルタが目標から大きく乖離しました！\n"
                                   "📊 **現在デルタ差(絶対値): 0.12** (許容値: 0.10)\n"
                                   "デルタニュートラルへのリバランス（調整）を検討してください。"
                    }
                    requests.post(discord_webhook, json=payload)
            time.sleep(2)
        st.success("🔄 監視シミュレーションの1サイクルが完了しました。")
