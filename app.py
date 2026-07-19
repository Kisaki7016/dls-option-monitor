import streamlit as st
import pandas as pd
import requests
import time

# 画面のタイトルと全体のレイアウト設定
st.set_page_config(page_title="DLSオプション監視システム", layout="wide")
st.title("📊 DLS戦略 複数銘柄監視ダッシュボード")
st.caption("サクソバンクAPI連携 × Discord通知機能搭載（クラウド版）")

# ------------------------------------------------------------------
# 画面を3つのタブに分割
# ------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🔧 ① 初期設定 & 準備ガイド", "📈 ② 銘柄・決算ターゲット管理", "🚨 ③ リアルタイム監視"])

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
                payload = {"content": "✅ **Web管理画面からDiscordの連携に成功しました！**\nこれでオプション監視アラートを制限なしで受け取れます。"}
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
# タブ②：銘柄・決算ターゲット管理
# ==========================================
with tab2:
    st.header("📈 監視銘柄の追加と編集")
    
    with st.form("add_symbol_form"):
        st.subheader("➕ 監視銘柄の新規登録")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            new_sym = st.text_input("銘柄コード", value="AMZN", help="例: AMZN, AAPL")
        with c2:
            new_strike = st.number_input("権利行使価格 (Strike)", value=240.0)
        with c3:
            new_expiry = st.text_input("満期日 (YYYY-MM-DD)", value="2026-07-31")
        with c4:
            new_threshold = st.number_input("デルタ差トリガー", value=0.05)
            
        # 🛠️ タイポを st.form_submit_button に修正しました
        submit_btn = st.form_submit_button("この銘柄を監視リストに追加する")
        
        if submit_btn:
            st.success(f"📌 {new_sym} (Strike: {new_strike}, 満期: {new_expiry}) を監視リストに追加しました！（※デモ動作）")

    st.subheader("📋 現在の監視銘柄一覧")
    monitor_data = {
        "銘柄": ["AMZN", "AAPL", "NVDA"],
        "タイプ": ["Put", "Put", "Call"],
        "権利行使価格": [240.0, 210.0, 120.0],
        "満期日": ["2026-07-31", "2026-08-21", "2026-07-24"],
        "現在デルタ": [-0.12, -0.08, 0.15],
        "目標値": [-0.15, -0.15, 0.20],
        "ステータス": ["正常", "正常", "要調整"]
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
    st.header("🚨 リアルタイム・シミュレーション")
    st.write("「自動監視をスタート」を押すと、擬似的に相場を監視し、トリガーに達した銘柄があれば通知を飛ばします。")
    
    run_monitor = st.checkbox("🔄 自動監視をバックグラウンドで実行する")
    
    if run_monitor:
        st.info("⏰ 5秒ごとにサクソバンクAPIからデータを取得中... (シミュレーション実行中)")
        status_area = st.empty()
        
        for i in range(3):
            if i == 1:
                status_area.warning("⚠️ NVDA のデルタが目標値に接近しています...")
            elif i == 2:
                status_area.error("🚨 【アラート発令】NVDA が目標トリガーに到達しました！Discordへ通知を送信します。")
                if discord_webhook:
                    payload = {"content": "🚨 **【DLSアラート】**\nNVDA (Strike: 120, 満期: 07-24) のデルタが目標値に到達しました！要調整ステータスです。"}
                    requests.post(discord_webhook, json=payload)
            time.sleep(2)
        st.success("🔄 監視シミュレーションの1サイクルが完了しました。")
