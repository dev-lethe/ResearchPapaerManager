# Research Paper Manager

論文PDFの管理・閲覧と、Markdownによる読書メモをひとつの画面で行える、個人向けのセルフホスト型Webアプリケーションです。

PDFとメモは手元のストレージに保存されます。DOIからの書誌情報取得、キーワードによる分類、メモ本文を含む検索に対応しています。

MITライセンスで公開しており、自分の環境で利用・改変できます。ライセンス全文は [LICENCE](LICENCE) を参照してください。

**現在のアプリにはログイン機能がありません。** 各利用者が自分の環境で動かす個人向けアプリです。標準設定では同じ端末からのみアクセスできます。インターネットに公開して利用する場合は、別途認証とアクセス制御を整える必要があります。

## 主な機能

- **論文の登録** — PDFをアップロードし、タイトル・著者・発表年・会議名／雑誌名などを入力できます。
- **DOIからの情報取得** — Crossrefから書誌情報を取得し、内容を確認・編集して登録できます。
- **検索と絞り込み** — タイトル・著者・DOI・キーワード・メモ本文を検索し、年・発表先・キーワードで絞り込めます。
- **PDFとメモの同時表示** — PDFを読みながらMarkdownメモを編集できます。メモは自動保存され、プレビューに切り替えられます。
- **書誌情報の編集** — 登録後も論文の詳細画面から情報を更新できます。
- **ローカル保存** — PDF、Markdownメモ、JSON形式の書誌情報をホスト側のディレクトリに保存します。

## クイックスタート

### 必要なもの

- Docker
- Docker Compose v2（`docker compose` コマンド）

Dockerで起動する場合、ホスト側にNode.jsやPythonをインストールする必要はありません。
初回ビルドでは、コンテナイメージと依存パッケージの取得にインターネット接続が必要です。
以下のコマンドは、リポジトリを取得した後、そのルートディレクトリで実行してください。

自分用にコードを変更する場合は、先にGitHubでこのリポジトリをForkし、自分のForkの「Code」に表示されるURLからクローンしてください。変更を保存する必要がない場合は、このリポジトリを直接クローンして利用できます。

### 1. 設定ファイルと保存先を用意する

```bash
cp .env.example .env
mkdir -p Paper Memo
```

`.env` を編集し、`POSTGRES_PASSWORD` と `DATABASE_URL` 内のパスワードを同じ値に変更します。
以下の `YOUR_DATABASE_PASSWORD` は、自分で用意した十分に長いパスワードに置き換えてください。

```dotenv
POSTGRES_PASSWORD=YOUR_DATABASE_PASSWORD
DATABASE_URL=postgresql+psycopg://paper_manager:YOUR_DATABASE_PASSWORD@postgres:5432/paper_manager
```

ユーザー名やデータベース名を変更する場合も、`DATABASE_URL` に反映してください。
パスワードにURLの予約文字を含める場合、`DATABASE_URL` 内ではパーセントエンコードが必要です。

### 2. 起動する

```bash
docker compose up --build -d
docker compose ps
```

初回はイメージのビルドが行われます。バックエンド起動時に、データベースのマイグレーションが自動実行されます。

### 3. ブラウザで開く

