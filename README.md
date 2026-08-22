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
python tools/make_thumbs.py   # サムネイルを先に作る
python app.py                 # http://localhost:5000
```

一覧画面に全枚数がサムネイルで撮影順に並ぶ。keep か reject を押すと即座に保存されるので、
いつ閉じても続きから再開できる。「unjudged only」で未判定だけに絞れる。

サムネイルをクリックすると詳細画面。等倍で表示されるのでピントを確認できる。画像をクリック
すると画面に収まるサイズに切り替わる。

ヘッダー右の `☰` で全ファイルの一覧が出る。緑が keep、赤が reject。`◐` で背景の明暗を切り替える。

## グループごとに表示する

`DATA_ROOT/groups.json` があれば、その区切りで見出しを挟んで並べる。無ければ今まで通り一列に並ぶ。

```json
[
  {"name": "scene 1", "image_ids": ["20260810_090000_wb", "20260810_090020_cc"]},
  {"name": "scene 2", "image_ids": ["20260810_093000_wb"]}
]
```

`name` が見出しに出る。リストの順がそのまま表示順。グループの中は image_id 順、つまり撮影順のまま。
どのグループにも入らなかった画像は最後に `ungrouped` として出る。隠れることはない。

見出しの名前の横に、そのグループの枚数と keep / reject の数が出る。絞り込んでも数は変わらない。
グループ全体の数であって、今見えている数ではない。

ページは分かれない。見出しはスクロールに追従するだけで、そのまま下まで流して選定できる。

## 置き場所

| 場所 | 中身 |
| --- | --- |
| `DATA_ROOT/**/{image_id}.jpg` | 写真。ファイル名が image_id |
| `DATA_ROOT/groups.json` | グループ分け。任意 |
| `data/selection.json` | 判定結果。このアプリが書く唯一のファイル |
| `cache/thumb/` | サムネイル。消して作り直しても安全 |
| `.env` | DATA_ROOT。コミットしない |

画像を追加または削除したら、アプリを再起動する。起動時に `DATA_ROOT` を読み直し、`selection.json`
に足りない image_id を `unjudged` で追記する。既にある判定は書き換えない。
