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

TODAY = pd.Timestamp.now().normalize()

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
    "alert_key",
    "queue_type",
    "record_type",
    "target_id",
    "user_id",
    "document_name",
    "detail",
    "reviewed_text",
    "review_status",
    "reviewed_by",
    "reviewed_at",
]

# 4分野15書類のカタログ。AIは記録・書類を確定しないため、ここでの「AI補填対象」は
# 「文章下書きの提示が可能」を意味するだけで、確定・承認はすべて職員が行う。
DOCUMENT_CATALOG = {
    "勤務形態一覧表": {
        "category": "人員・勤務体制",
        "ai_fillable": False,
        "ai_reason": "勤務体制は事実確認が必要な情報のため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "出勤簿": {
        "category": "人員・勤務体制",
        "ai_fillable": False,
        "ai_reason": "出勤実績は事実確認が必要な情報のため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "資格証": {
        "category": "人員・勤務体制",
        "ai_fillable": False,
        "ai_reason": "資格・有効期限は事実確認が必要な情報のため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "研修記録": {
        "category": "人員・勤務体制",
        "ai_fillable": True,
        "ai_reason": "",
    },
    "重要事項説明書": {
        "category": "利用者・契約",
        "ai_fillable": False,
        "ai_reason": "説明・同意の事実確認が必要なため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "利用契約書": {
        "category": "利用者・契約",
        "ai_fillable": False,
        "ai_reason": "契約締結・署名の事実確認が必要なため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "個人情報同意書": {
        "category": "利用者・契約",
        "ai_fillable": False,
        "ai_reason": "同意取得の事実確認が必要なため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "居宅サービス計画書": {
        "category": "利用者・契約",
        "ai_fillable": False,
        "ai_reason": "ケアマネジャーが作成する計画書であり、AIが内容を補填・確定してはいけません。職員が原本を確認してください。",
    },
    "訪問介護計画書": {
        "category": "利用者・契約",
        "ai_fillable": False,
        "ai_reason": "計画内容は職員間協議のうえ作成されるべきものであり、AIが補填・確定してはいけません。職員が内容を確認してください。",
    },
    "サービス提供記録": {
        "category": "サービス提供",
        "ai_fillable": True,
        "ai_reason": "",
    },
    "モニタリング記録": {
        "category": "サービス提供",
        "ai_fillable": True,
        "ai_reason": "",
    },
    "担当者会議記録": {
        "category": "サービス提供",
        "ai_fillable": True,
        "ai_reason": "",
    },
    "苦情処理記録": {
        "category": "運営・その他",
        "ai_fillable": True,
        "ai_reason": "",
    },
    "感染症対策マニュアル": {
        "category": "運営・その他",
        "ai_fillable": False,
        "ai_reason": "マニュアル内容は事業所として正式承認された内容である必要があり、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "緊急時対応マニュアル": {
        "category": "運営・その他",
        "ai_fillable": False,
        "ai_reason": "マニュアル内容は事業所として正式承認された内容である必要があり、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
}

# 書類詳細画面でAI補填後プレビュー（書類全体図つき）まで再現できる書類種別。
# それ以外はカタログ上「AI補填対象」であってもステータス確認のみとする
# （本MVPでは中身データを保持していないため）。
CONTENT_BACKED_SOURCE_TYPES = {"daily_record", "monitoring_record", "checklist"}

JAPANESE_WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

CONTRADICTION_RULES = [
    ("食事", ["摂取できなかった", "実施できず", "中止した", "できなかった", "困難であった"]),
    ("水分", ["摂取できなかった", "実施できず", "中止した", "できなかった", "困難であった"]),
    ("入浴", ["実施できず", "中止した", "できなかった"]),
]

MENU_ITEMS = [
    "使い方・業務フロー",
    "概要ダッシュボード",
    "書類アラート一覧",
    "書類詳細・AI補填プレビュー",
    "確認キュー",
    "確認履歴・監査ログ",
    "アラート根拠確認",
    "計画書連動レ点候補",
    "特記事項AI補填デモ",
    "月間モニタリングAI下書き",
    "職員確認済み保存",
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
    """outputs/を優先して読み込み、空または未生成の場合はsample_outputs/にフォールバックする。

    GitHub公開直後などoutputs/が空の状態でも、sample_outputs/の固定サンプルで
    Streamlitアプリがデモ表示できることを保証する。
    """
    primary_path = OUTPUTS_DIR / filename
    df = load_csv(primary_path)
    if not df.empty:
        return df, primary_path

    fallback_path = SAMPLE_OUTPUTS_DIR / filename
    fallback_df = load_csv(fallback_path)
    if not fallback_df.empty:
        return fallback_df, fallback_path

    return df, primary_path


def ensure_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """指定した列が存在しない場合は空文字列列として補い、古いCSVでも例外なく動作させる。"""
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df


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


def build_alert_key(source_type, target_id, user_key, document_name, alert_type) -> str:
    """行番号や保存順に依存しない、アラートの安定した一意キーを作る。"""
    return "|".join(str(x) for x in [source_type, target_id, user_key, document_name, alert_type])


def save_queue_log(
    alert_key: str,
    queue_type: str,
    record_type: str,
    target_id,
    user_id,
    document_name: str,
    detail: str,
    reviewed_text: str,
    reviewed_by: str,
) -> pd.DataFrame:
    """document/checklist/alert系の職員確認結果を、統一ログに1行追記する。

    confirmation_queue_log.csvが存在しない場合はここで自動作成される
    （load_csvは未存在ファイルに対して空DataFrameを返すため）。
    """
    existing_df = load_csv(QUEUE_LOG_PATH)
    if existing_df.empty:
        existing_df = pd.DataFrame(columns=QUEUE_LOG_COLUMNS)

    new_row = {
        "alert_key": alert_key,
        "queue_type": queue_type,
        "record_type": record_type,
        "target_id": target_id,
        "user_id": user_id,
        "document_name": document_name,
        "detail": detail,
        "reviewed_text": reviewed_text,
        "review_status": "confirmed",
        "reviewed_by": reviewed_by,
        "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    updated_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
    save_csv(updated_df, QUEUE_LOG_PATH)
    return updated_df


def get_confirmed_alert_keys() -> set:
    """確認済みのalert_key集合を返す（document/checklist/alert系の確認済み判定に使う）。"""
    queue_df, _ = load_outputs_csv(QUEUE_LOG_PATH.name)
    if queue_df.empty or "alert_key" not in queue_df.columns:
        return set()
    return set(queue_df["alert_key"].dropna().astype(str))


def split_keywords(text) -> list:
    """テキストを、読点・カンマ区切りのキーワードに分解する。"""
    if pd.isna(text):
        return []
    parts = re.split(r"[、,]", str(text))
    return [p.strip() for p in parts if p.strip()]


def get_japanese_weekday(date_value) -> str:
    """日付から日本語の曜日（月〜日）を返す。不正な日付の場合は空文字列。"""
    ts = pd.to_datetime(date_value, errors="coerce")
    if pd.isna(ts):
        return ""
    return JAPANESE_WEEKDAYS[ts.weekday()]


def resolve_subject_label(user_key, users_df: pd.DataFrame) -> tuple:
    """user_key（利用者ID／職員名／ORG）から、対象区分と表示名を解決する。"""
    if user_key == "ORG":
        return "事業所", "事業所全体"
    if isinstance(user_key, str) and user_key.startswith("職員"):
        return "職員", user_key

    if users_df is not None and not users_df.empty and "user_id" in users_df.columns:
        match = users_df[users_df["user_id"] == user_key]
        if not match.empty:
            return "利用者", f"{match.iloc[0]['user_name']}（{user_key}）"

    return "利用者", str(user_key)


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


def _checklist_row(plan, record, alert_type, severity, reason) -> dict:
    return {
        "source_type": "checklist",
        "target_id": record.get("record_id"),
        "user_key": plan.get("user_id"),
        "document_name": "サービス提供記録（レ点チェック）",
        "category": "サービス提供",
        "alert_type": alert_type,
        "alert_reason": reason,
        "shortage_detail": reason,
        "severity": severity,
        "ai_fillable": False,
        "checklist_target": True,
        "ai_reason": "",
    }


def build_checklist_alerts(care_plans_df: pd.DataFrame, daily_df: pd.DataFrame) -> pd.DataFrame:
    """計画書連動レ点チェックの統一アラートを生成する。

    レ点はAIやルールが実施事実を確定するものではなく、あくまで「計画書との
    不一致候補」「要確認」として提示するだけであり、最終確認は必ず職員が行う。
    """
    care_plans_df = ensure_columns(care_plans_df, ["visit_days", "time_slot", "service_category"])
    daily_df = ensure_columns(daily_df, ["time_slot", "service_category"])

    rows = []

    for _, plan in care_plans_df.iterrows():
        plan_keywords = split_keywords(plan.get("service_content"))
        visit_days = split_keywords(plan.get("visit_days"))
        plan_time = str(plan.get("time_slot", "") or "").strip()
        plan_category = str(plan.get("service_category", "") or "").strip()

        user_records = daily_df[daily_df["user_id"] == plan["user_id"]]

        for _, record in user_records.iterrows():
            service_items_text = str(record.get("service_items", "") or "")
            service_items_list = [s.strip() for s in re.split(r"[、,]", service_items_text) if s.strip()]

            # 1. レ点未入力候補：計画書上の支援内容が記録側に見当たらない
            # 1'. レ点未確認：計画書上の支援内容が記録側にも存在する（候補は一致）が、職員確認済みではない
            for keyword in plan_keywords:
                if keyword not in service_items_text:
                    rows.append(
                        _checklist_row(
                            plan,
                            record,
                            "レ点未入力候補",
                            "medium",
                            f"計画書上は「{keyword}」が必要ですが、記録側のレ点に未反映です。職員確認が必要です。",
                        )
                    )
                else:
                    rows.append(
                        _checklist_row(
                            plan,
                            record,
                            "レ点未確認",
                            "low",
                            f"計画書上の「{keyword}」に対応するレ点候補が記録側にありますが、計画書連動レ点候補が未確認です。職員確認が必要です。",
                        )
                    )

            # 2. 計画書との不一致候補：記録側にあるが計画に見当たらない項目
            for item in service_items_list:
                if not any(item in kw or kw in item for kw in plan_keywords):
                    rows.append(
                        _checklist_row(
                            plan,
                            record,
                            "計画書との不一致候補",
                            "medium",
                            f"記録側に「{item}」が選択されていますが、計画書上の支援内容に見当たりません。計画書との不一致候補として職員確認が必要です。",
                        )
                    )

            # 3. 曜日・時間帯・サービス区分の不一致候補
            mismatch_details = []
            record_weekday = get_japanese_weekday(record.get("record_date"))
            if visit_days and record_weekday and record_weekday not in visit_days:
                mismatch_details.append(
                    f"計画書の対象曜日（{'、'.join(visit_days)}）と記録の曜日（{record_weekday}）が一致していません。"
                )

            record_time = str(record.get("time_slot", "") or "").strip()
            if plan_time and record_time and plan_time != record_time:
                mismatch_details.append(
                    f"計画書の対象時間帯（{plan_time}）と記録の時間帯（{record_time}）が一致していません。"
                )

            record_category = str(record.get("service_category", "") or "").strip()
            if plan_category and record_category and plan_category != record_category:
                mismatch_details.append(
                    f"計画書のサービス区分（{plan_category}）と記録のサービス区分（{record_category}）が一致していません。"
                )

            if mismatch_details:
                rows.append(
                    _checklist_row(
                        plan,
                        record,
                        "曜日・時間帯・サービス区分の不一致候補",
                        "medium",
                        " ".join(mismatch_details) + " 職員確認が必要です。",
                    )
                )

            # 5. 特記事項との矛盾候補（簡易キーワード判定、MVPでは簡易判定に限定）
            special_notes = str(record.get("special_notes", "") or "")
            checklist_completed = bool(record.get("checklist_completed"))
            if checklist_completed:
                for positive_kw, negative_phrases in CONTRADICTION_RULES:
                    if positive_kw in service_items_text:
                        for negative_phrase in negative_phrases:
                            if negative_phrase in special_notes:
                                rows.append(
                                    _checklist_row(
                                        plan,
                                        record,
                                        "特記事項との矛盾候補",
                                        "low",
                                        f"「{positive_kw}」に関するレ点は完了となっていますが、特記事項に「{negative_phrase}」の記載があり差異があります。職員確認が必要です。",
                                    )
                                )

    return pd.DataFrame(rows)


def build_document_status_alerts(document_status_df: pd.DataFrame) -> pd.DataFrame:
    """document_status.csvから、書類ステータス系のアラートをルールベースで検知する。"""
    rows = []

    for _, doc in document_status_df.iterrows():
        doc_type = doc.get("document_type")
        catalog = DOCUMENT_CATALOG.get(doc_type, {"category": "その他", "ai_fillable": False, "ai_reason": ""})

        required = bool(doc.get("required"))
        file_exists = bool(doc.get("file_exists"))
        approved = bool(doc.get("approved"))
        approved_by = doc.get("approved_by")
        valid_from = doc.get("valid_from")
        valid_to = doc.get("valid_to")

        alert_specs = []

        if required and not file_exists:
            alert_specs.append(("未作成", "high", "必須書類が作成されていません。職員確認が必要です。"))

        if file_exists and not approved:
            alert_specs.append(("未承認", "medium", "書類は存在しますが、承認が完了していません。職員確認が必要です。"))

        if file_exists:
            valid_to_ts = pd.to_datetime(valid_to, errors="coerce")
            if pd.notna(valid_to_ts) and valid_to_ts < TODAY:
                alert_specs.append(("期限切れ", "high", f"有効期限（{valid_to}）が過ぎています。職員確認が必要です。"))

        if file_exists and approved and (pd.isna(approved_by) or not str(approved_by).strip()):
            alert_specs.append(("署名なし", "medium", "承認済みですが、承認者が記録されていません。職員確認が必要です。"))

        if file_exists and (pd.isna(valid_from) or not str(valid_from).strip()):
            alert_specs.append(("更新日不明", "low", "有効開始日が記録されていません。職員確認が必要です。"))

        for alert_type, severity, reason in alert_specs:
            rows.append(
                {
                    "source_type": "document",
                    "target_id": doc.get("document_id"),
                    "user_key": doc.get("user_id"),
                    "document_name": doc_type,
                    "category": catalog.get("category", "その他"),
                    "alert_type": alert_type,
                    "alert_reason": reason,
                    "shortage_detail": reason,
                    "severity": severity,
                    "ai_fillable": catalog.get("ai_fillable", False),
                    "checklist_target": False,
                    "ai_reason": catalog.get("ai_reason", ""),
                }
            )

    return pd.DataFrame(rows)


def build_ai_draft_alerts() -> pd.DataFrame:
    """AI下書きが職員未確認のまま残っている記録を検知する。"""
    rows = []

    daily_draft_df, _ = load_outputs_csv("daily_records_with_ai_note_draft.csv")
    daily_reviewed_df, _ = load_outputs_csv("daily_records_note_reviewed.csv")
    reviewed_daily_ids = (
        set(daily_reviewed_df["record_id"].astype(str)) if "record_id" in daily_reviewed_df.columns else set()
    )

    if not daily_draft_df.empty:
        draft_col = find_draft_column(daily_draft_df)
        if draft_col:
            preview_df = filter_rows_with_draft(daily_draft_df, draft_col)
            for _, row in preview_df.iterrows():
                if str(row.get("record_id")) in reviewed_daily_ids:
                    continue
                rows.append(
                    {
                        "source_type": "daily_record",
                        "target_id": row.get("record_id"),
                        "user_key": row.get("user_id"),
                        "document_name": "サービス提供記録（特記事項）",
                        "category": "サービス提供",
                        "alert_type": "AI下書き未確認",
                        "alert_reason": "特記事項に対するAI補填下書きが職員未確認です。",
                        "shortage_detail": "AI補填下書きの職員確認・保存が必要です。",
                        "severity": "medium",
                        "ai_fillable": True,
                        "checklist_target": False,
                        "ai_reason": "",
                    }
                )

    monitoring_draft_df, _ = load_outputs_csv("monitoring_records_with_ai_draft.csv")
    monitoring_reviewed_df, _ = load_outputs_csv("monitoring_records_reviewed.csv")
    reviewed_monitoring_ids = (
        set(monitoring_reviewed_df["monitoring_id"].astype(str))
        if "monitoring_id" in monitoring_reviewed_df.columns
        else set()
    )

    if not monitoring_draft_df.empty:
        draft_col = find_draft_column(monitoring_draft_df)
        if draft_col:
            preview_df = filter_rows_with_draft(monitoring_draft_df, draft_col)
            for _, row in preview_df.iterrows():
                if str(row.get("monitoring_id")) in reviewed_monitoring_ids:
                    continue
                rows.append(
                    {
                        "source_type": "monitoring_record",
                        "target_id": row.get("monitoring_id"),
                        "user_key": row.get("user_id"),
                        "document_name": "モニタリング記録（月間下書き）",
                        "category": "サービス提供",
                        "alert_type": "AI下書き未確認",
                        "alert_reason": "月間モニタリングのAI下書きが職員未確認です。",
                        "shortage_detail": "AI下書きの職員確認・保存が必要です。",
                        "severity": "medium",
                        "ai_fillable": True,
                        "checklist_target": False,
                        "ai_reason": "",
                    }
                )

    return pd.DataFrame(rows)


def adapt_legacy_alerts(alerts_df: pd.DataFrame) -> pd.DataFrame:
    """notebook生成のalerts_integrated.csv（特記事項不足など）を統一スキーマに変換する。既存ファイル・ロジックは変更しない。"""
    if alerts_df.empty:
        return pd.DataFrame()

    rows = []
    for _, row in alerts_df.iterrows():
        target_type = row.get("target_type")

        if target_type == "daily_record":
            source_type = "daily_record"
            document_name = "サービス提供記録（特記事項）"
            category = "サービス提供"
            ai_fillable = True
            ai_reason = ""
        elif target_type == "monitoring":
            source_type = "monitoring_record"
            document_name = "モニタリング記録（月間下書き）"
            category = "サービス提供"
            ai_fillable = True
            ai_reason = ""
        else:
            source_type = "document"
            document_name = row.get("document_type") or "書類"
            catalog = DOCUMENT_CATALOG.get(document_name, {"category": "その他", "ai_fillable": False, "ai_reason": ""})
            category = catalog.get("category", "その他")
            ai_fillable = catalog.get("ai_fillable", False)
            ai_reason = catalog.get("ai_reason", "")

        rows.append(
            {
                "source_type": source_type,
                "target_id": row.get("target_id"),
                "user_key": row.get("user_id"),
                "document_name": document_name,
                "category": category,
                "alert_type": row.get("alert_type"),
                "alert_reason": row.get("detail"),
                "shortage_detail": row.get("detail"),
                "severity": row.get("severity", "medium"),
                "ai_fillable": ai_fillable,
                "checklist_target": False,
                "ai_reason": ai_reason,
            }
        )

    return pd.DataFrame(rows)


def compute_alert_status(row, reviewed_daily_ids, reviewed_monitoring_ids, confirmed_keys) -> str:
    """アラートの確認済み判定。日々/月間記録は該当reviewed CSVへの反映有無、それ以外はalert_keyの一致で判定する。"""
    if row["source_type"] == "daily_record" and str(row["target_id"]) in reviewed_daily_ids:
        return "確認済み"
    if row["source_type"] == "monitoring_record" and str(row["target_id"]) in reviewed_monitoring_ids:
        return "確認済み"
    if row["alert_key"] in confirmed_keys:
        return "確認済み"
    return "未対応"


def build_document_alert_list() -> pd.DataFrame:
    """書類アラート一覧・確認キュー・概要ダッシュボードで共通利用する統一アラート一覧を構築する。"""
    document_status_df = load_csv(DATA_DIR / "document_status.csv")
    care_plans_df = load_csv(DATA_DIR / "care_plans.csv")
    daily_df = load_csv(DATA_DIR / "daily_records.csv")
    legacy_alerts_df, _ = load_outputs_csv("alerts_integrated.csv")

    parts = [
        build_document_status_alerts(document_status_df) if not document_status_df.empty else pd.DataFrame(),
        build_ai_draft_alerts(),
        build_checklist_alerts(care_plans_df, daily_df) if not care_plans_df.empty and not daily_df.empty else pd.DataFrame(),
        adapt_legacy_alerts(legacy_alerts_df),
    ]
    parts = [p for p in parts if not p.empty]

    if not parts:
        return pd.DataFrame()

    combined = pd.concat(parts, ignore_index=True)

    combined["alert_key"] = combined.apply(
        lambda r: build_alert_key(r["source_type"], r["target_id"], r["user_key"], r["document_name"], r["alert_type"]),
        axis=1,
    )

    users_df = load_csv(DATA_DIR / "users.csv")
    resolved = combined["user_key"].apply(lambda uk: resolve_subject_label(uk, users_df))
    combined["subject_type"] = resolved.apply(lambda t: t[0])
    combined["subject_label"] = resolved.apply(lambda t: t[1])

    daily_reviewed_df, _ = load_outputs_csv("daily_records_note_reviewed.csv")
    monitoring_reviewed_df, _ = load_outputs_csv("monitoring_records_reviewed.csv")
    reviewed_daily_ids = (
        set(daily_reviewed_df["record_id"].astype(str)) if "record_id" in daily_reviewed_df.columns else set()
    )
    reviewed_monitoring_ids = (
        set(monitoring_reviewed_df["monitoring_id"].astype(str))
        if "monitoring_id" in monitoring_reviewed_df.columns
        else set()
    )
    confirmed_keys = get_confirmed_alert_keys()

    combined["status"] = combined.apply(
        lambda r: compute_alert_status(r, reviewed_daily_ids, reviewed_monitoring_ids, confirmed_keys), axis=1
    )
    combined["confirmed"] = combined["status"] == "確認済み"

    severity_order = {"high": 0, "medium": 1, "low": 2}
    combined["severity_rank"] = combined["severity"].map(severity_order).fillna(3)
    combined = combined.sort_values(["confirmed", "severity_rank", "category"]).reset_index(drop=True)
    combined = combined.drop(columns=["severity_rank"])

    return combined


def get_unresolved_alerts(alert_df: pd.DataFrame) -> pd.DataFrame:
    if alert_df.empty:
        return alert_df
    return alert_df[~alert_df["confirmed"]].reset_index(drop=True)


def find_alert_position(unresolved_df: pd.DataFrame, source_type: str, target_id) -> int:
    """未対応リストの中で、指定した書類の位置（0始まり）を返す。見つからなければNone。

    daily_record由来のアラートとchecklist由来のアラートは同じ書類（日々の記録）を指すため、
    どちらから遷移しても同じ書類として位置を照合する。
    """
    if unresolved_df.empty:
        return None

    if source_type in ("daily_record", "checklist"):
        mask = unresolved_df["source_type"].isin(["daily_record", "checklist"]) & (
            unresolved_df["target_id"].astype(str) == str(target_id)
        )
    else:
        mask = (unresolved_df["source_type"] == source_type) & (
            unresolved_df["target_id"].astype(str) == str(target_id)
        )

    positions = unresolved_df.index[mask].tolist()
    return positions[0] if positions else None


def request_navigation(page_name: str) -> None:
    """次回実行で表示するページを予約する。

    サイドバーのradioウィジェット（key="nav_page"）は、既にインスタンス化された後の
    同一実行内でsession_state["nav_page"]を直接書き換えることができないため、
    st.rerun()後の次の実行の先頭（radio生成前）で反映される一時キーを介して切り替える。
    """
    st.session_state["_pending_nav_page"] = page_name


def go_to_detail(source_type, target_id, user_key) -> None:
    """書類詳細・AI補填プレビュー画面へ遷移する。"""
    st.session_state.selected_source_type = source_type
    st.session_state.selected_target_id = target_id
    st.session_state.selected_user_key = user_key
    request_navigation("書類詳細・AI補填プレビュー")
    st.rerun()


def render_draft_confirm_and_save(
    selected_row: pd.Series, draft_col: str, reviewed_path: Path, default_status: str, key_prefix: str
) -> bool:
    """AI下書きの内容確認・修正・保存UI。行選択済みの状態で呼び出す（職員確認済み保存／確認キュー／書類詳細で共用）。"""
    st.subheader("AI補填後プレビュー（職員確認前の下書き）")
    st.caption("この文章は確定記録ではありません。必ず職員が内容を確認・修正したうえで保存してください。")
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
            st.success("確認済みとして保存しました。この書類は未対応アラート一覧から除外されます。")
            st.dataframe(save_row_df, use_container_width=True)
            return True
    return False


def render_draft_review_flow(source_path: Path, reviewed_path: Path, default_status: str, key_prefix: str) -> None:
    """AI下書きを職員が確認・修正・保存する一連のUIフロー（行選択＋保存）。職員確認済み保存ページから利用する。"""
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

    render_draft_confirm_and_save(selected_row, draft_col, reviewed_path, default_status, key_prefix)


def get_draft_context(source_type: str, target_id):
    """daily_record／monitoring_record向けのAI下書き行・関連パスを取得する。"""
    if source_type == "daily_record":
        source_path = OUTPUTS_DIR / "daily_records_with_ai_note_draft.csv"
        reviewed_path = OUTPUTS_DIR / "daily_records_note_reviewed.csv"
        default_status = "note_reviewed"
        id_col = "record_id"
    elif source_type == "monitoring_record":
        source_path = OUTPUTS_DIR / "monitoring_records_with_ai_draft.csv"
        reviewed_path = OUTPUTS_DIR / "monitoring_records_reviewed.csv"
        default_status = "reviewed"
        id_col = "monitoring_id"
    else:
        return None

    df, _ = load_outputs_csv(source_path.name)
    if df.empty or id_col not in df.columns:
        return None

    matched = df[df[id_col].astype(str) == str(target_id)]
    if matched.empty:
        return None

    draft_col = find_draft_column(df)
    if draft_col is None:
        return None

    return {
        "row": matched.iloc[0],
        "draft_col": draft_col,
        "reviewed_path": reviewed_path,
        "default_status": default_status,
    }


# =========================
# サイドバー
# =========================

if "nav_page" not in st.session_state:
    st.session_state.nav_page = MENU_ITEMS[0]

if "_pending_nav_page" in st.session_state:
    st.session_state.nav_page = st.session_state.pop("_pending_nav_page")

st.sidebar.title("Care Compliance Copilot")
st.sidebar.caption("訪問介護向けコンプライアンス確認支援MVP")
st.sidebar.caption(
    "上6画面が主要導線（書類アラート一覧→書類詳細・AI補填プレビュー→確認キュー→確認履歴・監査ログ）、"
    "下5画面は個別確認用の補助画面です。"
)

page = st.sidebar.radio("メニュー", MENU_ITEMS, key="nav_page")


# =========================
# 画面：使い方・業務フロー
# =========================

if page == "使い方・業務フロー":
    st.title("使い方・業務フロー")
    st.write(
        "訪問介護事業所の運営指導前チェックにおいて、"
        "書類不備・未確認・未承認の記録を検出し、"
        "必要に応じてAI下書き候補を提示するコンプライアンス確認支援MVPです。"
    )

    st.info(
        "AIやルールは記録・書類・レ点チェックを確定しません。"
        "下書き・候補・不一致検知を提示するのみで、"
        "職員が確認・修正したうえで保存する運用を前提としています。"
    )

    st.subheader("主要導線（書類中心の業務フロー）")
    st.markdown(
        """
        1. **概要ダッシュボード** で、アラート状況の全体像を確認する
        2. **書類アラート一覧** で、対応が必要な書類・記録を一覧確認する（分野・重要度で絞り込み可能）
        3. 「▶ 詳細を見る」から **書類詳細・AI補填プレビュー** に進み、書類全体図・AI補填後プレビュー・計画書連動レ点チェック・根拠を確認する
        4. 内容を確認・必要に応じて修正し、確認者名を入力してチェックを入れ、「確認済みにする」ボタンで保存する
        5. 保存後、「次の未対応書類へ進む」で連続して次の書類を処理する（**確認キュー**からも同じ詳細画面に入れる）
        6. **確認履歴・監査ログ** で、保存された確認結果を確認する
        """
    )

    st.subheader("補助画面（個別に直接確認したい場合）")
    st.markdown(
        """
        - アラート根拠確認：アラート単位で元データを直接確認したい場合
        - 計画書連動レ点候補：レ点候補だけを一覧で見たい場合
        - 特記事項AI補填デモ：日々の記録の特記事項AI下書きだけを見たい場合
        - 月間モニタリングAI下書き：月間モニタリングのAI下書きだけを見たい場合
        - 職員確認済み保存：AI下書きの確認・保存だけを単独で行いたい場合
        """
    )

    with st.expander("開発者向け：入力CSVを直接確認する"):
        selected_name = st.selectbox("表示するCSVを選択", list(DATA_FILES.keys()), key="usage_data_select")
        selected_path = DATA_FILES[selected_name]
        df = load_csv(selected_path)

        show_file_path("表示ファイル", selected_path)
        show_dataframe(df, selected_name)


# =========================
# 画面：概要ダッシュボード
# =========================

elif page == "概要ダッシュボード":
    st.title("概要ダッシュボード")
    st.write(
        "訪問介護事業所の運営指導前チェックにおいて、"
        "書類不備・未確認・未承認の記録を検出し、"
        "必要に応じてAI下書き候補・レ点候補を提示するコンプライアンス確認支援MVPです。"
    )

    st.info(
        "AIやルールは記録・書類・レ点チェックを確定しません。"
        "職員が確認・修正したうえで保存する運用を前提としています。"
    )

    alert_df = build_document_alert_list()
    unresolved_df = get_unresolved_alerts(alert_df)

    total_alerts = len(alert_df)
    unresolved_count = len(unresolved_df)
    high_severity_count = int((unresolved_df["severity"] == "high").sum()) if not unresolved_df.empty else 0
    affected_subjects = unresolved_df["user_key"].nunique() if not unresolved_df.empty else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("総アラート件数", total_alerts)
        st.caption("書類・記録・レ点チェックの全アラート")

    with col2:
        st.metric("未対応アラート", unresolved_count)
        st.caption("職員確認が必要な件数")

    with col3:
        st.metric("重大アラート（high・未対応）", high_severity_count)
        st.caption("優先的に確認が必要な件数")

    with col4:
        st.metric("対象利用者・職員・事業所数", affected_subjects)
        st.caption("未対応アラートの対象数")

    if not unresolved_df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("分野別の未対応件数")
            st.bar_chart(unresolved_df["category"].value_counts())
        with col_b:
            st.subheader("アラート種別ごとの未対応件数")
            st.bar_chart(unresolved_df["alert_type"].value_counts())

    st.subheader("本MVPで確認できること")
    st.markdown(
        """
        - 4分野15書類カタログに基づく、未作成・未承認・期限切れなどの書類ステータス確認
        - 書類アラート一覧から書類詳細・AI補填プレビューへの一気通貫の確認フロー
        - 日々の記録の特記事項・月間モニタリングのAI下書き候補の確認
        - ケアプランと日々の記録を突き合わせた計画書連動レ点チェック（候補・不一致検知、ルールベース）
        - 確認キューによる、複数種別の確認待ち項目の横断的な処理
        - 職員確認済みとして保存する流れと、その履歴・監査ログの確認
        """
    )


# =========================
# 画面：書類アラート一覧
# =========================

elif page == "書類アラート一覧":
    st.title("書類アラート一覧")
    st.caption("運営指導で確認される書類・記録のうち、対応が必要なアラートを一覧確認する主要導線の入口画面です。")

    alert_df = build_document_alert_list()

    if alert_df.empty:
        st.success("現在、検知されているアラートはありません。")
    else:
        show_confirmed = st.checkbox("確認済みも表示する", value=False, key="alert_list_show_confirmed")
        working_df = alert_df if show_confirmed else alert_df[~alert_df["confirmed"]]

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        with filter_col1:
            category_options = ["すべて"] + sorted(alert_df["category"].dropna().unique().tolist())
            selected_category = st.selectbox("分野で絞り込み", category_options, key="alert_list_category")
        with filter_col2:
            alert_type_options = ["すべて"] + sorted(alert_df["alert_type"].dropna().unique().tolist())
            selected_alert_type = st.selectbox("アラート種別で絞り込み", alert_type_options, key="alert_list_type")
        with filter_col3:
            severity_options = ["すべて"] + sorted(alert_df["severity"].dropna().unique().tolist())
            selected_severity = st.selectbox("重要度で絞り込み", severity_options, key="alert_list_severity")
        with filter_col4:
            subject_options = ["すべて"] + sorted(alert_df["subject_type"].dropna().unique().tolist())
            selected_subject = st.selectbox("対象区分で絞り込み", subject_options, key="alert_list_subject")

        filtered_df = working_df
        if selected_category != "すべて":
            filtered_df = filtered_df[filtered_df["category"] == selected_category]
        if selected_alert_type != "すべて":
            filtered_df = filtered_df[filtered_df["alert_type"] == selected_alert_type]
        if selected_severity != "すべて":
            filtered_df = filtered_df[filtered_df["severity"] == selected_severity]
        if selected_subject != "すべて":
            filtered_df = filtered_df[filtered_df["subject_type"] == selected_subject]

        filtered_df = filtered_df.reset_index(drop=True)

        st.caption(
            f"表示件数：{len(filtered_df)}件（全{len(alert_df)}件中、未対応{len(alert_df[~alert_df['confirmed']])}件）"
        )

        display_df = filtered_df.copy()
        display_df["ステータス表示"] = display_df["status"].apply(
            lambda s: "✅ 確認済み" if s == "確認済み" else "🔲 未対応"
        )
        display_columns = [
            "user_key",
            "subject_label",
            "document_name",
            "category",
            "alert_type",
            "alert_reason",
            "severity",
            "ai_fillable",
            "checklist_target",
            "ステータス表示",
        ]
        rename_map = {
            "user_key": "利用者ID/対象",
            "subject_label": "利用者名・対象区分",
            "document_name": "書類名",
            "category": "分野",
            "alert_type": "アラート理由",
            "alert_reason": "不足内容",
            "severity": "重要度",
            "ai_fillable": "AI補填対象",
            "checklist_target": "レ点チェック対象",
        }
        st.dataframe(display_df[display_columns].rename(columns=rename_map), use_container_width=True)

        if not filtered_df.empty:
            row_labels = {
                f"No.{i} / {row['document_name']} / {row['subject_label']} / {row['alert_type']}": i
                for i, row in filtered_df.iterrows()
            }
            selected_label = st.selectbox("詳細を見るアラートを選択", list(row_labels.keys()), key="alert_list_detail_select")
            selected_row = filtered_df.iloc[row_labels[selected_label]]

            if st.button("▶ 詳細を見る", type="primary", key="alert_list_detail_button"):
                go_to_detail(selected_row["source_type"], selected_row["target_id"], selected_row["user_key"])


# =========================
# 画面：書類詳細・AI補填プレビュー
# =========================

elif page == "書類詳細・AI補填プレビュー":
    st.title("書類詳細・AI補填プレビュー")
    st.caption("選択した書類について、内容確認・AI補填後プレビュー・計画書連動レ点チェック・根拠確認・職員確認保存を行う画面です。")

    sel_source_type = st.session_state.get("selected_source_type")
    sel_target_id = st.session_state.get("selected_target_id")
    sel_user_key = st.session_state.get("selected_user_key")

    alert_df = build_document_alert_list()

    if sel_source_type is None or sel_target_id is None:
        st.info("書類アラート一覧または確認キューから書類を選択してください。あるいは、以下から直接選択できます。")
        if alert_df.empty:
            st.success("現在、検知されているアラートはありません。")
            st.stop()

        unresolved_df = get_unresolved_alerts(alert_df)
        picker_df = unresolved_df if not unresolved_df.empty else alert_df
        row_labels = {
            f"No.{i} / {row['document_name']} / {row['subject_label']} / {row['alert_type']}": i
            for i, row in picker_df.reset_index(drop=True).iterrows()
        }
        selected_label = st.selectbox("確認する書類を選択", list(row_labels.keys()), key="detail_picker_select")
        if st.button("この書類を確認する", type="primary", key="detail_picker_button"):
            picked = picker_df.reset_index(drop=True).iloc[row_labels[selected_label]]
            go_to_detail(picked["source_type"], picked["target_id"], picked["user_key"])
        st.stop()

    if sel_source_type in ("daily_record", "checklist"):
        related_rows = alert_df[
            alert_df["source_type"].isin(["daily_record", "checklist"])
            & (alert_df["target_id"].astype(str) == str(sel_target_id))
        ]
    else:
        related_rows = alert_df[
            (alert_df["source_type"] == sel_source_type) & (alert_df["target_id"].astype(str) == str(sel_target_id))
        ]

    unresolved_df = get_unresolved_alerts(alert_df)
    current_pos = find_alert_position(unresolved_df, sel_source_type, sel_target_id)

    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 1])
    with nav_col1:
        prev_disabled = current_pos is None or current_pos <= 0
        if st.button("← 前の未対応書類", disabled=prev_disabled, key="detail_nav_prev"):
            prev_row = unresolved_df.iloc[current_pos - 1]
            go_to_detail(prev_row["source_type"], prev_row["target_id"], prev_row["user_key"])
    with nav_col2:
        if st.button("書類アラート一覧へ戻る", key="detail_nav_back"):
            request_navigation("書類アラート一覧")
            st.rerun()
    with nav_col3:
        next_disabled = current_pos is None or current_pos >= len(unresolved_df) - 1
        if st.button("次の未対応書類 →", disabled=next_disabled, key="detail_nav_next"):
            next_row = unresolved_df.iloc[current_pos + 1]
            go_to_detail(next_row["source_type"], next_row["target_id"], next_row["user_key"])
    with nav_col4:
        if current_pos is not None:
            st.caption(f"現在 {current_pos + 1} / {len(unresolved_df)} 件")
        else:
            st.caption("この書類は未対応一覧にありません（確認済みの可能性があります）")

    st.divider()

    if related_rows.empty:
        st.warning("選択された書類の情報が見つかりませんでした。書類アラート一覧から選び直してください。")
        st.stop()

    primary_row = related_rows.iloc[0]
    document_name = primary_row["document_name"]
    category = primary_row["category"]
    subject_label = primary_row["subject_label"]
    ai_fillable = bool(related_rows["ai_fillable"].any())
    checklist_target = bool(related_rows["checklist_target"].any())

    st.subheader(f"{document_name}　（{subject_label}）")
    header_col1, header_col2, header_col3 = st.columns(3)
    with header_col1:
        st.write(f"**分野**：{category}")
        st.write(f"**対象**：{subject_label}")
    with header_col2:
        st.write(f"**AI補填対象**：{'はい' if ai_fillable else 'いいえ'}")
        st.write(f"**レ点チェック対象**：{'はい' if checklist_target else 'いいえ'}")
    with header_col3:
        st.write(f"**現在のステータス**：{'✅ 確認済み' if primary_row['confirmed'] else '🔲 未対応'}")

    st.write("**アラート理由・必要な職員対応：**")
    for _, r in related_rows.iterrows():
        st.write(f"- 〔{r['alert_type']}〕{r['alert_reason']}")

    st.divider()

    saved_this_run = False

    # --- AI補填対象・中身データがある書類（日々の記録／月間モニタリング） ---
    if sel_source_type in ("daily_record", "checklist"):
        draft_key_prefix = "detail_daily"
        context = get_draft_context("daily_record", sel_target_id)

        daily_df = load_csv(DATA_DIR / "daily_records.csv")
        record_match = daily_df[daily_df["record_id"].astype(str) == str(sel_target_id)]
        record_row = record_match.iloc[0] if not record_match.empty else None

        if record_row is not None:
            st.subheader("書類全体図（記載状況）")
            field_status = [
                ("service_items", "サービス内容", "記載済み" if str(record_row.get("service_items", "")).strip() else "未記載", False),
                ("checklist_completed", "チェックリスト完了", "完了" if bool(record_row.get("checklist_completed")) else "未完了", False),
                ("special_notes", "特記事項", "記載済み" if str(record_row.get("special_notes", "")).strip() else "不足（AI補填対象）", True),
                ("user_quote", "利用者の発言", "記載済み" if str(record_row.get("user_quote", "")).strip() else "未記載", False),
                ("observation", "観察事項", "記載済み" if str(record_row.get("observation", "")).strip() else "未記載", False),
                ("approved", "承認状態", "承認済み" if bool(record_row.get("approved")) else "未承認", False),
            ]
            field_df = pd.DataFrame(
                [{"項目": label, "状態": status, "AI補填対象": "はい" if ai_flag else "いいえ"} for _, label, status, ai_flag in field_status]
            )
            st.dataframe(field_df, use_container_width=True)

        if context is not None:
            saved_this_run = render_draft_confirm_and_save(
                context["row"], context["draft_col"], context["reviewed_path"], context["default_status"], draft_key_prefix
            ) or saved_this_run
        else:
            st.info("この記録に対するAI補填下書きは現在ありません。")

        # --- 計画書連動レ点チェック ---
        st.divider()
        st.subheader("計画書連動レ点チェック")
        st.warning(
            "レ点はAIやルールが実施事実を確定するものではありません。"
            "訪問介護計画書に基づく「計画書との不一致候補」「要確認」として提示するだけであり、"
            "最終確認は必ず職員が行ってください。"
        )

        care_plans_df = load_csv(DATA_DIR / "care_plans.csv")
        care_plans_df = ensure_columns(care_plans_df, ["visit_days", "time_slot", "service_category"])

        if record_row is not None and not care_plans_df.empty:
            plan_match = care_plans_df[care_plans_df["user_id"] == record_row.get("user_id")]
            if not plan_match.empty:
                plan_row = plan_match.iloc[0]
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.write(f"**訪問介護計画書上の支援内容**：{plan_row.get('service_content')}")
                    st.write(f"**サービス区分（計画）**：{plan_row.get('service_category')}")
                    st.write(f"**時間帯（計画）**：{plan_row.get('time_slot')}")
                    st.write(f"**対象曜日（計画）**：{plan_row.get('visit_days')}")
                with info_col2:
                    st.write(f"**対象日の記録内容**：{record_row.get('service_items')}")
                    st.write(f"**サービス区分（記録）**：{record_row.get('service_category')}")
                    st.write(f"**時間帯（記録）**：{record_row.get('time_slot')}")
                    st.write(f"**記録日の曜日**：{get_japanese_weekday(record_row.get('record_date'))}")

                record_checklist_alerts = related_rows[related_rows["source_type"] == "checklist"]
                if record_checklist_alerts.empty:
                    st.success("この記録について、計画書との不一致候補は検知されていません。")
                else:
                    for _, ca in record_checklist_alerts.iterrows():
                        st.write(f"- 〔{ca['alert_type']}〕{ca['alert_reason']}")

                candidates_df = build_checklist_candidates(care_plans_df, daily_df)
                if not candidates_df.empty:
                    record_candidates = candidates_df[candidates_df["record_id"].astype(str) == str(sel_target_id)]
                    if not record_candidates.empty:
                        with st.expander("計画書に基づくレ点候補（判定根拠）"):
                            st.dataframe(
                                record_candidates[["plan_keyword", "service_items", "candidate_status"]],
                                use_container_width=True,
                            )

                unresolved_checklist = record_checklist_alerts[~record_checklist_alerts["confirmed"]]
                if not unresolved_checklist.empty:
                    st.write("**レ点チェックの職員確認：**")
                    checklist_reviewed_text = st.text_area(
                        "確認コメント（任意）", value="", key="detail_checklist_review_text"
                    )
                    checklist_reviewed_by = st.text_input("確認者名", value="サ責A", key="detail_checklist_review_by")
                    checklist_confirmed = st.checkbox(
                        "計画書との不一致候補・レ点候補を確認しました。", key="detail_checklist_review_confirm"
                    )
                    if st.button("レ点チェックを確認済みにする", type="primary", key="detail_checklist_review_save"):
                        if not checklist_confirmed:
                            st.error("保存するには、確認チェックを入れてください。")
                        elif not checklist_reviewed_by.strip():
                            st.error("確認者名を入力してください。")
                        else:
                            for _, ca in unresolved_checklist.iterrows():
                                save_queue_log(
                                    ca["alert_key"],
                                    "checklist",
                                    "checklist",
                                    ca["target_id"],
                                    ca["user_key"],
                                    ca["document_name"],
                                    ca["alert_reason"],
                                    checklist_reviewed_text,
                                    checklist_reviewed_by.strip(),
                                )
                            st.success("確認済みとして保存しました。この書類は未対応アラート一覧から除外されます。")
                            saved_this_run = True
            else:
                st.info("この利用者のケアプランが見つかりませんでした。")

        # --- 根拠 ---
        st.divider()
        with st.expander("根拠を確認する"):
            if record_row is not None:
                st.write(f"**記録日**：{record_row.get('record_date')}")
                st.write(f"**元の特記事項**：{record_row.get('special_notes')}")
                st.write(f"**利用者の発言**：{record_row.get('user_quote')}")
                st.write(f"**観察事項**：{record_row.get('observation')}")
                st.write(f"**数値情報**：{record_row.get('numeric_data')}")
                st.write(f"**今後の対応**：{record_row.get('follow_up')}")
            for _, r in related_rows.iterrows():
                st.write(f"- 〔{r['alert_type']}〕{r['alert_reason']}")

    # --- AI補填対象・中身データがある書類（月間モニタリング） ---
    elif sel_source_type == "monitoring_record":
        context = get_draft_context("monitoring_record", sel_target_id)
        monitoring_df = load_csv(DATA_DIR / "monitoring_records.csv")
        record_match = monitoring_df[monitoring_df["monitoring_id"].astype(str) == str(sel_target_id)]
        record_row = record_match.iloc[0] if not record_match.empty else None

        if record_row is not None:
            st.subheader("書類全体図（記載状況）")
            field_status = [
                ("evaluation", "総合評価", "記載済み" if str(record_row.get("evaluation", "")).strip() else "不足（AI補填対象）", True),
                ("status_change", "状態変化", "記載済み" if str(record_row.get("status_change", "")).strip() else "未記載", False),
                ("goal_evaluation", "ケアプラン目標評価", "記載済み" if str(record_row.get("goal_evaluation", "")).strip() else "未記載", False),
                ("future_action", "今後の対応", "記載済み" if str(record_row.get("future_action", "")).strip() else "未記載", False),
                ("approved", "承認状態", "承認済み" if bool(record_row.get("approved")) else "未承認", False),
            ]
            field_df = pd.DataFrame(
                [{"項目": label, "状態": status, "AI補填対象": "はい" if ai_flag else "いいえ"} for _, label, status, ai_flag in field_status]
            )
            st.dataframe(field_df, use_container_width=True)

            st.markdown("**【月間モニタリング下書き構成】**")
            st.write(f"- 対象期間：{record_row.get('record_date')}")
            st.write(f"- 参照記録期間：{record_row.get('interview_date')}（{record_row.get('interview_method')}）")
            st.write(f"- 総合評価：{record_row.get('evaluation')}")
            st.write(f"- ケアプラン目標に対する状況：{record_row.get('goal_evaluation')}")
            st.write(f"- 状態変化：{record_row.get('status_change')}")
            st.write(f"- 支援内容の継続・見直し：{record_row.get('future_action')}")
            st.write(f"- 職員確認が必要な事項：{record_row.get('next_action')}")
            st.write(f"- 根拠となる記録日：{record_row.get('interview_date')}")

        if context is not None:
            saved_this_run = render_draft_confirm_and_save(
                context["row"], context["draft_col"], context["reviewed_path"], context["default_status"], "detail_monitoring"
            )
        else:
            st.info("この記録に対するAI下書きは現在ありません。")

        st.divider()
        with st.expander("根拠を確認する"):
            if record_row is not None:
                st.write(f"**面談日**：{record_row.get('interview_date')}")
                st.write(f"**面談方法**：{record_row.get('interview_method')}")
                st.write(f"**同席者**：{record_row.get('attendees')}")
                st.write(f"**利用者発言**：{record_row.get('user_quotes')}")
                st.write(f"**客観的事実**：{record_row.get('objective_facts')}")
                st.write(f"**情報源**：{record_row.get('information_sources')}")
            for _, r in related_rows.iterrows():
                st.write(f"- 〔{r['alert_type']}〕{r['alert_reason']}")

    # --- 書類ステータス系（AI補填対象外、または中身データを持たない書類） ---
    else:
        ai_reason = primary_row.get("ai_reason", "")
        if ai_fillable:
            st.info(
                "この書類はAI補填対象カタログに含まれますが、本MVPでは中身データを保持していないため、"
                "ステータス確認のみ可能です。AI下書きは生成しません。"
            )
        else:
            st.info("この書類はAI補填対象外です。")
            if ai_reason:
                st.write(f"**AIで補填できない理由**：{ai_reason}")

        st.write(f"**必要な職員対応**：{primary_row['shortage_detail']}")

        document_status_df = load_csv(DATA_DIR / "document_status.csv")
        doc_match = document_status_df[document_status_df["document_id"].astype(str) == str(sel_target_id)]
        with st.expander("根拠を確認する"):
            if not doc_match.empty:
                st.dataframe(doc_match, use_container_width=True)
            for _, r in related_rows.iterrows():
                st.write(f"- 〔{r['alert_type']}〕{r['alert_reason']}")

        unresolved_related = related_rows[~related_rows["confirmed"]]
        if not unresolved_related.empty:
            st.subheader("職員確認・保存")
            doc_reviewed_text = st.text_area("確認コメント（任意）", value="", key="detail_document_review_text")
            doc_reviewed_by = st.text_input("確認者名", value="管理者A", key="detail_document_review_by")
            doc_confirmed = st.checkbox("内容を確認しました。", key="detail_document_review_confirm")

            if st.button("確認済みにする", type="primary", key="detail_document_review_save"):
                if not doc_confirmed:
                    st.error("保存するには、確認チェックを入れてください。")
                elif not doc_reviewed_by.strip():
                    st.error("確認者名を入力してください。")
                else:
                    for _, r in unresolved_related.iterrows():
                        save_queue_log(
                            r["alert_key"],
                            "document",
                            r["source_type"],
                            r["target_id"],
                            r["user_key"],
                            r["document_name"],
                            r["alert_reason"],
                            doc_reviewed_text,
                            doc_reviewed_by.strip(),
                        )
                    st.success("確認済みとして保存しました。この書類は未対応アラート一覧から除外されます。")
                    saved_this_run = True
        else:
            st.success("この書類は確認済みです。")

    if saved_this_run:
        st.divider()
        after_col1, after_col2 = st.columns(2)
        with after_col1:
            if st.button("次の未対応書類へ進む", type="primary", key="detail_after_save_next"):
                fresh_alert_df = build_document_alert_list()
                fresh_unresolved = get_unresolved_alerts(fresh_alert_df)
                if not fresh_unresolved.empty:
                    nxt = fresh_unresolved.iloc[0]
                    go_to_detail(nxt["source_type"], nxt["target_id"], nxt["user_key"])
                else:
                    request_navigation("確認履歴・監査ログ")
                    st.rerun()
        with after_col2:
            if st.button("書類アラート一覧へ戻る", key="detail_after_save_back"):
                request_navigation("書類アラート一覧")
                st.rerun()


# =========================
# 画面：確認キュー
# =========================

elif page == "確認キュー":
    st.title("確認キュー")
    st.caption("未確認のAI下書き・未承認の記録や書類・確認が必要なレ点チェックを、確認待ちの入口としてまとめて確認する画面です。")
    st.info("各行の「詳細へ」から、書類詳細・AI補填プレビュー画面に移動して確認・修正・保存を行います。")

    alert_df = build_document_alert_list()
    unresolved_df = get_unresolved_alerts(alert_df)

    if unresolved_df.empty:
        st.success("現在、確認待ちの項目はありません。")
    else:
        severity_label = {"high": "高", "medium": "中", "low": "低"}
        display_df = unresolved_df.copy()
        display_df["優先度"] = display_df["severity"].map(severity_label).fillna("中")

        display_columns = [
            "source_type",
            "user_key",
            "document_name",
            "target_id",
            "alert_reason",
            "優先度",
            "status",
            "ai_fillable",
            "checklist_target",
        ]
        rename_map = {
            "source_type": "種別",
            "user_key": "利用者ID",
            "document_name": "書類名",
            "target_id": "対象ID",
            "alert_reason": "確認内容",
            "status": "ステータス",
            "ai_fillable": "AI補填対象",
            "checklist_target": "レ点チェック対象",
        }
        st.dataframe(display_df[display_columns].rename(columns=rename_map), use_container_width=True)

        row_labels = {
            f"No.{i} / {row['document_name']} / {row['subject_label']} / {row['alert_type']}": i
            for i, row in unresolved_df.reset_index(drop=True).iterrows()
        }
        selected_label = st.selectbox("詳細を確認する項目を選択", list(row_labels.keys()), key="queue_detail_select")
        selected_row = unresolved_df.reset_index(drop=True).iloc[row_labels[selected_label]]

        if st.button("詳細へ", type="primary", key="queue_detail_button"):
            go_to_detail(selected_row["source_type"], selected_row["target_id"], selected_row["user_key"])


# =========================
# 画面：確認履歴・監査ログ
# =========================

elif page == "確認履歴・監査ログ":
    st.title("確認履歴・監査ログ")
    st.caption("職員が確認・保存した記録の履歴を確認する画面です。")

    daily_reviewed_df, daily_reviewed_path = load_outputs_csv("daily_records_note_reviewed.csv")
    monitoring_reviewed_df, monitoring_reviewed_path = load_outputs_csv("monitoring_records_reviewed.csv")
    queue_log_df, _ = load_outputs_csv(QUEUE_LOG_PATH.name)

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
                "confirmed_via": "特記事項AI補填デモ / 書類詳細・AI補填プレビュー / 職員確認済み保存",
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
                "confirmed_via": "月間モニタリングAI下書き / 書類詳細・AI補填プレビュー / 職員確認済み保存",
            }
        )

    for _, row in queue_log_df.iterrows():
        history_rows.append(
            {
                "record_type": row.get("record_type"),
                "target_id": row.get("target_id"),
                "user_id": row.get("user_id"),
                "review_status": row.get("review_status"),
                "reviewed_text": row.get("reviewed_text") or row.get("detail"),
                "reviewed_by": row.get("reviewed_by"),
                "reviewed_at": row.get("reviewed_at"),
                "confirmed_via": "確認キュー / 書類詳細・AI補填プレビュー",
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


# =========================
# 補助画面：アラート根拠確認
# =========================

elif page == "アラート根拠確認":
    st.title("アラート根拠確認（補助画面）")
    st.caption("アラートの元になった記録・書類を、アラート単位で直接確認する画面です。")

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
# 補助画面：計画書連動レ点候補
# =========================

elif page == "計画書連動レ点候補":
    st.title("計画書連動レ点候補（補助画面）")
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
# 補助画面：特記事項AI補填デモ
# =========================

elif page == "特記事項AI補填デモ":
    st.title("特記事項AI補填デモ（補助画面）")
    st.caption("日々の介護記録の特記事項に対するAI下書き候補だけを確認する画面です。ここで表示される文章は確定記録ではありません。")

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
            st.caption(f"AI下書き列：{draft_col}（対象ID：record_id）")
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
# 補助画面：月間モニタリングAI下書き
# =========================

elif page == "月間モニタリングAI下書き":
    st.title("月間モニタリングAI下書き（補助画面）")
    st.caption("月間モニタリング文書のAI下書き候補だけを確認する画面です。ここで表示される文章は確定記録ではありません。")

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
            st.caption(f"AI下書き列：{draft_col}（対象ID：monitoring_id）")
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
# 補助画面：職員確認済み保存
# =========================

elif page == "職員確認済み保存":
    st.title("職員確認済み保存（補助画面）")
    st.caption("AI下書き候補を職員が確認・修正し、確認済みデータとしてCSVに保存する単独画面です。")

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
        key_prefix = "page9_daily"
    else:
        source_path = OUTPUTS_DIR / "monitoring_records_with_ai_draft.csv"
        reviewed_path = OUTPUTS_DIR / "monitoring_records_reviewed.csv"
        default_status = "reviewed"
        key_prefix = "page9_monitoring"

    st.info(
        "MVP検証用のため、同じ記録を複数回保存できる仕様です。"
        "実運用では、同一record_id / monitoring_idの重複チェックまたは上書き保存が必要です。"
    )

    render_draft_review_flow(source_path, reviewed_path, default_status, key_prefix=key_prefix)
