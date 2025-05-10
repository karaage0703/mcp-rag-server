"""
エンベディング生成モジュール

テキストからエンベディングを生成します。
"""

import logging
import os
from typing import List
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# .envの読み込み
load_dotenv()


class EmbeddingGenerator:
    """
    エンベディング生成クラス

    テキストからエンベディングを生成します。

    Attributes:
        model: SentenceTransformerモデル
        logger: ロガー
    """

    def __init__(self, model_name: str = None):
        """
        EmbeddingGeneratorのコンストラクタ

        Args:
            model_name: 使用するモデル名（.env優先）
        """
        # .envから設定を取得
        self.model_name = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
        self.prefix_query = os.getenv("EMBEDDING_PREFIX_QUERY", "")
        self.prefix_embedding = os.getenv("EMBEDDING_PREFIX_EMBEDDING", "")

        # ロガーの設定
        self.logger = logging.getLogger("embedding_generator")
        self.logger.setLevel(logging.INFO)

        # モデルの読み込み
        self.logger.info(f"モデル '{self.model_name}' を読み込んでいます...")
        try:
            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"モデル '{self.model_name}' を読み込みました")
        except Exception as e:
            self.logger.error(f"モデル '{self.model_name}' の読み込みに失敗しました: {str(e)}")
            raise

    def _add_prefix(self, text: str, prefix: str) -> str:
        if prefix and not text.lower().startswith(prefix.strip().lower()):
            return f"{prefix}{text}"
        return text

    def generate_embedding(self, text: str) -> List[float]:
        """
        テキストからエンベディングを生成します。

        Args:
            text: エンベディングを生成するテキスト

        Returns:
            エンベディング（浮動小数点数のリスト）
        """
        if not text:
            self.logger.warning("空のテキストからエンベディングを生成しようとしています")
            return []

        try:
            processed_text = self._add_prefix(text, self.prefix_embedding)
            embedding = self.model.encode(processed_text)
            embedding_list = embedding.tolist()
            self.logger.debug(f"テキスト '{text[:50]}...' のエンベディングを生成しました")
            return embedding_list
        except Exception as e:
            self.logger.error(f"エンベディングの生成中にエラーが発生しました: {str(e)}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        複数のテキストからエンベディングを生成します。

        Args:
            texts: エンベディングを生成するテキストのリスト

        Returns:
            エンベディングのリスト
        """
        if not texts:
            self.logger.warning("空のテキストリストからエンベディングを生成しようとしています")
            return []

        try:
            processed_texts = [self._add_prefix(text, self.prefix_embedding) for text in texts]
            embeddings = self.model.encode(processed_texts)
            embeddings_list = embeddings.tolist()
            self.logger.info(f"{len(texts)} 個のテキストのエンベディングを生成しました")
            return embeddings_list
        except Exception as e:
            self.logger.error(f"エンベディングの生成中にエラーが発生しました: {str(e)}")
            raise

    def generate_search_embedding(self, query: str) -> List[float]:
        """
        検索クエリからエンベディングを生成します。

        Args:
            query: 検索クエリ

        Returns:
            エンベディング（浮動小数点数のリスト）
        """
        if not query:
            self.logger.warning("空のクエリからエンベディングを生成しようとしています")
            return []

        try:
            processed_query = self._add_prefix(query, self.prefix_query)
            embedding = self.model.encode(processed_query)
            embedding_list = embedding.tolist()
            self.logger.debug(f"クエリ '{query}' のエンベディングを生成しました")
            return embedding_list
        except Exception as e:
            self.logger.error(f"クエリエンベディングの生成中にエラーが発生しました: {str(e)}")
            raise
