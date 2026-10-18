# GPT-SoVITS 项目能力、安装构建与使用指南

本文基于仓库提交 `48b1a0169a28582a8984402f82cf438d3bfa6aca`（2026-08-18）及当前源码整理。项目更新较快，命令与模型兼容性应以当前检出的源码为准。

## 1. 项目定位

GPT-SoVITS 是一个少样本语音合成（TTS）项目。它用参考音频提供说话人音色和语气，再将目标文本合成为语音。项目的主要交互入口是 Gradio WebUI，同时提供 FastAPI、命令行推理和模型导出代码。

核心使用方式有两种：

- 零样本：不训练角色模型，直接用约 5 秒（界面实际限制为 3～10 秒）的参考音频合成。
- 少样本微调：使用约 1 分钟或更多已标注语音，分别微调 SoVITS 和 GPT，再用训练出的权重推理，以提高音色相似度和稳定性。

这不是实时语音转换项目。主 WebUI 的“2-GPT-SoVITS-变声”页当前仍显示“施工中”，已完成的核心能力是文本到语音。

## 2. 支持能力

### 2.1 语音合成

| 能力 | 当前实现 |
| --- | --- |
| 零样本 TTS | 使用 3～10 秒参考音频，无需训练即可克隆音色 |
| 少样本 TTS | 通过 SoVITS + GPT 两阶段微调生成角色权重 |
| 跨语言合成 | 中文、英语、日语、韩语、粤语及混合/自动识别模式；V1 只支持中、英、日相关模式 |
| 多参考音频 | V1/V2/V2Pro 系列可融合多条辅助参考音频；V3/V4 界面不开放该能力 |
| 无参考文本 | 部分版本可省略参考音频文本；V3/V4 不支持 |
| 长文本处理 | 支持不切、每四句、约 50 字、按中英文句号、按标点切分 |
| 推理控制 | top-k、top-p、temperature、随机种子、语速、句间停顿、重复惩罚、批量/并行推理 |
| 流式输出 | API V2 支持多档流式模式，可在质量、首包速度和分块大小间选择 |
| 音频格式 | API V2 支持 WAV、RAW、OGG、AAC；AAC 依赖 FFmpeg |

### 2.2 模型版本

推理配置代码支持 `v1`、`v2`、`v3`、`v4`、`v2Pro`、`v2ProPlus`。当前主 WebUI 默认选择 `v2Pro`，也可在界面内动态切换版本。

- V1：较早版本，语言范围较窄。
- V2：通用稳定版本，加入粤语、韩语及更多混合语言模式。
- V3/V4：SoVITS 使用 LoRA 微调入口；V3 可调采样步数和超分，V4 使用独立声码器。V3 输出为 24 kHz，V4 为 48 kHz。
- V2Pro/V2ProPlus：在 V2 系列推理接口基础上加入说话人表征相关处理。

不同版本的 GPT、SoVITS 权重不能随意混用。应在 WebUI 中选择同一版本的底模和训练权重，V3/V4 LoRA 还要求对应底模存在。

### 2.3 数据集制作工具

主 WebUI 已串起完整的数据准备链：

1. UVR5 人声/伴奏分离、去混响和去延迟（需另行下载 UVR5 权重）。
2. 长音频自动切片。
3. 可选降噪。
4. ASR 自动转写：Fun-ASR-Nano、SenseVoice、经典 FunASR，以及可选 Faster Whisper。
5. 浏览器内校对文本标注。
6. 文本与 BERT 特征提取。
7. HuBERT/音频特征提取；V2Pro 系列还会提取说话人特征。
8. 语义 Token 提取。

训练标注文件使用以下格式：

```text
音频路径|说话人名称|语言代码|文本
```

语言代码为 `zh`、`en`、`ja`、`ko`、`yue`。例如：

```text
/data/speaker/001.wav|speaker_a|zh|你好，欢迎使用语音合成。
```

格式化结果默认写入 `logs/<实验名>/`，关键中间文件包括：

- `2-name2text.txt`：清洗后的文本和音素特征。
- `4-cnhubert/`、`5-wav32k/`：语音特征与重采样音频。
- `6-name2semantic.tsv`：GPT 训练使用的语义 Token。

### 2.4 训练与部署接口

- SoVITS 训练：V1/V2/V2Pro 系列使用 `s2_train.py`；V3/V4 使用 `s2_train_v3_lora.py`。
- GPT 训练：使用 `s1_train.py`，支持保存最新权重、周期权重和 DPO 选项。
- Web 推理：独立 Gradio 页面，支持模型热切换和参数调节。
- API：推荐 `api_v2.py`，提供合成、切换权重、设置参考音频、重启/退出接口。
- CLI：`inference_cli.py` 可完成单次文件式推理，但语言选项少于 WebUI/API。
- 模型导出：仓库包含 ONNX 和 TorchScript 导出脚本；这些是开发级入口，部分脚本内仍有固定示例路径，不属于开箱即用的主流程。

