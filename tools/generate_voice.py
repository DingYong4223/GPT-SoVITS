"""使用默认 V2 模型和参考录音生成中文 WAV 或 MP3。"""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


PROJECT_DIR = Path(__file__).resolve().parents[1]
AUDIO_DIR = PROJECT_DIR.parent / "ChessGame/res/audio"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", help="要合成的中文文本，如：开始下注")
    parser.add_argument(
        "-o", "--output", type=Path, default=AUDIO_DIR / "gen/output.wav",
        help="输出 WAV 或 MP3 文件路径（默认：ChessGame/res/audio/gen/output.wav；覆盖同名文件）",
    )
    parser.add_argument(
        "--ref-audio", type=Path, default=AUDIO_DIR / "VOICE_POINT_8_13.mp3",
        help="3～10 秒的中文参考录音路径",
    )
    parser.add_argument(
        "--ref-text", default="8点,9点,10点,11点,12点,13点",
        help="参考录音对应的文字，直接传文字，无需文本文件",
    )
    args = parser.parse_args()
    if not args.text.strip() or not args.ref_text.strip():
        parser.error("合成文本和参考文本不能为空")
    output = args.output.expanduser().resolve()
    ref_audio = args.ref_audio.expanduser().resolve()
    if not ref_audio.is_file():
        parser.error(f"参考录音不存在：{ref_audio}")
    if output.suffix.lower() not in (".wav", ".mp3"):
        parser.error("输出文件必须使用 .wav 或 .mp3 后缀")
    if output == ref_audio:
        parser.error("输出文件不能覆盖参考录音")
    if output.suffix.lower() == ".mp3" and not shutil.which("ffmpeg"):
        parser.error("输出 MP3 需要 FFmpeg，请先安装并加入 PATH")

    # 模型路径由工程根目录解析；用户路径在切换目录前解析。
    os.chdir(PROJECT_DIR)
    sys.path[:0] = [str(PROJECT_DIR), str(PROJECT_DIR / "GPT_SoVITS")]
    import numpy as np
    import soundfile as sf
    from TTS_infer_pack.TTS import TTS, TTS_Config

    with TemporaryDirectory(prefix="gpt-sovits-") as tmp:
        config = TTS_Config({"custom": TTS_Config.default_configs["v2"]})
        config.configs_path = str(Path(tmp) / "tts_infer.yaml")
        config.device = "cpu"
        config.is_half = False
        tts = TTS(config)
        sr, audio = next(tts.run({
            "text": args.text,
            "text_lang": "all_zh",
            "ref_audio_path": str(ref_audio),
            "prompt_text": args.ref_text,
            "prompt_lang": "all_zh",
            "seed": 42,
        }))
        if not audio.size or not np.isfinite(audio).all() or not np.any(audio):
            raise RuntimeError("合成结果为空、静音或包含无效数值，未写入输出文件")
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.suffix.lower() == ".mp3":
            wav_path = Path(tmp) / "audio.wav"
            mp3_path = Path(tmp) / "audio.mp3"
            sf.write(str(wav_path), audio, sr, subtype="PCM_16")
            subprocess.run([
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                "-y", "-i", str(wav_path), "-codec:a", "libmp3lame",
                "-b:a", "128k", str(mp3_path),
            ], check=True)
            shutil.copyfile(mp3_path, output)
        else:
            sf.write(str(output), audio, sr, subtype="PCM_16")
        print(f"已生成：{output}（{len(audio) / sr:.2f} 秒，{sr} Hz）")


if __name__ == "__main__":
    main()
