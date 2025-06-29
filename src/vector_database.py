"""
ベクトルデータベースモジュール

PostgreSQLとpgvectorを使用してベクトルの保存と検索を行います。
"""

import logging
import psycopg2
import json
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# .envの読み込み
load_dotenv()
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))


class VectorDatabase:
    """
    ベクトルデータベースクラス

    PostgreSQLとpgvectorを使用してベクトルの保存と検索を行います。

    Attributes:
        connection_params: 接続パラメータ
        connection: データベース接続
        logger: ロガー
    """

    def __init__(self, connection_params: Dict[str, Any]):
        """
        VectorDatabaseのコンストラクタ

        Args:
            connection_params: 接続パラメータ
                - host: ホスト名
                - port: ポート番号
                - user: ユーザー名
                - password: パスワード
                - database: データベース名
        """
        # ロガーの設定
        self.logger = logging.getLogger("vector_database")
        self.logger.setLevel(logging.INFO)

        # 接続パラメータの保存
        self.connection_params = connection_params
        self.connection = None

    def connect(self) -> None:
        """
        データベースに接続します。

        Raises:
            Exception: 接続に失敗した場合
        """
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            self.logger.info("データベースに接続しました")
        except Exception as e:
            self.logger.error(f"データベースへの接続に失敗しました: {str(e)}")
            raise

    def disconnect(self) -> None:
        """
        データベースから切断します。
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("データベースから切断しました")

    def initialize_database(self) -> None:
        """
        データベースを初期化します。

        テーブルとインデックスを作成します。

        Raises:
            Exception: 初期化に失敗した場合
        """
        try:
            # 接続がない場合は接続
            if not self.connection:
                self.connect()

            # カーソルの作成
            cursor = self.connection.cursor()

            # pgvectorエクステンションの有効化
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            # ドキュメントテーブルの作成
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    document_id TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    metadata JSONB,
                    embedding vector({EMBEDDING_DIM}),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # インデックスの作成
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_document_id ON documents (document_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents (file_path);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);
            """)

            # コミット
            self.connection.commit()
            self.logger.info("データベースを初期化しました")

        except Exception as e:
            # ロールバック
            if self.connection:
                self.connection.rollback()
            self.logger.error(f"データベースの初期化に失敗しました: {str(e)}")
            raise

        finally:
            # カーソルを閉じる
            if "cursor" in locals() and cursor:
                cursor.close()

    def insert_document(
        self,
        document_id: str,
        content: str,
        file_path: str,
        chunk_index: int,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        ドキュメントを挿入します。

        Args:
            document_id: ドキュメントID
            content: ドキュメントの内容
            file_path: ファイルパス
            chunk_index: チャンクインデックス
            embedding: エンベディング
            metadata: メタデータ（オプション）

        Raises:
            Exception: 挿入に失敗した場合
        """
        try:
            # 接続がない場合は接続
            if not self.connection:
                self.connect()

            # カーソルの作成
            cursor = self.connection.cursor()

            # メタデータをJSON形式に変換
            metadata_json = json.dumps(metadata) if metadata else None

            # ドキュメントの挿入
            cursor.execute(
                """
                INSERT INTO documents (document_id, content, file_path, chunk_index, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id) 
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    file_path = EXCLUDED.file_path,
                    chunk_index = EXCLUDED.chunk_index,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    created_at = CURRENT_TIMESTAMP;
            """,
                (document_id, content, file_path, chunk_index, embedding, metadata_json),
            )

            # コミット
            self.connection.commit()
            self.logger.debug(f"ドキュメント '{document_id}' を挿入しました")

        except Exception as e:
            # ロールバック
            if self.connection:
                self.connection.rollback()
            self.logger.error(f"ドキュメントの挿入に失敗しました: {str(e)}")
            raise

        finally:
            # カーソルを閉じる
            if "cursor" in locals() and cursor:
                cursor.close()

    def batch_insert_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        複数のドキュメントをバッチ挿入します。

        Args:
            documents: ドキュメントのリスト
                各ドキュメントは以下のキーを持つ辞書:
                - document_id: ドキュメントID
                - content: ドキュメントの内容
                - file_path: ファイルパス
                - chunk_index: チャンクインデックス
                - embedding: エンベディング
                - metadata: メタデータ（オプション）

        Raises:
            Exception: 挿入に失敗した場合
        """
        if not documents:
            self.logger.warning("挿入するドキュメントがありません")
            return

        try:
            # 接続がない場合は接続
            if not self.connection:
                self.connect()

            # カーソルの作成
            cursor = self.connection.cursor()

            # バッチ挿入用のデータ作成
            values = []
            for doc in documents:
                metadata_json = json.dumps(doc.get("metadata")) if doc.get("metadata") else None
                values.append(
                    (doc["document_id"], doc["content"], doc["file_path"], doc["chunk_index"], doc["embedding"], metadata_json)
                )

            # バッチ挿入
            cursor.executemany(
                """
                INSERT INTO documents (document_id, content, file_path, chunk_index, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id) 
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    file_path = EXCLUDED.file_path,
                    chunk_index = EXCLUDED.chunk_index,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    created_at = CURRENT_TIMESTAMP;
            """,
                values,
            )

            # コミット
            self.connection.commit()
            self.logger.info(f"{len(documents)} 個のドキュメントを挿入しました")

        except Exception as e:
            # ロールバック
            if self.connection:
                self.connection.rollback()
            self.logger.error(f"ドキュメントのバッチ挿入に失敗しました: {str(e)}")
            raise

        finally:
            # カーソルを閉じる
            if "cursor" in locals() and cursor:
                cursor.close()

    def search(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        ベクトル検索を行います。

        Args:
            query_embedding: クエリのエンベディング
            limit: 返す結果の数（デフォルト: 5）

        Returns:
            検索結果のリスト（関連度順）

        Raises:
            Exception: 検索に失敗した場合
        """
        try:
            # 接続がない場合は接続
            if not self.connection:
                self.connect()

            # カーソルの作成
            cursor = self.connection.cursor()

            # クエリエンベディングをPostgreSQLの配列構文に変換
            embedding_str = str(query_embedding)
            embedding_array = f"ARRAY{embedding_str}::vector"

            # ベクトル検索
            cursor.execute(
                f"""
                SELECT
                    document_id,
                    content,
                    file_path,
                    chunk_index,
                    metadata,
                    1 - (embedding <=> {embedding_array}) AS similarity
                FROM
                    documents
                WHERE
                    embedding IS NOT NULL
                ORDER BY
                    embedding <=> {embedding_array}
                LIMIT %s;
                """,
                (limit,),
            )

            # 結果の取得
            results = []
            for row in cursor.fetchall():
                document_id, content, file_path, chunk_index, metadata_json, similarity = row

                # メタデータをJSONからデコード
                if metadata_json:
                    if isinstance(metadata_json, str):
                        try:
                            metadata = json.loads(metadata_json)
                        except json.JSONDecodeError:
                            metadata = {}
                    else:
                        # 既に辞書型の場合はそのまま使用
                        metadata = metadata_json
                else:
                    metadata = {}

                results.append(
                    {
                        "document_id": document_id,
                        "content": content,
                        "file_path": file_path,
                        "chunk_index": chunk_index,
                        "metadata": metadata,
                        "similarity": similarity,
                    }
                )

            self.logger.info(f"クエリに対して {len(results)} 件の結果が見つかりました")
            return results

        except Exception as e:
            self.logger.error(f"ベクトル検索中にエラーが発生しました: {str(e)}")
            raise

        finally:
            # カーソルを閉じる
            if "cursor" in locals() and cursor:
                cursor.close()

    def delete_document(self, document_id: str) -> bool:
        """
        ドキュメントを削除します。

        Args:
            document_id: 削除するドキュメントのID

        Returns:
            削除に成功した場合はTrue、ドキュメントが見つからない場合はFalse

        Raises:
            Exception: 削除に失敗した場合
        """
        try:
            # 接続がない場合は接続
            if not self.connection:
                self.connect()

            # カーソルの作成
            cursor = self.connection.cursor()

            # ドキュメントの削除
            cursor.execute("DELETE FROM documents WHERE document_id = %s;", (document_id,))

            # 削除された行数を取得
            deleted_rows = cursor.rowcount

            # コミット
            self.connection.commit()

            if deleted_rows > 0:
                self.logger.info(f"ドキュメント '{document_id}' を削除しました")
                return True
            else:
                self.logger.warning(f"ドキュメント '{document_id}' が見つかりません")
                return False

        except Exception as e:
            # ロールバック
            if self.connection:
                self.connection.rollback()
            self.logger.error(f"ドキュメントの削除中にエラーが発生しました: {str(e)}")
            raise

        finally:
            # カーソルを閉じる
            if "cursor" in locals() and cursor:
                cursor.close()

    def delete_by_file_path(self, file_path: str) -> int:
        """
        ファイルパスに基づいてドキュメントを削除します。

        Args:
            file_path: 削除するドキュメントのファイルパス

        Returns:
            削除されたドキュメントの数

        Raises:
            Exception: 削除に失敗した場合
        """
        try:
            # 接続がない場合は接続
            if not self.connection:
                self.connect()

            # カーソルの作成
            cursor = self.connection.cursor()

            # ドキュメントの削除
            cursor.execute("DELETE FROM documents WHERE file_path = %s;", (file_path,))

            # 削除された行数を取得
            deleted_rows = cursor.rowcount

            # コミット
            self.connection.commit()

            self.logger.info(f"ファイルパス '{file_path}' に関連する {deleted_rows} 個のドキュメントを削除しました")
            return deleted_rows

        except Exception as e:
            # ロールバック
            if self.connection:
                self.connection.rollback()
            self.logger.error(f"ドキュメントの削除中にエラーが発生しました: {str(e)}")
            raise

        finally:
            # カーソルを閉じる
            if "cursor" in locals() and cursor:
                cursor.close()

    def clear_database(self) -> int:
        """
        データベースをクリアします（全てのドキュメントを削除）。

        Raises:
            Exception: クリアに失敗した場合

        Returns:
            削除されたドキュメントの数。テーブルをDROPするため、削除前の数を返します。
        """
        try:
            # 接続がない場合は接続
            if not self.connection:
                self.connect()

            # 削除前のドキュメント数を取得
            count_before_delete = self.get_document_count()

            # カーソルの作成
            cursor = self.connection.cursor()

            # テーブルを削除してスキーマもクリア
            cursor.execute("DROP TABLE IF EXISTS documents;")

            # コミット
            self.connection.commit()

            if count_before_delete > 0:
                self.logger.info(
                    f"データベースをクリアしました（documentsテーブルを削除、{count_before_delete} 個のドキュメントが対象でした）"
                )
            else:
                self.logger.info("データベースをクリアしました（documentsテーブルを削除）")
            return count_before_delete

        except Exception as e:
            # ロールバック
            if self.connection:
                self.connection.rollback()
            self.logger.error(f"データベースのクリア中にエラーが発生しました: {str(e)}")
            raise

        finally:
            # カーソルを閉じる
            if "cursor" in locals() and cursor:
                cursor.close()

    def get_document_count(self) -> int:
        """
        データベース内のドキュメント数を取得します。

        Returns:
            ドキュメント数

        Raises:
            Exception: 取得に失敗した場合
        """
        try:
            # 接続がない場合は接続
            if not self.connection:
                self.connect()

            # カーソルの作成
            cursor = self.connection.cursor()

            # ドキュメント数を取得
            cursor.execute("SELECT COUNT(*) FROM documents;")
            count = cursor.fetchone()[0]

            self.logger.info(f"データベース内のドキュメント数: {count}")
            return count

        except psycopg2.errors.UndefinedTable:
            # テーブルが存在しない場合は0を返す
            self.connection.rollback()  # エラー状態をリセット
            self.logger.info("documentsテーブルが存在しないため、ドキュメント数は0です")
            return 0
        except Exception as e:
            self.logger.error(f"ドキュメント数の取得中にエラーが発生しました: {str(e)}")
            raise

    def get_adjacent_chunks(self, file_path: str, chunk_index: int, context_size: int = 1) -> List[Dict[str, Any]]:
        """
        指定されたチャンクの前後のチャンクを取得します。

        Args:
            file_path: ファイルパス
            chunk_index: チャンクインデックス
            context_size: 前後に取得するチャンク数（デフォルト: 1）

        Returns:
            前後のチャンクのリスト

        Raises:
            Exception: 取得に失敗した場合
        """
        try:
            # 接続がない場合は接続
            if not self.connection:
                self.connect()

            # カーソルの作成
            cursor = self.connection.cursor()

            # 前後のチャンクを取得
            min_index = max(0, chunk_index - context_size)
            max_index = chunk_index + context_size

            cursor.execute(
                """
                SELECT
                    document_id,
                    content,
                    file_path,
                    chunk_index,
                    metadata,
                    1 AS similarity
                FROM
                    documents
                WHERE
                    file_path = %s
                    AND chunk_index >= %s
                    AND chunk_index <= %s
                    AND chunk_index != %s
                ORDER BY
                    chunk_index
                """,
                (file_path, min_index, max_index, chunk_index),
            )

            # 結果の取得
            results = []
            for row in cursor.fetchall():
                document_id, content, file_path, chunk_index, metadata_json, similarity = row

                # メタデータをJSONからデコード
                if metadata_json:
                    if isinstance(metadata_json, str):
                        try:
                            metadata = json.loads(metadata_json)
                        except json.JSONDecodeError:
                            metadata = {}
                    else:
                        # 既に辞書型の場合はそのまま使用
                        metadata = metadata_json
                else:
                    metadata = {}

                results.append(
                    {
                        "document_id": document_id,
                        "content": content,
                        "file_path": file_path,
                        "chunk_index": chunk_index,
                        "metadata": metadata,
                        "similarity": similarity,
                        "is_context": True,  # コンテキストチャンクであることを示すフラグ
                    }
                )

            self.logger.info(
                f"ファイル '{file_path}' のチャンク {chunk_index} の前後 {len(results)} 件のチャンクを取得しました"
            )
            return results

        except Exception as e:
            self.logger.error(f"前後のチャンク取得中にエラーが発生しました: {str(e)}")
            raise

        finally:
            # カーソルを閉じる
            if "cursor" in locals() and cursor:
                cursor.close()

    def get_document_by_file_path(self, file_path: str) -> List[Dict[str, Any]]:
        """
        指定されたファイルパスに基づいてドキュメント全体を取得します。

        Args:
            file_path: ファイルパス

        Returns:
            ドキュメント全体のチャンクのリスト

        Raises:
            Exception: 取得に失敗した場合
        """
        try:
            # 接続がない場合は接続
            if not self.connection:
                self.connect()

            # カーソルの作成
            cursor = self.connection.cursor()

            # ファイルパスに基づいてドキュメントを取得
            cursor.execute(
                """
                SELECT
                    document_id,
                    content,
                    file_path,
                    chunk_index,
                    metadata,
                    1 AS similarity
                FROM
                    documents
                WHERE
                    file_path = %s
                ORDER BY
                    chunk_index
                """,
                (file_path,),
            )

            # 結果の取得
            results = []
            for row in cursor.fetchall():
                document_id, content, file_path, chunk_index, metadata_json, similarity = row

                # メタデータをJSONからデコード
                if metadata_json:
                    if isinstance(metadata_json, str):
                        try:
                            metadata = json.loads(metadata_json)
                        except json.JSONDecodeError:
                            metadata = {}
                    else:
                        # 既に辞書型の場合はそのまま使用
                        metadata = metadata_json
                else:
                    metadata = {}

                results.append(
                    {
                        "document_id": document_id,
                        "content": content,
                        "file_path": file_path,
                        "chunk_index": chunk_index,
                        "metadata": metadata,
                        "similarity": similarity,
                        "is_full_document": True,  # 全文ドキュメントであることを示すフラグ
                    }
                )

            self.logger.info(f"ファイル '{file_path}' の全文 {len(results)} チャンクを取得しました")
            return results

        except Exception as e:
            self.logger.error(f"ドキュメント全文の取得中にエラーが発生しました: {str(e)}")
            raise

        finally:
            # カーソルを閉じる
            if "cursor" in locals() and cursor:
                cursor.close()
