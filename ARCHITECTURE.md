# ARCHITECTURE.md



## 概要

このアプリは、macOSのターミナル上で動くTUIポモドーロタイマーである。

ユーザーは `25` や `5` のような分数を指定する。アプリは指定分数のカウントダウンを開始し、TUI上に残り時間と進捗バーを表示する。終了時には `afplay` を使って音を鳴らす。

設計方針は「小さく、壊れにくく、後から拡張しやすく」である。

## 技術方針

- 言語: Python 3
- TUI: 標準ライブラリ `curses`
- 時刻計算: `time.monotonic()`
- 音再生: `subprocess.run(["afplay", sound_path])`
- 設定: まずは定数とCLIオプションで対応
- 依存ライブラリ: MVPではなし

## 全体構成

```text
pomo/
  __init__.py
  __main__.py
  app.py
  timer.py
  tui.py
  sound.py
  config.py
```

### `__main__.py`

`python3 -m pomo 25` で起動するためのエントリーポイント。

責務:

- CLI引数を受け取る。
- `app.run()` を呼ぶ。

### `app.py`

アプリ全体の制御を担当する。

責務:

- 分数入力の解決。
- `Timer` の生成。
- TUIループの開始。
- 終了時の音再生。
- 例外時の後始末。

### `timer.py`

タイマーの状態と時間計算を担当する。

責務:

- 合計秒数を保持する。
- 開始時刻を保持する。
- 残り秒数を返す。
- 進捗率を返す。
- 一時停止/再開を扱う。
- 完了判定を行う。

このモジュールはTUIや音再生を知らない純粋なロジックに近づける。

### `tui.py`

画面描画とキー入力を担当する。

責務:

- cursesの初期化。
- 残り時間の描画。
- セグメント型プログレスバーの描画。
- キー入力の取得。
- ターミナルサイズ変化への対応。

### `sound.py`

終了音の再生を担当する。

責務:

- `afplay` が使えるか確認する。
- 指定された音声ファイルを再生する。
- 失敗時にベル文字 `\a` へフォールバックする。

### `config.py`

デフォルト値をまとめる。

例:

```python
DEFAULT_WORK_MINUTES = 25
DEFAULT_BREAK_MINUTES = 5
DEFAULT_SOUND_PATH = "/System/Library/Sounds/Glass.aiff"
DEFAULT_SEGMENTS = 24
TICK_INTERVAL_SEC = 0.2
```

## 状態モデル

タイマーは以下の状態を持つ。

```text
IDLE
  ↓ start
RUNNING
  ↓ pause
PAUSED
  ↓ resume
RUNNING
  ↓ finish
FINISHED
```

### `IDLE`

まだタイマーが開始されていない状態。

### `RUNNING`

カウントダウン中。

### `PAUSED`

一時停止中。残り時間は減らない。

### `FINISHED`

タイマーが完了した状態。音再生を行い、終了表示に切り替える。

## 時間計算

タイマーは `time.sleep(1)` の積み上げで残り時間を管理しない。

代わりに、開始時に `deadline` を作る。

```text
start_monotonic = time.monotonic()
deadline = start_monotonic + duration_seconds
remaining = max(0, deadline - time.monotonic())
```

この方式により、描画ループが多少遅延してもタイマー全体のズレが少ない。

一時停止時は、停止した瞬間の残り秒数を保存する。再開時に現在時刻から新しい `deadline` を作り直す。

```text
paused_remaining = deadline - pause_time
resume_deadline = time.monotonic() + paused_remaining
```

## 描画設計
見た目のイメージは sample.png として置いてあるので適宜参照すること
TUIは1フレームごとに以下を描画する。

1. タイトル。
2. セグメント型プログレスバー。
3. 残り時間 `MM:SS`。
4. 操作ヘルプ。

### プログレスバー

バーは固定個数のセグメントで表現する。

```text
████ ████ ████ ████ ░░░░ ░░░░
```

進捗率から点灯セグメント数を計算する。

```text
ratio = remaining_seconds / total_seconds
active_segments = ceil(total_segments * ratio)
```

ポモドーロでは「時間が減っていく」ことが直感的なので、残り時間が減るほど点灯セグメントも減らす。

### 色

cursesで色が使える場合は、セグメント位置に応じて色を変える。

例:

- 前半: 緑系
- 中盤: 黄系
- 終盤: 赤系
- 空き: 暗い灰色

ただしMVPでは、色が使えない環境でも読めることを優先する。



## 入力設計

MVPで扱うキー:

```text
q: quit
p: pause/resume
r: restart
```

キー入力はノンブロッキングで取得する。

```python
stdscr.nodelay(True)
key = stdscr.getch()
```

描画更新は `TICK_INTERVAL_SEC` ごとに行う。

## 音再生設計

終了時に以下を実行する。

```sh
afplay /System/Library/Sounds/Glass.aiff
```

Pythonからは以下のように呼ぶ。

```python
subprocess.run(["afplay", sound_path], check=False)
```

音再生に失敗してもアプリ全体は落とさない。

フォールバック:

1. `afplay` があれば `afplay`。
2. なければターミナルベル `\a`。
3. それも目立たない場合は `DONE` 表示を点滅させる。

## エラーハンドリング

### 無効な分数

以下はエラーにする。

- 空文字
- 0以下
- 数字以外
- 極端に大きい値

例:

```text
error: minutes must be a positive integer: 25
```

### ターミナルが小さい

最低限のコンパクト表示に切り替える。

```text
12:34 [#####-----] q:quit
```

### `afplay` がない

警告だけ出して、ベルにフォールバックする。

## テスト方針

### `timer.py`

最重要。TUIから切り離してテストする。

- 初期残り秒数。
- 時間経過後の残り秒数。
- 完了判定。
- pause/resume。
- progress ratio。

### `sound.py`

- `afplay` がある場合の呼び出し。
- `afplay` がない場合のフォールバック。
- 存在しない音声ファイル指定時の挙動。

### `tui.py`

curses自体の細かい見た目は自動テストしにくいので、描画文字列を作る関数を切り出してテストする。

例:

```python
render_bar(total_segments=10, active_segments=6)
# => "████ ████ ████ ████ ████ ████ ░░░░ ░░░░ ░░░░ ░░░░"
```

## 将来拡張

### ポモドーロサイクル

```sh
pomo --cycle 25 5
```

作業25分と休憩5分を交互に繰り返す。

### 長休憩

```sh
pomo --work 25 --break 5 --long-break 15 --rounds 4
```

4セットごとに15分休憩する。

### 終了後の自動遷移

作業完了後に自動で休憩タイマーへ移る。

### 設定ファイル

```toml
work_minutes = 25
break_minutes = 5
long_break_minutes = 15
sound = "/System/Library/Sounds/Glass.aiff"
segments = 24
```

### 通知

macOSでは `osascript` を使って通知センターへ通知できる。

```sh
osascript -e 'display notification "Pomodoro finished" with title "pomo"'
```

ただしMVPでは `afplay` のみでよい。

## 設計上の重要ポイント

- タイマー計算とTUI描画を分離する。
- 時刻は `monotonic()` で扱う。
- 音再生失敗でアプリを落とさない。
- TUIが壊れてもタイマーのロジックはテスト可能にする。
- 最初は25分/5分が気持ちよく使えることだけに集中する。
