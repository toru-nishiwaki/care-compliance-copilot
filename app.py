from pathlib import Path
from datetime import datetime

import re

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# =========================
# 基本設定
# =========================

st.set_page_config(
    page_title="Care Compliance Copilot",
    page_icon="✅",
    layout="wide",
)

# 見た目のみを整えるCSS（配色は.streamlit/config.tomlのテーマ設定と合わせた落ち着いた業務アプリ風）。
# ロジック・ウィジェットのkeyには一切影響しない表示専用のスタイル調整。
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    h1, h2, h3 {
        color: #1f2d3d;
    }

    h1 {
        border-bottom: 2px solid #eef2f8;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid #dde3ea;
    }

    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #dde3ea;
        border-radius: 10px;
        padding: 0.9rem 1rem 0.7rem 1rem;
    }

    [data-testid="stMetricLabel"] {
        color: #5a6472;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
    }

    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #2b4c7e;
        border-color: #2b4c7e;
    }

    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #1f3b63;
        border-color: #1f3b63;
    }

    .demo-card-badge {
        display: inline-block;
        background-color: #2b4c7e;
        color: #ffffff;
        font-size: 0.72em;
        font-weight: 700;
        letter-spacing: 0.06em;
        padding: 2px 9px;
        border-radius: 4px;
        margin-bottom: 0.6rem;
    }

    .demo-card-title {
        font-size: 1.08em;
        font-weight: 700;
        color: #1f2d3d;
        margin: 0.1rem 0 0.5rem 0;
    }

    .demo-card-meta {
        font-size: 0.92em;
        color: #3d4a59;
        margin-bottom: 0.2rem;
    }

    .demo-feature-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin: 0.5rem 0 0.7rem 0;
    }

    .demo-feature-chip {
        display: inline-block;
        background-color: #eef2f8;
        color: #2b4c7e;
        font-size: 0.78em;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        border: 1px solid #dbe4f0;
    }

    .hero-card {
        background-color: #f4f6f9;
        border: 1px solid #dde3ea;
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.4rem;
    }

    .hero-eyebrow {
        display: inline-block;
        font-size: 0.75em;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #2b4c7e;
        background-color: #e3e9f3;
        padding: 2px 10px;
        border-radius: 4px;
        margin-bottom: 0.6rem;
    }

    .hero-title {
        font-size: 1.6em;
        font-weight: 700;
        color: #1f2d3d;
        margin-bottom: 0.3rem;
    }

    .hero-subtitle {
        font-size: 1em;
        color: #3d4a59;
        margin-bottom: 0.9rem;
    }

    .hero-point-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
    }

    .hero-point {
        display: inline-block;
        background-color: #ffffff;
        border: 1px solid #dde3ea;
        color: #1f2d3d;
        font-size: 0.85em;
        font-weight: 600;
        padding: 5px 12px;
        border-radius: 8px;
    }

    .kpi-flag {
        display: inline-block;
        font-size: 0.72em;
        font-weight: 700;
        letter-spacing: 0.02em;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 0.4rem;
    }

    .kpi-flag-info { background-color: #eef2f8; color: #2b4c7e; }
    .kpi-flag-warn { background-color: #fff8e1; color: #8a6d00; }
    .kpi-flag-risk { background-color: #fdecea; color: #c0392b; }
    .kpi-flag-ok { background-color: #e6f4ea; color: #1e7e34; }

    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #dde3ea;
        border-radius: 10px;
        padding: 0.9rem 1rem 0.85rem 1rem;
        min-height: 176px;
        display: flex;
        flex-direction: column;
    }

    .kpi-card-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #1f2d3d;
        line-height: 1.15;
        margin: 0.15rem 0 0.1rem 0;
    }

    .kpi-card-label {
        font-size: 0.85em;
        font-weight: 600;
        color: #3d4a59;
        margin-bottom: 0.35rem;
    }

    .kpi-card-caption {
        font-size: 0.78em;
        color: #5a6472;
        line-height: 1.4;
        margin-top: auto;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.9rem;
        font-weight: 700;
    }

    [data-testid="stMetric"] [data-testid="stCaptionContainer"] {
        font-size: 0.8em;
    }

    hr {
        margin: 1.1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
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

DOCUMENT_DETAIL_SAMPLES_PATH = DATA_DIR / "document_detail_samples.csv"

# service_items（自由記述のキーワード列）を、サービス提供記録の紙面上の項目名・分類に
# 部分一致で対応付けるための表。実施事実をAIやルールが確定するものではなく、
# あくまで紙面表示・不一致候補検知のためのルールベースの対応付けである。
KEYWORD_TO_FIELD = [
    ("排泄", "排泄", "身体介護"),
    ("食事", "食事", "身体介護"),
    ("水分", "食事", "身体介護"),
    ("入浴", "入浴・清拭", "身体介護"),
    ("清拭", "入浴・清拭", "身体介護"),
    ("整容", "身体整容", "身体介護"),
    ("更衣", "身体整容", "身体介護"),
    ("歩行", "移動", "身体介護"),
    ("移動", "移動", "身体介護"),
    ("起床", "起床・就寝", "身体介護"),
    ("就寝", "起床・就寝", "身体介護"),
    ("服薬", "服薬・医療", "身体介護"),
    ("自立", "自立支援", "身体介護"),
    ("見守り", "声掛け・見守り", "身体介護"),
    ("声かけ", "声掛け・見守り", "身体介護"),
    ("声掛け", "声掛け・見守り", "身体介護"),
    ("掃除", "清掃", "生活援助"),
    ("清掃", "清掃", "生活援助"),
    ("洗濯", "洗濯", "生活援助"),
    ("調理", "調理", "生活援助"),
    ("買い物", "買物等", "生活援助"),
    ("買物", "買物等", "生活援助"),
]

STATUS_BADGE_STYLES = {
    "記載済み": "background:#e6f4ea;color:#1e7e34;",
    "職員確認済み": "background:#e6f4ea;color:#1e7e34;",
    "✅ 確認済み": "background:#e6f4ea;color:#1e7e34;",
    "不足": "background:#fdecea;color:#c0392b;",
    "未記載": "background:#fdecea;color:#c0392b;",
    "未対応": "background:#fdecea;color:#c0392b;",
    "🔲 未対応": "background:#fdecea;color:#c0392b;",
    "要確認": "background:#fff8e1;color:#8a6d00;",
    "AI補填対象": "background:#e8f0fe;color:#1a56cc;",
    "AI補填対象外": "background:#f1f1f1;color:#555555;",
    "AI候補": "background:#e8f0fe;color:#1a56cc;",
    "AI補填": "background:#e8f0fe;color:#1a56cc;",
    "下書き": "background:#e8f0fe;color:#1a56cc;",
    "職員確認が必要": "background:#fff8e1;color:#8a6d00;",
    "高リスク": "background:#fdecea;color:#c0392b;",
    "高リスク未対応": "background:#fdecea;color:#c0392b;",
    "AI下書きあり": "background:#e8f0fe;color:#1a56cc;",
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

# 4分野15書類・記録のカタログ。AIは記録・書類を確定しないため、ここでの「AI補填対象」は
# 「文章下書きの提示が可能」を意味するだけで、確定・承認はすべて職員が行う。
# 4分野：サービス提供・記録関連／利用者・契約関連／人員・勤務体制関連／運営・その他関連
DOCUMENT_CATALOG = {
    "訪問介護計画書": {
        "category": "サービス提供・記録関連",
        "ai_fillable": False,
        "ai_reason": "計画内容は職員間協議のうえ作成されるべきものであり、AIが補填・確定してはいけません。職員が内容を確認してください。",
    },
    "サービス提供記録": {
        "category": "サービス提供・記録関連",
        "ai_fillable": True,
        "ai_reason": "",
    },
    "モニタリング記録": {
        "category": "サービス提供・記録関連",
        "ai_fillable": True,
        "ai_reason": "",
    },
    "担当者会議記録": {
        "category": "サービス提供・記録関連",
        "ai_fillable": True,
        "ai_reason": "",
    },
    "苦情処理記録": {
        "category": "サービス提供・記録関連",
        "ai_fillable": True,
        "ai_reason": "",
    },
    "重要事項説明書": {
        "category": "利用者・契約関連",
        "ai_fillable": False,
        "ai_reason": "説明・同意の事実確認が必要なため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "利用契約書": {
        "category": "利用者・契約関連",
        "ai_fillable": False,
        "ai_reason": "契約締結・署名の事実確認が必要なため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "個人情報同意書": {
        "category": "利用者・契約関連",
        "ai_fillable": False,
        "ai_reason": "同意取得の事実確認が必要なため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "居宅サービス計画書": {
        "category": "利用者・契約関連",
        "ai_fillable": False,
        "ai_reason": "ケアマネジャーが作成する計画書であり、AIが内容を補填・確定してはいけません。職員が原本を確認してください。",
    },
    "勤務形態一覧表": {
        "category": "人員・勤務体制関連",
        "ai_fillable": False,
        "ai_reason": "勤務体制は事実確認が必要な情報のため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "出勤簿": {
        "category": "人員・勤務体制関連",
        "ai_fillable": False,
        "ai_reason": "出勤実績は事実確認が必要な情報のため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "資格証": {
        "category": "人員・勤務体制関連",
        "ai_fillable": False,
        "ai_reason": "資格・有効期限は事実確認が必要な情報のため、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "研修記録": {
        "category": "人員・勤務体制関連",
        "ai_fillable": True,
        "ai_reason": "",
    },
    "感染症対策マニュアル": {
        "category": "運営・その他関連",
        "ai_fillable": False,
        "ai_reason": "マニュアル内容は事業所として正式承認された内容である必要があり、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
    "緊急時対応マニュアル": {
        "category": "運営・その他関連",
        "ai_fillable": False,
        "ai_reason": "マニュアル内容は事業所として正式承認された内容である必要があり、AIが補填・確定してはいけません。職員が原本を確認してください。",
    },
}

# 書類詳細画面でAI補填後プレビュー（書類全体図つき）まで再現できる書類種別。
# それ以外はカタログ上「AI補填対象」であってもステータス確認のみとする
# （本MVPでは中身データを保持していないため）。
CONTENT_BACKED_SOURCE_TYPES = {"daily_record", "monitoring_record", "checklist"}

# 「期限切れ」は期限・更新日の概念がある書類にのみ適用する。
# モニタリング記録など月次で内容が更新される書類には適用しない（専用の状態判定を別途行う）。
EXPIRY_APPLICABLE_DOCUMENT_TYPES = {
    "訪問介護計画書",
    "居宅サービス計画書",
    "資格証",
    "利用契約書",
    "感染症対策マニュアル",
    "緊急時対応マニュアル",
}

DEMO_RECORD_ID = "R011"
DEMO_RECORD_USER = "U004"
# 確認済みR011の最新状態（レ点チェック・文章・修正回数）を保持するsession_stateキー。
# 監査ログ（CSV）は履歴として追記のみ・編集不可のままとし、こちらは「全体図」に
# 最新の確認・修正内容を即時反映するための表示専用キャッシュとして使う。
DEMO_CONFIRMED_RECORD_KEY = "demo_confirmed_record"

JAPANESE_WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

CONTRADICTION_RULES = [
    ("食事", ["摂取できなかった", "実施できず", "中止した", "できなかった", "困難であった"]),
    ("水分", ["摂取できなかった", "実施できず", "中止した", "できなかった", "困難であった"]),
    ("入浴", ["実施できず", "中止した", "できなかった"]),
]

PRIMARY_MENU_ITEMS = [
    "使い方・業務フロー",
    "概要ダッシュボード",
    "書類アラート一覧",
    "書類詳細・AI補填プレビュー",
    "確認キュー",
    "確認履歴・監査ログ",
]

AUXILIARY_MENU_ITEMS = [
    "アラート根拠確認",
    "計画書連動レ点候補",
    "特記事項AI補填デモ",
    "月間モニタリングAI下書き",
    "職員確認済み保存",
]

MENU_ITEMS = PRIMARY_MENU_ITEMS + AUXILIARY_MENU_ITEMS


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


def status_badge_html(label: str) -> str:
    """状態ラベルを色分けバッジのHTMLにする（表示専用。ウィジェットは含まない）。"""
    style = STATUS_BADGE_STYLES.get(label, "background:#f1f1f1;color:#333333;")
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:10px;'
        f'font-size:0.85em;font-weight:600;{style}">{label}</span>'
    )


def render_page_top_anchor() -> None:
    """ページ最上部の目印となる、表示上は見えないアンカー要素を配置する。"""
    st.markdown('<div id="page-top-anchor"></div>', unsafe_allow_html=True)


def scroll_to_top() -> None:
    """画面を最上部までスクロールする（表示専用）。

    ページ遷移・状態遷移の直後に1回だけ呼び出す想定。呼び出し側は
    st.session_state["scroll_to_top"]フラグをpopしてから呼ぶことで、
    通常操作の再描画では発火しないようにする。Streamlitの再描画が
    このスクリプト実行より後にずれ込む場合があるため、複数タイミングで
    再試行する。
    """
    components.html(
        """
        <script>
        function scrollParentToTop() {
            const doc = window.parent.document;

            const anchor = doc.getElementById("page-top-anchor");
            if (anchor) {
                anchor.scrollIntoView({ behavior: "auto", block: "start" });
            }

            const selectors = [
                "section.main",
                "[data-testid='stAppViewContainer']",
                "[data-testid='stMain']",
                ".main",
            ];

            selectors.forEach((selector) => {
                const el = doc.querySelector(selector);
                if (el) {
                    el.scrollTop = 0;
                }
            });

            window.parent.scrollTo(0, 0);
        }

        scrollParentToTop();
        setTimeout(scrollParentToTop, 50);
        setTimeout(scrollParentToTop, 150);
        setTimeout(scrollParentToTop, 350);
        </script>
        """,
        height=0,
    )


def render_kpi_card(flag_label: str, flag_class: str, value, label: str, caption: str) -> None:
    """概要ダッシュボード上部のKPIカードを、高さ・上端位置を揃えた1枚のHTMLカードとして表示する。

    st.metric単体では、カード外に置いたバッジの有無でカードごとに高さがずれるため、
    バッジ・数値・ラベル・説明文をすべて1つのHTMLブロックに収めて表示専用で統一する。
    """
    st.markdown(
        f'<div class="kpi-card">'
        f'<span class="kpi-flag {flag_class}">{flag_label}</span>'
        f'<div class="kpi-card-value">{value}</div>'
        f'<div class="kpi-card-label">{label}</div>'
        f'<div class="kpi-card-caption">{caption}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_paper_header(title: str, meta: dict) -> None:
    """書類詳細の紙面風ヘッダー（タイトル中央寄せ＋メタ情報）を表示する。ウィジェットはネストしない。"""
    meta_html = "".join(f"<div>{k}：{v}</div>" for k, v in meta.items())
    st.markdown(
        f"""
        <div style="border-bottom:1px solid #e0e0e0;padding-bottom:0.75rem;margin-bottom:1rem;">
            <h3 style="text-align:center;margin-bottom:0.5rem;">{title}</h3>
            <div style="text-align:right;color:#555555;font-size:0.9em;line-height:1.6;">{meta_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_document_detail_samples() -> pd.DataFrame:
    """document_detail_samples.csv（紙面風モックアップ用のMVPデモデータ）を読み込む。"""
    return load_csv(DOCUMENT_DETAIL_SAMPLES_PATH)


def get_field_taxonomy() -> dict:
    """document_detail_samples.csvのサービス提供記録テンプレート行から、section→[field_name...]の構成を作る。"""
    samples_df = get_document_detail_samples()
    taxonomy = {"共通・状態確認": [], "身体介護": [], "生活援助": []}
    if samples_df.empty:
        return taxonomy

    template_df = samples_df[samples_df["document_type"] == "サービス提供記録"]
    for section in taxonomy:
        taxonomy[section] = template_df[template_df["section"] == section]["field_name"].tolist()
    return taxonomy


def classify_service_items(service_items_text: str) -> list:
    """service_itemsの自由記述テキストを、KEYWORD_TO_FIELDでfield_name・care_categoryに分類する。

    ルールベースの部分一致判定であり、AIによる判定は行わない。
    """
    matches = []
    matched_fields = set()
    for keyword, field_name, care_category in KEYWORD_TO_FIELD:
        if keyword in service_items_text and field_name not in matched_fields:
            matches.append({"field_name": field_name, "care_category": care_category, "keyword": keyword})
            matched_fields.add(field_name)
    return matches


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
        "category": "サービス提供・記録関連",
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
                            "high",
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
                            "high",
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

            # 4. サービス区分とレ点項目カテゴリの不一致候補：
            # care_plans.service_categoryと、記録側レ点項目の分類（KEYWORD_TO_FIELD由来）を突き合わせる。
            # 「誤り」ではなく、あくまで職員確認が必要な候補として提示する。
            if plan_category in ("身体介護", "生活援助"):
                classified_items = classify_service_items(service_items_text)
                mismatched_fields = [
                    m for m in classified_items if m["care_category"] != plan_category
                ]
                if mismatched_fields:
                    field_list = "、".join(f"{m['field_name']}（{m['care_category']}）" for m in mismatched_fields)
                    rows.append(
                        _checklist_row(
                            plan,
                            record,
                            "サービス区分とレ点項目カテゴリの不一致候補",
                            "medium",
                            f"計画書のサービス区分は「{plan_category}」ですが、記録側のレ点に{field_list}が含まれています。"
                            "サービス区分とレ点項目カテゴリの不一致候補として職員確認が必要です。",
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


def get_monitoring_unconfirmed_draft_users() -> set:
    """モニタリングAI下書きがあり、まだ職員確認済み（reviewed）に反映されていない利用者IDの集合を返す。"""
    draft_df, _ = load_outputs_csv("monitoring_records_with_ai_draft.csv")
    reviewed_df, _ = load_outputs_csv("monitoring_records_reviewed.csv")

    if draft_df.empty:
        return set()

    draft_col = find_draft_column(draft_df)
    if draft_col is None:
        return set()

    drafted_users = set(filter_rows_with_draft(draft_df, draft_col)["user_id"].astype(str))
    reviewed_ids = set(reviewed_df["monitoring_id"].astype(str)) if "monitoring_id" in reviewed_df.columns else set()

    if reviewed_ids and "user_id" in draft_df.columns and "monitoring_id" in draft_df.columns:
        reviewed_users = set(
            draft_df[draft_df["monitoring_id"].astype(str).isin(reviewed_ids)]["user_id"].astype(str)
        )
        drafted_users -= reviewed_users

    return drafted_users


def build_document_status_alerts(document_status_df: pd.DataFrame) -> pd.DataFrame:
    """document_status.csvから、書類ステータス系のアラートをルールベースで検知する。"""
    rows = []
    monitoring_unconfirmed_users = get_monitoring_unconfirmed_draft_users()

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

        if doc_type == "モニタリング記録":
            # モニタリング記録は「有効期限切れ」を使わず、下書き未確認／未提出／未承認の優先順位で判定する。
            if str(doc.get("user_id")) in monitoring_unconfirmed_users:
                alert_specs.append(("下書きあり・未確認", "high", "月間モニタリングのAI下書きが職員未確認です。職員確認が必要です。"))
            elif not file_exists:
                alert_specs.append(("未提出・未作成", "high", "月間モニタリング記録が未提出です。職員確認が必要です。"))
            elif not approved:
                alert_specs.append(("作成済み・未承認", "high", "記録は作成済みですが、承認が完了していません。職員確認が必要です。"))
        else:
            if required and not file_exists:
                alert_specs.append(("未作成", "high", "必須書類が作成されていません。職員確認が必要です。"))

            if file_exists and not approved:
                alert_specs.append(("未承認", "high", "書類は存在しますが、承認が完了していません。職員確認が必要です。"))

            if file_exists and doc_type in EXPIRY_APPLICABLE_DOCUMENT_TYPES:
                valid_to_ts = pd.to_datetime(valid_to, errors="coerce")
                if pd.notna(valid_to_ts) and valid_to_ts < TODAY:
                    alert_specs.append(("期限切れ", "high", f"有効期限（{valid_to}）が過ぎています。職員確認が必要です。"))

        if file_exists and approved and (pd.isna(approved_by) or not str(approved_by).strip()):
            alert_specs.append(("署名なし", "high", "承認済みですが、承認者が記録されていません。職員確認が必要です。"))

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
                        "category": "サービス提供・記録関連",
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
                        "category": "サービス提供・記録関連",
                        "alert_type": "AI下書き未確認",
                        "alert_reason": "月間モニタリングのAI下書きが職員未確認です。",
                        "shortage_detail": "AI下書きの職員確認・保存が必要です。",
                        "severity": "high",
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
            category = "サービス提供・記録関連"
            ai_fillable = True
            ai_reason = ""
        elif target_type == "monitoring":
            source_type = "monitoring_record"
            document_name = "モニタリング記録（月間下書き）"
            category = "サービス提供・記録関連"
            ai_fillable = True
            ai_reason = ""
        else:
            source_type = "document"
            document_name = row.get("document_type") or "書類"
            catalog = DOCUMENT_CATALOG.get(document_name, {"category": "その他", "ai_fillable": False, "ai_reason": ""})
            category = catalog.get("category", "その他")
            ai_fillable = catalog.get("ai_fillable", False)
            ai_reason = catalog.get("ai_reason", "")

        alert_type = row.get("alert_type")
        # 「サービス提供記録の特記事項不足」は重大アラートの定義に含めているため、
        # 元データ（notebook生成）のseverity値に関わらずhighとして扱う。
        severity = "high" if alert_type == "特記事項不足" else row.get("severity", "medium")

        rows.append(
            {
                "source_type": source_type,
                "target_id": row.get("target_id"),
                "user_key": row.get("user_id"),
                "document_name": document_name,
                "category": category,
                "alert_type": alert_type,
                "alert_reason": row.get("detail"),
                "shortage_detail": row.get("detail"),
                "severity": severity,
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

    combined["is_demo"] = combined["source_type"].isin(["daily_record", "checklist"]) & (
        combined["target_id"].astype(str) == DEMO_RECORD_ID
    )

    # 書類・記録単位での集計用キー。daily_record（AI下書き）とchecklist（レ点候補）は
    # 同じ提供記録に対する複数アラートのため、同じ書類・記録として1件に数える。
    combined["document_unit_source"] = combined["source_type"].replace({"checklist": "daily_record"})
    combined["document_unit_key"] = (
        combined["user_key"].astype(str)
        + "|"
        + combined["document_unit_source"].astype(str)
        + "|"
        + combined["target_id"].astype(str)
    )
    combined = combined.drop(columns=["document_unit_source"])

    severity_order = {"high": 0, "medium": 1, "low": 2}
    combined["severity_rank"] = combined["severity"].map(severity_order).fillna(3)
    # デモ行（未対応のもの）は常に最上部に表示する。保存後（確認済み）は通常の並び順に戻す。
    combined["demo_rank"] = ~(combined["is_demo"] & ~combined["confirmed"])
    combined = combined.sort_values(["demo_rank", "confirmed", "severity_rank", "category"]).reset_index(drop=True)
    combined = combined.drop(columns=["severity_rank", "demo_rank"])

    return combined


def get_unresolved_alerts(alert_df: pd.DataFrame) -> pd.DataFrame:
    if alert_df.empty:
        return alert_df
    return alert_df[~alert_df["confirmed"]].reset_index(drop=True)


HIGH_RISK_BUCKET_ORDER = [
    "未提出・未作成",
    "未承認",
    "AI下書き未確認",
    "計画書・記録の不一致/未入力候補",
    "署名・確認漏れ",
]


def classify_high_risk_bucket(alert_type) -> str:
    """アラート種別を「高リスク未対応」の内訳カテゴリに分類する。該当しなければNoneを返す。

    件数表示（概要ダッシュボード）と内訳の説明文が食い違わないよう、
    severity列ではなくalert_typeの文字列判定で一貫して分類する。
    """
    alert_type = str(alert_type or "")
    if "未提出" in alert_type or "未作成" in alert_type:
        return "未提出・未作成"
    if "未承認" in alert_type:
        return "未承認"
    if "下書き" in alert_type and "未確認" in alert_type:
        return "AI下書き未確認"
    if "不一致候補" in alert_type or "未入力候補" in alert_type:
        return "計画書・記録の不一致/未入力候補"
    if "署名" in alert_type:
        return "署名・確認漏れ"
    return None


def extract_checklist_field_names(alert_type: str, detail: str) -> list:
    """checklist系アラートのdetail文言から、対象のレ点項目名を抽出する。

    「サービス区分とレ点項目カテゴリの不一致候補」は複数項目を
    「清掃（生活援助）、洗濯（生活援助）」のように丸括弧付きでまとめて記載するため、
    正規表現による曖昧な抽出は誤マッチ（前方の助詞なども拾ってしまう）を招く。
    そのため、既知のレ点項目名（DEMO_FIELD_LAYOUTの全項目）に対する完全一致で判定する。
    """
    if alert_type == "サービス区分とレ点項目カテゴリの不一致候補":
        known_fields = [name for names in DEMO_FIELD_LAYOUT.values() for name in names]
        matches = [name for name in known_fields if f"{name}（" in detail]
        return matches if matches else [alert_type]

    match = re.search(r"「(.+?)」", detail)
    return [match.group(1)] if match else [alert_type]


def describe_history_bullet(row) -> str:
    """確認履歴の1行から、タイムラインカードに表示する確認内容の1行を組み立てる。"""
    record_type = row.get("record_type")
    if record_type == "daily_record":
        return "特記事項AI下書き確認"
    if record_type == "monitoring_record":
        return "月間モニタリングAI下書き確認"
    if record_type == "revision":
        return str(row.get("reviewed_text") or row.get("detail") or "確認済み記録を修正")
    if record_type == "mismatch_ack":
        return "不一致候補を職員確認済み"
    if record_type == "checklist":
        detail = str(row.get("detail") or "")
        alert_type = row.get("alert_type") or "レ点チェック"
        keywords = extract_checklist_field_names(alert_type, detail)
        if alert_type in ("計画書との不一致候補", "サービス区分とレ点項目カテゴリの不一致候補"):
            keyword_text = "、".join(keywords)
            return f"要確認項目：{keyword_text}（計画書・サービス区分との不一致候補、職員入力を保持）"
        return f"レ点候補：{'、'.join(keywords)}"
    alert_type = row.get("alert_type")
    if alert_type:
        return f"書類確認：{alert_type}"
    return "確認"


def build_history_events(history_df: pd.DataFrame) -> list:
    """確認履歴の行を、target_id・確認者・確認時刻（分単位）でグルーピングし、1回の確認操作を1イベントにまとめる。"""
    if history_df.empty:
        return []

    df = history_df.copy()
    df["_time_key"] = df["reviewed_at"].astype(str).str[:16]

    events = []
    for (target_id, reviewed_by, time_key), group in df.groupby(["target_id", "reviewed_by", "_time_key"], dropna=False):
        first = group.iloc[0]
        bullets = [describe_history_bullet(row) for _, row in group.iterrows()]
        events.append(
            {
                "reviewed_at": first.get("reviewed_at"),
                "reviewed_by": reviewed_by,
                "target_id": target_id,
                "user_id": first.get("user_id"),
                "document_name": first.get("document_name") or "書類",
                "bullets": bullets,
                "rows": group,
            }
        )

    events.sort(key=lambda e: str(e["reviewed_at"]), reverse=True)
    return events


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


# デモ用サービス提供記録（R011）専用の簡略フィールド構成。
# 一般のFIELD_TAXONOMY（9項目の身体介護等）とは別に、ビフォーアフターが
# 一目で分かるよう、デモの物語に沿った少数の項目だけを表示する。
DEMO_FIELD_LAYOUT = {
    "共通・状態確認": ["顔色", "発汗", "バイタル", "体調観察", "その他"],
    "身体介護": ["食事見守り", "水分補給促し", "声掛け・見守り"],
    "生活援助": ["清掃", "洗濯", "衣類・寝具", "調理", "買物等"],
}

# R011は「食事見守り」に「見守り」の文字列を含むため、汎用のキーワード部分一致に任せると
# 「声掛け・見守り」まで誤ってチェック済みと判定されてしまう。そのためBefore画面の初期値は
# デモ専用に明示的なマッピングとして固定する（レコードから動的に導出しない）。
DEMO_R011_INITIAL_CHECKS = {
    "顔色": False,
    "発汗": False,
    "バイタル": True,
    "体調観察": False,
    "その他": False,
    "食事見守り": True,
    "水分補給促し": False,
    "声掛け・見守り": False,
    "清掃": True,
    "洗濯": False,
    "衣類・寝具": False,
    "調理": False,
    "買物等": False,
}

DEMO_AI_CANDIDATE_FIELDS = ["水分補給促し", "体調観察"]  # AI補填で追加する項目
# R011のサービス区分は「身体介護」のため、生活援助カテゴリの項目がBeforeでチェックされていた場合、
# 計画書・サービス区分との不一致候補として「要確認」フラグを立てる対象とする。
# 職員の手入力（チェック状態）はAIが勝手に外さず、そのまま保持する。
DEMO_FLAGGED_CANDIDATE_FIELDS = list(DEMO_FIELD_LAYOUT["生活援助"])

DEMO_AI_CANDIDATE_NOTES = [
    ("水分補給促し", "訪問介護計画書上の支援内容に含まれるため、AI補填案で追加しました。"),
    ("体調観察", "訪問介護計画書上の支援内容に含まれるため、AI補填案で追加しました。"),
]


def build_demo_flagged_note(field_name: str) -> str:
    return f"職員によりチェックされています。ただし、現在の計画書・サービス区分とは不一致候補のため、確認が必要です。"


def build_demo_mismatch_warning_line(field_name: str) -> str:
    return f"{field_name}：身体介護の記録に生活援助項目が含まれています。"


def get_demo_before_checks() -> dict:
    """Beforeでの手入力修正を反映した、現在のR011チェック状態を返す（未操作項目は初期値のまま）。

    Before画面のcheckboxキー（demo_before_check_*）だけを参照する。Afterの表示状態とは
    完全に分離しており、After側のstale widget stateの影響を受けない。
    """
    return {
        field_name: st.session_state.get(f"demo_before_check_{field_name}", default_value)
        for field_name, default_value in DEMO_R011_INITIAL_CHECKS.items()
    }


def build_demo_ai_final_checks() -> tuple:
    """Beforeの現在値のスナップショットをもとに、AI補填後の完成案チェック状態を新規に組み立てる。

    AI補填ボタンが押されるたびに必ず呼び出し、st.session_state["demo_ai_final_checks"]と
    st.session_state["demo_ai_flagged_fields_actual"]を上書きする。古いAfter結果を使い回さない
    ための唯一の生成経路とする。(ai_final_checks, flagged_fields_actual)のタプルを返す。

    AIは不足している項目（水分補給促し・体調観察）を補填するが、職員がBeforeで手入力した
    チェックは勝手に外さず保持する。計画書・サービス区分との不一致候補がある場合は、
    チェックはそのままに「要確認」フラグを立てるだけにとどめる。
    """
    before_checks = get_demo_before_checks()
    ai_final_checks = before_checks.copy()
    for field_name in DEMO_AI_CANDIDATE_FIELDS:
        ai_final_checks[field_name] = True
    # 生活援助項目は職員入力を保持する（Falseで上書きしない）。

    # Beforeで実際にチェックされていた生活援助項目を「要確認フラグを立てた項目」として記録する。
    flagged_fields_actual = [
        field_name for field_name in DEMO_FLAGGED_CANDIDATE_FIELDS if before_checks.get(field_name, False)
    ]
    return ai_final_checks, flagged_fields_actual


def build_fallback_ai_note_body(record_row) -> str:
    """事前生成ドラフトが無い記録向けに、実データからルールベースで特記事項の補填文（本文のみ）を組み立てる。

    LLM等は呼び出さず、既存フィールドをテンプレートで組み合わせるだけの
    ルールベース処理であり、AIが事実を確定するものではない。根拠は別枠で表示するため、
    本文には含めない。
    """
    body_parts = []
    special_notes = str(record_row.get("special_notes") or "").strip()
    if special_notes:
        body_parts.append(special_notes.rstrip("。"))
    user_quote = str(record_row.get("user_quote") or "").strip()
    if user_quote:
        body_parts.append(f"本人より「{user_quote}」との発言があった")
    observation = str(record_row.get("observation") or "").strip()
    if observation:
        body_parts.append(observation.rstrip("。"))
    follow_up = str(record_row.get("follow_up") or "").strip()
    if follow_up:
        body_parts.append(follow_up.rstrip("。"))

    return "。".join(body_parts) + "。" if body_parts else "（記録内容が不足しています）"


def save_demo_confirmation(
    record_row, reviewed_text: str, reviewed_by: str, related_rows: pd.DataFrame, flagged_fields=None
) -> None:
    """デモ記録（R011）に紐づく未対応アラートを、特記事項の保存とあわせてまとめて確認済みにする。

    他の利用者・他の記録のアラートには一切影響しない。
    flagged_fieldsに項目がある場合（計画書・サービス区分との不一致候補を職員が確認したうえで
    保存した場合）は、監査ログに「不一致候補を職員確認済み」の記録を追加で残す。
    """
    save_reviewed_row(
        OUTPUTS_DIR / "daily_records_note_reviewed.csv",
        record_row,
        reviewed_text,
        reviewed_by,
        "note_reviewed",
    )

    checklist_unresolved = related_rows[(related_rows["source_type"] == "checklist") & (~related_rows["confirmed"])]
    for _, ca in checklist_unresolved.iterrows():
        save_queue_log(
            ca["alert_key"],
            "checklist",
            "checklist",
            ca["target_id"],
            ca["user_key"],
            ca["document_name"],
            ca["alert_reason"],
            reviewed_text,
            reviewed_by,
        )

    if flagged_fields:
        ack_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_queue_log(
            f"mismatch_ack|{DEMO_RECORD_ID}|{DEMO_RECORD_USER}|サービス提供記録|{ack_timestamp}",
            "mismatch_ack",
            "mismatch_ack",
            DEMO_RECORD_ID,
            DEMO_RECORD_USER,
            "サービス提供記録",
            "不一致候補を職員確認したうえで保存しました。要確認項目：" + "、".join(flagged_fields),
            reviewed_text,
            reviewed_by,
        )


def save_demo_revision(record_row, reviewed_text: str, revised_by: str, summary: str) -> None:
    """確認済みR011記録の修正を、既存の監査ログを上書きせず新しい履歴として追加する。

    daily_records_note_reviewed.csvには新しい行（review_status="revised"）を追記し、
    confirmation_queue_log.csvには修正の概要を記録する専用のrevisionエントリを追記する。
    どちらも既存行の書き換え・削除は行わない。
    """
    save_reviewed_row(
        OUTPUTS_DIR / "daily_records_note_reviewed.csv",
        record_row,
        reviewed_text,
        revised_by,
        "revised",
    )

    revision_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_queue_log(
        f"revision|{DEMO_RECORD_ID}|{DEMO_RECORD_USER}|サービス提供記録|{revision_timestamp}",
        "revision",
        "revision",
        DEMO_RECORD_ID,
        DEMO_RECORD_USER,
        "サービス提供記録",
        summary,
        summary,
        revised_by,
    )


def render_demo_confirmed_summary(record_row) -> None:
    """確認済みになったR011の全体図を表示する。

    今回のセッションでst.session_state["demo_confirmed_record"]（最新の確認・修正内容の
    表示用キャッシュ）があればそれを優先して使う。無い場合（別セッション・再読込直後など）は、
    保存済みCSV（outputs/配下）から再構築する。監査ログCSV自体は編集せず、
    いずれの経路でも履歴としては追記のみで保持される。
    """
    st.markdown(status_badge_html("✅ 確認済み"), unsafe_allow_html=True)
    st.caption("この書類は職員確認済みです。以下はAI補填後の完成案として保存された内容です。")

    care_plans_df = load_csv(DATA_DIR / "care_plans.csv")
    plan_match = care_plans_df[care_plans_df["user_id"] == DEMO_RECORD_USER]
    plan_row = plan_match.iloc[0] if not plan_match.empty else None

    with st.container(border=True):
        st.subheader("基本情報")
        base_col1, base_col2 = st.columns(2)
        with base_col1:
            st.write(f"**利用者**：{DEMO_RECORD_USER}")
            st.write(f"**提供日**：{record_row.get('record_date')}（{get_japanese_weekday(record_row.get('record_date'))}曜日）")
            st.write(f"**提供時間**：{record_row.get('time_slot') or 'データなし'}")
        with base_col2:
            st.write(f"**サービス区分**：{record_row.get('service_category') or 'データなし'}")
            st.write(f"**担当職員**：{record_row.get('staff_name')}")
            st.write("**事業所**：Care Compliance Copilot デモ事業所")

    confirmed_state = st.session_state.get(DEMO_CONFIRMED_RECORD_KEY)

    if confirmed_state is not None:
        final_checks = confirmed_state.get("final_checks") or {}
        added_fields = confirmed_state.get("added_fields") or []
        flagged_fields = confirmed_state.get("flagged_fields") or []
        note_text = confirmed_state.get("reviewed_text") or ""
        byline_by = confirmed_state.get("revised_by") or confirmed_state.get("reviewed_by")
        byline_at = confirmed_state.get("revised_at") or confirmed_state.get("confirmed_at")
        revision_no = int(confirmed_state.get("revision_no", 0))
    else:
        added_fields, flagged_fields, note_text = get_demo_confirmed_state()
        final_checks = None
        daily_reviewed_df, _ = load_outputs_csv("daily_records_note_reviewed.csv")
        reviewed_row = None
        if not daily_reviewed_df.empty and "record_id" in daily_reviewed_df.columns:
            matched = daily_reviewed_df[daily_reviewed_df["record_id"].astype(str) == DEMO_RECORD_ID]
            if not matched.empty:
                reviewed_row = matched.sort_values("reviewed_at").iloc[-1]
        byline_by = reviewed_row.get("reviewed_by") if reviewed_row is not None else None
        byline_at = reviewed_row.get("reviewed_at") if reviewed_row is not None else None
        revision_no = 0

    st.write("**補正後・職員確認後のレ点チェック（読み取り専用・保存済み）**")
    for section, field_names in DEMO_FIELD_LAYOUT.items():
        st.markdown(f"**{section}**")
        for field_name in field_names:
            if final_checks is not None:
                checked = bool(final_checks.get(field_name, DEMO_R011_INITIAL_CHECKS.get(field_name, False)))
            elif field_name in added_fields or field_name in flagged_fields:
                checked = True
            else:
                checked = DEMO_R011_INITIAL_CHECKS.get(field_name, False)

            if field_name in added_fields:
                suffix = status_badge_html("AI補填") + " " + status_badge_html("職員確認が必要")
            elif field_name in flagged_fields and checked:
                suffix = status_badge_html("要確認") + "：計画書・サービス区分との不一致候補"
            else:
                suffix = ""
            mark = "☑" if checked else "☐"
            st.markdown(f"{mark} {field_name} {suffix}", unsafe_allow_html=True)

    if added_fields or flagged_fields:
        with st.container(border=True):
            st.write("**AI補填内容と要確認項目**")
            for field_name in added_fields:
                st.write(f"- {field_name}：訪問介護計画書上の支援内容に含まれるため、AI補填案で追加しました。")
            for field_name in flagged_fields:
                st.write(f"- {field_name}：{build_demo_flagged_note(field_name)}")

    if flagged_fields:
        with st.container(border=True):
            st.write("**要確認項目一覧**")
            for field_name in flagged_fields:
                st.write(f"- {field_name}：職員入力を保持。ただし、計画書・サービス区分との不一致候補")

    st.divider()
    with st.container(border=True):
        st.write("**職員確認後の文章（保存済み・最新版）**")
        st.text_area(
            "職員確認後の文章", value=str(note_text or "（記録が見つかりませんでした）"), height=160, disabled=True,
            key="demo_confirmed_note", label_visibility="collapsed",
        )
        if byline_by or byline_at:
            st.caption(f"確認者：{byline_by} ／ 確認日時：{byline_at}")
        if revision_no > 0:
            st.caption(f"修正回数：{revision_no}回（監査ログには各修正が履歴として個別に残ります）")

    with st.container(border=True):
        st.write("**使用した根拠**")
        if plan_row is not None:
            st.write(f"- 訪問介護計画書：{plan_row.get('service_content')}")
        st.write(f"- 日々の記録：{record_row.get('service_items')}")
        st.write(f"- 本人発言：{record_row.get('user_quote') or '（未記載）'}")
        st.write(f"- 観察内容：{record_row.get('observation') or '（未記載）'}")
        with st.expander("詳細な根拠を見る"):
            st.write(f"- 数値情報：{record_row.get('numeric_data') or '（未記載）'}")
            st.write(f"- 今後の対応：{record_row.get('follow_up') or '（未記載）'}")


def get_demo_confirmed_state() -> tuple:
    """保存済みデータから、現在の確認済みR011の added_fields・flagged_fields・最新の職員確認後の文章を再構築する。"""
    queue_log_df, _ = load_outputs_csv(QUEUE_LOG_PATH.name)
    added_fields, flagged_fields = [], []
    if not queue_log_df.empty and "target_id" in queue_log_df.columns:
        checklist_log = queue_log_df[
            (queue_log_df["target_id"].astype(str) == DEMO_RECORD_ID) & (queue_log_df["record_type"] == "checklist")
        ]
        for _, row in checklist_log.iterrows():
            alert_key = str(row.get("alert_key") or "")
            alert_type = alert_key.split("|")[-1] if alert_key else ""
            detail = str(row.get("detail") or "")
            keywords = extract_checklist_field_names(alert_type, detail)
            if alert_type == "レ点未入力候補":
                for keyword in keywords:
                    if keyword not in added_fields:
                        added_fields.append(keyword)
            elif alert_type in ("計画書との不一致候補", "サービス区分とレ点項目カテゴリの不一致候補"):
                for keyword in keywords:
                    if keyword not in flagged_fields:
                        flagged_fields.append(keyword)

    daily_reviewed_df, _ = load_outputs_csv("daily_records_note_reviewed.csv")
    latest_text = ""
    if not daily_reviewed_df.empty and "record_id" in daily_reviewed_df.columns:
        matched = daily_reviewed_df[daily_reviewed_df["record_id"].astype(str) == DEMO_RECORD_ID]
        if not matched.empty:
            latest_text = str(matched.sort_values("reviewed_at").iloc[-1].get("reviewed_text") or "")

    return added_fields, flagged_fields, latest_text


def render_demo_edit_form(record_row) -> bool:
    """確認済みR011記録を修正するための編集画面。保存すると新しい履歴として追加され、既存の監査ログは上書きしない。"""
    st.markdown(status_badge_html("✅ 確認済み"), unsafe_allow_html=True)
    st.info("確認済み記録を修正します。保存すると、既存の監査ログは変更せず、修正履歴として新たに追加されます。")

    if st.button("← 全体図に戻る（修正せず終了）", key="demo_edit_cancel"):
        st.session_state["demo_edit_mode"] = False
        st.session_state["scroll_to_top"] = True
        st.rerun()

    confirmed_state = st.session_state.get(DEMO_CONFIRMED_RECORD_KEY)
    if confirmed_state is not None:
        final_checks = confirmed_state.get("final_checks") or {}
        added_fields = confirmed_state.get("added_fields") or []
        flagged_fields = confirmed_state.get("flagged_fields") or []
        latest_text = confirmed_state.get("reviewed_text") or ""
        revision_no = int(confirmed_state.get("revision_no", 0))
    else:
        added_fields, flagged_fields, latest_text = get_demo_confirmed_state()
        final_checks = None
        revision_no = 0

    # checkboxはkey再利用時にvalue引数を無視するため、修正回数をkeyに含めて
    # 修正のたびに新しいwidget stateとして生成し、直前の保存内容を確実に初期値へ反映する。
    check_key_prefix = f"demo_revise_check_{revision_no}_"

    st.write("**レ点チェック（修正できます）**")
    edited_checks = {}
    for section, field_names in DEMO_FIELD_LAYOUT.items():
        st.markdown(f"**{section}**")
        for field_name in field_names:
            if final_checks is not None:
                default_checked = bool(final_checks.get(field_name, DEMO_R011_INITIAL_CHECKS.get(field_name, False)))
            else:
                default_checked = (
                    field_name in added_fields
                    or field_name in flagged_fields
                    or DEMO_R011_INITIAL_CHECKS.get(field_name, False)
                )
            edited_checks[field_name] = st.checkbox(
                field_name, value=default_checked, key=f"{check_key_prefix}{field_name}"
            )

    st.write("**職員確認後の文章（修正できます）**")
    revised_text = st.text_area(
        "職員確認後の文章", value=latest_text, height=160, key=f"demo_revise_text_{revision_no}", label_visibility="collapsed"
    )

    revised_by = st.text_input("修正者名", value="サ責A", key="demo_revise_by")
    revise_confirmed = st.checkbox("修正内容を確認しました。", key="demo_revise_confirm")

    saved = False
    if st.button("修正版として保存", type="primary", key="demo_revise_save"):
        if not revise_confirmed:
            st.error("保存するには、確認チェックを入れてください。")
        elif not revised_by.strip():
            st.error("修正者名を入力してください。")
        else:
            flagged_now = [f for f in DEMO_FIELD_LAYOUT["生活援助"] if edited_checks.get(f, False)]
            summary_parts = ["レ点チェックを修正しました。", "職員確認後の文章を修正しました。"]
            if flagged_now:
                summary_parts.append("要確認項目：" + "、".join(flagged_now))
            summary = " ".join(summary_parts)

            save_demo_revision(record_row, revised_text, revised_by.strip(), summary)

            previous_state = st.session_state.get(DEMO_CONFIRMED_RECORD_KEY) or {}
            added_fields_prev = previous_state.get("added_fields") or list(DEMO_AI_CANDIDATE_FIELDS)
            revised_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state[DEMO_CONFIRMED_RECORD_KEY] = {
                "target_id": DEMO_RECORD_ID,
                "user_id": DEMO_RECORD_USER,
                "final_checks": dict(edited_checks),
                "added_fields": added_fields_prev,
                "flagged_fields": flagged_now,
                "reviewed_text": revised_text,
                "confirmed_at": previous_state.get("confirmed_at", revised_at),
                "reviewed_by": previous_state.get("reviewed_by", revised_by.strip()),
                "revised_at": revised_at,
                "revised_by": revised_by.strip(),
                "revision_no": int(previous_state.get("revision_no", 0)) + 1,
            }

            st.session_state["demo_edit_mode"] = False
            st.session_state["scroll_to_top"] = True
            st.success("修正版として保存しました。確認履歴・監査ログに修正履歴が追加されます。")
            saved = True

    return saved


def render_demo_service_record(related_rows: pd.DataFrame) -> bool:
    """デモ用サービス提供記録（R011）のBefore/After体験を描画する。保存が実行されたらTrueを返す。"""
    daily_df = load_csv(DATA_DIR / "daily_records.csv")
    record_match = daily_df[daily_df["record_id"].astype(str) == DEMO_RECORD_ID]
    if record_match.empty:
        st.error("デモ用記録が見つかりませんでした。")
        return False
    record_row = record_match.iloc[0]

    checklist_alerts = related_rows[related_rows["source_type"] == "checklist"]
    other_alerts = related_rows[related_rows["source_type"] != "checklist"]

    is_confirmed = not related_rows.empty and bool(related_rows["confirmed"].all())
    if is_confirmed:
        if st.session_state.get("demo_edit_mode"):
            return render_demo_edit_form(record_row)
        render_demo_confirmed_summary(record_row)
        return False

    with st.container(border=True):
        st.subheader("アラート理由・AI補填対象")
        for _, ca in checklist_alerts.iterrows():
            st.write(f"- {ca['alert_reason']}")
        for _, oa in other_alerts.iterrows():
            st.write(f"- 〔{oa['alert_type']}〕{oa['alert_reason']}")
        st.write("AI補填プレビューを作成できます。")

        with st.expander("計画書連動レ点チェックの詳細"):
            care_plans_df = load_csv(DATA_DIR / "care_plans.csv")
            care_plans_df = ensure_columns(care_plans_df, ["visit_days", "time_slot", "service_category"])
            plan_match = care_plans_df[care_plans_df["user_id"] == DEMO_RECORD_USER]
            if not plan_match.empty:
                plan_row = plan_match.iloc[0]
                st.write(f"**訪問介護計画書上の支援内容**：{plan_row.get('service_content')}")
                st.write(f"**サービス区分（計画）**：{plan_row.get('service_category')}")
                st.write(f"**対象日の記録内容**：{record_row.get('service_items')}")
                st.write(f"**サービス区分（記録）**：{record_row.get('service_category')}")
            st.caption(
                "レ点はAIやルールが実施事実を確定するものではありません。"
                "計画書との不一致候補・要確認として提示するだけであり、最終確認は必ず職員が行ってください。"
            )

    preview_key = "demo_ai_preview_generated"
    preview_generated = st.session_state.get(preview_key, False)

    saved_this_run = False

    if not preview_generated:
        # --- Before：元の記録を確認・修正する画面（checkbox・text_areaは操作可能） ---
        st.subheader("基本情報")
        base_col1, base_col2 = st.columns(2)
        with base_col1:
            st.write(f"**利用者**：{DEMO_RECORD_USER}")
            st.write(f"**提供日**：{record_row.get('record_date')}（{get_japanese_weekday(record_row.get('record_date'))}曜日）")
            st.write(f"**提供時間**：{record_row.get('time_slot') or 'データなし'}")
        with base_col2:
            st.write(f"**サービス区分**：{record_row.get('service_category') or 'データなし'}")
            st.write(f"**担当職員**：{record_row.get('staff_name')}")
            st.write("**事業所**：Care Compliance Copilot デモ事業所")
            st.write("**サービス名**：訪問介護")

        st.divider()
        st.subheader("共通・状態確認")
        for field_name in DEMO_FIELD_LAYOUT["共通・状態確認"]:
            st.checkbox(field_name, value=DEMO_R011_INITIAL_CHECKS[field_name], key=f"demo_before_check_{field_name}")

        st.divider()
        st.subheader("身体介護")
        for field_name in DEMO_FIELD_LAYOUT["身体介護"]:
            st.checkbox(field_name, value=DEMO_R011_INITIAL_CHECKS[field_name], key=f"demo_before_check_{field_name}")

        st.divider()
        st.subheader("生活援助")
        for field_name in DEMO_FIELD_LAYOUT["生活援助"]:
            st.checkbox(field_name, value=DEMO_R011_INITIAL_CHECKS[field_name], key=f"demo_before_check_{field_name}")

        st.divider()
        st.subheader("特記事項")
        st.text_area(
            "現在の特記事項（手入力で修正できます）",
            value=str(record_row.get("special_notes") or ""),
            height=150,
            key="demo_special_notes_before",
        )

        st.divider()
        if st.button("AI補填プレビューを作成", type="primary", key="demo_generate_preview"):
            # ボタンが押されるたびに、Beforeの現在値から完成案を必ず作り直す（古い結果は使い回さない）。
            final_checks, flagged_actual = build_demo_ai_final_checks()
            st.session_state["demo_ai_final_checks"] = final_checks
            st.session_state["demo_ai_flagged_fields_actual"] = flagged_actual
            st.session_state["demo_ai_final_note_body"] = build_fallback_ai_note_body(record_row)
            st.session_state[preview_key] = True
            st.session_state["scroll_to_top"] = True
            st.rerun()

    else:
        # --- After：AI補填後の完成案を確認する画面（レ点チェックは読み取り専用） ---
        # 画面最上部へのスクロールは、スクリプト先頭の共通処理（page確定直後）でまとめて行う。

        if st.button("← 元の記録画面に戻って修正する", key="demo_back_to_before"):
            # previewフラグだけを解除する。Beforeのcheckbox状態（demo_before_check_*）は保持したままにする。
            st.session_state[preview_key] = False
            st.session_state["scroll_to_top"] = True
            st.rerun()

        st.subheader("AI補填後のサービス提供記録（完成案）")
        st.warning("この内容は職員確認前の完成案です。確定記録として保存する前に、必ず職員が確認・修正してください。")

        st.write("**補填後のレ点チェック（読み取り専用）**")
        # AfterはBeforeのcheckbox状態を直接参照せず、AI補填ボタン押下時にスナップショットした
        # st.session_state["demo_ai_final_checks"]のみを参照する。st.checkboxウィジェットは
        # 同一keyの再利用時にvalue引数を無視しsession_stateの古い値を表示し続けるため、
        # ここではウィジェットを使わずテキストラベルで表示する（読み取り専用を確実にするため）。
        # 職員がBeforeでチェックした項目はAIが勝手に外さず保持し、計画書・サービス区分との
        # 不一致候補がある場合は「要確認」フラグを添えるだけにとどめる。
        ai_final_checks = st.session_state.get("demo_ai_final_checks")
        flagged_fields_actual = st.session_state.get("demo_ai_flagged_fields_actual")
        if ai_final_checks is None or flagged_fields_actual is None:
            ai_final_checks, flagged_fields_actual = build_demo_ai_final_checks()
        for section, field_names in DEMO_FIELD_LAYOUT.items():
            st.markdown(f"**{section}**")
            for field_name in field_names:
                checked = ai_final_checks.get(field_name, False)
                mark = "☑" if checked else "☐"
                if field_name in DEMO_AI_CANDIDATE_FIELDS:
                    label_suffix = status_badge_html("AI補填") + " " + status_badge_html("職員確認が必要")
                elif field_name in flagged_fields_actual:
                    label_suffix = status_badge_html("要確認") + "：計画書・サービス区分との不一致候補"
                else:
                    label_suffix = ""
                st.markdown(f"{mark} {field_name} {label_suffix}", unsafe_allow_html=True)

        with st.container(border=True):
            st.write("**AI補填内容と要確認項目**")
            for field_name, note in DEMO_AI_CANDIDATE_NOTES:
                st.write(f"- {field_name}：{note}")
            for field_name in flagged_fields_actual:
                st.write(f"- {field_name}：{build_demo_flagged_note(field_name)}")

        st.divider()
        note_body = st.session_state.get("demo_ai_final_note_body") or build_fallback_ai_note_body(record_row)

        with st.container(border=True):
            st.write("**AI補填後の特記事項**")
            st.text_area(
                "AI補填後の特記事項", value=note_body, height=160, disabled=True,
                key="demo_note_readonly", label_visibility="collapsed",
            )
            st.caption("この内容はAI下書きです。確定前に職員確認が必要です。")

        st.write("**職員確認後の文章（修正できます）**")
        reviewed_text = st.text_area(
            "職員確認後の文章", value=note_body, height=160, key="demo_draft_editable", label_visibility="collapsed"
        )

        with st.container(border=True):
            st.write("**使用した根拠**")
            care_plans_df = load_csv(DATA_DIR / "care_plans.csv")
            plan_match = care_plans_df[care_plans_df["user_id"] == DEMO_RECORD_USER]
            plan_content = plan_match.iloc[0].get("service_content") if not plan_match.empty else "データなし"
            st.write(f"- 訪問介護計画書：{plan_content}")
            st.write(f"- 日々の記録：{record_row.get('service_items')}")
            st.write(f"- 本人発言：{record_row.get('user_quote') or '（未記載）'}")
            st.write(f"- 観察内容：{record_row.get('observation') or '（未記載）'}")
            with st.expander("詳細な根拠を見る"):
                st.write(f"- 数値情報：{record_row.get('numeric_data') or '（未記載）'}")
                st.write(f"- 今後の対応：{record_row.get('follow_up') or '（未記載）'}")

        st.divider()

        mismatch_confirmed = True
        if flagged_fields_actual:
            with st.container(border=True):
                st.warning("⚠ 計画書・サービス区分との不一致候補があります")
                st.write("以下の項目は、現在の訪問介護計画書またはサービス区分と一致しない可能性があります。")
                for field_name in flagged_fields_actual:
                    st.write(f"- {build_demo_mismatch_warning_line(field_name)}")
                st.write(
                    "計画書の更新遅れの可能性、当日の支援変更の可能性、職員判断による追加記録の可能性があります。"
                    "内容を確認したうえで保存してください。"
                )
                mismatch_confirmed = st.checkbox(
                    "不一致候補を確認したうえで、職員判断として保存します。",
                    key="demo_mismatch_confirm_checkbox",
                )

        reviewed_by = st.text_input("確認者名", value="サ責A", key="demo_reviewed_by")
        confirmed_checkbox = st.checkbox("内容を確認しました。", key="demo_confirm_checkbox")

        if st.button("職員確認済みにする", type="primary", key="demo_save_button"):
            if not confirmed_checkbox:
                st.error("保存するには、確認チェックを入れてください。")
            elif flagged_fields_actual and not mismatch_confirmed:
                st.error("不一致候補を確認したうえで保存するには、上のチェックを入れてください。")
            elif not reviewed_by.strip():
                st.error("確認者名を入力してください。")
            else:
                save_demo_confirmation(
                    record_row, reviewed_text, reviewed_by.strip(), related_rows, flagged_fields_actual
                )
                st.session_state[DEMO_CONFIRMED_RECORD_KEY] = {
                    "target_id": DEMO_RECORD_ID,
                    "user_id": DEMO_RECORD_USER,
                    "final_checks": dict(ai_final_checks),
                    "added_fields": list(DEMO_AI_CANDIDATE_FIELDS),
                    "flagged_fields": list(flagged_fields_actual),
                    "reviewed_text": reviewed_text,
                    "confirmed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "reviewed_by": reviewed_by.strip(),
                    "revision_no": 0,
                }
                st.session_state[preview_key] = False
                st.success("確認済みとして保存しました。この書類は未対応アラート一覧から除外され、確認履歴・監査ログに反映されます。")
                saved_this_run = True

    return saved_this_run


# =========================
# サイドバー
# =========================

def _apply_nav_page(target_page: str) -> None:
    """指定ページを主要導線／補助画面いずれかのradioに反映し、もう一方は選択解除する。"""
    st.session_state.nav_page = target_page
    st.session_state["scroll_to_top"] = True
    if target_page in PRIMARY_MENU_ITEMS:
        st.session_state["nav_primary_radio"] = target_page
        st.session_state["nav_secondary_radio"] = None
    else:
        st.session_state["nav_secondary_radio"] = target_page
        st.session_state["nav_primary_radio"] = None


def _on_primary_nav_change() -> None:
    selected = st.session_state.get("nav_primary_radio")
    if selected is not None:
        st.session_state.nav_page = selected
        st.session_state["nav_secondary_radio"] = None
        st.session_state["scroll_to_top"] = True


def _on_secondary_nav_change() -> None:
    selected = st.session_state.get("nav_secondary_radio")
    if selected is not None:
        st.session_state.nav_page = selected
        st.session_state["nav_primary_radio"] = None
        st.session_state["scroll_to_top"] = True


if "nav_page" not in st.session_state:
    _apply_nav_page(PRIMARY_MENU_ITEMS[0])

if "_pending_nav_page" in st.session_state:
    _apply_nav_page(st.session_state.pop("_pending_nav_page"))

st.sidebar.title("Care Compliance Copilot")
st.sidebar.caption("訪問介護事業所の運営指導前チェックを支援するAI活用MVP")
st.sidebar.info("👉 まずは「書類アラート一覧」最上部のR011デモから操作するのがおすすめです。")

st.sidebar.markdown("### メニューの主要導線")
st.sidebar.caption("書類アラート一覧→書類詳細・AI補填プレビュー→確認キュー→確認履歴・監査ログの一本道フローです。")
st.sidebar.radio(
    "メニューの主要導線",
    PRIMARY_MENU_ITEMS,
    key="nav_primary_radio",
    on_change=_on_primary_nav_change,
    label_visibility="collapsed",
)

st.sidebar.divider()

st.sidebar.markdown("### 補助画面")
st.sidebar.caption("アラート根拠・レ点候補・AI下書きなどを個別に確認したい場合に使う画面です。")
st.sidebar.radio(
    "補助画面",
    AUXILIARY_MENU_ITEMS,
    key="nav_secondary_radio",
    on_change=_on_secondary_nav_change,
    label_visibility="collapsed",
)

page = st.session_state.nav_page

render_page_top_anchor()

if st.session_state.pop("scroll_to_top", False):
    # ページ遷移・状態遷移の直後だけ、画面最上部へスクロールする。
    # 通常操作（チェック・入力など）による再描画では発火しない。
    scroll_to_top()


# =========================
# 画面：使い方・業務フロー
# =========================

if page == "使い方・業務フロー":
    st.title("使い方・業務フロー")
    st.markdown(
        '<div class="hero-card">'
        '<span class="hero-eyebrow">CARE COMPLIANCE COPILOT</span>'
        '<div class="hero-title">訪問介護事業所の運営指導前チェックを支援するAI活用MVP</div>'
        '<div class="hero-subtitle">'
        "書類不備・未確認・未承認・期限切れ・記録不一致を検出し、必要に応じてAI下書き候補を提示します。"
        "最終確認・保存は必ず職員が行います。"
        "</div>"
        '<div class="hero-point-row">'
        '<span class="hero-point">📋 4分野15書類・記録を横断チェック</span>'
        '<span class="hero-point">🛡️ AIは確定せず、職員確認が必須</span>'
        '<span class="hero-point">🧾 確認履歴・監査ログを保持</span>'
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.subheader("主要導線（書類中心の業務フロー）")
    st.markdown(
        """
        1. **概要ダッシュボード** で、アラート状況の全体像を確認する
        2. **書類アラート一覧** で、対応が必要な書類・記録を一覧確認する（分野・重要度で絞り込み可能）
        3. 「▶ この書類の全体図を確認する」から **書類詳細・AI補填プレビュー** に進み、書類全体図・AI補填後プレビュー・計画書連動レ点チェック・根拠を確認する
        4. 内容を確認・必要に応じて修正し、確認者名を入力してチェックを入れ、「確認済みにする」ボタンで保存する
        5. 保存後、「次の未対応書類へ進む」で連続して次の書類を処理する（**確認キュー**からも同じ詳細画面に入れる）
        6. **確認履歴・監査ログ** で、保存された確認結果を確認する
        """
    )

    st.subheader("補助画面（個別に直接確認したい場合）")
    st.info(
        "補助画面は、アラート根拠、レ点候補、特記事項AI補填、月間モニタリングAI下書き、職員確認済み保存を"
        "個別に確認するための画面です。通常の業務フローでは、書類アラート一覧から書類詳細・AI補填プレビュー"
        "画面に進む導線を使用します。"
    )
    st.markdown(
        """
        - アラート根拠確認：アラート単位で元データを直接確認したい場合
        - 計画書連動レ点候補：レ点候補だけを一覧で見たい場合
        - 特記事項AI補填デモ：日々の記録の特記事項AI下書きだけを見たい場合
        - 月間モニタリングAI下書き：月間モニタリングのAI下書きだけを見たい場合
        - 職員確認済み保存：AI下書きの確認・保存だけを単独で行いたい場合
        """
    )

    st.subheader("このアプリが検知する主な書類・記録")
    st.caption(
        "4分野15書類・記録カタログに基づき、運営指導前に確認すべき未対応・期限切れ・承認漏れ・記録不一致を可視化します。"
        "R011デモは、このうち「サービス提供記録」1件のBefore/Afterデモです。"
    )
    st.markdown(
        """
        **1. サービス提供・記録関連**
        - 訪問介護計画書：未作成、承認漏れ、更新期限切れ、署名・確認漏れ
        - サービス提供記録：レ点未入力候補、計画書との不一致候補、サービス区分とレ点項目カテゴリの不一致候補、特記事項不足、AI下書き未確認（★R011デモ対象）
        - モニタリング記録：未提出、下書きあり・未確認、未承認
        - 担当者会議記録：未作成、承認漏れ、署名・確認漏れ
        - 苦情処理記録：未作成、承認漏れ、署名・確認漏れ

        **2. 利用者・契約関連**
        - 重要事項説明書：未作成、承認漏れ、署名・確認漏れ
        - 利用契約書：未作成、承認漏れ、更新期限切れ、署名・確認漏れ
        - 個人情報同意書：未作成、承認漏れ、署名・確認漏れ
        - 居宅サービス計画書：未作成、承認漏れ、更新期限切れ、署名・確認漏れ

        **3. 人員・勤務体制関連**
        - 勤務形態一覧表：未作成、承認漏れ、署名・確認漏れ
        - 出勤簿：未作成、承認漏れ、署名・確認漏れ
        - 資格証：未作成、承認漏れ、更新期限切れ、署名・確認漏れ
        - 研修記録：未作成、承認漏れ、署名・確認漏れ

        **4. 運営・その他関連**
        - 感染症対策マニュアル：未作成、承認漏れ、更新期限切れ、署名・確認漏れ
        - 緊急時対応マニュアル：未作成、承認漏れ、更新期限切れ、署名・確認漏れ
        """
    )
    st.caption("上記のうち、AI補填後プレビュー（完成案の作成体験）はサービス提供記録のR011デモに集約しています。それ以外の書類は主にステータス確認・不足確認が対象です。")

    with st.expander("開発者向け：入力CSVを直接確認する"):
        selected_name = st.selectbox("表示するCSVを選択", list(DATA_FILES.keys()), key="usage_data_select")
        selected_path = DATA_FILES[selected_name]
        df = load_csv(selected_path)

        show_file_path("表示ファイル", selected_path)
        show_dataframe(df, selected_name)

    with st.expander("開発・デモ用：デモ状態をリセットする"):
        st.caption(
            "確認履歴・監査ログと、デモ用サービス提供記録（R011）の確認状態を初期状態に戻します。"
            "outputs/配下の生成ファイルのみ削除し、sample_outputs/は変更しません。"
        )
        if st.button("デモ状態をリセットする", key="reset_demo_state_button"):
            for filename in (
                "confirmation_queue_log.csv",
                "daily_records_note_reviewed.csv",
                "monitoring_records_reviewed.csv",
            ):
                target_path = OUTPUTS_DIR / filename
                if target_path.exists():
                    target_path.unlink()
            st.cache_data.clear()

            # デモ用R011のBefore/After操作状態（session_state）も初期化する。
            # ファイル削除だけではBefore画面のcheckbox修正やAfterプレビュー状態が
            # 残ってしまうため、デモ関連のキーを明示的にすべて削除する。
            demo_state_keys = [
                key
                for key in list(st.session_state.keys())
                if key.startswith("demo_")
            ]
            for key in demo_state_keys:
                del st.session_state[key]

            st.session_state["scroll_to_top"] = True
            st.success("デモ状態をリセットしました。")
            st.rerun()


# =========================
# 画面：概要ダッシュボード
# =========================

elif page == "概要ダッシュボード":
    st.title("概要ダッシュボード")
    st.write("4分野15書類・記録カタログに基づき、運営指導前に確認すべき未対応・期限切れ・承認漏れ・記録不一致を可視化します。")

    st.info(
        "AIやルールは記録・書類・レ点チェックを確定しません。"
        "職員が確認・修正したうえで保存する運用を前提としています。"
    )

    alert_df = build_document_alert_list()
    unresolved_df = get_unresolved_alerts(alert_df)

    # 総検知アラート数は、これまでに検知されたアラート行の総数（確認済みでも減らない）。
    total_alerts = len(alert_df)

    if not alert_df.empty:
        unit_all_confirmed = alert_df.groupby("document_unit_key")["confirmed"].agg(lambda s: bool(s.all()))
        unresolved_document_keys = set(unit_all_confirmed[~unit_all_confirmed].index)
        confirmed_document_keys = set(unit_all_confirmed[unit_all_confirmed].index)
    else:
        unresolved_document_keys = set()
        confirmed_document_keys = set()

    unresolved_document_count = len(unresolved_document_keys)
    confirmed_document_count = len(confirmed_document_keys)
    affected_subjects = unresolved_df["user_key"].nunique() if not unresolved_df.empty else 0

    if not unresolved_df.empty:
        unresolved_df = unresolved_df.copy()
        unresolved_df["high_risk_bucket"] = unresolved_df["alert_type"].apply(classify_high_risk_bucket)
        high_risk_document_keys = set(
            unresolved_df.loc[unresolved_df["high_risk_bucket"].notna(), "document_unit_key"]
        )
    else:
        high_risk_document_keys = set()
    high_risk_document_count = len(high_risk_document_keys)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        render_kpi_card(
            "累計", "kpi-flag-info", total_alerts, "総検知アラート数",
            "これまでに検知された書類・記録・レ点チェックのアラート行数（確認済みになっても減りません）",
        )

    with col2:
        render_kpi_card(
            "要対応", "kpi-flag-warn", unresolved_document_count, "未対応書類・記録件数",
            "未対応アラートが1件でも残っている書類・記録の数（同じ書類・記録の複数アラートは1件で集計）",
        )

    with col3:
        render_kpi_card(
            "優先確認", "kpi-flag-risk", high_risk_document_count, "高リスク未対応書類・記録件数",
            "未提出・未作成、未承認、AI下書き未確認、計画書・記録の不一致/未入力候補、"
            "署名・確認漏れのいずれかを含む未対応書類・記録の数です。",
        )

    with col4:
        render_kpi_card(
            "完了", "kpi-flag-ok", confirmed_document_count, "確認済み書類・記録件数",
            "検知されたアラートがすべて職員確認済みになった書類・記録の数",
        )

    with col5:
        render_kpi_card(
            "対象", "kpi-flag-info", affected_subjects, "対象利用者・職員・事業所数",
            "未対応アラートの対象数",
        )

    if high_risk_document_count > 0:
        st.write("**高リスク未対応書類・記録件数の内訳（分野別）**")
        bucket_cols = st.columns(len(HIGH_RISK_BUCKET_ORDER))
        for col, bucket_name in zip(bucket_cols, HIGH_RISK_BUCKET_ORDER):
            with col:
                bucket_unit_count = unresolved_df.loc[
                    unresolved_df["high_risk_bucket"] == bucket_name, "document_unit_key"
                ].nunique()
                st.metric(bucket_name, int(bucket_unit_count))

    if not unresolved_df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("分野別の未対応書類・記録件数")
            unit_by_category = (
                unresolved_df.drop_duplicates("document_unit_key").groupby("category")["document_unit_key"].nunique()
            )
            st.bar_chart(unit_by_category, horizontal=True)
        with col_b:
            st.subheader("アラート種別ごとの詳細アラート件数")
            st.bar_chart(unresolved_df["alert_type"].value_counts(), horizontal=True)
        st.caption(
            "「アラート種別ごとの詳細アラート件数」はアラート行数ベースの内訳です。"
            "1つの書類・記録に複数のアラートが検知される場合があるため、"
            "上記の「未対応書類・記録件数」とは合計が一致しません。"
        )

    with st.expander("詳細アラート件数・定義を見る"):
        st.write(f"詳細アラート行数（未対応）：{len(unresolved_df)}件")
        st.write(
            "高リスク未対応とは、運営指導時に確認リスクが高い可能性がある未対応項目です。"
            "本MVPでは、未提出・未作成、未承認、AI下書き未確認、"
            "訪問介護計画書と日々の記録のレ点内容に関する不一致候補・未入力候補、"
            "署名・承認者未確認（確認漏れ）を高リスク未対応として扱います。"
        )
        st.caption("いずれも「誤り」の断定ではなく、職員確認が必要な候補として扱います。")

    with st.expander("検知対象の例"):
        st.markdown(
            """
            - サービス提供・記録関連（訪問介護計画書・サービス提供記録・モニタリング記録・担当者会議記録・苦情処理記録）
            - 利用者・契約関連（重要事項説明書・利用契約書・個人情報同意書・居宅サービス計画書）
            - 人員・勤務体制関連（勤務形態一覧表・出勤簿・資格証・研修記録）
            - 運営・その他関連（感染症対策マニュアル・緊急時対応マニュアル）
            """
        )
        st.caption(
            "詳細な検知対象は「使い方・業務フロー」の「このアプリが検知する主な書類・記録」を確認してください。"
        )

    st.subheader("本MVPで確認できること")
    st.markdown(
        """
        - 4分野15書類・記録カタログに基づく、未作成・未承認・期限切れなどの書類ステータス確認
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

    if "_pending_alert_user_filter" in st.session_state:
        st.session_state["alert_list_user_filter"] = st.session_state.pop("_pending_alert_user_filter")

    alert_df = build_document_alert_list()

    if alert_df.empty:
        st.success("現在、検知されているアラートはありません。")
    else:
        demo_rows = alert_df[alert_df["is_demo"] & ~alert_df["confirmed"]]
        if not demo_rows.empty:
            demo_row = demo_rows.iloc[0]
            with st.container(border=True):
                st.markdown(
                    '<span class="demo-card-badge">DEMO</span>'
                    '<div class="demo-card-title">サービス提供記録 AI補填体験</div>'
                    f'<div class="demo-card-meta">{demo_row["user_key"]} ／ サービス提供記録</div>'
                    '<div class="demo-card-meta">アラート：レ点未入力候補＋特記事項不足＋サービス区分との不一致候補</div>'
                    f'<div class="demo-card-meta">重要度：{demo_row["severity"]}</div>'
                    '<div class="demo-feature-row">'
                    '<span class="demo-feature-chip">Before / Afterで体験</span>'
                    '<span class="demo-feature-chip">不足レ点・不一致候補を確認</span>'
                    '<span class="demo-feature-chip">特記事項AI下書き候補を確認</span>'
                    '<span class="demo-feature-chip">職員確認・監査ログまで確認</span>'
                    "</div>",
                    unsafe_allow_html=True,
                )
                st.caption("この行は、レ点チェックと特記事項AI補填の流れを確認するためのデモ用サンプルです。")
                if st.button("▶ R011のBefore/Afterデモを開く", type="primary", key="demo_row_button"):
                    go_to_detail("daily_record", DEMO_RECORD_ID, DEMO_RECORD_USER)
            st.divider()

        unresolved_df = get_unresolved_alerts(alert_df)
        user_card_df = unresolved_df[~unresolved_df["is_demo"]]

        if not user_card_df.empty:
            st.subheader("利用者別の未対応状況")
            for user_key, group in user_card_df.groupby("user_key"):
                high_risk_in_group = int(group["alert_type"].apply(classify_high_risk_bucket).notna().sum())
                with st.container(border=True):
                    st.markdown(f"**{group.iloc[0]['subject_label']}**")
                    badge_html = status_badge_html("未対応") + f" {len(group)}件"
                    if high_risk_in_group > 0:
                        badge_html += "&nbsp;&nbsp;" + status_badge_html("高リスク") + f" {high_risk_in_group}件"
                    st.markdown(badge_html, unsafe_allow_html=True)
                    for _, row in group.head(3).iterrows():
                        st.write(f"- {row['document_name']}：{row['alert_type']}")
                    if st.button("この利用者の未対応を確認する", key=f"user_card_button_{user_key}"):
                        st.session_state["_pending_alert_user_filter"] = user_key
                        st.rerun()
            st.divider()

        with st.expander("詳細表を表示", expanded=False):
            show_confirmed = st.checkbox("確認済みも表示する", value=False, key="alert_list_show_confirmed")
            working_df = alert_df if show_confirmed else alert_df[~alert_df["confirmed"]]

            filter_col0, filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(5)
            with filter_col0:
                user_options = ["すべて"] + sorted(alert_df["user_key"].dropna().astype(str).unique().tolist())
                selected_user = st.selectbox("利用者IDで絞り込み", user_options, key="alert_list_user_filter")
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
            if selected_user != "すべて":
                filtered_df = filtered_df[filtered_df["user_key"].astype(str) == selected_user]
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

            # alert_keyでの特定を安定させるため、フィルタ・並び替え後のfiltered_dfの位置(0始まり)と
            # alert_keyを対応付ける辞書を持つ。st.dataframeの行選択イベントはこの位置番号を返すが、
            # 実際の対象特定・保存・遷移は必ずalert_keyを介して行う。
            position_to_alert_key = {i: row["alert_key"] for i, row in filtered_df.iterrows()}

            table_state = st.dataframe(
                display_df[display_columns].rename(columns=rename_map),
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key="alert_list_table",
            )

            selected_alert_key = None
            selected_rows = []
            try:
                selected_rows = table_state.selection.rows
            except AttributeError:
                selected_rows = []

            if selected_rows:
                selected_alert_key = position_to_alert_key.get(selected_rows[0])

            if selected_alert_key is None and not filtered_df.empty:
                label_to_alert_key = {
                    f"{row['user_key']} ／ {row['document_name']} ／ {row['alert_type']} ／ 重要度:{row['severity']}": row["alert_key"]
                    for _, row in filtered_df.iterrows()
                }
                selected_label = st.selectbox(
                    "確認するアラートを選択（利用者ID／書類名／アラート理由／重要度）",
                    list(label_to_alert_key.keys()),
                    key="alert_list_detail_select",
                )
                selected_alert_key = label_to_alert_key[selected_label]

            if selected_alert_key is not None:
                match = filtered_df[filtered_df["alert_key"] == selected_alert_key]
                if not match.empty:
                    selected_row = match.iloc[0]
                    if st.button("▶ この書類の全体図を確認する", type="primary", key="alert_list_detail_button"):
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

    if sel_source_type in ("daily_record", "checklist") and str(sel_target_id) == DEMO_RECORD_ID:
        st.title("サービス提供記録（デモ）")
        demo_saved = render_demo_service_record(related_rows)
        # related_rowsは保存前の状態で取得済みのため、保存直後の同一実行ではconfirmed列が
        # まだFalseのままになっている。demo_savedで同一実行分を、confirmed列で以降の再実行分
        # （「次の未対応書類へ進む」等のボタン押下によるrerun）をそれぞれカバーする。
        demo_is_confirmed = not related_rows.empty and bool(related_rows["confirmed"].all())
        show_demo_after_buttons = demo_saved or (demo_is_confirmed and not st.session_state.get("demo_edit_mode"))
        if show_demo_after_buttons:
            st.divider()
            after_col1, after_col2, after_col3 = st.columns(3)
            with after_col1:
                if st.button("次の未対応書類へ進む", type="primary", key="demo_after_save_next"):
                    fresh_alert_df = build_document_alert_list()
                    fresh_unresolved = get_unresolved_alerts(fresh_alert_df)
                    if not fresh_unresolved.empty:
                        nxt = fresh_unresolved.iloc[0]
                        go_to_detail(nxt["source_type"], nxt["target_id"], nxt["user_key"])
                    else:
                        request_navigation("確認履歴・監査ログ")
                        st.rerun()
            with after_col2:
                if st.button("確認履歴・監査ログへ移動", key="demo_after_save_history"):
                    request_navigation("確認履歴・監査ログ")
                    st.rerun()
            with after_col3:
                if st.button("書類アラート一覧へ戻る", key="demo_after_save_back"):
                    request_navigation("書類アラート一覧")
                    st.rerun()
        st.stop()

    primary_row = related_rows.iloc[0]
    document_name = primary_row["document_name"]
    category = primary_row["category"]
    subject_label = primary_row["subject_label"]
    ai_fillable = bool(related_rows["ai_fillable"].any())
    checklist_target = bool(related_rows["checklist_target"].any())

    saved_this_run = False
    paper_container = st.container(border=True)

    with paper_container:
        render_paper_header(
            document_name,
            {
                "対象": subject_label,
                "分野": category,
                "AI補填対象": "はい" if ai_fillable else "いいえ",
                "レ点チェック対象": "はい" if checklist_target else "いいえ",
                "確認状態": "確認済み" if primary_row["confirmed"] else "未対応",
            },
        )
        st.markdown(
            status_badge_html("職員確認済み" if primary_row["confirmed"] else "未対応"),
            unsafe_allow_html=True,
        )

        st.write("**アラート理由・必要な職員対応：**")
        for _, r in related_rows.iterrows():
            st.write(f"- 〔{r['alert_type']}〕{r['alert_reason']}")

    # --- AI補填対象・中身データがある書類（サービス提供記録：日々の記録／レ点チェック） ---
    if sel_source_type in ("daily_record", "checklist"):
        draft_key_prefix = "detail_daily"
        context = get_draft_context("daily_record", sel_target_id)

        daily_df = load_csv(DATA_DIR / "daily_records.csv")
        daily_df = ensure_columns(daily_df, ["time_slot", "service_category"])
        record_match = daily_df[daily_df["record_id"].astype(str) == str(sel_target_id)]
        record_row = record_match.iloc[0] if not record_match.empty else None

        care_plans_df = load_csv(DATA_DIR / "care_plans.csv")
        care_plans_df = ensure_columns(care_plans_df, ["visit_days", "time_slot", "service_category"])
        plan_row = None
        if record_row is not None and not care_plans_df.empty:
            plan_match = care_plans_df[care_plans_df["user_id"] == record_row.get("user_id")]
            if not plan_match.empty:
                plan_row = plan_match.iloc[0]

        with paper_container:
            if record_row is not None:
                st.divider()
                st.subheader("基本情報")
                base_col1, base_col2 = st.columns(2)
                with base_col1:
                    st.write(f"**利用者**：{subject_label}")
                    st.write(f"**提供日時**：{record_row.get('record_date')}（{get_japanese_weekday(record_row.get('record_date'))}曜日）")
                    st.write(f"**サービス区分**：{record_row.get('service_category') or 'データなし'}")
                with base_col2:
                    st.write(f"**提供時間**：{record_row.get('time_slot') or 'データなし'}")
                    st.write(f"**職員名**：{record_row.get('staff_name')}")
                    st.write("**事業所**：Care Compliance Copilot デモ事業所")
                    st.write("**サービス名**：訪問介護")

                taxonomy = get_field_taxonomy()
                classified_items = classify_service_items(str(record_row.get("service_items", "") or ""))
                matched_field_names = {m["field_name"] for m in classified_items}

                st.divider()
                st.subheader("共通・状態確認")
                common_value_map = {
                    "バイタル": record_row.get("numeric_data"),
                    "その他": record_row.get("follow_up"),
                }
                common_rows_html = ""
                for field_name in taxonomy.get("共通・状態確認", []):
                    value = common_value_map.get(field_name)
                    status_label = "記載済み" if value and str(value).strip() else "未記載"
                    common_rows_html += (
                        f'<div style="display:flex;justify-content:space-between;padding:3px 0;">'
                        f'<span>{field_name}</span><span>{value or "データなし"} {status_badge_html(status_label)}</span></div>'
                    )
                st.markdown(common_rows_html, unsafe_allow_html=True)

                st.divider()
                st.subheader("身体介護")
                physical_rows_html = ""
                for field_name in taxonomy.get("身体介護", []):
                    status_label = "記載済み" if field_name in matched_field_names else "未記載"
                    physical_rows_html += (
                        f'<div style="display:flex;justify-content:space-between;padding:3px 0;">'
                        f'<span>{field_name}</span><span>{status_badge_html(status_label)}</span></div>'
                    )
                st.markdown(physical_rows_html, unsafe_allow_html=True)

                st.divider()
                st.subheader("生活援助")
                life_rows_html = ""
                for field_name in taxonomy.get("生活援助", []):
                    status_label = "記載済み" if field_name in matched_field_names else "未記載"
                    life_rows_html += (
                        f'<div style="display:flex;justify-content:space-between;padding:3px 0;">'
                        f'<span>{field_name}</span><span>{status_badge_html(status_label)}</span></div>'
                    )
                st.markdown(life_rows_html, unsafe_allow_html=True)

                st.divider()
                st.subheader("特記事項")
                st.write(f"**現在の特記事項**：{record_row.get('special_notes') or '（未記載）'}")
                st.markdown(
                    status_badge_html("AI補填対象" if not str(record_row.get("special_notes", "")).strip() else "記載済み"),
                    unsafe_allow_html=True,
                )

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

            if record_row is not None and plan_row is not None:
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
                        st.markdown(
                            f"- 〔{ca['alert_type']}〕{ca['alert_reason']} {status_badge_html('要確認')}",
                            unsafe_allow_html=True,
                        )

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
            else:
                unresolved_checklist = related_rows[
                    (related_rows["source_type"] == "checklist") & (~related_rows["confirmed"])
                ]
                if plan_row is None:
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
                if plan_row is not None:
                    st.write(f"**ケアプラン上の支援内容**：{plan_row.get('service_content')}")
                    st.write(f"**計画書のサービス区分／時間帯**：{plan_row.get('service_category')} ／ {plan_row.get('time_slot')}")
                for _, r in related_rows.iterrows():
                    st.write(f"- 〔{r['alert_type']}〕{r['alert_reason']}")

            # --- 保存前確認 ---
            st.divider()
            st.subheader("保存前確認")
            unfilled_candidates = related_rows[
                related_rows["alert_type"].isin(["レ点未入力候補", "計画書との不一致候補"])
            ]
            review_needed = related_rows[~related_rows["confirmed"]]

            st.write(f"**未入力候補**：{len(unfilled_candidates)}件")
            st.write(f"**要確認項目**：{len(review_needed)}件")
            st.write(
                f"**AI補填後の特記事項**：{context['row'][context['draft_col']] if context is not None else '（下書きなし）'}"
            )
            st.write(f"**計画書連動レ点チェック結果**：{len(unresolved_checklist)}件が未確認です")
            st.warning("この内容はAI下書き・候補であり、確定前に職員確認が必要です。")

            if not unresolved_checklist.empty:
                st.write("**レ点チェックの職員確認：**")
                checklist_reviewed_text = st.text_area(
                    "確認コメント（任意）", value="", key="detail_checklist_review_text"
                )
                checklist_reviewed_by = st.text_input("確認者名", value="サ責A", key="detail_checklist_review_by")
                checklist_confirmed = st.checkbox(
                    "計画書との不一致候補・レ点候補を確認しました。", key="detail_checklist_review_confirm"
                )
                if st.button("職員確認済みにする（レ点チェック）", type="primary", key="detail_checklist_review_save"):
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

    # --- AI補填対象・中身データがある書類（月間モニタリング） ---
    elif sel_source_type == "monitoring_record":
        context = get_draft_context("monitoring_record", sel_target_id)
        monitoring_df = load_csv(DATA_DIR / "monitoring_records.csv")
        record_match = monitoring_df[monitoring_df["monitoring_id"].astype(str) == str(sel_target_id)]
        record_row = record_match.iloc[0] if not record_match.empty else None

        with paper_container:
            if record_row is not None:
                st.divider()
                st.subheader("書類全体図（記載状況）")
                field_status = [
                    ("evaluation", "総合評価", "記載済み" if str(record_row.get("evaluation", "")).strip() else "不足", True),
                    ("status_change", "状態変化", "記載済み" if str(record_row.get("status_change", "")).strip() else "未記載", False),
                    ("goal_evaluation", "ケアプラン目標評価", "記載済み" if str(record_row.get("goal_evaluation", "")).strip() else "未記載", False),
                    ("future_action", "今後の対応", "記載済み" if str(record_row.get("future_action", "")).strip() else "未記載", False),
                    ("approved", "承認状態", "承認済み" if bool(record_row.get("approved")) else "未承認", False),
                ]
                field_rows_html = ""
                for _, label, status, ai_flag in field_status:
                    field_rows_html += (
                        f'<div style="display:flex;justify-content:space-between;padding:3px 0;">'
                        f'<span>{label}</span><span>{status_badge_html(status)} '
                        f'{status_badge_html("AI補填対象" if ai_flag else "AI補填対象外")}</span></div>'
                    )
                st.markdown(field_rows_html, unsafe_allow_html=True)

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
        with paper_container:
            ai_reason = primary_row.get("ai_reason", "")
            if ai_fillable:
                st.info(
                    "この書類はAI補填対象カタログに含まれますが、本MVPでは中身データを保持していないため、"
                    "ステータス確認のみ可能です。AI下書きは生成しません。"
                )
                st.markdown(status_badge_html("AI補填対象"), unsafe_allow_html=True)
            else:
                st.info("この書類はAI補填対象外です。")
                st.markdown(status_badge_html("AI補填対象外"), unsafe_allow_html=True)
                if ai_reason:
                    st.write(f"**AIで補填できない理由**：{ai_reason}")

            st.write(f"**必要な職員対応**：{primary_row['shortage_detail']}")

            samples_df = get_document_detail_samples()
            document_samples = samples_df[samples_df["document_type"] == document_name] if not samples_df.empty else pd.DataFrame()

            if not document_samples.empty:
                st.divider()
                st.subheader("書類全体図（紙面モックアップ）")
                st.caption("MVPデモ用のダミーデータです。実在の書類ではありません。")
                for section in document_samples["section"].drop_duplicates():
                    st.markdown(f"**{section}**")
                    section_rows = document_samples[document_samples["section"] == section]
                    section_html = ""
                    for _, field_row in section_rows.iterrows():
                        value = field_row.get("current_value")
                        status_label = field_row.get("status") or "記載済み"
                        section_html += (
                            f'<div style="display:flex;justify-content:space-between;padding:3px 0;">'
                            f'<span>{field_row.get("field_name")}</span>'
                            f'<span>{value or "（未記入）"} {status_badge_html(status_label)}</span></div>'
                        )
                    st.markdown(section_html, unsafe_allow_html=True)

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
    st.info(
        "確認キューは、未対応のアラート書類を順番に処理するための作業リストです。"
        "書類アラート一覧が全体確認用であるのに対し、この画面では職員が確認すべき未対応タスクだけを並べています。"
        "実際の確認・修正・保存は、各タスクの「詳細へ」から書類詳細画面で行います。"
    )

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
        review_status = row.get("review_status")
        # 確認済み記録の修正（review_status="revised"）は、通常のdaily_record確認とは
        # 別のrecord_typeとして扱い、タイムラインで「修正しました」の表示・専用bulletに分ける。
        is_revision_row = review_status == "revised"
        history_rows.append(
            {
                "record_type": "revision" if is_revision_row else "daily_record",
                "target_id": row.get("record_id"),
                "user_id": row.get("user_id"),
                "document_name": "サービス提供記録",
                "alert_type": None,
                "detail": None,
                "review_status": review_status,
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
                "document_name": "モニタリング記録",
                "alert_type": None,
                "detail": None,
                "review_status": row.get("review_status"),
                "reviewed_text": row.get("reviewed_text"),
                "reviewed_by": row.get("reviewed_by"),
                "reviewed_at": row.get("reviewed_at"),
                "confirmed_via": "月間モニタリングAI下書き / 書類詳細・AI補填プレビュー / 職員確認済み保存",
            }
        )

    for _, row in queue_log_df.iterrows():
        alert_key = str(row.get("alert_key") or "")
        alert_type = alert_key.split("|")[-1] if alert_key else None
        history_rows.append(
            {
                "record_type": row.get("record_type"),
                "target_id": row.get("target_id"),
                "user_id": row.get("user_id"),
                "document_name": row.get("document_name") or "書類",
                "alert_type": alert_type,
                "detail": row.get("detail"),
                "review_status": row.get("review_status"),
                "reviewed_text": row.get("reviewed_text") or row.get("detail"),
                "reviewed_by": row.get("reviewed_by"),
                "reviewed_at": row.get("reviewed_at"),
                "confirmed_via": "確認キュー / 書類詳細・AI補填プレビュー",
            }
        )

    history_df = pd.DataFrame(history_rows)

    if history_df.empty:
        st.info("まだ確認履歴はありません。書類詳細画面で『職員確認済みにする』を押すと、ここに確認履歴が追加されます。")
    else:
        events = build_history_events(history_df)

        st.subheader("確認履歴タイムライン")
        for i, event in enumerate(events):
            is_revision_event = bool((event["rows"]["record_type"] == "revision").all())
            action_label = "を修正しました" if is_revision_event else "を確認済みにしました"
            content_label = "修正内容：" if is_revision_event else "確認内容："
            with st.container(border=True):
                st.write(f"**{event['reviewed_at']}**")
                st.write(f"{event['reviewed_by']} が {event['document_name']} {event['target_id']} {action_label}")
                st.write(f"対象利用者：{event['user_id']}")
                st.write(content_label)
                for bullet in event["bullets"]:
                    st.write(f"- {bullet}")
                with st.expander("詳細を見る"):
                    st.dataframe(event["rows"].drop(columns=["_time_key"], errors="ignore"), use_container_width=True)

                if str(event["target_id"]) == DEMO_RECORD_ID and not is_revision_event:
                    view_col, edit_col = st.columns(2)
                    with view_col:
                        if st.button("この確認済み記録の全体図を見る", key=f"history_view_demo_{i}"):
                            st.session_state.selected_source_type = "daily_record"
                            st.session_state.selected_target_id = DEMO_RECORD_ID
                            st.session_state.selected_user_key = DEMO_RECORD_USER
                            st.session_state["demo_edit_mode"] = False
                            request_navigation("書類詳細・AI補填プレビュー")
                            st.rerun()
                    with edit_col:
                        if st.button("この確認済み記録を修正する", key=f"history_edit_demo_{i}"):
                            st.session_state.selected_source_type = "daily_record"
                            st.session_state.selected_target_id = DEMO_RECORD_ID
                            st.session_state.selected_user_key = DEMO_RECORD_USER
                            st.session_state["demo_edit_mode"] = True
                            request_navigation("書類詳細・AI補填プレビュー")
                            st.rerun()

        st.divider()

        with st.expander("詳細ログCSVを表示", expanded=False):
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
