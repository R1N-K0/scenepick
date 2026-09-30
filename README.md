## 準備

```
uv venv
uv pip install -r requirements.txt
cp .env.example .env          # DATA_ROOT に画像のある場所を書く
```

`.env` に要るのは `DATA_ROOT` だけ。`DATA_ROOT` の下に `.jpg` か `.png` があればよい。サブディレクトリの中も探す。
NAS で使うときは `RGB_ROOT`・`SELECTION`・`PORT` も書く（→「NAS で使う」）。
`.json` など他のファイルが混ざっていても、拡張子で無視する。ファイル名から拡張子を取ったものが
image_id になるので、同じファイル名が2つあると起動時に止まる。

```
DATA_ROOT=D:/hs2026
```

実データがまだ無いときは dummy を作る。

```
python tools/make_dummy.py
```

## NAS で使う

画像も `group.json` も判定も NAS に置き，リモートの Windows から scenepick を動かす．
ファイルを手で置いたり，消したり，送ったりすることは無い．

**初回だけ**

自分のユーザーのフォルダの直下（例 `C:\Users\<自分>\scenepick`）に clone する．OneDrive が同期しているフォルダ（ドキュメント・デスクトップなど）と NAS の中は避ける
（`.venv/` とサムネイルの何千ものファイルが同期や NAS の上に乗って遅くなり，NAS ではもう1人の選定担当の分と混ざる）．

```
git clone https://github.com/R1N-K0/scenepick.git
```

clone しておけば，`start.bat` が起動のたびに `git pull` して最新になる（ZIP で落としたものも動くが，更新は受け取らない）．
そのあと `setup_nas.bat` をダブルクリックする。Python の環境（`.venv/`）を作り，`.env` を書く．
`.env` は，`cvpr_work` のある NAS のドライブを探して，次の形で書く（見つからなければ，エクスプローラーのアドレス欄からパスを貼ってもらう）．
`.env` が既にあれば書き換えない．

```
DATA_ROOT=Z:\datasets\hyperspectral\cvpr_work
RGB_ROOT=Z:\datasets\hyperspectral\cvpr_dataset\*\rgb_sat
SELECTION=Z:\datasets\hyperspectral\cvpr_work\scenepick\selection.json
PORT=5101
```

- `RGB_ROOT` は画像（読むだけ）．各まとまりには同じ画像が `rgb/`・`rgb_sat/`・`rgb_view/` の3版あるので，`*/rgb_sat` で選定用の版（飽和したところが赤くなる）だけを読む．まとまりが増えても書き換えない
- `DATA_ROOT` は `group.json` と `calibration.json`（本人が置く），`SELECTION` は判定を書く場所
- `PORT` は選定担当2人とも **5101**．同じ番号なので，1人が立ち上げているあいだにもう1人が立ち上げようとすると「port 5101 is already in use」で止まる．選定は1人ずつ行うので，止まったら相手が作業中ということ（声をかける）．マスクを手伝う人の maskeditor は 5201 から，5000 は誰も使わない
- 起動すると，これから判定する画像（unjudged でシーンに入っているもの）を先の 300 枚まで裏で読んでメモリに置く．NAS から1枚読むより判定する方が速いので，読み終えるまで一覧に「先に読み込んでいます 37 / 300（あと約 130 秒）」と出る．待ってから始めると，途中で待たされない（待たずに始めてもよい）．判定しながら先を読み足し，通り過ぎた分は捨てる．
  メモリは 300 枚で約 1.4 GB（8 bit の PNG にして持つ．ブラウザは 16 bit の PNG も 8 bit で表示するので見え方は同じ）．NAS の画像は読むだけで変えない．枚数は `.env` の `PREFETCH=150` のように変えられる（リモートの Windows は皆でつないでいて空きが 10 GB ほどなので，大きくしすぎない）
- `.bat` は CRLF で commit してある（`.gitattributes`）．LF だと cmd がラベルを読み違える

**まとまりごと**

本人から「まとまり N の `group.json` ができた」と連絡が来たら：

1. `start.bat` をダブルクリック．clone なら最新を受け取り，新しい分のサムネイルを作り，scenepick を立ち上げ，ブラウザで `http://localhost:5101` を開く．
   止めるときは黒いウィンドウを閉じる（起動中なら閉じてからダブルクリックし直す）
