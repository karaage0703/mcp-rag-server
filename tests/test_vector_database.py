import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# `src`ディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# psycopg2をグローバルにモック化
sys.modules["psycopg2"] = MagicMock()


class TestVectorDatabase(unittest.TestCase):
    def setUp(self):
        # 各テストの前にvector_databaseモジュールをアンロードする
        if "vector_database" in sys.modules:
            del sys.modules["vector_database"]

    @patch.dict(os.environ, {"EMBEDDING_DIM": "512"})
    def test_create_table_with_custom_embedding_dim(self):
        """環境変数からEMBEDDING_DIMを読み取り、テーブル作成クエリが正しくフォーマットされるかテスト"""
        # パッチされた環境でモジュールをインポート
        from vector_database import VectorDatabase, EMBEDDING_DIM

        mock_connect = MagicMock()
        with patch("vector_database.psycopg2.connect", return_value=mock_connect):
            mock_cursor = MagicMock()
            mock_connect.cursor.return_value = mock_cursor

            db = VectorDatabase(connection_params={"dbname": "test_db"})
            db.initialize_database()

            # CREATE TABLEのSQL文を取得
            create_table_sql = mock_cursor.execute.call_args_list[1][0][0]

            # SQL内に正しいベクトル次元が含まれているか確認
            self.assertEqual(EMBEDDING_DIM, 512)
            self.assertIn("embedding vector(512)", create_table_sql)

            # executeが5回呼ばれることを確認
            self.assertEqual(mock_cursor.execute.call_count, 5)

    @patch("dotenv.load_dotenv")  # .envの読み込みを無効化
    def test_create_table_with_default_embedding_dim(self, mock_load_dotenv):
        """環境変数がない場合にデフォルトのEMBEDDING_DIMでテーブルが作成されるかテスト"""
        # 環境変数をクリア
        with patch.dict(os.environ, {}, clear=True):
            # パッチされた環境でモジュールをインポート
            from vector_database import VectorDatabase, EMBEDDING_DIM

            mock_connect = MagicMock()
            with patch("vector_database.psycopg2.connect", return_value=mock_connect):
                mock_cursor = MagicMock()
                mock_connect.cursor.return_value = mock_cursor

                db = VectorDatabase(connection_params={"dbname": "test_db"})
                db.initialize_database()

                # CREATE TABLEのSQL文を取得
                create_table_sql = mock_cursor.execute.call_args_list[1][0][0]

                # デフォルトの次元(1024)が使われているか確認
                self.assertEqual(EMBEDDING_DIM, 1024)
                self.assertIn("embedding vector(1024)", create_table_sql)


if __name__ == "__main__":
    unittest.main()
