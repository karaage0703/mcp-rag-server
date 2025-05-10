# Python基礎知識

## Pythonとは

Pythonは、汎用プログラミング言語の一つで、コードの読みやすさを重視した設計思想を持っています。インタープリタ型言語であり、動的型付け言語です。多くのプラットフォームで動作し、大規模なシステムから小さなスクリプトまで、さまざまな用途に使用されています。

## Pythonの特徴

- **読みやすい構文**: インデントを使用したブロック構造により、コードが読みやすい
- **豊富なライブラリ**: 標準ライブラリが充実しており、多くのサードパーティライブラリも利用可能
- **マルチパラダイム**: 手続き型、オブジェクト指向型、関数型など、複数のプログラミングパラダイムをサポート
- **インタープリタ型**: コンパイル不要で実行可能
- **動的型付け**: 変数の型を明示的に宣言する必要がない
- **自動メモリ管理**: ガベージコレクションによるメモリ管理

## Pythonの基本構文

### 変数と型

Pythonでは、変数を宣言する際に型を指定する必要はありません。

```python
# 整数
x = 10

# 浮動小数点数
y = 3.14

# 文字列
name = "Python"

# ブール値
is_active = True

# リスト
numbers = [1, 2, 3, 4, 5]

# タプル
coordinates = (10, 20)

# 辞書
person = {"name": "Alice", "age": 30}

# 集合
unique_numbers = {1, 2, 3, 4, 5}
```

### 条件分岐

```python
x = 10

if x > 0:
    print("正の数です")
elif x < 0:
    print("負の数です")
else:
    print("ゼロです")
```

### ループ

```python
# forループ
for i in range(5):
    print(i)  # 0, 1, 2, 3, 4

# whileループ
count = 0
while count < 5:
    print(count)
    count += 1
```

### 関数

```python
def greet(name):
    """挨拶を返す関数"""
    return f"こんにちは、{name}さん！"

# 関数の呼び出し
message = greet("太郎")
print(message)  # こんにちは、太郎さん！
```

### クラス

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def introduce(self):
        return f"私の名前は{self.name}、{self.age}歳です。"

# クラスのインスタンス化
person = Person("太郎", 30)
print(person.introduce())  # 私の名前は太郎、30歳です。
```

## Pythonの高度な機能

### ジェネレータ

ジェネレータは、イテレータを作成するための簡単な方法です。メモリ効率が良く、大きなデータセットを扱う際に役立ちます。

```python
def count_up_to(n):
    i = 0
    while i < n:
        yield i
        i += 1

# ジェネレータの使用
for number in count_up_to(5):
    print(number)  # 0, 1, 2, 3, 4
```

### デコレータ

デコレータは、関数やメソッドの動作を変更するための構文です。

```python
def log_function_call(func):
    def wrapper(*args, **kwargs):
        print(f"関数 {func.__name__} が呼び出されました")
        return func(*args, **kwargs)
    return wrapper

@log_function_call
def add(a, b):
    return a + b

result = add(3, 5)  # 関数 add が呼び出されました
print(result)  # 8
```

### コンテキストマネージャ

`with`文を使用して、リソースの確保と解放を自動的に行うことができます。

```python
# ファイル操作の例
with open("example.txt", "w") as file:
    file.write("Hello, World!")
# ファイルは自動的に閉じられる
```

### 内包表記

リスト、辞書、集合の作成を簡潔に記述できます。

```python
# リスト内包表記
squares = [x**2 for x in range(10)]

# 条件付きリスト内包表記
even_squares = [x**2 for x in range(10) if x % 2 == 0]

# 辞書内包表記
square_dict = {x: x**2 for x in range(5)}

# 集合内包表記
square_set = {x**2 for x in range(5)}
```

## Pythonのモジュールとパッケージ

### モジュール

モジュールは、Pythonのコードを論理的に整理するための方法です。

```python
# math モジュールのインポート
import math

# math モジュールの関数を使用
print(math.sqrt(16))  # 4.0

# 特定の関数だけをインポート
from math import sqrt
print(sqrt(16))  # 4.0

# 別名をつけてインポート
import math as m
print(m.sqrt(16))  # 4.0
```

### パッケージ

パッケージは、複数のモジュールを含むディレクトリです。

```
my_package/
    __init__.py
    module1.py
    module2.py
    subpackage/
        __init__.py
        module3.py