## 3. 运行环境与依赖

### 3.1 推荐环境

- Python：项目徽标声明支持 3.10～3.12，官方安装示例统一使用 Python 3.10，优先选 3.10。
- NVIDIA：安装脚本支持 CUDA 12.6、12.8。
- AMD：Linux 安装脚本支持 ROCm 6.2，并包含 WSL2 兼容处理。
- Apple Silicon：支持 MPS 推理；官方提示 macOS GPU 训练质量不佳，训练暂以 CPU 为主。
- CPU：可安装和运行，但训练及推理速度明显更慢。
- 系统工具：Conda、FFmpeg、CMake、Make；Linux 可能还需 GCC/G++ 11 和 `libsox-dev`。

自动安装脚本还会下载预训练模型、中文 G2PW、多音字/日语处理数据及 Python 依赖。FunASR 模型通常首次使用时下载；UVR5 权重只有传入可选参数才下载。

### 3.2 当前检出状态

仓库中的以下模型目录目前只有 `.gitignore`，不能直接离线运行完整推理：

- `GPT_SoVITS/pretrained_models/`
- `tools/asr/models/`
- `tools/uvr5/uvr5_weights/`

先运行官方安装脚本或手工放入对应模型。仅安装 Python 包而没有模型权重，WebUI 可以启动到一定阶段，但训练、中文前端或推理会失败/自动下载。

## 4. 安装与构建

Python 项目本身不需要传统编译；这里的“构建”分为环境安装和可选 Docker 镜像构建。

### 4.1 Linux / macOS 自动安装

```bash
conda create -n GPTSoVits python=3.10
conda activate GPTSoVits

# NVIDIA CUDA 12.8 示例
bash install.sh --device CU128 --source ModelScope --download-uvr5
```

按机器选择参数：

```bash
# NVIDIA
bash install.sh --device CU126 --source HF
bash install.sh --device CU128 --source HF-Mirror

# AMD / Linux
bash install.sh --device ROCM --source ModelScope

# Apple Silicon 或纯 CPU
bash install.sh --device MPS --source ModelScope
bash install.sh --device CPU --source ModelScope
```

`--device` 与 `--source` 都是必填项；`--download-uvr5` 可选。

### 4.2 Windows 自动安装

在 PowerShell 中执行：

```powershell
conda create -n GPTSoVits python=3.10
conda activate GPTSoVits
pwsh -F install.ps1 -Device CU128 -Source ModelScope -DownloadUVR5
```

Windows 脚本支持 `CU126`、`CU128`、`CPU`。也可使用官方整合包，解压后运行 `go-webui.bat` 或 `go-webui.ps1`；这两个启动器只适用于包含 `runtime/python.exe` 的整合包，不适用于普通源码环境。

### 4.3 手工安装

```bash
conda create -n GPTSoVits python=3.10
conda activate GPTSoVits
pip install -r extra-req.txt --no-deps
pip install -r requirements.txt
conda install -c conda-forge ffmpeg cmake make
```

手工安装还需自行准备：

- `GPT_SoVITS/pretrained_models/` 下的 GPT、SoVITS、BERT、HuBERT、V2Pro、V3/V4 声码器等底模。
- 中文所需的 `GPT_SoVITS/text/G2PWModel/`。
- 需要人声分离时的 `tools/uvr5/uvr5_weights/`。
- 离线 ASR 所需的 `tools/asr/models/`；否则允许程序首次使用时联网下载。

手工方案最容易出现 PyTorch 与 CUDA/ROCm 不匹配，通常优先使用自动安装脚本。

### 4.4 Docker 直接运行

Compose 只提供 NVIDIA CUDA 12.6/12.8 服务：

```bash
# 在项目根目录执行，选择一个服务（先阅读下方的当前版本说明）
docker compose run --service-ports GPT-SoVITS-CU128

# 容器进入 bash 后启动主界面
python webui.py zh_CN
```

可选服务：

- `GPT-SoVITS-CU126`
- `GPT-SoVITS-CU128`
- `GPT-SoVITS-CU126-Lite`
- `GPT-SoVITS-CU128-Lite`

完整版带完整模型资源；Lite 镜像不包含 ASR 和 UVR5 模型。Compose 将当前仓库整体挂载到 `/workspace/GPT-SoVITS`，并暴露 `9871`～`9874` 和 `9880`。默认要求 NVIDIA Container Runtime，并配置 16 GB 共享内存。

