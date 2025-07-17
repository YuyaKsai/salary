import streamlit as st
import pandas as pd

# --- アプリの基本設定 ---
st.set_page_config(page_title="昇給シミュレーター", layout="wide")
st.title('昇給シミュレーション（マトリクス版）')


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

# 2. 昇給率マトリクスをUIで設定
st.sidebar.subheader('昇給率マトリクス (%)')

c1, c2, c3 = st.sidebar.columns(3)
with c1:
    st.write("**下位1/3**")
    rate_s_low = st.number_input('S評価', value=8.0, key='s_low', format="%.1f", step=0.1)
    rate_a_low = st.number_input('A評価', value=6.0, key='a_low', format="%.1f", step=0.1)
    rate_b_low = st.number_input('B評価', value=4.0, key='b_low', format="%.1f", step=0.1)
    rate_c_low = st.number_input('C評価', value=1.0, key='c_low', format="%.1f", step=0.1)

with c2:
    st.write("**中位1/3**")
    rate_s_mid = st.number_input('S評価', value=7.0, key='s_mid', format="%.1f", step=0.1)
    rate_a_mid = st.number_input('A評価', value=5.0, key='a_mid', format="%.1f", step=0.1)
    rate_b_mid = st.number_input('B評価', value=3.0, key='b_mid', format="%.1f", step=0.1)
    rate_c_mid = st.number_input('C評価', value=0.0, key='c_mid', format="%.1f", step=0.1)

with c3:
    st.write("**上位1/3**")
    rate_s_high = st.number_input('S評価', value=6.0, key='s_high', format="%.1f", step=0.1)
    rate_a_high = st.number_input('A評価', value=4.0, key='a_high', format="%.1f", step=0.1)
    rate_b_high = st.number_input('B評価', value=2.0, key='b_high', format="%.1f", step=0.1)
    rate_c_high = st.number_input('C評価', value=0.0, key='c_high', format="%.1f", step=0.1)

# 入力値から計算用のマトリクスを動的に作成
raise_matrix_lookup = {
    'S': {'下位': rate_s_low / 100, '中位': rate_s_mid / 100, '上位': rate_s_high / 100},
    'A': {'下位': rate_a_low / 100, '中位': rate_a_mid / 100, '上位': rate_a_high / 100},
    'B': {'下位': rate_b_low / 100, '中位': rate_b_mid / 100, '上位': rate_b_high / 100},
    'C': {'下位': rate_c_low / 100, '中位': rate_c_mid / 100, '上位': rate_c_high / 100},
    'D': {'下位': 0.00, '中位': 0.00, '上位': 0.00}
}

# 3. 社員データのアップロード
st.sidebar.subheader('社員データ')
uploaded_file = st.sidebar.file_uploader(
    "社員リストのExcelまたはCSVファイルをアップロード",
    type=['xlsx', 'csv']
)

# --- メイン画面 (出力部分) ---

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)

        st.header('1. アップロードされた社員データ')
        st.dataframe(df)

        # --- 計算ロジック ---
        required_cols = ['salary', 'rating', 'band_position']
        if not all(col in df.columns for col in required_cols):
            st.error(f"エラー: ファイルには {', '.join(required_cols)} の列が必要です。")
        else:
            def get_raise_rate(row):
                rating = row['rating']
                position = row['band_position']
                return raise_matrix_lookup.get(rating, {}).get(position, 0)

            df_sim = df.copy()
            df_sim['raise_rate'] = df_sim.apply(get_raise_rate, axis=1)
            df_sim['increase_amount'] = (df_sim['salary'] * df_sim['raise_rate']).round()
            df_sim['new_salary'] = df_sim['salary'] + df_sim['increase_amount']
            df_sim['monthly_salary_current'] = (df_sim['salary'] / 12).round()
            df_sim['monthly_salary_new'] = (df_sim['new_salary'] / 12).round()
            
            # 月給の増減額を計算
            df_sim['monthly_increase'] = df_sim['monthly_salary_new'] - df_sim['monthly_salary_current']

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

            # 表示する列を定義
            display_columns = [
                'name', 'rating', 'band_position', 'raise_rate',
                'salary', 'new_salary', 'increase_amount',
                'monthly_salary_current', 'monthly_salary_new', 'monthly_increase'
            ]
            # フォーマットを定義
            format_dict = {
                'raise_rate': '{:.2%}',
                'salary': '{:,.0f} 円',
                'new_salary': '{:,.0f} 円',
                'increase_amount': '{:+,} 円',
                'monthly_salary_current': '{:,.0f} 円',
                'monthly_salary_new': '{:,.0f} 円',
                'monthly_increase': '{:+,} 円'
            }
            
            display_columns_exist = [col for col in display_columns if col in df_sim.columns]
            st.dataframe(df_sim[display_columns_exist].style.format(format_dict))

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
