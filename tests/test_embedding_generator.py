import unittest
from unittest.mock import patch, MagicMock
import os
import numpy as np

# `src`ディレクトリをパスに追加して、`embedding_generator`をインポート可能にする
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from embedding_generator import EmbeddingGenerator


class TestEmbeddingGenerator(unittest.TestCase):
    def setUp(self):
        """テストケースごとに環境をクリーンアップし、モックを設定"""
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.mock_sentence_transformer_patcher = patch("embedding_generator.SentenceTransformer")

        self.env_patcher.start()
        self.mock_sentence_transformer = self.mock_sentence_transformer_patcher.start()

        # SentenceTransformerのコンストラクタとencodeメソッドをモック化
        self.mock_model_instance = MagicMock()
        self.mock_sentence_transformer.return_value = self.mock_model_instance
        # encodeが呼ばれたら固定のnumpy配列を返すように設定
        self.mock_model_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]])

    def tearDown(self):
        """パッチを停止"""
        self.env_patcher.stop()
        self.mock_sentence_transformer_patcher.stop()

    def test_initialization_with_env_variables(self):
        """環境変数から設定が読み込まれることをテスト"""
        test_env = {
            "EMBEDDING_MODEL": "test-model",
            "EMBEDDING_PREFIX_QUERY": "query: ",
            "EMBEDDING_PREFIX_EMBEDDING": "passage: ",
        }
        with patch.dict(os.environ, test_env, clear=True):
            generator = EmbeddingGenerator()
            self.assertEqual(generator.model_name, "test-model")
            self.assertEqual(generator.prefix_query, "query: ")
            self.assertEqual(generator.prefix_embedding, "passage: ")
            self.mock_sentence_transformer.assert_called_with("test-model")

    def test_initialization_with_defaults(self):
        """環境変数がない場合にデフォルト値が使われることをテスト"""
        generator = EmbeddingGenerator()
        self.assertEqual(generator.model_name, "intfloat/multilingual-e5-large")
        self.assertEqual(generator.prefix_query, "")
        self.assertEqual(generator.prefix_embedding, "")
        self.mock_sentence_transformer.assert_called_with("intfloat/multilingual-e5-large")

    def test_add_prefix(self):
        """_add_prefixメソッドのロジックをテスト"""
        generator = EmbeddingGenerator()
        self.assertEqual(generator._add_prefix("text", "prefix: "), "prefix: text")
        self.assertEqual(generator._add_prefix("prefix: text", "prefix: "), "prefix: text")
        self.assertEqual(generator._add_prefix("text", ""), "text")
        self.assertEqual(generator._add_prefix("TEXT", "prefix: "), "prefix: TEXT")

    def test_generate_embedding_with_prefix(self):
        """generate_embeddingが正しいプレフィックスを使用することをテスト"""
        test_env = {"EMBEDDING_PREFIX_EMBEDDING": "passage: "}
        with patch.dict(os.environ, test_env, clear=True):
            generator = EmbeddingGenerator()
            generator.generate_embedding("my text")
            self.mock_model_instance.encode.assert_called_with("passage: my text")

    def test_generate_embeddings_with_prefix(self):
        """generate_embeddingsが正しいプレフィックスを使用することをテスト"""
        test_env = {"EMBEDDING_PREFIX_EMBEDDING": "passage: "}
        with patch.dict(os.environ, test_env, clear=True):
            generator = EmbeddingGenerator()
            generator.generate_embeddings(["text1", "text2"])
            self.mock_model_instance.encode.assert_called_with(["passage: text1", "passage: text2"])

    def test_generate_query_embedding_with_prefix(self):
        """generate_query_embeddingが正しいプレフィックスを使用することをテスト"""
        test_env = {"EMBEDDING_PREFIX_QUERY": "query: "}
        with patch.dict(os.environ, test_env, clear=True):
            generator = EmbeddingGenerator()
            generator.generate_search_embedding("my query")
            self.mock_model_instance.encode.assert_called_with("query: my query")


if __name__ == "__main__":
    unittest.main()
