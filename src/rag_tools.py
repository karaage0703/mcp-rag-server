"""
RAGツールモジュール

MCPサーバーに登録するRAG関連ツールを提供します。
"""

import os

from typing import Dict, Any

from .document_processor import DocumentProcessor
from .embedding_generator import EmbeddingGenerator
from .vector_database import VectorDatabase
from .rag_service import RAGService

from dotenv import load_dotenv

load_dotenv()


def register_rag_tools(server, rag_service: RAGService):
    """
    RAG関連ツールをMCPサーバーに登録します。

    Args:
        server: MCPサーバーのインスタンス
        rag_service: RAGサービスのインスタンス
    """
    # 検索ツールの登録
    server.register_tool(
        name="search",
        description="ベクトル検索を行います",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "検索クエリ",
                },
                "limit": {
                    "type": "integer",
                    "description": "返す結果の数（デフォルト: 5）",
                    "default": 5,
                },
                "with_context": {
                    "type": "boolean",
                    "description": "前後のチャンクも取得するかどうか（デフォルト: true）",
                    "default": True,
                },
                "context_size": {
                    "type": "integer",
                    "description": "前後に取得するチャンク数（デフォルト: 1）",
                    "default": 1,
                },
                "full_document": {
                    "type": "boolean",
                    "description": "ドキュメント全体を取得するかどうか（デフォルト: false）",
                    "default": False,
                },
            },
            "required": ["query"],
        },
        handler=lambda params: search_handler(params, rag_service),
    )

    # ドキュメント数取得ツールの登録
    server.register_tool(
        name="get_document_count",
        description="インデックス内のドキュメント数を取得します",
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
        },
        handler=lambda params: get_document_count_handler(params, rag_service),
    )


def search_handler(params: Dict[str, Any], rag_service: RAGService) -> Dict[str, Any]:
    """
    ベクトル検索を行うハンドラ関数

    Args:
        params: パラメータ
            - query: 検索クエリ
            - limit: 返す結果の数（デフォルト: 5）
            - with_context: 前後のチャンクも取得するかどうか（デフォルト: true）
            - context_size: 前後に取得するチャンク数（デフォルト: 1）
            - full_document: ドキュメント全体を取得するかどうか（デフォルト: false）
        rag_service: RAGサービスのインスタンス

    Returns:
        検索結果
    """
    query = params.get("query")
    limit = params.get("limit", 5)
    with_context = params.get("with_context", True)
    context_size = params.get("context_size", 1)
    full_document = params.get("full_document", False)

    if not query:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "エラー: 検索クエリが指定されていません",
                }
            ],
            "isError": True,
        }

    try:
        # ドキュメント数を確認
        doc_count = rag_service.get_document_count()
        if doc_count == 0:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "インデックスにドキュメントが存在しません。CLIコマンド `python -m src.cli index` を使用してドキュメントをインデックス化してください。",
                    }
                ],
                "isError": True,
            }

        # 検索を実行（前後のチャンクも取得、ドキュメント全体も取得）
        results = rag_service.search(query, limit, with_context, context_size, full_document)

        if not results:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"クエリ '{query}' に一致する結果が見つかりませんでした",
                    }
                ]
            }

        # 結果をファイルごとにグループ化
        file_groups = {}
        for result in results:
            file_path = result["file_path"]
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(result)

        # 各グループ内でチャンクインデックスでソート
        for file_path in file_groups:
            file_groups[file_path].sort(key=lambda x: x["chunk_index"])

        # 結果を整形
        content_items = [
            {
                "type": "text",
                "text": f"クエリ '{query}' の検索結果（{len(results)} 件）:",
            }
        ]

        # ファイルごとに結果を表示
        for i, (file_path, group) in enumerate(file_groups.items()):
            file_name = os.path.basename(file_path)

            # ファイルヘッダー
            content_items.append(
                {
                    "type": "text",
                    "text": f"\n[{i + 1}] ファイル: {file_name}",
                }
            )

            # 各チャンクを表示
            for j, result in enumerate(group):
                similarity_percent = result.get("similarity", 0) * 100
                is_context = result.get("is_context", False)
                is_full_document = result.get("is_full_document", False)

                # 全文ドキュメント、コンテキストチャンク、検索ヒットチャンクで表示を変える
                if is_full_document:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n+++ ドキュメント全文（チャンク {result['chunk_index']}) +++\n{result['content']}",
                        }
                    )
                elif is_context:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n--- 前後のコンテキスト（チャンク {result['chunk_index']}) ---\n{result['content']}",
                        }
                    )
                else:
                    content_items.append(
                        {
                            "type": "text",
                            "text": f"\n=== 検索ヒット（チャンク {result['chunk_index']}, 類似度: {similarity_percent:.2f}%) ===\n{result['content']}",
                        }
                    )

        return {"content": content_items}

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"検索中にエラーが発生しました: {str(e)}",
                }
            ],
            "isError": True,
        }


def get_document_count_handler(params: Dict[str, Any], rag_service: RAGService) -> Dict[str, Any]:
    """
    インデックス内のドキュメント数を取得するハンドラ関数

    Args:
        params: パラメータ（未使用）
        rag_service: RAGサービスのインスタンス

    Returns:
        ドキュメント数
    """
    try:
        # ドキュメント数を取得
        count = rag_service.get_document_count()

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"インデックス内のドキュメント数: {count}",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"ドキュメント数の取得中にエラーが発生しました: {str(e)}",
                }
            ],
            "isError": True,
        }


def create_rag_service_from_env() -> RAGService:
    """
    環境変数からRAGサービスを作成します。

    Returns:
        RAGサービスのインスタンス
    """
    # 環境変数から接続情報を取得
    postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
    postgres_port = os.environ.get("POSTGRES_PORT", "5432")
    postgres_user = os.environ.get("POSTGRES_USER", "postgres")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "password")
    postgres_db = os.environ.get("POSTGRES_DB", "ragdb")

    embedding_model = os.environ.get("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")

    # コンポーネントの作成
    document_processor = DocumentProcessor()
    embedding_generator = EmbeddingGenerator(model_name=embedding_model)
    vector_database = VectorDatabase(
        {
            "host": postgres_host,
            "port": postgres_port,
            "user": postgres_user,
            "password": postgres_password,
            "database": postgres_db,
        }
    )

    # RAGサービスの作成
    rag_service = RAGService(document_processor, embedding_generator, vector_database)

    return rag_service
