## 準備

```
uv venv
uv pip install -r requirements.txt
cp .env.example .env          # DATA_ROOT に画像のある場所を書く
```

`.env` はこれだけ。`DATA_ROOT` の下に `.jpg` か `.png` があればよい。サブディレクトリの中も探す。
`.json` など他のファイルが混ざっていても、拡張子で無視する。ファイル名から拡張子を取ったものが
image_id になるので、同じファイル名が2つあると起動時に止まる。

```
DATA_ROOT=D:/hs2026
```

実データがまだ無いときは dummy を作る。

```
python tools/make_dummy.py
```

## 使い方

```
python tools/make_thumbs.py   # サムネイルを先に作る(少し時間がかかる)
python app.py                 # http://localhost:5000
```

一覧画面に全枚数がサムネイルで撮影順に並ぶ。keep か reject を押すと即座に保存されるので、
いつ閉じても続きから再開できる。「unjudged only」で未判定だけに絞れる。

サムネイルをクリックすると詳細画面。最初は写真全体が映る。ヘッダー右の `⛶` かダブルクリックで
等倍に切り替わる.

| キー | 詳細画面 |
| --- | --- |
| `1` | keep。もう一度押すと unjudged に戻る |
| `0` | reject。もう一度押すと unjudged に戻る |
| `←` `→` | 判定せず前後へ |
| `Esc` | メニューを閉じる |

判定しても画面は動かない。押し間違えてもその場で押し直せる。

ヘッダー右の `☰` で全ファイルの一覧が出る。緑が keep、赤が reject。`◐` で背景の明暗を切り替える。

## グループごとに表示する

`DATA_ROOT/groups.json` があれば、その区切りで見出しを挟んで並べる。無ければ今まで通り一列に並ぶ。

```json
[
  {"name": "1", "image_ids": ["20260810_090000_wb", "20260810_090020_cc"]},
  {"name": "2", "image_ids": ["20260810_093000_wb"]}
]
```


## 置き場所

| 場所 | 中身 |
| --- | --- |
| `DATA_ROOT/**/{image_id}.png` | 写真。ファイル名が image_id |
| `DATA_ROOT/groups.json` | グループ分け。任意 |
| `data/selection.json` | 判定結果。このアプリが書く唯一のファイル |
| `cache/thumb/` | サムネイル。消して作り直しても安全 |
| `.env` | DATA_ROOT。コミットしない |

画像を追加または削除したら、アプリを再起動する。起動時に `DATA_ROOT` を読み直し、`selection.json`
に足りない image_id を `unjudged` で追記する。既にある判定は書き換えない。
