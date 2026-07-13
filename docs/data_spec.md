# データ仕様

本MVPでは、実在個人情報を含まないデモ用CSVのみを使用しています。

## 入力データ（`data/`）

### `users.csv`

利用者情報を保持します。

### `care_plans.csv`

ケアプラン情報を保持します。`service_content`に加え、`visit_days`・`time_slot`・`service_category`を用いて、日々の記録との突合（曜日・時間帯・サービス区分の不一致検知）に使います。

### `daily_records.csv`

日々の介護記録を保持します。`record_id`・`user_id`・`service_items`・`special_notes`・`user_quote`・`observation`・`numeric_data`・`follow_up`・`time_slot`・`service_category`などを、特記事項AI補填・計画書連動レ点チェックに使います。

### `monitoring_records.csv`

月間モニタリング記録を保持します。

### `document_status.csv`

4分野15書類・記録カタログに基づき、書類ステータス（`required`・`file_exists`・`valid_from`・`valid_to`・`approved`・`approved_by`）を保持します。勤務形態一覧表・出勤簿・資格証・研修記録は職員（`user_id`列に`職員A`等）、感染症対策マニュアル等は事業所全体（`user_id`列に`ORG`）に紐づくサンプル行として表現しています。

#### 4分野15書類・記録カタログ

**サービス提供・記録関連**
* 訪問介護計画書
* サービス提供記録
* モニタリング記録
* 担当者会議記録
* 苦情処理記録

**利用者・契約関連**
* 重要事項説明書
* 利用契約書
* 個人情報同意書
* 居宅サービス計画書

**人員・勤務体制関連**
* 勤務形態一覧表
* 出勤簿
* 資格証
* 研修記録

**運営・その他関連**
* 感染症対策マニュアル
* 緊急時対応マニュアル

担当者会議記録・研修記録・苦情処理記録はカタログ上「AI補填対象」に分類していますが、本MVPでは中身データを保持していないため、書類詳細画面ではステータス確認のみとしています。

### `document_detail_samples.csv`（書類全体図の紙面表示用データ）

書類詳細・AI補填プレビュー画面の「紙面風UI」で使う、MVPデモ用のダミーデータです。実在の利用者・書類の内容ではありません。

列構成：`document_id, document_type, section, field_name, current_value, status, ai_fillable, suggested_value, evidence, care_category`

* **サービス提供記録**：`section`（共通・状態確認／身体介護／生活援助）と`field_name`の構成（型）のみを定義するテンプレート行です。実際の値・状態は選択した`daily_records.csv`の記録から動的に判定して表示します（キーワード部分一致によるルールベース判定で、AIによる判定ではありません）。清掃・洗濯・衣類/寝具・調理・買物等は必ず生活援助側、排泄・食事・入浴・清拭・身体整容・移動・起床/就寝・服薬/医療・自立支援・声掛け/見守りは必ず身体介護側に分類し、UI上も明確な区切り線で分けています。
* **重要事項説明書・変更同意書／出勤簿／感染症対策マニュアル／資格証／利用契約書**：中身データを持たない書類のため、`document_id`ごとに全項目の値をこのCSVで保持し、そのまま紙面表示します。重要事項説明書・変更同意書の構成（基本情報・変更内容・料金変更・衛生管理等・業務継続計画・同意確認・職員確認）は、一般的な書類構造を参考にしたサンプルであり、特定の実在書類の文面を複製したものではありません。これらの書類はいずれも契約・同意・署名・資格・勤務実績に関わるため、**AI補填対象外**として扱い、理由（事実確認が必要なため職員が原本を確認する必要がある旨）を明示しています。

## 出力データ（`outputs/`）

Notebook実行後、または`app.py`（Streamlit版）の操作後に、`outputs/`以下に以下のCSVが生成されます。

| ファイル名 | 内容 |
| ----- | ----- |
| `alerts_integrated.csv` | 統合アラート一覧 |
| `alert_summary_by_user.csv` | 利用者別・状態別アラート集計 |
| `daily_records_with_ai_note_draft.csv` | 特記事項AI補填案入りの日々の記録 |
| `daily_records_note_reviewed.csv` | 職員確認済みの日々の記録 |
| `monitoring_records_with_ai_draft.csv` | 月間モニタリングAI下書き入り記録 |
| `monitoring_records_reviewed.csv` | 職員確認済みのモニタリング記録 |
| `confirmation_queue_log.csv` | 誰が・いつ・どの書類/アラートを確認したかを記録する統一ログ |

`outputs/`は実行のたびに内容が更新・追記される作業ディレクトリのため、Git管理からは除外しています（`outputs/.gitkeep`のみ追跡）。出力イメージを確認したい場合は、固定サンプルを置いた`sample_outputs/`を参照してください。

`sample_outputs/daily_records_note_reviewed.csv`・`sample_outputs/monitoring_records_reviewed.csv`・`sample_outputs/confirmation_queue_log.csv`は、列構成（ヘッダー）のみを保持しデータ行は空にしています。これは、GitHub公開直後・クローン直後の「確認履歴・監査ログ」が意図的に0件から始まり、デモ用サービス提供記録（R011）を確認・保存する操作前後の違いが分かりやすくなるようにするためです。
