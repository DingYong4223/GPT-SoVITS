"""无需加载模型的命令行参数检查。"""

from pathlib import Path
import os
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from tools.generate_voice import resolve_output


class GenerateVoiceTest(unittest.TestCase):
    def test_directory_output_uses_first_four_characters(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve()
            for text, name in [
                ("不要", "buyao.mp3"),
                ("开始下注", "kaishixiazhu.mp3"),
                ("开始下注请稍候", "kaishixiazhu.mp3"),
                ("  不要！ ", "buyao.mp3"),
                ("不要/下注", "buyaoxiazhu.mp3"),
            ]:
                with self.subTest(text=text):
                    self.assertEqual(resolve_output(text, directory), directory / name)
            self.assertEqual(resolve_output("不要", directory / "new"), directory / "new/buyao.mp3")
            self.assertEqual(resolve_output("不要", directory / "custom.wav"), directory / "custom.wav")
            with self.assertRaises(ValueError):
                resolve_output("！！！", directory)

    def test_rejects_invalid_input_before_loading_models(self):
        script = Path(__file__).with_name("generate_voice.py")
        with TemporaryDirectory() as tmp:
            reference = Path(tmp) / "reference.wav"
            reference.touch()
            cases = [
                ([" "], "不能为空"),
                (["开始下注", "--ref-audio", str(Path(tmp) / "missing.wav")], "参考录音不存在"),
                (["开始下注", "--ref-audio", str(reference), "-o", "result.ogg"], ".wav 或 .mp3 后缀"),
                (["开始下注", "--ref-audio", str(reference), "-o", str(reference)], "不能覆盖参考录音"),
            ]
            for args, message in cases:
                with self.subTest(args=args):
                    result = subprocess.run(
                        [sys.executable, str(script), *args], cwd=tmp,
                        capture_output=True, text=True,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn(message, result.stderr)
                    self.assertNotIn("Loading", result.stdout)

            result = subprocess.run(
                [sys.executable, str(script), "开始下注", "--ref-audio", str(reference), "-o", "result.mp3"],
                cwd=tmp, env={**os.environ, "PATH": ""}, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("输出 MP3 需要 FFmpeg", result.stderr)
            self.assertFalse((Path(tmp) / "result.mp3").exists())


if __name__ == "__main__":
    unittest.main()
