import streamlit as st
import pandas as pd

# --- アプリの基本設定 ---
st.set_page_config(page_title="昇給シミュレーター", layout="wide")
st.title('社員昇給シミュレーター')

# --- サイドバー (入力部分) ---
st.sidebar.header('シミュレーション条件の設定')

# 1. 昇給原資の入力
total_budget = st.sidebar.number_input(
    '昇給原資（予算）を入力してください',
    min_value=0,
    value=1000000,  # 初期値を100万円に設定
    step=100000,
    format='%d'
)

# 2. 昇給率の設定
st.sidebar.subheader('評価ごとの昇給率 (%)')
# st.sliderは小数を返すので、後で100で割る必要はない
rate_s = st.sidebar.slider('S評価 (%)', 0.0, 50.0, 5.0, 0.1)
rate_a = st.sidebar.slider('A評価 (%)', 0.0, 50.0, 3.0, 0.1)
rate_b = st.sidebar.slider('B評価 (%)', 0.0, 50.0, 2.0, 0.1)
rate_c = st.sidebar.slider('C評価 (%)', 0.0, 50.0, 1.0, 0.1)
# D評価は昇給なしで固定
rate_d = 0.0

# 計算で使いやすいように、パーセンテージを小数に変換
raise_rates = {
    'S': rate_s / 100,
    'A': rate_a / 100,
    'B': rate_b / 100,
    'C': rate_c / 100,
    'D': rate_d / 100
}

# 3. 社員データのアップロード
st.sidebar.subheader('社員データ')
uploaded_file = st.sidebar.file_uploader(
    "社員リストのExcelまたはCSVファイルをアップロード",
    type=['xlsx', 'csv']
)

# --- メイン画面 (出力部分) ---

# ファイルがアップロードされたら処理を開始
if uploaded_file is not None:
    try:
        # アップロードされたファイルに応じて読み込み方法を変更
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.header('1. アップロードされた社員データ')
        st.dataframe(df)

        # --- 計算ロジック ---
        # 必須列の確認
        if 'salary' not in df.columns or 'rating' not in df.columns:
            st.error("エラー: アップロードされたファイルには 'salary' と 'rating' という列が必要です。")
        else:
            df_sim = df.copy() # シミュレーション用にデータフレームをコピー
            df_sim['raise_rate'] = df_sim['rating'].map(raise_rates)
            df_sim['increase_amount'] = (df_sim['salary'] * df_sim['raise_rate']).round() # 小数点以下を丸める
            df_sim['new_salary'] = df_sim['salary'] + df_sim['increase_amount']

            total_cost = df_sim['increase_amount'].sum()
            remaining_budget = total_budget - total_cost

            # --- 結果表示 ---
            st.header('2. シミュレーション結果')

            # st.metricで見やすく表示
            col1, col2, col3 = st.columns(3)
            col1.metric("昇給原資（予算）", f"{total_budget:,.0f} 円")
            col2.metric("昇給コスト合計", f"{total_cost:,.0f} 円")

            if remaining_budget >= 0:
                col3.metric("差額（残り予算）", f"{remaining_budget:,.0f} 円")
            else:
                col3.metric("差額（予算不足額）", f"{remaining_budget:,.0f} 円", delta=f"{remaining_budget:,.0f} 円", delta_color="inverse")

            st.header('3. 昇給詳細データ')
            # 表示用にカラムのフォーマットを整える
            df_display = df_sim.copy()
            df_display['raise_rate'] = df_display['raise_rate'].map('{:.2%}'.format) # パーセント表示
            
            st.dataframe(df_display.style.format({
                'salary': '{:,.0f}',
                'increase_amount': '{:,.0f}',
                'new_salary': '{:,.0f}'
            }))

    except Exception as e:
        st.error(f"ファイルの読み込みまたは処理中にエラーが発生しました: {e}")

else:
    # ファイルがアップロードされていない時の案内
    st.info('サイドバーから社員データをアップロードして、シミュレーションを開始してください。')
    st.markdown("""
    ### 期待されるファイル形式
    ExcelまたはCSVファイルで、最低でも以下の2つの列が必要です。
    - `salary`: 現在の年収（数値）
    - `rating`: 評価（S, A, B, C, Dのいずれか）

    **例 (`employees.xlsx`):**
    | name   | salary    | rating |
    |--------|-----------|--------|
    | 佐藤   | 7000000   | S      |
    | 鈴木   | 6500000   | A      |
    | ...    | ...       | ...    |
    """)