# 中文声音生成命令

在项目根目录执行（使用已有 `.venv`，无需启动 WebUI 或 API）：

```bash
./generate-voice "开始下注" -o ../ChessGame/res/audio/gen/start_bet.wav
./generate-voice "停止下注" -o ../ChessGame/res/audio/gen/stop_bet.wav
./generate-voice "开始下注" -o ../ChessGame/res/audio/gen/start_bet.mp3
./generate-voice --help
```

默认使用 V2 预训练模型、CPU、固定随机种子 42，以及相邻 ChessGame 工程中的
`res/audio/VOICE_POINT_8_13.mp3`，参考文字为 `8点,9点,10点,11点,12点,13点`。
不指定 `-o` 时，输出到 `ChessGame/res/audio/gen/output.wav`。同名输出会被覆盖。
每次执行重新加载模型，不修改工程的持久推理配置。

更换参考声音时，录音与对应文字需同时匹配：

```bash
./generate-voice "开始下注" \
  --ref-audio /绝对路径/reference.wav \
  --ref-text "参考录音中实际说出的中文" \
  -o /绝对路径/result.wav
```

参考音频须为 3～10 秒；当前命令按中文合成，根据输出后缀生成 WAV 或 MP3。
MP3 使用 FFmpeg 编码为 128 kbps，需系统中已安装 `ffmpeg`；中间音频自动清理。
可以从任何目录通过命令的绝对路径调用，传入的相对路径均相对于调用时所在目录。
