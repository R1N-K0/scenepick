# scenepick

撮影した写真を 1 枚ずつ見て、データセットに入れるか捨てるかを決めるためのローカル Web アプリ。
ピンボケ、白飛び、被写体の切れといった失敗を弾くために使う。

判定結果は `{image_id: status}` だけの JSON に書く。image_id は RGB のファイル名から拡張子を
取ったもの。それ以外は何も持たない。

## 準備

```
uv venv
uv pip install -r requirements.txt
cp .env.example .env          # DATA_ROOT に画像のある場所を書く
```

`.env` はこれだけ。`DATA_ROOT` に `.jpg` か `.png` が並んでいればよい。サブディレクトリは作らない。
`.json` など他のファイルが同じ場所にあっても、拡張子で無視する。

```
DATA_ROOT=D:/hs2026
```

実データがまだ無いときは dummy を作る。

```
python tools/make_dummy.py
```

## 使う

```
python tools/make_thumbs.py   # サムネイルを先に作る
python app.py                 # http://localhost:5000
```

一覧画面に全枚数がサムネイルで撮影順に並ぶ。keep か reject を押すと即座に保存されるので、
いつ閉じても続きから再開できる。「unjudged only」で未判定だけに絞れる。

サムネイルをクリックすると詳細画面。等倍で表示されるのでピントを確認できる。画像をクリック
すると画面に収まるサイズに切り替わる。

| 操作 | 詳細画面 |
| --- | --- |
| `1` | keep にして次へ |
| `0` | reject にして次へ |
| `←` `→` | 判定せず前後へ |
| `Esc` | メニューを閉じる |

ヘッダー右の `☰` で全ファイルの一覧が出る。緑が keep、赤が reject。`◐` で背景の明暗を切り替える。

## 判定を元データに戻す

```
python tools/add_status.py
```

`DATA_ROOT/data.json` に `status` を足して `data/meta_data.json` に書き出す。元のファイルは
書き換えない。DATA_ROOT には何も書かない。

## 置き場所

| 場所 | 中身 |
| --- | --- |
| `DATA_ROOT/{image_id}.jpg` | 写真。ファイル名が image_id |
| `data/selection.json` | 判定結果。このアプリが書く唯一のファイル |
| `cache/thumb/` | サムネイル。消して作り直しても安全 |
| `.env` | DATA_ROOT。コミットしない |

画像を追加または削除したら、アプリを再起動する。起動時に `DATA_ROOT` を読み直し、`selection.json`
に足りない image_id を `unjudged` で追記する。既にある判定は書き換えない。
