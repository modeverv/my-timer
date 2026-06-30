# pomo

`pomo` は、ターミナル上で動くシンプルなTUIポモドーロタイマーである。

画像のような「横長のセグメント型プログレスバー」と「デジタル残り時間表示」を目指す。

```text
POMODORO

████ ████ ████ ████ ████ ████ ████ ░░░░ ░░░░ ░░░░

                         12:34

p: pause/resume   r: restart   q: quit
```

## 目的

ポモドーロテクニック用に、作業25分、休憩5分のような短いタイマーを素早く起動する。

```sh
pomo 25
pomo 5
```

タイマー終了時には macOS の `afplay` で音を鳴らす。

## 特徴

- 分数を指定するだけで開始。
- TUIで残り時間を表示。
- セグメント型プログレスバーを表示。
- 同梱したフリー音源を `afplay` で再生する終了音。
- 色対応ターミナルでは、進捗バーを緑、黄、赤、暗色で表示。
- `p` で一時停止/再開。
- `r` でリスタート。
- `q` で終了。
- Python標準ライブラリ中心で軽量に実装。

## 必要環境

- macOS
- Python 3.10以上
- `afplay`
- curses対応ターミナル

macOSには通常 `afplay` が最初から入っている。

確認:

```sh
which afplay
```

## インストール

開発中はリポジトリをcloneして直接実行する。

```sh
git clone <repo-url>
cd pomo
python3 main.py 25
```

パッケージ化後は以下を想定する。

```sh
pipx install .
pomo 25
```

テスト実行には `pytest` を使う。

```sh
python3 -m pip install pytest
python3 -m pytest
```

## 使い方

### 25分タイマー

```sh
pomo 25
```

### 5分タイマー

```sh
pomo 5
```

### 引数なしで起動

```sh
pomo
```

その場合は分数入力を求める。

```text
Minutes: 25
```

## 操作キー

| キー | 動作 |
|---|---|
| `p` | 一時停止/再開 |
| `r` | 現在の分数でリスタート |
| `q` | 終了 |
| `Ctrl-C` | 強制終了 |

## 終了音

デフォルトでは以下を鳴らす。

```text
pomo/assets/alarm-or-siren.mp3
```

音源は Wikimedia Commons の public domain 音源を同梱している。詳細は `THIRD_PARTY_NOTICES.md` を参照。

内部的には以下と同等のことを行う。

```sh
afplay pomo/assets/alarm-or-siren.mp3
```

将来的には `--sound` オプションで変更可能にする。

```sh
pomo 25 --sound /System/Library/Sounds/Ping.aiff
```

## 開発用ディレクトリ構成

```text
pomo/
  __init__.py
  __main__.py
  app.py
  timer.py
  tui.py
  sound.py
  config.py
tests/
  test_timer.py
  test_sound.py
README.md
PLAN.md
ARCHITECTURE.md
pyproject.toml
```

## 実装方針

タイマーの時間計算には `time.monotonic()` を使う。

単純に `sleep(1)` を積み上げると、描画遅延や処理遅延でズレが出る。そこで、開始時に終了予定時刻を決め、毎フレーム現在時刻との差分から残り時間を計算する。

```python
remaining = max(0, deadline - time.monotonic())
```

これにより、TUIの描画が少し遅れてもタイマー全体の精度が保たれやすい。

## 最小実装の仕様

### 入力

分数は正の整数のみ。

有効:

```sh
pomo 25
pomo 5
pomo 1
```

無効:

```sh
pomo 0
pomo -1
pomo abc
```

### 表示

- 残り時間は `MM:SS`。
- プログレスバーは残り時間に応じて短くなる。
- タイマー終了時は `DONE` を表示する。

### 終了

残り時間が0になったら終了音を鳴らす。

その後、以下のどちらかの挙動にする。

- `DONE` 表示のままキー入力待ち。
- 音を鳴らしたあと自動終了。

MVPでは「`DONE` 表示のままキー入力待ち」を推奨する。理由は、終了に気づかなかった場合でも画面上で完了状態が残るため。

## 開発メモ

### curses起動時の注意

TUIアプリは例外で落ちるとターミナル表示が崩れることがある。そのため、`curses.wrapper()` を使う。

```python
import curses

curses.wrapper(main)
```

### キー入力

ノンブロッキング入力にする。

```python
stdscr.nodelay(True)
```

### 更新間隔

描画更新は0.2秒程度でよい。

```python
TICK_INTERVAL_SEC = 0.2
```

表示上は滑らかで、CPU負荷も低い。

## 将来の拡張案

### ポモドーロサイクル

作業25分、休憩5分を繰り返す。

```sh
pomo --cycle 25 5
```

### 長休憩

4セットごとに15分休憩する。

```sh
pomo --work 25 --break 5 --long-break 15 --rounds 4
```

### macOS通知

`osascript` を使って通知センターに出す。

```sh
osascript -e 'display notification "Timer finished" with title "pomo"'
```

### 設定ファイル

```toml
work_minutes = 25
break_minutes = 5
sound = "/System/Library/Sounds/Glass.aiff"
segments = 24
```

## ライセンス

MIT
