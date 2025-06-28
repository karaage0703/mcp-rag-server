#!/usr/bin/env python
"""
MCP RAG Server

Model Context Protocol (MCP)に準拠したRAG機能を持つPythonサーバー
"""

import sys
import os
import argparse
import importlib
import logging
from dotenv import load_dotenv

from .mcp_server import MCPServer
from .rag_tools import register_rag_tools, create_rag_service_from_env


def main():
    """
    メイン関数

    コマンドライン引数を解析し、MCPサーバーを起動します。
    """
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="MCP RAG Server - Model Context Protocol (MCP)に準拠したRAG機能を持つPythonサーバー"
    )
    parser.add_argument("--name", default="mcp-rag-server", help="サーバー名")
    parser.add_argument("--version", default="0.1.0", help="サーバーバージョン")
    parser.add_argument("--description", default="MCP RAG Server - 複数形式のドキュメントのRAG検索", help="サーバーの説明")
    parser.add_argument("--module", help="追加のツールモジュール（例: myapp.tools）")
    args = parser.parse_args()

    # 環境変数の読み込み
    load_dotenv()

    # ディレクトリの作成
    os.makedirs("logs", exist_ok=True)
    os.makedirs(os.environ.get("SOURCE_DIR", "data/source"), exist_ok=True)
    os.makedirs(os.environ.get("PROCESSED_DIR", "data/processed"), exist_ok=True)

    # ロギングの設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(os.path.join("logs", "mcp_rag_server.log"), encoding="utf-8"),
        ],
    )
    logger = logging.getLogger("main")

    try:
        # MCPサーバーの作成
        server = MCPServer()

        # RAGサービスの作成と登録
        logger.info("RAGサービスを初期化しています...")
        rag_service = create_rag_service_from_env()
        register_rag_tools(server, rag_service)
        logger.info("RAGツールを登録しました")

        # 追加のツールモジュールがある場合は読み込む
        if args.module:
            try:
                module = importlib.import_module(args.module)
                if hasattr(module, "register_tools"):
                    module.register_tools(server)
                    print(f"モジュール '{args.module}' からツールを登録しました", file=sys.stderr)
                else:
                    print(f"警告: モジュール '{args.module}' に register_tools 関数が見つかりません", file=sys.stderr)
            except ImportError as e:
                print(f"警告: モジュール '{args.module}' の読み込みに失敗しました: {str(e)}", file=sys.stderr)

        # MCPサーバーの起動
        server.start(args.name, args.version, args.description)

    except KeyboardInterrupt:
        print("サーバーを終了します。", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
