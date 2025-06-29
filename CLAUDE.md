# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

MCP RAG Serverは、Model Context Protocol (MCP)とRAG (Retrieval-Augmented Generation)機能を実装したPythonサーバーです。複数のドキュメント形式に対応したベクトル検索システムを提供します。

## 主要コマンド

### 開発環境セットアップ
```bash
# 依存関係のインストール (uvを使用)
uv sync

# PostgreSQLとpgvectorのセットアップが必要
# DockerでPostgreSQLを起動:
docker run -d \
  --name pgvector-db \
  -e POSTGRES_USER=your_user \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=your_database \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# .envファイルの設定が必要
```

### 実行コマンド
```bash
# MCPサーバーの起動
uv run python -m src.main

# CLIでドキュメントをインデックス
uv run python -m src.cli index
uv run python -m src.cli index --incremental  # 差分インデックス

# インデックスのクリア
uv run python -m src.cli clear

# ドキュメント数の確認
uv run python -m src.cli count
```

### テスト実行
```bash
# pytestでテスト実行
uv run pytest
```

### Lint・フォーマット
```bash
# ruffでlintチェック
uv run ruff check --line-length=127

# ruffで自動フォーマット
uv run ruff format --line-length=127

# フォーマットチェック（差分表示）
uv run ruff format --check --diff --line-length=127
```

### Pull Request(PR)

#### PR作成時
- PRを要望されたら、gitコマンドで差分を確認したうえで、`gh pr` コマンドを使ってPRを作成してください
- PRのdescriptionは .github/pull_request_template.md を読み取ってフォーマットを合わせてください

#### PRレビュー時
以下の手順でファイルごとにコメントを付けてください：

1. チェックする観点は .github/pull_request_template.md を参照してください
2. PRの差分を確認:
   ```bash
   gh pr diff <PR番号>
   ```

3. ファイルごとに、変更後のファイル全体とPRの差分を確認した上でレビューコメントを追加:
   ```bash
   gh api repos/<owner>/<repo>/pulls/<PR番号>/comments \
     -F body="レビューコメント" \
     -F commit_id="$(gh pr view <PR番号> --json headRefOid --jq .headRefOid)" \
     -F path="対象ファイルのパス" \
     -F position=<diffの行番号>
   ```

   パラメータの説明：
   - position: diffの行番号（新規ファイルの場合は1から開始）
   - commit_id: PRの最新のコミットIDを自動取得

## アーキテクチャ概要

### コア構成
- **MCPサーバー層**: `src/mcp_server.py`がJSON-RPC通信を処理
- **RAGサービス層**: `src/rag_service.py`がドキュメント処理と検索を統括
- **データ層**: PostgreSQL + pgvectorでベクトルデータベースを実装

### 主要モジュール
- `src/main.py`: エントリーポイント
- `src/rag_tools.py`: MCP用の検索ツール定義
- `src/document_processor.py`: ドキュメント解析とチャンク化
- `src/embedding_generator.py`: multilingual-e5-largeモデルでの埋め込み生成
- `src/vector_database.py`: PostgreSQL/pgvectorインターフェース

### データフロー
1. `data/source/`配下のドキュメントを読み込み
2. markitdownでテキスト変換、チャンク分割
3. sentence-transformersで埋め込みベクトル生成
4. PostgreSQLにベクトルと共に保存
5. MCPツール経由でセマンティック検索を提供

### 重要な設計パターン
- 差分インデックス: ファイルハッシュで変更検知
- オーバーラップチャンク: コンテキスト保持のため重複あり
- 隣接チャンク取得: 検索結果の前後文脈も取得可能

## 環境変数設定

`.env`ファイルに以下を設定:
```
# PostgreSQL接続情報
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database

# パス設定
SOURCE_DIR=data/source
PROCESSED_DIR=data/processed
```

## 対応ドキュメント形式
- Markdown (.md)
- テキスト (.txt)
- PowerPoint (.pptx)
- PDF (.pdf)
- Word (.docx)

## 開発時の注意点
- 新しいドキュメント形式を追加する場合は`document_processor.py`を拡張
- ベクトルデータベースのスキーマ変更時は`vector_database.py`の`create_tables()`を更新
- MCPツールを追加する場合は`rag_tools.py`にツール定義を追加