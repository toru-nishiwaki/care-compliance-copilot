from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st


# =========================
# 基本設定
# =========================

st.set_page_config(
    page_title="Care Compliance Copilot",
    page_icon="✅",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"


# =========================
# 共通関数
# =========================

@st.cache_data
def load_csv(file_path: Path) -> pd.DataFrame:
    """CSVを読み込む。文字コード差による事故を少しだけ回避する。"""
    if not file_path.exists():
        return pd.DataFrame()

    encodings = ["utf-8-sig", "utf-8", "cp932"]
    for encoding in encodings:
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            continue

    return pd.read_csv(file_path)


def save_csv(df: pd.DataFrame, file_path: Path) -> None:
    """CSVを保存する。"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    st.cache_data.clear()


def show_dataframe(df: pd.DataFrame, title: str) -> None:
    """DataFrameを安全に表示する。"""
    st.subheader(title)

    if df.empty:
        st.warning("データが見つかりません。CSVファイルの配置を確認してください。")
        return

    st.caption(f"{len(df)}件 / {len(df.columns)}列")
    st.dataframe(df, use_container_width=True)

def show_file_path(label, file_path):
    """画面上に表示中・保存先のファイルパスを表示する。"""
    try:
        path_text = file_path.relative_to(BASE_DIR)
    except ValueError:
        path_text = file_path

    st.caption(f"{label}：`{path_text}`")


def find_draft_column(df):
    """AI下書きらしき列を探す。中身が入っている列を優先する。"""
    candidates = [
        "ai_note_draft",
        "ai_draft",
        "ai_draft_text",
        "draft",
        "note_draft",
        "monitoring_draft",
    ]

    for candidate in candidates:
        if candidate in df.columns:
            non_empty_count = df[candidate].fillna("").astype(str).str.strip().ne("").sum()
            if non_empty_count > 0:
                return candidate

    for col in df.columns:
        lower_col = str(col).lower()
        if "draft" in lower_col or "ai" in lower_col:
            non_empty_count = df[col].fillna("").astype(str).str.strip().ne("").sum()
            if non_empty_count > 0:
                return col

    return None

def filter_rows_with_draft(df, draft_col):
    """AI下書きが入っている行だけを抽出する。"""
    return df[
        df[draft_col].fillna("").astype(str).str.strip().ne("")
    ].copy()

def build_row_label(row: pd.Series, index: int) -> str:
    """選択ボックス用の表示名を作る。"""
    parts = [f"No.{index}"]

    for col in ["user_id", "record_date", "monitoring_id", "record_id", "document_type", "alert_type"]:
        if col in row.index and pd.notna(row[col]):
            parts.append(f"{col}: {row[col]}")

    return " / ".join(parts)


# =========================
# サイドバー
# =========================

st.sidebar.title("Care Compliance Copilot")
st.sidebar.caption("訪問介護向けコンプライアンス確認支援MVP")

page = st.sidebar.radio(
    "メニュー",
    [
        "概要",
        "データ確認",
        "アラート一覧",
        "AI下書き確認",
        "職員確認済み保存",
    ],
)


# =========================
# 画面1：概要
# =========================

if page == "概要":
    st.title("Care Compliance Copilot")
    st.write(
        "訪問介護事業所の運営指導前チェックにおいて、"
        "書類不備・未確認・未承認の記録を検出し、"
        "必要に応じてAI下書き候補を提示するコンプライアンス確認支援MVPです。"
    )

    st.info(
        "AIが記録を自動確定するのではなく、"
        "職員が確認・修正したうえで保存する運用を前提としています。"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("入力CSV", "5種類")
        st.caption("利用者情報、ケアプラン、日々の記録など")

    with col2:
        st.metric("出力CSV", "6種類")
        st.caption("アラート、AI下書き、確認済み記録など")

    with col3:
        st.metric("確認フロー", "職員確認必須")
        st.caption("AI下書きは確定記録ではありません")

    st.subheader("本MVPで確認できること")
    st.markdown(
        """
        - 書類不備・未確認・未承認状態の確認
        - 利用者別アラートの確認
        - 日々の介護記録に対するAI下書き候補の確認
        - 月間モニタリング文書のAI下書き候補の確認
        - 職員確認済みとして保存する流れの確認
        """
    )


# =========================
# 画面2：データ確認
# =========================

elif page == "データ確認":
    st.title("データ確認")
    st.caption("入力CSVの内容を確認する画面です。利用者情報、ケアプラン、日々の介護記録などを切り替えて確認できます。")

    data_files = {
        "利用者情報 users.csv": DATA_DIR / "users.csv",
        "ケアプラン care_plans.csv": DATA_DIR / "care_plans.csv",
        "日々の介護記録 daily_records.csv": DATA_DIR / "daily_records.csv",
        "モニタリング記録 monitoring_records.csv": DATA_DIR / "monitoring_records.csv",
        "書類ステータス document_status.csv": DATA_DIR / "document_status.csv",
    }

    selected_name = st.selectbox("表示するCSVを選択", list(data_files.keys()))
    selected_path = data_files[selected_name]
    df = load_csv(selected_path)

    show_file_path("表示ファイル", selected_path)
    show_dataframe(df, selected_name)


# =========================
# 画面3：アラート一覧
# =========================

elif page == "アラート一覧":
    st.title("アラート一覧")
    st.caption("書類不備・未確認・未承認などのアラートを一覧で確認する画面です。")

    alerts_path = OUTPUTS_DIR / "alerts_integrated.csv"
    summary_path = OUTPUTS_DIR / "alert_summary_by_user.csv"

    alerts_df = load_csv(alerts_path)
    summary_df = load_csv(summary_path)

    st.subheader("統合アラート")
    show_file_path("表示ファイル", alerts_path)

    if alerts_df.empty:
        st.warning("alerts_integrated.csv が見つからないか、内容が空です。")
    else:
        filtered_df = alerts_df.copy()

        if "user_id" in filtered_df.columns:
            user_options = ["すべて"] + sorted(filtered_df["user_id"].dropna().astype(str).unique().tolist())
            selected_user = st.selectbox("利用者IDで絞り込み", user_options)

            if selected_user != "すべて":
                filtered_df = filtered_df[filtered_df["user_id"].astype(str) == selected_user]

        if "alert_type" in filtered_df.columns:
            alert_options = ["すべて"] + sorted(filtered_df["alert_type"].dropna().astype(str).unique().tolist())
            selected_alert = st.selectbox("アラート種別で絞り込み", alert_options)

            if selected_alert != "すべて":
                filtered_df = filtered_df[filtered_df["alert_type"].astype(str) == selected_alert]

        st.caption(f"表示件数：{len(filtered_df)}件")
        st.dataframe(filtered_df, use_container_width=True)

    st.subheader("利用者別アラート集計")
    show_file_path("表示ファイル", summary_path)
    show_dataframe(summary_df, "alert_summary_by_user.csv")


# =========================
# 画面4：AI下書き確認
# =========================

elif page == "AI下書き確認":
    st.title("AI下書き確認")
    st.caption("AIが生成した下書き候補を確認する画面です。ここで表示される文章は確定記録ではありません。")

    st.warning(
        "ここに表示される文章はAI下書き候補です。"
        "確定記録として使用する前に、必ず職員が確認・修正してください。"
    )

    draft_type = st.radio(
        "確認する下書きの種類",
        [
            "日々の介護記録",
            "月間モニタリング",
        ],
        horizontal=True,
    )

    if draft_type == "日々の介護記録":
        draft_path = OUTPUTS_DIR / "daily_records_with_ai_note_draft.csv"
    else:
        draft_path = OUTPUTS_DIR / "monitoring_records_with_ai_draft.csv"

    show_file_path("表示ファイル", draft_path)

    df = load_csv(draft_path)

    if df.empty:
        st.warning("AI下書きCSVが見つからないか、内容が空です。")
    else:
        draft_col = find_draft_column(df)

        if draft_col is None:
            st.error("AI下書き列が見つかりません。列名を確認してください。")
            st.dataframe(df, use_container_width=True)
        else:
            st.caption(f"AI下書き列：{draft_col}")
            st.dataframe(df, use_container_width=True)

            st.subheader("下書き本文プレビュー")

            preview_df = filter_rows_with_draft(df, draft_col)

            if preview_df.empty:
                st.warning("表示できるAI下書き候補がありません。")
            else:
                row_labels = {
                    build_row_label(row, index): index
                    for index, row in preview_df.iterrows()
                }

                selected_label = st.selectbox("確認する行を選択", list(row_labels.keys()))
                selected_index = row_labels[selected_label]
                selected_row = preview_df.loc[selected_index]

                st.text_area(
                    "AI下書き候補",
                    value=str(selected_row[draft_col]),
                    height=300,
                    disabled=True,
                )


# =========================
# 画面5：職員確認済み保存
# =========================

elif page == "職員確認済み保存":
    st.title("職員確認済み保存")
    st.caption("AI下書き候補を職員が確認・修正し、確認済みデータとしてCSVに保存する画面です。")

    review_type = st.radio(
        "確認する記録の種類",
        [
            "日々の介護記録",
            "月間モニタリング",
        ],
        horizontal=True,
    )

    if review_type == "日々の介護記録":
        source_path = OUTPUTS_DIR / "daily_records_with_ai_note_draft.csv"
        reviewed_path = OUTPUTS_DIR / "daily_records_note_reviewed.csv"
        default_status = "note_reviewed"
    else:
        source_path = OUTPUTS_DIR / "monitoring_records_with_ai_draft.csv"
        reviewed_path = OUTPUTS_DIR / "monitoring_records_reviewed.csv"
        default_status = "reviewed"

    show_file_path("読み込み元", source_path)
    show_file_path("保存先", reviewed_path)

    st.info(
        "MVP検証用のため、同じ記録を複数回保存できる仕様です。"
        "実運用では、同一record_id / monitoring_idの重複チェックまたは上書き保存が必要です。"
    )

    source_df = load_csv(source_path)
    if source_df.empty:
        st.warning("確認対象のAI下書きCSVが見つからないか、内容が空です。")
    else:
        draft_col = find_draft_column(source_df)

        if draft_col is None:
            st.error("AI下書き列が見つかりません。列名を確認してください。")
            st.dataframe(source_df, width="stretch")
        else:
            review_df = filter_rows_with_draft(source_df, draft_col)

            if review_df.empty:
                st.warning("職員確認できるAI下書き候補がありません。")
                st.stop()

            row_labels = {
                build_row_label(row, index): index
                for index, row in review_df.iterrows()
            }

            selected_label = st.selectbox("確認する行を選択", list(row_labels.keys()))
            selected_index = row_labels[selected_label]
            selected_row = review_df.loc[selected_index]
            st.subheader("AI下書き候補")
            st.text_area(
                "元のAI下書き",
                value=str(selected_row[draft_col]),
                height=220,
                disabled=True,
            )

            st.subheader("職員確認後の文章")
            reviewed_text = st.text_area(
                "必要に応じて修正してください",
                value=str(selected_row[draft_col]),
                height=260,
            )

            reviewed_by = st.text_input("確認者名", value="サ責A")

            confirmed = st.checkbox(
                "AI下書き内容を確認し、必要な修正を行いました。"
            )

            if st.button("職員確認済みとして保存", type="primary"):
                if not confirmed:
                    st.error("保存するには、職員確認チェックを入れてください。")
                elif not reviewed_by.strip():
                    st.error("確認者名を入力してください。")
                else:
                    reviewed_df = load_csv(reviewed_path)

                    save_row = selected_row.copy()
                    save_row["reviewed_text"] = reviewed_text
                    save_row["review_status"] = default_status
                    save_row["reviewed_by"] = reviewed_by.strip()
                    save_row["reviewed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    save_row_df = pd.DataFrame([save_row])

                    if reviewed_df.empty:
                        updated_df = save_row_df
                    else:
                        updated_df = pd.concat([reviewed_df, save_row_df], ignore_index=True)

                    save_csv(updated_df, reviewed_path)

                    st.success(f"{reviewed_path.name} に職員確認済みデータを保存しました。")
                    st.dataframe(save_row_df, width="stretch")