```

```python
# パッケージのインポート
import my_package.module1

# サブパッケージのインポート
import my_package.subpackage.module3
```

## Pythonの例外処理

```python
try:
    # 例外が発生する可能性のあるコード
    result = 10 / 0
except ZeroDivisionError:
    # ゼロ除算エラーの処理
    print("ゼロで割ることはできません")
except Exception as e:
    # その他の例外の処理
    print(f"エラーが発生しました: {e}")
else:
    # 例外が発生しなかった場合の処理
    print("計算が成功しました")
finally:
    # 例外の有無にかかわらず実行される処理
    print("処理を終了します")
```

## Pythonの標準ライブラリ

Pythonには、多くの便利な標準ライブラリが含まれています。

- **os**: オペレーティングシステムとの対話
- **sys**: Pythonインタープリタとの対話
- **datetime**: 日付と時刻の操作
- **math**: 数学関数
- **random**: 乱数生成
- **json**: JSONデータの処理
- **re**: 正規表現
- **collections**: 特殊なコンテナデータ型
- **itertools**: イテレータ操作のための関数
- **functools**: 高階関数と呼び出し可能オブジェクトの操作

## Pythonの仮想環境

仮想環境は、プロジェクトごとに独立したPython環境を作成するための機能です。

```bash
# 仮想環境の作成
python -m venv myenv

# 仮想環境の有効化（Windows）
myenv\Scripts\activate

# 仮想環境の有効化（macOS/Linux）
source myenv/bin/activate

# パッケージのインストール
pip install package_name

# 仮想環境の無効化
deactivate
```

## Pythonのパッケージ管理

```bash
# パッケージのインストール
pip install package_name

# 特定のバージョンのインストール
pip install package_name==1.0.0

# パッケージのアップグレード
pip install --upgrade package_name

# インストール済みパッケージの一覧表示
pip list

# requirements.txtの作成
pip freeze > requirements.txt

# requirements.txtからのインストール
pip install -r requirements.txt
```

## Pythonのテスト

### unittest

```python
import unittest

def add(a, b):
    return a + b

class TestAddFunction(unittest.TestCase):
    def test_add_positive_numbers(self):
        self.assertEqual(add(1, 2), 3)
    
    def test_add_negative_numbers(self):
        self.assertEqual(add(-1, -2), -3)
    
    def test_add_mixed_numbers(self):
        self.assertEqual(add(-1, 2), 1)

if __name__ == "__main__":
    unittest.main()
```

### pytest

```python
# test_add.py
def add(a, b):
    return a + b

def test_add_positive_numbers():
    assert add(1, 2) == 3

def test_add_negative_numbers():
    assert add(-1, -2) == -3

def test_add_mixed_numbers():
    assert add(-1, 2) == 1
```

```bash
# pytestの実行
pytest test_add.py
```

## Pythonのデバッグ

### pdb（Python Debugger）

```python
import pdb

def complex_function():
    x = 10
    y = 20
    pdb.set_trace()  # デバッガが起動
    z = x + y
    return z

result = complex_function()
```

## Pythonのドキュメント

### Docstring

```python
def calculate_area(radius):
    """
    円の面積を計算します。
    
    Args:
        radius (float): 円の半径
    
    Returns:
        float: 円の面積
    
    Raises:
        ValueError: 半径が負の値の場合
    """
    if radius < 0:
        raise ValueError("半径は負の値にできません")
    return 3.14159 * radius ** 2
```

## Pythonのコーディング規約

Pythonには、PEP 8と呼ばれるコーディング規約があります。主なルールは以下の通りです：

- インデントには4つのスペースを使用
- 行の長さは最大79文字
- 関数やクラスの間には2行の空行
- インポートは別々の行に記述
- スペースの使用法（演算子の前後にスペース、カンマの後にスペースなど）
- 命名規則（クラス名はCamelCase、関数名とメソッド名はlower_case_with_underscoresなど）

## まとめ

Pythonは、読みやすさと書きやすさを重視した汎用プログラミング言語です。豊富な標準ライブラリとサードパーティライブラリにより、さまざまな用途に使用できます。初心者にも優しい言語設計でありながら、高度な機能も備えているため、プログラミング初心者から専門家まで幅広く利用されています。