当前提交的 `docker-compose.yaml` 无法通过现代 Docker Compose 校验：Lite 服务中的以下两个短卷写法会被解释为包含 `/` 的非法命名卷：

```yaml
- tools/asr/models:/workspace/models/asr_models
- tools/uvr5/uvr5_weights:/workspace/models/uvr5_weights
```

使用 Compose 前，需要把四个 Lite 服务卷条目（每个服务两条）改为明确的相对宿主路径，即在左侧补 `./`：

```yaml
- ./tools/asr/models:/workspace/models/asr_models
- ./tools/uvr5/uvr5_weights:/workspace/models/uvr5_weights
```

不修改仓库时，可绕过 Compose 直接启动官方完整版镜像：

```bash
docker run --rm -it --gpus all --shm-size 16g \
  -p 9871-9874:9871-9874 -p 9880:9880 \
  -e is_half=true \
  -v "$PWD:/workspace/GPT-SoVITS" \
  xxxxrt666/gpt-sovits:latest-cu128
```

### 4.5 本地构建 Docker 镜像

```bash
bash docker_build.sh --cuda 12.8
bash docker_build.sh --cuda 12.6 --lite
```

镜像名为 `${USER}/gpt-sovits:local`。构建脚本仅接受 CUDA 12.6 或 12.8，并按宿主架构选择 `linux/amd64` 或 `linux/arm64`。

## 5. 使用流程

### 5.1 最短零样本推理流程

```bash
conda activate GPTSoVits
cd /path/to/GPT-SoVITS
python webui.py zh_CN
```

浏览器访问 `http://127.0.0.1:9874`，然后：

1. 进入 `1-GPT-SoVITS-TTS` → `1C-推理`。
2. 选择相互匹配的 GPT 和 SoVITS 底模。
3. 点击“开启 TTS 推理 WebUI”，打开 `http://127.0.0.1:9872`。
4. 上传 3～10 秒、尽量干净且只有一个说话人的参考音频。
5. 填写参考音频的准确文本和语言。
6. 填写目标文本与语言模式，先保留默认采样参数。
7. 点击“合成语音”。

`webui.py` 当前默认版本为 V2Pro，并支持在页面内切换版本。旧 README 提到的 `python webui.py v1` 与当前入口实现不一致：`v1` 参数不会设置模型版本，只可能被当作界面语言参数后忽略，应使用页面中的版本选择器。

### 5.2 少样本微调流程

1. 准备单说话人干净音频，长录音可先切片。
2. 按需要运行 UVR5、降噪；处理过度也会损伤音质，不需要就跳过。
3. 运行 ASR，得到 `.list` 标注。
4. 在标注界面逐条校对文字；每页修改后要提交保存。
5. 进入 `1A-训练集格式化工具`，执行 `1Aa`、`1Ab`、`1Ac`，也可用组合入口一次完成。
6. 确认 `logs/<实验名>/` 已产生 `2-name2text.txt`、HuBERT/音频目录和 `6-name2semantic.tsv`。
7. 进入 `1B-微调训练`，先后训练 SoVITS 与 GPT；两者没有强制先后依赖，也可按显存情况分别执行。
8. 成品权重写入版本对应的 `SoVITS_weights*`、`GPT_weights*` 目录。
9. 进入 `1C-推理`，刷新模型列表并选择同一实验、同一版本的两份权重。

训练是显存和耗时敏感任务。首次使用先用默认 batch size 和 epoch 跑通小数据集，再按实际显存调整；不要直接复制别人的高显存参数。

### 5.3 独立推理 WebUI

已知模型路径时可以直接启动：

```bash
python GPT_SoVITS/inference_webui.py zh_CN
```

默认监听 `0.0.0.0:9872`。模型路径来自配置和权重目录，若底模缺失会在加载阶段报错。

### 5.4 API V2

先编辑 `GPT_SoVITS/configs/tts_infer.yaml` 的 `custom` 段，保证版本、设备、GPT 权重和 SoVITS 权重一致，然后启动：

```bash
python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

最小 POST 示例：

```bash
curl -X POST http://127.0.0.1:9880/tts \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "你好，这是一次语音合成测试。",
    "text_lang": "zh",
    "ref_audio_path": "/absolute/path/reference.wav",
    "prompt_text": "这是参考音频对应的文字。",
    "prompt_lang": "zh",
    "media_type": "wav",
    "streaming_mode": false
  }' \
  --output output.wav
