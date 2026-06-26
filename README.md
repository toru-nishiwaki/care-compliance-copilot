# Care Compliance Copilot

訪問介護事業所における運営指導前の書類確認業務を支援する、コンプライアンス確認AI支援MVPです。

本プロジェクトでは、利用者情報・ケアプラン・日々の介護記録・モニタリング記録・書類ステータスをCSVで読み込み、未作成・未確認・未承認の書類や記録を検出します。
また、必要に応じてAI下書き候補を生成し、職員が確認・修正したうえで「職員確認済み」として保存する業務フローを検証しています。

## 背景

訪問介護事業所では、運営指導前に以下のような書類確認が必要になります。

* 訪問介護計画書が有効期間内に作成されているか
* 月間モニタリング記録が作成・確認されているか
* 日々の介護記録に不足や未確認がないか
* 必要な特記事項や補足記録が残されているか
* 書類の未作成・未確認・未承認が放置されていないか

これらの確認は人手に依存しやすく、確認漏れや書類不備が発生しやすい業務です。
本MVPでは、CSVデータをもとに書類不備リスクを検出し、AIが下書きや確認候補を提示することで、職員の確認業務を支援する仕組みを検証しました。

## 目的

本プロジェクトの目的は、AIが介護記録や書類を自動確定することではありません。

AIはあくまで以下を支援します。

* 書類不備の検出
* 状態別アラートの作成
* 特記事項・補足記録の下書き生成
* 月間モニタリング文書の下書き生成
* 職員確認が必要な項目の可視化

最終判断と確定保存は、必ず職員が行う前提です。

## 主な機能

### 1. 書類ステータス確認

利用者ごとの書類状態を確認し、以下のようなリスクを検出します。

* 未作成
* 未確認
* 未承認
* 有効期間外
* モニタリング記録の不足

### 2. 統合アラート作成

複数のCSVデータを横断して確認し、利用者別・書類別にアラートを作成します。

出力例：

* `alerts_integrated.csv`
* `alert_summary_by_user.csv`

### 3. 日々の介護記録に対するAI下書き生成

日々の介護記録から、特記事項や補足が必要な可能性がある記録を抽出し、AI下書き候補を生成します。

職員が確認・修正したうえで、確認済みデータとして保存する想定です。

出力例：

* `daily_records_with_ai_note_draft.csv`
* `daily_records_note_reviewed.csv`

### 4. 月間モニタリング文書の下書き生成

ケアプランと日々の介護記録をもとに、月間モニタリング文書の下書きを生成します。

下書き作成時には、以下を重視しています。

* 記録にない内容を推測で追加しない
* 医学的な診断を行わない
* 状態変化がある場合は根拠日を明記する
* 情報が不足している場合は不足事項として明記する
* 職員確認・修正を前提にする

出力例：

* `monitoring_records_with_ai_draft.csv`
* `monitoring_records_reviewed.csv`

## 本MVPで検証した業務フロー

1. 利用者情報・ケアプラン・日々の介護記録・書類ステータスをCSVで読み込む
2. 書類の不足・未確認・未承認を検出する
3. 利用者別にアラートを作成する
4. 必要に応じてAI下書き候補を生成する
5. 職員が下書きを確認・修正する
6. 確認済みデータとして保存する
7. 最終チェックでMVP全体の処理結果を確認する

## フォルダ構成

```txt
care-compliance-copilot/
├── README.md
├── requirements.txt
├── data/
│   ├── users.csv
│   ├── care_plans.csv
│   ├── daily_records.csv
│   ├── monitoring_records.csv
│   └── document_status.csv
├── notebook/
│   └── care_compliance_copilot_mvp.ipynb
└── outputs/
    ├── alerts_integrated.csv
    ├── alert_summary_by_user.csv
    ├── daily_records_with_ai_note_draft.csv
    ├── daily_records_note_reviewed.csv
    ├── monitoring_records_with_ai_draft.csv
    └── monitoring_records_reviewed.csv
```

## Notebook

MVPの処理内容は以下のNotebookで確認できます。

* [care_compliance_copilot_mvp.ipynb](notebook/care_compliance_copilot_mvp.ipynb)

## 使用技術

* Python
* pandas
* Jupyter Notebook
* CSV
* Streamlit

## セットアップ

必要なライブラリは `requirements.txt` に記載しています。

```bash
pip install -r requirements.txt
```

## 実行方法

1. `data/` フォルダにCSVファイルを配置する
2. `notebook/care_compliance_copilot_mvp.ipynb` を開く
3. Notebookを上から順に実行する
4. `outputs/` フォルダに出力されたCSVを確認する

## 出力ファイル

| ファイル名                                  | 内容                    |
| -------------------------------------- | --------------------- |
| `alerts_integrated.csv`                | 書類不備・未確認・未承認などの統合アラート |
| `alert_summary_by_user.csv`            | 利用者別のアラート集計           |
| `daily_records_with_ai_note_draft.csv` | 日々の介護記録に対するAI下書き候補    |
| `daily_records_note_reviewed.csv`      | 職員確認済みの日々の介護記録        |
| `monitoring_records_with_ai_draft.csv` | 月間モニタリング文書のAI下書き      |
| `monitoring_records_reviewed.csv`      | 職員確認済みの月間モニタリング記録     |

## 設計上のポイント

本MVPでは、AIによる自動確定ではなく、職員確認を前提とした運用設計を重視しています。

介護記録やモニタリング文書は、利用者の状態やサービス提供内容に関わる重要な記録です。
そのため、AIは記録作成を代替するのではなく、確認漏れの防止や下書き作成を支援する位置づけとしています。

## 今後の拡張案

* 任意書類・任意期限に対するアラート設定
* 職員確認済み保存フローの画面化
* Streamlitによる簡易UI実装
* 既存介護ソフトから出力したCSVとの連携
* 書類別・利用者別のリスクダッシュボード
* 管理者向けの確認状況レポート

## 注意事項

※ 本リポジトリ内のCSVデータは、ポートフォリオ検証用に作成したサンプルデータです。実在の利用者情報は含みません。

本プロジェクトは、ポートフォリオ用に作成したMVPです。
実運用を想定する場合は、個人情報保護、アクセス権限管理、監査ログ、職員承認フロー、既存介護ソフトとの連携設計が必要です。

また、AIが生成した文章はそのまま確定記録として使用せず、必ず職員が確認・修正する前提です。
