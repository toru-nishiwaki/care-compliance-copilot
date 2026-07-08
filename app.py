from pathlib import Path
from datetime import datetime

import re

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
SAMPLE_OUTPUTS_DIR = BASE_DIR / "sample_outputs"

DATA_FILES = {
    "利用者情報 users.csv": DATA_DIR / "users.csv",
    "ケアプラン care_plans.csv": DATA_DIR / "care_plans.csv",
    "日々の介護記録 daily_records.csv": DATA_DIR / "daily_records.csv",
    "モニタリング記録 monitoring_records.csv": DATA_DIR / "monitoring_records.csv",
    "書類ステータス document_status.csv": DATA_DIR / "document_status.csv",
}

TARGET_TYPE_SOURCE_MAP = {
    "daily_record": (DATA_DIR / "daily_records.csv", "record_id", "日々の介護記録"),
    "monitoring": (DATA_DIR / "monitoring_records.csv", "monitoring_id", "月間モニタリング記録"),
    "document": (DATA_DIR / "document_status.csv", "document_id", "書類ステータス"),
}

QUEUE_LOG_PATH = OUTPUTS_DIR / "confirmation_queue_log.csv"
QUEUE_LOG_COLUMNS = [
    "queue_type",
    "record_type",
    "target_id",
    "user_id",
    "detail",
    "reviewed_text",
    "review_status",
    "reviewed_by",
    "reviewed_at",
]


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


def load_outputs_csv(filename: str) -> tuple[pd.DataFrame, Path]:
    """outputs/を優先して読み込み、空または未生成の場合はsample_outputs/にフォールバックする。"""
    primary_path = OUTPUTS_DIR / filename
    df = load_csv(primary_path)
    if not df.empty:
        return df, primary_path

    fallback_path = SAMPLE_OUTPUTS_DIR / filename
    fallback_df = load_csv(fallback_path)
    if not fallback_df.empty:
        return fallback_df, fallback_path

    return df, primary_path


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