2. 黒いウィンドウに「port 5101 is already in use」と出たら，もう1人が作業中．閉じて声をかける
3. 「unjudged only」で，今回の分を全部 keep か reject にする
4. 終わったら本人に伝える．判定は `SELECTION` に保存されているので，送らなくてよい

- 起動時の1行 `group.json: N grouped, M ungrouped, ...` の `ungrouped` は，NAS に置かれたがまだ `group` されていない画像．
  **`ungrouped` の画像は判定しない．** 次の連絡のあと，シーンに分かれてから判定する
- **NAS の `cvpr_dataset/` と `cvpr_work/` の中のファイルは，開いて書き換えたり，消したり，動かしたりしない．** 画像は RGB 化担当の，`cvpr_work/` は本人とアプリの置き場所
- **scenepick は1か所でだけ動かす．** 2か所で同時に立ち上げると，同じ `selection.json` を両方が書き直し，片方の判定が消える（同じ Windows なら，上の 5101 で2つ目は止まる）
- `cache/thumb/` はいつ消してもよい（作り直せる）

## 使い方

```
python tools/make_thumbs.py   # サムネイルを先に作る(少し時間がかかる)
python app.py                 # http://localhost:5000
```

一覧画面に全枚数がサムネイルで撮影順に並ぶ。keep か reject を押すと即座に保存されるので、
いつ閉じても続きから再開できる。「unjudged only」で未判定だけに絞れる。

サムネイルをクリックすると詳細画面。最初は写真全体が映る。ヘッダー右の `⛶` かダブルクリックで
等倍に切り替わる．ヘッダーには今のシーン（`scene N`）が出る．

「unjudged only」は一覧と詳細画面で同じものを指す．入れたときに unjudged だった画像だけを `←` `→` でたどり，
位置も `3 / 120 unjudged` のようにその中で数える．判定しても外れないので，`←` で今判定した画像に戻って押し直せる．
入れ直すか一覧に戻ると，その時点の unjudged に絞り直す．

| キー | 詳細画面 |
| --- | --- |
| `1` | keep。もう一度押すと unjudged に戻る |
| `0` | reject。もう一度押すと unjudged に戻る |
| `←` `→` | 判定せず前後へ |
| `Esc` | メニューを閉じる |

判定しても画面は動かない。押し間違えてもその場で押し直せる。

ヘッダー右の `☰` で全ファイルの一覧が出る。緑が keep、赤が reject。`◐` で背景の明暗を切り替える。

## グループごとに表示する

`DATA_ROOT/group.json` があれば、その区切りで見出しを挟んで並べる。無ければ今まで通り一列に並ぶ。

```json
[
  {"name": "1", "image_ids": ["20260810_090000_01", "20260810_090020_01"]},
  {"name": "2", "image_ids": ["20260810_093000_01"]}
]
```

## 白板の枠を表示する

`DATA_ROOT/calibration.json` があれば、詳細画面で白板の範囲を細い枠で重ねる。全体表示でも等倍でも
同じ位置に出る。無ければ今まで通り。枠を出すだけで、判定には使わない。

```json
{"20260810_090000_01": [812, 530, 1172, 770]}
```

値は元画像のピクセル座標で `[x0, y0, x1, y1]`。x1 と y1 は含まない。載っていない画像には枠が出ない。
形が崩れた値があると起動時に止まる。

## 置き場所

| 場所 | 中身 |
| --- | --- |
| `DATA_ROOT/**/{image_id}.png` | 写真。ファイル名が image_id（`RGB_ROOT` を書いたらその下） |
| `DATA_ROOT/group.json` | グループ分け。任意 |
| `DATA_ROOT/calibration.json` | 白板の範囲。任意 |
| `data/selection.json` | 判定結果。このアプリが書く唯一のファイル（`SELECTION` を書いたらそちら） |
| `cache/thumb/` | サムネイル。消して作り直しても安全 |
| `.env` | DATA_ROOT。コミットしない |

画像を追加または削除したら、アプリを再起動する。起動時に `DATA_ROOT` を読み直し、`selection.json`
に足りない image_id を `unjudged` で追記する。既にある判定は書き換えない。