[http://127.0.0.1:8080](http://127.0.0.1:8080) にアクセスしてください。

起動状態やエラーは、次のコマンドで確認できます。

```bash
docker compose logs -f backend frontend caddy
```

停止する場合は次を実行します。PDF・メモ・データベースはホスト側に保存されるため、コンテナを停止・削除しても残ります。

```bash
docker compose down
```

## 使い方

1. **論文を追加する**：ヘッダーの追加ボタンから「Add Paper」を開き、PDFを選択します。DOIがある場合は入力して「Autofill」を押すと書誌情報を取得できます。内容を確認して「Add Paper」で登録します。
2. **論文を探す**：Library画面で検索語、年、発表先、キーワードを指定します。複数のキーワードを指定した場合は、すべてを含む論文に絞り込みます。
3. **読んでメモを残す**：論文カードを開くと、PDFとメモが並んで表示されます。メモを編集したら「Saved」の表示を確認してください。切替ボタンでMarkdownのプレビューを表示できます。
4. **書誌情報を更新する**：論文詳細画面の設定ボタンから「Edit Metadata」を開き、変更後に「Save」を押します。

著者やキーワードを複数入力する場合は、カンマで区切ります。DOIの入力は任意です。Crossrefによる情報取得にはインターネット接続が必要です。

## 設定

設定項目のテンプレートは [.env.example](.env.example) にあります。

| 変数 | 用途 | 初期値・補足 |
| --- | --- | --- |
| `POSTGRES_DB` | データベース名 | `paper_manager` |
| `POSTGRES_USER` | データベースのユーザー名 | `paper_manager` |
| `POSTGRES_PASSWORD` | データベースのパスワード | 初回起動前に変更 |
| `DATABASE_URL` | バックエンドのDB接続先 | 上記の接続情報と一致させる |
| `HOST_PAPERS_PATH` | ホスト側のPDF保存先 | `./Paper` |
| `HOST_NOTES_PATH` | ホスト側のメモ・書誌情報保存先 | `./Memo` |
| `LOCAL_PAPERS_PATH` | コンテナ内のPDF保存先 | `/workspace/Paper` |
| `LOCAL_NOTES_PATH` | コンテナ内のメモ・書誌情報保存先 | `/workspace/Memo` |
| `CROSSREF_MAILTO` | Crossrefへのリクエストに含める連絡先メールアドレス | 任意 |
| `ENVIRONMENT` | 実行環境 | テンプレートでは `production`。APIドキュメントを無効化 |
| `ALLOWED_HOSTS` | バックエンドが受け付けるHost名 | `localhost,127.0.0.1,*.ts.net` |

ホスト側の保存先を変える場合は、`HOST_PAPERS_PATH` と `HOST_NOTES_PATH` を変更します。
`LOCAL_*` はコンテナ内のパスなので、通常は初期値のまま使用してください。変更する場合は [compose.yaml](compose.yaml) のマウント先も合わせる必要があります。

バックエンドはUID `1000` で動作します。特にLinuxでは、PDFとメモの保存先がこのユーザーから書き込み可能になっていることを確認してください。

データベースの初期化後にパスワードを変える場合は、`.env` の編集に加えて、PostgreSQL内のユーザーのパスワード変更も必要です。

## データの保存場所

標準設定では、次の場所にデータが保存されます。

```text
Paper/
  <paper-id>.pdf             # アップロードされたPDF
Memo/
  <paper-id>.md              # Markdownメモ（初めてメモを開いたときに作成）
  <paper-id>.meta.json       # 書誌情報・キーワード
data/research-manager/
  postgres/                 # PostgreSQLのデータ
  backups/                  # バックアップスクリプトの出力先
```

アップロードされたPDFにはUUIDのファイル名が付与されます。メモ・書誌情報は、対応するPDFと同じベース名で保存されます。
サブディレクトリにあるPDFについても、対応するメモは同じディレクトリ構造を使います。

`.env`、`Paper/`、`Memo/`、`data/` のユーザーデータは [.gitignore](.gitignore) でGitの追跡対象から除外しています。ただし、すでに追跡されているファイルと過去のコミットには適用されません。保存先をリポジトリ内の別のディレクトリに変更した場合は、その場所も `.gitignore` に追加してください。

## アクセス範囲

現在のアプリにはログイン機能がありません。個人利用を想定し、Composeの公開ポートは `127.0.0.1:8080` に限定しています。PostgreSQLのポートはホストに公開しません。

別の端末から利用する場合は、Tailscaleなどのプライベートネットワーク内で、利用者を制限してアクセスしてください。
認証を追加するまでは、ポートの外部公開やTailscale Funnelによるインターネットへの公開を避けてください。

アプリにアクセスできる人は、PDF・メモの閲覧や登録、メモ・書誌情報の変更ができます。`ALLOWED_HOSTS` は受け付けるHost名の制限であり、利用者の認証ではありません。プライベートネットワーク内でも、アクセスを自分の端末・アカウントに限定してください。

DOIによる書誌情報取得ではCrossrefへDOIを送信します。`CROSSREF_MAILTO` を設定した場合は、そのメールアドレスもリクエストに含まれます。PDF・メモの保存先はローカルですが、書誌情報取得には外部サービスを利用します。

## 自分用にカスタマイズする

Forkしたリポジトリで変更をコミットすると、自分の設定・機能の変更を管理できます。パスワードや個人の保存先などは `.env` に置き、コミットしないでください。

| 変更したい内容 | 主な変更先 |
| --- | --- |
| PDF・メモの保存先、DB接続情報 | [.env.example](.env.example) をコピーした `.env` |
| 画面全体の見た目 | [frontend/app/globals.css](frontend/app/globals.css) |
| Library画面 | [frontend/app/library/page.tsx](frontend/app/library/page.tsx)、[library.css](frontend/app/library/library.css) |
| PDF・メモの詳細画面 | [PaperDetailClient.tsx](frontend/app/papers/[id]/PaperDetailClient.tsx)、[paper-detail.css](frontend/app/papers/[id]/paper-detail.css) |
| 論文の登録・検索・API | [backend/app/api/v1/router.py](backend/app/api/v1/router.py)、`backend/app/services/` |
| 書誌情報の項目 | [backend/app/schemas/local_metadata.py](backend/app/schemas/local_metadata.py)、対応する入力画面・保存処理 |
| 公開ポート・マウント・コンテナ構成 | [compose.yaml](compose.yaml)、`docker/` |

変更後は、[開発・検証](#開発検証) のコマンドで確認してください。DBのスキーマを変更する場合は、Alembicのマイグレーションも用意します。

### 設定変更時の注意

- ホスト側の保存先を変えた場合は、新しいディレクトリを作成し、バックエンドのUID `1000` が書き込めるようにしてください。既存データは自動では移動されません。
- [バックアップスクリプト](scripts/backup.sh) の保存先は固定です。`HOST_PAPERS_PATH`・`HOST_NOTES_PATH` を変えた場合は、スクリプト内の `PAPERS_DIR`・`MEMOS_DIR` も合わせて変更してください。
- [メタデータ補修スクリプト](scripts/backfill_metadata_after_dedupe.sh) はコンテナ内の `/workspace/Paper`・`/workspace/Memo` を直接参照し、直下のPDFを対象に既存の書誌情報から不足項目を補います。コンテナ内の保存先を変えた場合は、このスクリプトも修正してください。実行前にバックアップしてください。
- 同じ端末で複数のコピーを起動する場合は、Composeの固定 `container_name` を削除または個別の名前に変更し、ホスト側のポートとPDF・メモ・DBの保存先も分けてください。別のComposeプロジェクト名を指定するだけでは、固定コンテナ名の衝突は解消されません。

### 現在の制限

- ログイン・利用者ごとの権限分離には対応していません。
- アップロードするPDFは1ファイル100 MiBまでです。プロキシの制限はリクエスト全体に適用されるため、上限付近のPDFは受け付けられない場合があります。
- Crossrefで取得できる情報には欠落や誤りがあり得ます。登録前に内容を確認してください。
- Docker Composeでの起動を基本としています。Linuxでは保存先の所有者・権限の確認が必要です。OSごとの動作保証や継続的なサポートはありません。
- 自動バックアップのスケジュール、保存先設定への自動追従、復元の自動化はありません。

## バックアップ

データベースが起動している状態で、次のコマンドを実行します。

```bash
./scripts/backup.sh
```

[バックアップスクリプト](scripts/backup.sh) は、PostgreSQLのSQLダンプ、`Paper/`、`Memo/` の圧縮アーカイブを `data/research-manager/backups/` に作成し、それぞれ直近7世代を保持します。

- 保存先をカスタマイズした場合は、スクリプト内の `PAPERS_DIR` と `MEMOS_DIR` も変更してください。
- DBのユーザー名・データベース名を変更した場合は、実行するシェルで `POSTGRES_USER` と `POSTGRES_DB` を設定してください。スクリプトはこれらを `.env` から自動読込しません。

整合性を保つため、バックアップ中はアップロードやメモ・書誌情報の編集を止めてください。バックアップはPDF・メモ・DBを順に保存するため、同時更新に対する一括スナップショットではありません。

バックアップには個人データが含まれます。GitHubにはアップロードせず、アクセスを制限した別のストレージにもコピーしてください。スクリプトは `.env` を保存しないため、接続設定などは別途安全に保管してください。

### 復元する

まず、バックアップ取得時と同じコードのバージョンを使い、元の環境とは保存先・公開ポート・コンテナ名を分けた新しい環境で復元を確認してください。以下は標準の保存先・DBユーザー名・DB名を使う例です。

1. `.env` と空の保存先を用意します。`data/research-manager/postgres/` も新しい保存先を使い、既存のDBを流用しないでください。
2. `Paper/` と `Memo/` に、同じバックアップ実行で作成されたアーカイブを展開します。下の `/path/to/...` は、実際のバックアップファイルのパスに置き換えてください。

   ```bash
   tar -xzf /path/to/papers-YYYYMMDD-HHMMSS.tar.gz -C Paper
   tar -xzf /path/to/memos-YYYYMMDD-HHMMSS.tar.gz -C Memo
   ```

3. PostgreSQLだけを起動します。`docker compose ps` で `healthy` になるまで待ちます。この段階ではバックエンドを起動せず、マイグレーションを実行していない空のDBに復元します。

   ```bash
   docker compose up -d postgres
   docker compose ps
   docker compose exec -T postgres psql -X -v ON_ERROR_STOP=1 -U paper_manager -d paper_manager < /path/to/postgres-YYYYMMDD-HHMMSS.sql
   ```

4. PDF・メモの書き込み権限を確認してから `docker compose up --build -d` で全体を起動します。Library、PDF、メモ、書誌情報が復元されていることを確認してください。

DBのユーザー名・DB名や保存先を変更した場合は、コマンドも設定に合わせて変更してください。元のデータを削除する前に、復元した環境の動作を確認してください。

## 更新する

更新前にPDF・メモ・DBと `.env` をバックアップし、現在使用しているコミットを控えてください。Forkで変更している場合は、元のリポジトリを `upstream` として登録し、変更内容とマイグレーションを確認してから自分のブランチへ取り込みます。

更新後は、リポジトリのルートで次を実行します。

```bash
docker compose up --build -d
docker compose ps
```

バックエンド起動時にDBマイグレーションが自動実行されます。DBを変更する更新では、古いコードに戻すだけで復旧できるとは限りません。更新後にPDFの表示、メモの保存、検索を確認してください。

## 開発・検証

### フロントエンド

Node.js 20.9以上が必要です。DockerイメージではNode.js 22を使用しています。

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

UIの開発サーバーは `npm run dev` で起動できます。APIリクエストは同一オリジンの `/api/v1` に送信するため、APIを使う動作確認にはCaddyなどのプロキシ設定も必要です。アプリ全体の動作確認はCompose環境で行えます。

### バックエンド

Python 3.12を使用します。リポジトリのルートで実行してください。

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests -q
```

テストは一時ファイルとインメモリDBを利用し、稼働中のPostgreSQLを必要としません。

### スモークテスト

Bash、Docker Compose、curl、Python 3が必要です。

```bash
./scripts/smoke_local.sh
```

スタックをビルド・起動し、ヘルスチェック、Library画面、検索APIを確認します。
アップロード・論文詳細・書誌情報・メモ作成まで確認する場合は、サンプルPDFを明示的に指定します。

```bash
SAMPLE_PDF=/path/to/sample.pdf ./scripts/smoke_local.sh
```

アップロード確認では、指定したPDFがライブラリに追加されます。テスト用の環境とファイルを使用してください。

## 技術構成

| 役割 | 使用技術 |
| --- | --- |
| フロントエンド | Next.js App Router、React、TypeScript、Tailwind CSS |
| PDF表示 | PDF.js |
| Markdown表示 | react-markdown、remark-gfm |
| バックエンド | FastAPI、Pydantic |
| DB・マイグレーション | PostgreSQL、SQLAlchemy、Alembic |
| リバースプロキシ | Caddy |
| 実行環境 | Docker Compose |

## ディレクトリ構成

```text
frontend/       # 画面・コンポーネント・スタイル
backend/
  app/          # API・書誌情報取得・検索・ファイル保存
  migrations/   # DBマイグレーション
  tests/        # バックエンドのテスト
docker/         # Dockerfile・Caddy設定
scripts/        # バックアップ・動作確認・メタデータ補修用スクリプト
compose.yaml    # サービス構成
.env.example    # 環境変数のテンプレート
LICENCE         # MITライセンス
```

## 公開・再配布する場合

自分のForkを公開する場合も、公開前に次を確認してください。

- `.env`、PDF、メモ、書誌情報、DBダンプ、バックアップ、ログ、個人の設定がコミット対象に入っていないこと。`git status --short` と `git ls-files` で現在の状態を確認し、過去のコミットも調べてください。
- 秘密情報の検査は現在のファイルだけでなくGit履歴にも行うこと。必要に応じてGitleaksなどを使用してください。漏えいした認証情報は、ファイルや履歴の削除だけでなく失効・再発行が必要です。
- スクリーンショットやサンプルに個人データがないこと。サンプルPDFは自作など、再配布できるものを使ってください。
- コミットの著者名・メールアドレスが公開されてもよいこと。必要に応じてGitHubのnoreplyアドレスを設定してください。設定変更は既存のコミットには反映されません。
- 他者のコード・画像などの利用条件や、所属先の規程などに照らして公開できること。
- 利用できるGitHubのDependabot alerts、secret scanning、push protectionを設定し、依存関係と秘密情報の混入を継続的に確認すること。

一度公開した内容は、非公開に戻しても他の人のForkやローカルコピーからは消えません。詳細は [GitHubの秘密情報削除ガイド](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) と [セキュリティ機能の説明](https://docs.github.com/en/code-security/getting-started/github-security-features) を参照してください。

不具合を報告する場合は、再現手順、利用環境、個人データを除いたログを添えてください。公開Issueにパスワード・トークン・PDF・メモを貼り付けないでください。

## ライセンス

このプロジェクトのコードは [MITライセンス](LICENCE) で提供します。著作権表示とライセンス文を維持することを条件として、個人利用、改変、再配布、商用利用が可能です。個人で改変したコードを公開する義務はありません。ソフトウェアは無保証で提供します。

依存ライブラリや第三者の素材には、それぞれのライセンスが適用されます。このプロジェクトのライセンスは、利用者が登録する論文PDF、外部サービスのコンテンツ、その他の第三者の著作物の再配布を許可するものではありません。それぞれの権利・利用条件を確認してください。
