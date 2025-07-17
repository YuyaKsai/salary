import streamlit as st
import pandas as pd

# --- アプリの基本設定 ---
st.set_page_config(page_title="昇給シミュレーター", layout="wide")
st.title('昇給シミュレーション（マトリクス版）')

# --- 昇給率マトリクスを定義 ---
# 画像の昇給率を辞書形式で定義（S評価-下位なら8% -> 0.08）
raise_matrix_data = {
    '評価': ['S (傑出)', 'A (期待以上)', 'B (期待通り)', 'C (要改善)'],
    '下位1/3': [0.08, 0.06, 0.04, 0.01],
    '中位1/3': [0.07, 0.05, 0.03, 0.00],
    '上位1/3': [0.06, 0.04, 0.02, 0.00],
}
# 計算で使いやすいように、評価（S,A,B,C）と昇給率をマッピングする辞書を作成
# {'S': {'下位': 0.08, '中位': 0.07, '上位': 0.06}, 'A': ...}
raise_matrix_lookup = {
    'S': {'下位': 0.08, '中位': 0.07, '上位': 0.06},
    'A': {'下位': 0.06, '中位': 0.05, '上位': 0.04},
    'B': {'下位': 0.04, '中位': 0.03, '上位': 0.02},
    'C': {'下位': 0.01, '中位': 0.00, '上位': 0.00},
    'D': {'下位': 0.00, '中位': 0.00, '上位': 0.00} # 念のためDも定義
}
# Streamlitでの表示用にデータフレームを作成
matrix_df = pd.DataFrame(raise_matrix_data).set_index('評価')


# --- サイドバー (入力部分) ---
st.sidebar.header('シミュレーション条件の設定')

# 1. 昇給原資の入力
total_budget = st.sidebar.number_input(
    '昇給原資（予算）を入力してください',
    min_value=0,
    value=1000000,
    step=100000,
    format='%d'
)

# 2. 社員データのアップロード
st.sidebar.subheader('社員データ')
uploaded_file = st.sidebar.file_uploader(
    "社員リストのExcelまたはCSVファイルをアップロード",
    type=['xlsx', 'csv']
)

# 昇給マトリクスをサイドバーに表示
st.sidebar.subheader('昇給率マトリクス')
st.sidebar.dataframe(matrix_df.style.format('{:.0%}'))


# --- メイン画面 (出力部分) ---

# ファイルがアップロードされたら処理を開始
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)

        st.header('1. アップロードされた社員データ')
        st.dataframe(df)

        # --- 計算ロジック ---
        # 必須列の確認
        required_cols = ['salary', 'rating', 'band_position']
        if not all(col in df.columns for col in required_cols):
            st.error(f"エラー: ファイルには {', '.join(required_cols)} の列が必要です。")
        else:
            # 昇給率を決定する関数
            def get_raise_rate(row):
                rating = row['rating']
                position = row['band_position']
                return raise_matrix_lookup.get(rating, {}).get(position, 0) # 見つからない場合は0%

            df_sim = df.copy()
            df_sim['raise_rate'] = df_sim.apply(get_raise_rate, axis=1)
            df_sim['increase_amount'] = (df_sim['salary'] * df_sim['raise_rate']).round()
            df_sim['new_salary'] = df_sim['salary'] + df_sim['increase_amount']

            total_cost = df_sim['increase_amount'].sum()
            remaining_budget = total_budget - total_cost

            # --- 結果表示 ---
            st.header('2. シミュレーション結果')
            col1, col2, col3 = st.columns(3)
            col1.metric("昇給原資（予算）", f"{total_budget:,.0f} 円")
            col2.metric("昇給コスト合計", f"{total_cost:,.0f} 円")
            delta_color = "normal" if remaining_budget >= 0 else "inverse"
            col3.metric("差額", f"{remaining_budget:,.0f} 円", delta_color=delta_color)

            st.header('3. 昇給詳細データ')
            st.dataframe(df_sim.style.format({
                'raise_rate': '{:.2%}',
                'salary': '{:,.0f}',
                'increase_amount': '{:,.0f}',
                'new_salary': '{:,.0f}'
            }))

    except Exception as e:
        st.error(f"ファイルの読み込みまたは処理中にエラーが発生しました: {e}")

else:
    st.info('サイドバーから社員データをアップロードしてシミュレーションを開始してください。')
    st.markdown("""
    ### 期待されるファイル形式
    ExcelまたはCSVファイルで、以下の3つの列が必須です。
    - `salary`: 現在の年収（数値）
    - `rating`: 評価（S, A, B, C, Dのいずれか）
    - `band_position`: 給与バンド内の位置（**下位**, **中位**, **上位** のいずれか）
    """)
