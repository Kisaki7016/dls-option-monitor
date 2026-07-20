import streamlit as st
import pandas as pd
import requests
import time
import datetime

# 画面のタイトルと全体のレイアウト設定
st.set_page_config(page_title="DLSストラドル監視システム", layout="wide")

# タイトル表示の重なりを防ぐために少し余白を持たせたデザインに変更
st.markdown("<h1 style='margin-bottom: 0px;'>📊 DLS戦略 ストラドル専用監視ダッシュボード</h1>", unsafe_allow_html=True)
st.caption("サクソバンクAPI連携 × Discord通知機能搭載（絶対値デルタ監視版）")
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 状態管理（Session State）の初期化
# ==========================================
if 'positions' not in st.session_state:
    st.session_state['positions'] = [
        {"ticker": "AMZN", "strike": 240.0, "expiry": "2026-07-31", "current_delta": -0.02, "target_delta": 0.0, "trigger": 0.05},
        {"ticker": "AAPL", "strike": 210.0, "expiry": "2026-08-21", "current_delta": 0.04, "target_delta": 0.0, "trigger": 0.05},
        {"ticker": "NVDA", "strike": 120.0, "expiry": "2026-07-24", "current_delta": 0.12, "target_delta": 0.0, "trigger": 0.10},
    ]

# ==========================================
# サクソバンクAPIからデルタを取得する関数（仮）
# ==========================================
def fetch_current_delta(ticker, strike, expiry, token):
    if not token:
        import random
        return round(random.uniform(-0.15, 0.15), 3)
    return 0.00

# ==========================================
# 🚨 ライブ監視 ＆ 一覧表示セクション
# ==========================================
@st.fragment(run_every=5)
def render_live_monitor_zone(token_input):
    st.header("📋 現在のストラドル監視一覧 (5秒自動更新)")
    
    if not st.session_state['positions']:
        st.info("現在監視中のポジションはありません。上のフォームから登録してください。")
        return

    # 1. リアルタイムデータの更新処理
    updated_positions = []
    for pos in st.session_state['positions']:
        pos['current_delta'] = fetch_current_delta(pos['ticker'], pos['strike'], pos['expiry'], token_input)
        updated_positions.append(pos)
    st.session_state['positions'] = updated_positions

    # 2. 表示用データフレームの作成と計算
    df = pd.DataFrame(st.session_state['positions'])
    df['delta_diff'] = (df['current_delta'] - df['target_delta']).abs()
    df['status'] = df.apply(lambda r: "要調整" if r['delta_diff'] > r['trigger'] else "正常", axis=1)
    
    # 🛠️ 【改善】事前に数値を適切な桁数にフォーマット（丸め処理）して視認性をUP
    df['strike'] = df['strike'].map(lambda x: f"{x:.2f}")
    df['current_delta'] = df['current_delta'].map(lambda x: f"{x:+.3f}") # 符号付き表示
    df['target_delta'] = df['target_delta'].map(lambda x: f"{x:.3f}")
    df['delta_diff'] = df['delta_diff'].map(lambda x: f"{x:.3f}")
    df['trigger'] = df['trigger'].map(lambda x: f"{x:.2f}")

    # カラム名を日本語に整形
    df_display = df.rename(columns={
        "ticker": "銘柄",
        "strike": "権利行使価格",
        "expiry": "満期日",
        "current_delta": "現在ネットデルタ",
        "target_delta": "目標デルタ",
        "delta_diff": "現在のデルタ差(絶対値)",
        "trigger": "許容トリガー",
        "status": "ステータス"
    })
    
    df_display = df_display[["銘柄", "権利行使価格", "満期日", "現在ネットデルタ", "目標デルタ", "現在のデルタ差(絶対値)", "許容トリガー", "ステータス"]]

    # 3. 「要調整」の行を赤くハイライトするスタイリング
    def highlight_status(row):
        return ['background-color: #ffcccc; color: #cc0000; font-weight: bold;' if row['ステータス'] == "要調整" else '' for _ in row]

    st.dataframe(df_display.style.apply(highlight_status, axis=1), use_container_width=True, hide_index=True)
    
    # 4. ❌ ポジションの削除機能
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("❌ 監視ポジションの削除")
    delete_options = [
        f"{idx}: {p['ticker']} (Strike: {float(p['strike']):.2f}, 満期: {p['expiry']})" 
        for idx, p in enumerate(st.session_state['positions'])
    ]
    
    col_del1, col_del2 = st.columns([3, 1])
    with col_del1:
        target_to_delete = st.selectbox("削除するポジションを選択してください", options=delete_options, label_visibility="collapsed")
    with col_del2:
        if st.button("選択したポジションを削除", use_container_width=True):
            target_idx = int(target_to_delete.split(":")[0])
            removed = st.session_state['positions'].pop(target_idx)
            st.warning(f" ⚠️ {removed['ticker']} を監視リストから削除しました。")
            time.sleep(1)
            st.rerun()

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
        discord_webhook = st.text_input("Discord Webhook URL", type="password")
    with col2:
        st.subheader("🔵 STEP 2: サクソバンク OpenAPI の準備")
        saxo_token = st.text_input("サクソバンク Access Token", type="password")

# ==========================================
# タブ②：ストラドル銘柄管理
# ==========================================
with tab2:
    st.header("➕ 監視ポジションの新規登録")
    
    col_in1, col_in2, col_in3, col_in4 = st.columns(4)
    with col_in1:
        input_ticker = st.text_input("対象銘柄コード", value="AMZN")
    with col_in2:
        input_strike = st.number_input("権利行使価格 (Strike)", value=250.00, step=5.0)
    with col_in3:
        input_expiry = st.date_input("満期日 (YYYY-MM-DD)", value=datetime.date(2026, 8, 7))
    with col_in4:
        input_trigger = st.number_input("デルタ乖離トリガー（絶対値）", value=0.13, step=0.01)
        
    if st.button("このストラドルを監視リストに追加する", type="primary"):
        new_position = {
            "ticker": input_ticker.upper(),
            "strike": float(input_strike),
            "expiry": input_expiry.strftime("%Y-%m-%d"),
            "current_delta": 0.0,
            "target_delta": 0.0,
            "trigger": float(input_trigger)
        }
        st.session_state['positions'].append(new_position)
        st.success(f" 🟢 {input_ticker.upper()} ストラドルを監視リストに追加しました！")
        time.sleep(1)
        st.rerun()

    st.markdown("---")
    render_live_monitor_zone(saxo_token)

# ==========================================
# タブ③：リアルタイム監視
# ==========================================
with tab3:
    st.header("🚨 アラートログ ＆ 通知履歴")
    st.write("ここにDiscordへの通知履歴などを流すロジックを今後作り込めます。")