```

主要接口：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET / POST | `/tts` | 合成并返回音频 |
| GET | `/set_refer_audio` | 设置复用的参考音频 |
| GET | `/set_gpt_weights` | 热切换 GPT 权重 |
| GET | `/set_sovits_weights` | 热切换 SoVITS 权重 |
| GET | `/control` | `restart` 或 `exit` |

`streaming_mode` 可取 `0`/`false`（关闭）、`1`/`true`（较高质量分片）、`2`（中等质量流式）、`3`（更小固定分片、更快首包）。API 同时支持 GET，但长文本和复杂参数优先使用 POST。

服务没有内置认证。默认只绑定 `127.0.0.1`；若改成 `0.0.0.0`，应在反向代理层增加鉴权、访问控制和请求大小限制，不要直接暴露到公网。`/control` 能结束或重启进程，也不应公开。

### 5.5 命令行单次推理

```bash
mkdir -p output
python GPT_SoVITS/inference_cli.py \
  --gpt_model /path/to/model.ckpt \
  --sovits_model /path/to/model.pth \
  --ref_audio /path/to/reference.wav \
  --ref_text /path/to/reference.txt \
  --ref_language 中文 \
  --target_text /path/to/target.txt \
  --target_language 中文 \
  --output_path output
```

结果固定写为 `output/output.wav`。CLI 的参考语言只允许中文、英文、日文，目标语言支持中文、英文、日文及部分混合模式；需要韩语、粤语、流式或高级参数时使用 WebUI/API V2。

## 6. 端口和目录速查

| 项目 | 默认值 |
| --- | --- |
| 主 WebUI | `9874` |
| UVR5 WebUI | `9873` |
| TTS 推理 WebUI | `9872` |
| 标注 WebUI | `9871` |
| API | `9880` |
| 数据处理中间目录 | `logs/<实验名>/` |
| SoVITS 权重 | `SoVITS_weights*` |
| GPT 权重 | `GPT_weights*` |
| 预训练模型 | `GPT_SoVITS/pretrained_models/` |

## 7. 常见问题与边界

- 启动即提示模型不存在：先完成自动安装，或核对 `tts_infer.yaml` 中四类基础路径和版本。
- CUDA 不可用：安装脚本会回退 CPU；手工安装时检查 NVIDIA 驱动、PyTorch wheel 和 CUDA 版本是否匹配。
- CPU 上 fp16：推理配置会自动关闭；不要强制启用。
- 参考音频报长度错误：控制在 3～10 秒，尽量无背景音乐、混响和多人说话。
- 中文读音异常：确认 G2PWModel 已下载，并校对文本、数字和多音字。
- AAC 无输出：确认系统命令行可执行 `ffmpeg`。
- Docker Compose 解析即失败：当前 Lite 卷路径缺少 `./`，按 4.4 节修正四个条目，或直接使用 `docker run`。
- Docker 启动后没有 Web 页面：容器默认进入 bash，需要在容器内手工执行 `python webui.py zh_CN`。
- Lite 镜像缺少 UVR5：这是镜像设计，不是安装失败；按需挂载或下载权重。
- WebUI 能监听公网地址不代表适合公网部署：Gradio 和 API 均未提供项目级账号、权限、配额和租户隔离。
- ONNX/TorchScript：仓库有导出实现，但不是主 WebUI 的稳定按钮式流程。只有在明确目标运行时和模型版本后再使用并单独验收音质。

## 8. 建议选择

- 第一次体验：Python 3.10 + 自动安装脚本 + 主 WebUI + 零样本推理。
- 中国网络环境：优先 `--source ModelScope` 或 `HF-Mirror`。
- NVIDIA 生产推理：先用 API V2 本机绑定验证，再通过带鉴权的反向代理部署。
- 需要训练：从小而干净的数据集开始，先跑通格式化、SoVITS、GPT、推理整条链，再扩大数据量。
- 只需调用服务：不必启动主 WebUI，配置 `tts_infer.yaml` 后直接运行 `api_v2.py`。

项目采用 MIT 许可证，但模型、数据集和生成声音仍涉及独立的授权、隐私和声音人格权问题。使用他人声音前应取得明确许可，并对生成内容负责。

## 9. 本次核验范围

本指南完成了以下本地静态核验：

- `install.sh`、`docker_build.sh` 通过 Bash 语法检查。
- `api_v2.py`、`inference_cli.py`、`config.py` 通过 Python 字节码编译；`config.py` 有一处仓库原有的无效转义 `SyntaxWarning`。
- 文档通过 Git 空白错误检查。
- `docker compose config` 确认失败，原因是 4.4 节记录的 Lite 卷路径，而不是本机缺少 Docker。

本机没有 Conda，仓库也没有实际模型权重，因此没有执行依赖安装、模型下载、GPU/CPU 推理、训练、浏览器或音质验收。安装脚本会在解析 `--help` 前检查 Conda，所以未安装 Conda 时连帮助命令也会直接报告 `Conda Not Found`。这些运行验收应在目标硬件和模型准备完成后进行。
