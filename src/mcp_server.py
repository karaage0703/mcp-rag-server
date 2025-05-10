"""
MCPサーバーモジュール

Model Context Protocol (MCP)に準拠したサーバーを提供します。
JSON-RPC over stdioを使用してクライアントからのリクエストを処理します。
"""

import sys
import json
import logging
from typing import Dict, Any, List, Callable
from pathlib import Path


class MCPServer:
    """
    Model Context Protocol (MCP)に準拠したサーバークラス

    JSON-RPC over stdioを使用してクライアントからのリクエストを処理します。

    Attributes:
        tools: 登録されたツールのディクショナリ
        logger: ロガー
    """

    def __init__(self):
        """
        MCPServerのコンストラクタ
        """
        self.tools = {}
        self.tool_handlers = {}

        # ロガーの設定
        self.logger = logging.getLogger("mcp_server")
        self.logger.setLevel(logging.INFO)

        # ファイルハンドラの設定
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "mcp_server.log")
        file_handler.setLevel(logging.INFO)

        # フォーマッタの設定
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # ハンドラの追加
        self.logger.addHandler(file_handler)

    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any], handler: Callable):
        """
        ツールを登録します。

        Args:
            name: ツール名
            description: ツールの説明
            input_schema: 入力スキーマ
            handler: ツールのハンドラ関数
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self.tool_handlers[name] = handler
        self.logger.info(f"ツール '{name}' を登録しました")

    def start(self, server_name: str = "mcp-server-python", version: str = "0.1.0", description: str = "Python MCP Server"):
        """
        サーバーを起動し、stdioからのリクエストをリッスンします。

        Args:
            server_name: サーバー名
            version: バージョン
            description: 説明
        """
        self.logger.info(f"MCPサーバー '{server_name}' を起動しました")

        # サーバー情報を出力
        self._send_response(
            {
                "jsonrpc": "2.0",
                "method": "server/info",
                "params": {
                    "name": server_name,
                    "version": version,
                    "description": description,
                    "tools": self._get_tools(),
                    "resources": self._get_resources(),
                },
            }
        )

        # ツール情報を出力
        self._send_response(
            {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {
                    "tools": self._get_tools(),
                },
            }
        )

        # リクエストをリッスン
        while True:
            try:
                # 標準入力からリクエストを読み込む
                request_line = sys.stdin.readline()
                if not request_line:
                    break

                # リクエストをパース
                request = json.loads(request_line)
                self.logger.info(f"リクエストを受信しました: {request}")

                # リクエストを処理
                self._handle_request(request)

            except json.JSONDecodeError:
                self.logger.error("JSONのパースに失敗しました")
                self._send_error(-32700, "Parse error", None)

            except Exception as e:
                self.logger.error(f"エラーが発生しました: {str(e)}")
                self._send_error(-32603, f"Internal error: {str(e)}", None)

    def _handle_request(self, request: Dict[str, Any]):
        """
        リクエストを処理します。

        Args:
            request: JSONリクエスト
        """
        # リクエストのバリデーション
        if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
            self._send_error(-32600, "Invalid Request", request.get("id"))
            return

        if "method" not in request:
            self._send_error(-32600, "Method not specified", request.get("id"))
            return

        # メソッドの取得
        method = request["method"]
        params = request.get("params", {})
        request_id = request.get("id")

        # メソッドの処理
        if method == "initialize":
            self._handle_initialize(params, request_id)
        elif method == "tools/list":
            self._handle_tools_list(request_id)
        elif method == "tools/call":
            self._handle_tools_call(params, request_id)
        elif method == "notifications/initialized":
            self._handle_notifications_initialized(params, request_id)
        elif method == "resources/list":
            self._handle_resources_list(request_id)
        elif method == "resources/templates/list":
            self._handle_resources_templates_list(request_id)
        else:
            # 登録されたツールを直接呼び出す
            if method in self.tool_handlers:
                try:
                    result = self.tool_handlers[method](params)
                    self._send_result(result, request_id)
                except Exception as e:
                    self._send_error(-32603, f"Tool execution error: {str(e)}", request_id)
            else:
                self._send_error(-32601, f"Method not found: {method}", request_id)

    def _handle_initialize(self, params: Dict[str, Any], request_id: Any):
        """
        initializeメソッドを処理します。

        Args:
            params: リクエストパラメータ
            request_id: リクエストID
        """
        # クライアント情報を取得（オプション）
        client_name = params.get("client_name", "unknown")
        client_version = params.get("client_version", "unknown")

        self.logger.info(f"クライアント '{client_name} {client_version}' が接続しました")

        # サーバーの機能を返す
        response = {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "mcp-server-python", "version": "0.1.0", "description": "Python MCP Server"},
            "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False, "subscribe": False}},
            "instructions": "Python MCPサーバーを使用する際の注意点:\n1. 各ツールの入力パラメータを確認してください。\n2. エラーが発生した場合はログを確認してください。",
        }

        self._send_result(response, request_id)

        # ツール情報を送信
        self._send_response(
            {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {
                    "tools": self._get_tools(),
                },
            }
        )

    def _send_result(self, result: Any, request_id: Any):
        """
        成功レスポンスを送信します。

        Args:
            result: レスポンス結果
            request_id: リクエストID
        """
        response = {"jsonrpc": "2.0", "result": result, "id": request_id}

        self._send_response(response)

    def _send_error(self, code: int, message: str, request_id: Any):
        """
        エラーレスポンスを送信します。

        Args:
            code: エラーコード
            message: エラーメッセージ
            request_id: リクエストID
        """
        response = {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": request_id}

        self._send_response(response)

    def _send_response(self, response: Dict[str, Any]):
        """
        レスポンスを標準出力に送信します。

        Args:
            response: レスポンス
        """
        response_json = json.dumps(response)
        print(response_json, flush=True)
        self.logger.info(f"レスポンスを送信しました: {response_json}")

    def _get_tools(self) -> List[Dict[str, Any]]:
        """
        サーバーが提供するツールの一覧を取得します。

        Returns:
            ツールの一覧
        """
        return list(self.tools.values())

    def _handle_tools_call(self, params: Dict[str, Any], request_id: Any):
        """
        tools/callメソッドを処理します。

        Args:
            params: リクエストパラメータ
            request_id: リクエストID
        """
        # パラメータのバリデーション
        if "name" not in params:
            self._send_error(-32602, "Invalid params: name is required", request_id)
            return

        if "arguments" not in params:
            self._send_error(-32602, "Invalid params: arguments is required", request_id)
            return

        tool_name = params["name"]
        arguments = params["arguments"]

        # ツールの処理
        if tool_name in self.tool_handlers:
            try:
                result = self.tool_handlers[tool_name](arguments)
                if isinstance(result, dict) and "content" in result:
                    self._send_result(result, request_id)
                else:
                    # 結果をコンテンツ形式に変換
                    content = [{"type": "text", "text": str(result)}]
                    self._send_result({"content": content}, request_id)
            except Exception as e:
                self.logger.error(f"ツール '{tool_name}' の実行中にエラーが発生しました: {str(e)}")
                self._send_result(
                    {
                        "content": [{"type": "text", "text": f"ツールの実行中にエラーが発生しました: {str(e)}"}],
                        "isError": True,
                    },
                    request_id,
                )
        else:
            self._send_result(
                {"content": [{"type": "text", "text": f"ツールが見つかりません: {tool_name}"}], "isError": True}, request_id
            )

    def _handle_tools_list(self, request_id: Any):
        """
        tools/listメソッドを処理します。

        Args:
            request_id: リクエストID
        """
        tools = self._get_tools()
        self._send_result({"tools": tools}, request_id)

    def _handle_notifications_initialized(self, params: Dict[str, Any], request_id: Any):
        """
        notifications/initializedメソッドを処理します。
        クライアントの初期化完了通知を処理します。

        Args:
            params: リクエストパラメータ
            request_id: リクエストID
        """
        self.logger.info("クライアントの初期化が完了しました")
        # 通知なのでレスポンスは不要
        # ただし、エラーが発生した場合はエラーレスポンスを返す必要がある
        if request_id is not None:
            self._send_result({}, request_id)

    def _handle_resources_list(self, request_id: Any):
        """
        resources/listメソッドを処理します。
        利用可能なリソースの一覧を返します。

        Args:
            request_id: リクエストID
        """
        resources = self._get_resources()
        self._send_result({"resources": resources}, request_id)

    def _handle_resources_templates_list(self, request_id: Any):
        """
        resources/templates/listメソッドを処理します。
        利用可能なリソーステンプレートの一覧を返します。

        Args:
            request_id: リクエストID
        """
        templates = self._get_resource_templates()
        self._send_result({"templates": templates}, request_id)

    def _get_resources(self) -> List[Dict[str, Any]]:
        """
        サーバーが提供するリソースの一覧を取得します。

        Returns:
            リソースの一覧
        """
        return []

    def _get_resource_templates(self) -> List[Dict[str, Any]]:
        """
        サーバーが提供するリソーステンプレートの一覧を取得します。

        Returns:
            リソーステンプレートの一覧
        """
        return []