def save_reviewed_row(
    reviewed_path: Path,
    selected_row: pd.Series,
    reviewed_text: str,
    reviewed_by: str,
    review_status: str,
) -> pd.DataFrame:
    """AI下書きに対する職員確認済みの内容を、確認済みCSVに1行追記する。"""
    reviewed_df = load_csv(reviewed_path)

    save_row = selected_row.copy()
    save_row["reviewed_text"] = reviewed_text
    save_row["review_status"] = review_status
    save_row["reviewed_by"] = reviewed_by
    save_row["reviewed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_row_df = pd.DataFrame([save_row])

    if reviewed_df.empty:
        updated_df = save_row_df
    else:
        updated_df = pd.concat([reviewed_df, save_row_df], ignore_index=True)

    save_csv(updated_df, reviewed_path)
    return save_row_df


def save_queue_log(
    queue_type: str,
    record_type: str,
    target_id,
    user_id,
    detail: str,
    reviewed_text: str,
    reviewed_by: str,
) -> pd.DataFrame:
    """確認キュー（未承認記録・アラート確認）の職員確認結果を、統一ログに1行追記する。"""
    existing_df = load_csv(QUEUE_LOG_PATH)
    if existing_df.empty:
        existing_df = pd.DataFrame(columns=QUEUE_LOG_COLUMNS)

    new_row = {
        "queue_type": queue_type,
        "record_type": record_type,
        "target_id": target_id,
        "user_id": user_id,
        "detail": detail,
        "reviewed_text": reviewed_text,
        "review_status": "confirmed",
        "reviewed_by": reviewed_by,
        "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    updated_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
    save_csv(updated_df, QUEUE_LOG_PATH)
    return updated_df


def split_keywords(text) -> list:
    """ケアプランのservice_contentを、読点・カンマ区切りのキーワードに分解する。"""
    if pd.isna(text):
        return []
    parts = re.split(r"[、,]", str(text))
    return [p.strip() for p in parts if p.strip()]


def build_checklist_candidates(care_plans_df: pd.DataFrame, daily_df: pd.DataFrame) -> pd.DataFrame:
    """ケアプランのservice_contentキーワードと、日々の記録のservice_itemsをキーワード部分一致で突き合わせる。

    完全一致ではなくルールベースの部分一致判定であり、AIによる判定は行わない。
    結果はあくまで「職員確認が必要なレ点候補」であり、実施有無の確定情報ではない。
    """
    rows = []

    for _, plan in care_plans_df.iterrows():
        keywords = split_keywords(plan.get("service_content"))
        if not keywords:
            continue

        user_records = daily_df[daily_df["user_id"] == plan["user_id"]]

        for _, record in user_records.iterrows():
            service_items_text = str(record.get("service_items", ""))

            for keyword in keywords:
                matched = keyword in service_items_text
                rows.append(
                    {
                        "user_id": plan["user_id"],
                        "plan_id": plan.get("plan_id"),
                        "record_id": record.get("record_id"),
                        "record_date": record.get("record_date"),
                        "plan_keyword": keyword,
                        "service_items": record.get("service_items"),
                        "checklist_completed": record.get("checklist_completed"),
                        "candidate_status": "実施候補あり（要確認）" if matched else "未実施候補（要確認）",
                    }
                )

    return pd.DataFrame(rows)


def render_draft_review_flow(source_path: Path, reviewed_path: Path, default_status: str, key_prefix: str) -> None:
    """AI下書きを職員が確認・修正・保存する一連のUIフロー。職員確認済み保存ページと確認キューの両方から呼び出す。"""
    source_df, resolved_source_path = load_outputs_csv(source_path.name)

    show_file_path("読み込み元", resolved_source_path)
    show_file_path("保存先", reviewed_path)

    if source_df.empty:
        st.warning("確認対象のAI下書きCSVが見つからないか、内容が空です。")
        return

    draft_col = find_draft_column(source_df)

    if draft_col is None:
        st.error("AI下書き列が見つかりません。列名を確認してください。")
        st.dataframe(source_df, use_container_width=True)
        return

    review_df = filter_rows_with_draft(source_df, draft_col)

    if review_df.empty:
        st.warning("職員確認できるAI下書き候補がありません。")
        return

    row_labels = {
        build_row_label(row, index): index
        for index, row in review_df.iterrows()
    }

    selected_label = st.selectbox("確認する行を選択", list(row_labels.keys()), key=f"{key_prefix}_select")
    selected_index = row_labels[selected_label]
    selected_row = review_df.loc[selected_index]

    st.subheader("AI下書き候補")
    st.text_area(
        "元のAI下書き",
        value=str(selected_row[draft_col]),
        height=220,
        disabled=True,
        key=f"{key_prefix}_original",
    )

    st.subheader("職員確認後の文章")
    reviewed_text = st.text_area(
        "必要に応じて修正してください",
        value=str(selected_row[draft_col]),
        height=260,
        key=f"{key_prefix}_text",
    )

    reviewed_by = st.text_input("確認者名", value="サ責A", key=f"{key_prefix}_by")

    confirmed = st.checkbox(
        "AI下書き内容を確認し、必要な修正を行いました。",
        key=f"{key_prefix}_confirm",
    )

    if st.button("職員確認済みとして保存", type="primary", key=f"{key_prefix}_save"):
        if not confirmed:
            st.error("保存するには、職員確認チェックを入れてください。")
        elif not reviewed_by.strip():
            st.error("確認者名を入力してください。")
        else:
            save_row_df = save_reviewed_row(
                reviewed_path, selected_row, reviewed_text, reviewed_by.strip(), default_status
            )
            st.success(f"{reviewed_path.name} に職員確認済みデータを保存しました。確認履歴・監査ログにも反映されます。")
            st.dataframe(save_row_df, use_container_width=True)


# =========================
# サイドバー
# =========================

st.sidebar.title("Care Compliance Copilot")
st.sidebar.caption("訪問介護向けコンプライアンス確認支援MVP")

page = st.sidebar.radio(
    "メニュー",
    [
        "使い方・業務フロー",
        "概要ダッシュボード",
        "書類アラート一覧",
        "アラート根拠確認",
        "計画書連動レ点候補",
        "特記事項AI補填デモ",
        "月間モニタリングAI下書き",
        "確認キュー",
        "職員確認済み保存",
        "確認履歴・監査ログ",
    ],
)


# =========================
# 画面1：使い方・業務フロー
# =========================

if page == "使い方・業務フロー":
    st.title("使い方・業務フロー")
    st.write(
        "訪問介護事業所の運営指導前チェックにおいて、"
        "書類不備・未確認・未承認の記録を検出し、"
        "必要に応じてAI下書き候補を提示するコンプライアンス確認支援MVPです。"
    )

    st.info(
        "AIが記録を自動確定するのではなく、"
        "職員が確認・修正したうえで保存する運用を前提としています。"
    )

    st.subheader("業務フロー")
    st.markdown(
        """
        1. **書類アラート一覧** で、未作成・未承認・未確認のアラートを確認する
        2. **アラート根拠確認** で、アラートの元になった記録・書類を確認する
        3. **計画書連動レ点候補**・**特記事項AI補填デモ**・**月間モニタリングAI下書き** で、AIが提示する候補・下書きを確認する
        4. **確認キュー** または **職員確認済み保存** で、職員が内容を確認・必要に応じて修正する
        5. 確認者名を入力し、確認チェックを入れて保存する
        6. **確認履歴・監査ログ** で、保存された確認結果を確認する
        """
    )

    st.subheader("画面一覧")
    st.markdown(
        """
        1. 使い方・業務フロー：このページ
        2. 概要ダッシュボード：アラート状況の全体像を確認
        3. 書類アラート一覧：未作成・未承認・未確認のアラート一覧
        4. アラート根拠確認：アラートの元データを確認
        5. 計画書連動レ点候補：ケアプランと日々の記録のキーワード突合候補（ルールベース）
        6. 特記事項AI補填デモ：日々の記録の特記事項AI補填案
        7. 月間モニタリングAI下書き：月間モニタリング文書のAI下書き
        8. 確認キュー：未確認AI下書き・未承認記録・要確認アラートを横断して確認・保存
        9. 職員確認済み保存：AI下書きを職員が確認・修正・保存
        10. 確認履歴・監査ログ：職員確認済みの履歴一覧
        """
    )

    with st.expander("開発者向け：入力CSVを直接確認する"):
        selected_name = st.selectbox("表示するCSVを選択", list(DATA_FILES.keys()), key="usage_data_select")
        selected_path = DATA_FILES[selected_name]
        df = load_csv(selected_path)

        show_file_path("表示ファイル", selected_path)
        show_dataframe(df, selected_name)


# =========================
# 画面2：概要ダッシュボード
# =========================

elif page == "概要ダッシュボード":
    st.title("概要ダッシュボード")
    st.write(
        "訪問介護事業所の運営指導前チェックにおいて、"
        "書類不備・未確認・未承認の記録を検出し、"
        "必要に応じてAI下書き候補を提示するコンプライアンス確認支援MVPです。"
    )

    st.info(
        "AIが記録を自動確定するのではなく、"
        "職員が確認・修正したうえで保存する運用を前提としています。"
    )

    alerts_df, _ = load_outputs_csv("alerts_integrated.csv")
    summary_df, _ = load_outputs_csv("alert_summary_by_user.csv")

    total_alerts = len(alerts_df)
    high_severity_count = int((alerts_df["severity"] == "high").sum()) if "severity" in alerts_df.columns else 0
    affected_users = summary_df["user_id"].nunique() if "user_id" in summary_df.columns else 0
    review_required_count = (
        int(alerts_df["human_review_required"].sum()) if "human_review_required" in alerts_df.columns else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("総アラート件数", total_alerts)
        st.caption("alerts_integrated.csv の件数")

    with col2:
        st.metric("重大アラート（high）", high_severity_count)
        st.caption("severity=high の件数")

    with col3:
        st.metric("対象利用者数", affected_users)
        st.caption("アラート対象の利用者数")

    with col4:
        st.metric("要職員確認", review_required_count)
        st.caption("human_review_required=True の件数")

    if not alerts_df.empty and "alert_category" in alerts_df.columns:
        st.subheader("アラート種別ごとの件数")
        st.bar_chart(alerts_df["alert_category"].value_counts())

    st.subheader("本MVPで確認できること")
    st.markdown(
        """
        - 書類不備・未確認・未承認状態の確認と、その根拠データの確認
        - ケアプランと日々の記録を突き合わせたレ点候補の確認（ルールベース）
        - 日々の介護記録に対するAI下書き候補の確認
        - 月間モニタリング文書のAI下書き候補の確認
        - 確認キューによる、複数種別の確認待ち項目の横断確認・保存
        - 職員確認済みとして保存する流れと、その履歴・監査ログの確認
        """
    )


# =========================
# 画面3：書類アラート一覧
# =========================

elif page == "書類アラート一覧":
    st.title("書類アラート一覧")
    st.caption("書類不備・未確認・未承認などのアラートを一覧で確認する画面です。")

    alerts_path = OUTPUTS_DIR / "alerts_integrated.csv"
    summary_path = OUTPUTS_DIR / "alert_summary_by_user.csv"

    alerts_df, resolved_alerts_path = load_outputs_csv("alerts_integrated.csv")
    summary_df, resolved_summary_path = load_outputs_csv("alert_summary_by_user.csv")

    st.subheader("統合アラート")
    show_file_path("表示ファイル", resolved_alerts_path)

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
    show_file_path("表示ファイル", resolved_summary_path)
    show_dataframe(summary_df, "alert_summary_by_user.csv")


# =========================
# 画面4：アラート根拠確認
# =========================

elif page == "アラート根拠確認":
    st.title("アラート根拠確認")
    st.caption("アラートの元になった記録・書類を確認する画面です。")

    st.warning(
        "アラートはルールベースで自動検知されたものです。"
        "対応の要否は、必ず元データを確認したうえで職員が判断してください。"
    )

    alerts_df, resolved_alerts_path = load_outputs_csv("alerts_integrated.csv")
    show_file_path("表示ファイル", resolved_alerts_path)

    if alerts_df.empty:
        st.warning("alerts_integrated.csv が見つからないか、内容が空です。")
    else:
        row_labels = {
            f"No.{index} / {row.get('user_id')} / {row.get('alert_type')} / {row.get('target_type')}:{row.get('target_id')}": index
            for index, row in alerts_df.iterrows()
        }

        selected_label = st.selectbox("確認するアラートを選択", list(row_labels.keys()))
        selected_index = row_labels[selected_label]
        selected_alert = alerts_df.loc[selected_index]

        st.subheader("アラート内容")
        st.dataframe(pd.DataFrame([selected_alert]), use_container_width=True)

        target_type = selected_alert.get("target_type")
        target_id = selected_alert.get("target_id")

        st.subheader("根拠となる元データ")

        if target_type not in TARGET_TYPE_SOURCE_MAP:
            st.error(f"target_type '{target_type}' に対応する元データが定義されていません。")
        else:
            source_path, id_col, source_label = TARGET_TYPE_SOURCE_MAP[target_type]
            source_df = load_csv(source_path)
            show_file_path(f"参照元（{source_label}）", source_path)

            if source_df.empty or id_col not in source_df.columns:
                st.warning("元データが見つかりませんでした。")
            else:
                matched_df = source_df[source_df[id_col].astype(str) == str(target_id)]

                if matched_df.empty:
                    st.warning(f"{id_col} = {target_id} に一致する元データが見つかりませんでした。")
                else:
                    st.dataframe(matched_df, use_container_width=True)


# =========================
# 画面5：計画書連動レ点候補
# =========================

elif page == "計画書連動レ点候補":
    st.title("計画書連動レ点候補")
    st.caption("ケアプランの内容と、日々の介護記録の実施内容をキーワードで突き合わせる画面です。")

    st.warning(
        "ここに表示される内容は、キーワードベースのルールベース判定による候補です。AIによる判定ではありません。"
        "「実施候補あり」「未実施候補」のいずれも確定情報ではなく、必ず職員が元の記録を確認してください。"
    )

    care_plans_df = load_csv(DATA_DIR / "care_plans.csv")
    daily_df = load_csv(DATA_DIR / "daily_records.csv")

    if care_plans_df.empty or daily_df.empty:
        st.warning("care_plans.csv または daily_records.csv が見つからないか、内容が空です。")
    else:
        candidates_df = build_checklist_candidates(care_plans_df, daily_df)

        if candidates_df.empty:
            st.warning("レ点候補を生成できませんでした。ケアプランのservice_content列を確認してください。")
        else:
            user_options = ["すべて"] + sorted(candidates_df["user_id"].dropna().astype(str).unique().tolist())
            selected_user = st.selectbox("利用者IDで絞り込み", user_options)

            filtered_df = candidates_df
            if selected_user != "すべて":
                filtered_df = filtered_df[filtered_df["user_id"].astype(str) == selected_user]

            status_options = ["すべて"] + sorted(filtered_df["candidate_status"].dropna().unique().tolist())
            selected_status = st.selectbox("候補ステータスで絞り込み", status_options)

            if selected_status != "すべて":
                filtered_df = filtered_df[filtered_df["candidate_status"] == selected_status]

            st.caption(f"表示件数：{len(filtered_df)}件（職員確認が必要なレ点候補）")
            st.dataframe(filtered_df, use_container_width=True)


# =========================
# 画面6：特記事項AI補填デモ
# =========================

elif page == "特記事項AI補填デモ":
    st.title("特記事項AI補填デモ")
    st.caption("日々の介護記録の特記事項に対するAI下書き候補を確認する画面です。ここで表示される文章は確定記録ではありません。")

    st.warning(
        "ここに表示される文章はAI下書き候補です。"
        "確定記録として使用する前に、必ず職員が確認・修正してください。"
    )

    draft_path = OUTPUTS_DIR / "daily_records_with_ai_note_draft.csv"
    df, resolved_path = load_outputs_csv(draft_path.name)

    show_file_path("表示ファイル", resolved_path)

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

                selected_label = st.selectbox("確認する行を選択", list(row_labels.keys()), key="daily_draft_select")
                selected_index = row_labels[selected_label]
                selected_row = preview_df.loc[selected_index]

                st.text_area(
                    "AI下書き候補",
                    value=str(selected_row[draft_col]),
                    height=300,
                    disabled=True,
                    key="daily_draft_preview",
                )


# =========================
# 画面7：月間モニタリングAI下書き
# =========================

elif page == "月間モニタリングAI下書き":
    st.title("月間モニタリングAI下書き")
    st.caption("月間モニタリング文書のAI下書き候補を確認する画面です。ここで表示される文章は確定記録ではありません。")

    st.warning(
        "ここに表示される文章はAI下書き候補です。"
        "確定記録として使用する前に、必ず職員が確認・修正してください。"
    )

    draft_path = OUTPUTS_DIR / "monitoring_records_with_ai_draft.csv"
    df, resolved_path = load_outputs_csv(draft_path.name)

    show_file_path("表示ファイル", resolved_path)

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

                selected_label = st.selectbox("確認する行を選択", list(row_labels.keys()), key="monitoring_draft_select")
                selected_index = row_labels[selected_label]
                selected_row = preview_df.loc[selected_index]

                st.text_area(
                    "AI下書き候補",
                    value=str(selected_row[draft_col]),
                    height=300,
                    disabled=True,
                    key="monitoring_draft_preview",
                )


# =========================
# 画面8：確認キュー
# =========================

elif page == "確認キュー":
    st.title("確認キュー")
    st.caption("未確認のAI下書き・未承認の記録や書類・確認が必要なアラートを横断して確認する画面です。")

    st.info(
        "各項目は、以下の流れで確認・保存します。\n"
        "1. 対象レコードを選ぶ　2. AI下書き・元記録・アラート理由を確認する　3. 必要に応じて修正する　"
        "4. 確認者名を入力する　5. 確認チェックを入れる　6. 「職員確認済みにする」ボタンで保存する　"
        "7. 保存後、確認履歴・監査ログに反映される"
    )

    tab_draft, tab_unapproved, tab_alert = st.tabs(
        ["未確認のAI下書き", "未承認の記録・書類", "確認が必要なアラート"]
    )

    with tab_draft:
        review_type = st.radio(
            "確認する記録の種類",
            ["日々の介護記録", "月間モニタリング"],
            horizontal=True,
            key="queue_draft_type",
        )

        if review_type == "日々の介護記録":
            source_path = OUTPUTS_DIR / "daily_records_with_ai_note_draft.csv"
            reviewed_path = OUTPUTS_DIR / "daily_records_note_reviewed.csv"
            default_status = "note_reviewed"
        else:
            source_path = OUTPUTS_DIR / "monitoring_records_with_ai_draft.csv"
            reviewed_path = OUTPUTS_DIR / "monitoring_records_reviewed.csv"
            default_status = "reviewed"

        render_draft_review_flow(source_path, reviewed_path, default_status, key_prefix="queue_draft")

    with tab_unapproved:
        unapproved_items = []

        doc_df = load_csv(DATA_DIR / "document_status.csv")
        if not doc_df.empty and "approved" in doc_df.columns:
            for _, row in doc_df[~doc_df["approved"]].iterrows():
                unapproved_items.append(
                    {
                        "record_type": "document",
                        "target_id": row.get("document_id"),
                        "user_id": row.get("user_id"),
                        "detail": f"{row.get('document_type')}が未承認です（有効期間: {row.get('valid_from')}〜{row.get('valid_to')}）",
                    }
                )

        daily_df = load_csv(DATA_DIR / "daily_records.csv")
        if not daily_df.empty and "approved" in daily_df.columns:
            for _, row in daily_df[~daily_df["approved"]].iterrows():
                unapproved_items.append(
                    {
                        "record_type": "daily_record",
                        "target_id": row.get("record_id"),
                        "user_id": row.get("user_id"),
                        "detail": f"{row.get('record_date')}の日々の介護記録が未承認です",
                    }
                )

        monitoring_df = load_csv(DATA_DIR / "monitoring_records.csv")
        if not monitoring_df.empty and "approved" in monitoring_df.columns:
            for _, row in monitoring_df[~monitoring_df["approved"]].iterrows():
                unapproved_items.append(
                    {
                        "record_type": "monitoring_record",
                        "target_id": row.get("monitoring_id"),
                        "user_id": row.get("user_id"),
                        "detail": f"{row.get('record_date')}の月間モニタリング記録が未承認です",
                    }
                )

        unapproved_df = pd.DataFrame(unapproved_items)

        if unapproved_df.empty:
            st.success("現在、未承認の記録・書類はありません。")
        else:
            labels = {
                f"No.{index} / {row['record_type']} / {row['target_id']} / {row['user_id']}": index
                for index, row in unapproved_df.iterrows()
            }
            selected_label = st.selectbox("確認する未承認項目を選択", list(labels.keys()), key="queue_unapproved_select")
            selected_item = unapproved_df.loc[labels[selected_label]]

            st.write(selected_item["detail"])

            reviewed_text = st.text_area(
                "確認コメント（必要に応じて記入してください）",
                value="",
                key="queue_unapproved_text",
            )
            reviewed_by = st.text_input("確認者名", value="サ責A", key="queue_unapproved_by")
            confirmed = st.checkbox("内容を確認しました。", key="queue_unapproved_confirm")

            if st.button("職員確認済みにする", type="primary", key="queue_unapproved_save"):
                if not confirmed:
                    st.error("保存するには、確認チェックを入れてください。")
                elif not reviewed_by.strip():
                    st.error("確認者名を入力してください。")
                else:
                    save_queue_log(
                        "unapproved",
                        selected_item["record_type"],
                        selected_item["target_id"],
                        selected_item["user_id"],
                        selected_item["detail"],
                        reviewed_text,
                        reviewed_by.strip(),
                    )
                    st.success("確認履歴・監査ログに保存しました。")

    with tab_alert:
        alerts_df, _ = load_outputs_csv("alerts_integrated.csv")

        if alerts_df.empty or "human_review_required" not in alerts_df.columns:
            review_alerts_df = pd.DataFrame()
        else:
            review_alerts_df = alerts_df[alerts_df["human_review_required"] == True]  # noqa: E712

        if review_alerts_df.empty:
            st.success("現在、職員確認が必要なアラートはありません。")
        else:
            labels = {
                f"No.{index} / {row.get('user_id')} / {row.get('alert_type')} / {row.get('target_id')}": index
                for index, row in review_alerts_df.iterrows()
            }
            selected_label = st.selectbox("確認するアラートを選択", list(labels.keys()), key="queue_alert_select")
            selected_item = review_alerts_df.loc[labels[selected_label]]

            st.write(selected_item.get("detail"))

            reviewed_text = st.text_area(
                "確認コメント（必要に応じて記入してください）",
                value="",
                key="queue_alert_text",
            )
            reviewed_by = st.text_input("確認者名", value="サ責A", key="queue_alert_by")
            confirmed = st.checkbox("内容を確認しました。", key="queue_alert_confirm")

            if st.button("職員確認済みにする", type="primary", key="queue_alert_save"):
                if not confirmed:
                    st.error("保存するには、確認チェックを入れてください。")
                elif not reviewed_by.strip():
                    st.error("確認者名を入力してください。")
                else:
                    save_queue_log(
                        "alert",
                        selected_item.get("target_type"),
                        selected_item.get("target_id"),
                        selected_item.get("user_id"),
                        selected_item.get("detail"),
                        reviewed_text,
                        reviewed_by.strip(),
                    )
                    st.success("確認履歴・監査ログに保存しました。")


# =========================
# 画面9：職員確認済み保存
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
        key="page9_review_type",
    )

    if review_type == "日々の介護記録":
        source_path = OUTPUTS_DIR / "daily_records_with_ai_note_draft.csv"
        reviewed_path = OUTPUTS_DIR / "daily_records_note_reviewed.csv"
        default_status = "note_reviewed"
    else:
        source_path = OUTPUTS_DIR / "monitoring_records_with_ai_draft.csv"
        reviewed_path = OUTPUTS_DIR / "monitoring_records_reviewed.csv"
        default_status = "reviewed"

    st.info(
        "MVP検証用のため、同じ記録を複数回保存できる仕様です。"
        "実運用では、同一record_id / monitoring_idの重複チェックまたは上書き保存が必要です。"
    )

    render_draft_review_flow(source_path, reviewed_path, default_status, key_prefix="page9")


# =========================
# 画面10：確認履歴・監査ログ
# =========================

elif page == "確認履歴・監査ログ":
    st.title("確認履歴・監査ログ")
    st.caption("職員が確認・保存した記録の履歴を確認する画面です。")

    daily_reviewed_df, daily_reviewed_path = load_outputs_csv("daily_records_note_reviewed.csv")
    monitoring_reviewed_df, monitoring_reviewed_path = load_outputs_csv("monitoring_records_reviewed.csv")
    queue_log_df = load_csv(QUEUE_LOG_PATH)

    history_rows = []

    for _, row in daily_reviewed_df.iterrows():
        history_rows.append(
            {
                "record_type": "daily_record",
                "target_id": row.get("record_id"),
                "user_id": row.get("user_id"),
                "review_status": row.get("review_status"),
                "reviewed_text": row.get("reviewed_text"),
                "reviewed_by": row.get("reviewed_by"),
                "reviewed_at": row.get("reviewed_at"),
                "confirmed_via": "特記事項AI補填デモ / 職員確認済み保存 / 確認キュー",
            }
        )

    for _, row in monitoring_reviewed_df.iterrows():
        history_rows.append(
            {
                "record_type": "monitoring_record",
                "target_id": row.get("monitoring_id"),
                "user_id": row.get("user_id"),
                "review_status": row.get("review_status"),
                "reviewed_text": row.get("reviewed_text"),
                "reviewed_by": row.get("reviewed_by"),
                "reviewed_at": row.get("reviewed_at"),
                "confirmed_via": "月間モニタリングAI下書き / 職員確認済み保存 / 確認キュー",
            }
        )

    for _, row in queue_log_df.iterrows():
        history_rows.append(
            {
                "record_type": row.get("record_type"),
                "target_id": row.get("target_id"),
                "user_id": row.get("user_id"),
                "review_status": row.get("review_status"),
                "reviewed_text": row.get("reviewed_text"),
                "reviewed_by": row.get("reviewed_by"),
                "reviewed_at": row.get("reviewed_at"),
                "confirmed_via": "確認キュー",
            }
        )

    history_df = pd.DataFrame(history_rows)

    if history_df.empty:
        st.warning("確認済みの履歴がまだありません。各確認画面で保存すると、ここに表示されます。")
    else:
        reviewer_options = ["すべて"] + sorted(history_df["reviewed_by"].dropna().astype(str).unique().tolist())
        selected_reviewer = st.selectbox("確認者で絞り込み", reviewer_options, key="history_reviewer_filter")

        filtered_df = history_df
        if selected_reviewer != "すべて":
            filtered_df = filtered_df[filtered_df["reviewed_by"].astype(str) == selected_reviewer]

        record_type_options = ["すべて"] + sorted(filtered_df["record_type"].dropna().astype(str).unique().tolist())
        selected_record_type = st.selectbox("種別で絞り込み", record_type_options, key="history_type_filter")

        if selected_record_type != "すべて":
            filtered_df = filtered_df[filtered_df["record_type"].astype(str) == selected_record_type]

        filtered_df = filtered_df.sort_values("reviewed_at", ascending=False, na_position="last")

        st.caption(f"表示件数：{len(filtered_df)}件")
        st.dataframe(filtered_df, use_container_width=True)
