# 博弈论短片：三人决斗

一支约 90 秒的博弈论故事视频，最终用 Remotion 制作。

## 进度

- [x] **第 1 步 · 选主题**：[docs/01-选题.md](docs/01-选题.md)
- [x] **第 2 步 · 写文案**：[docs/02-文案.md](docs/02-文案.md)（分镜脚本，含博弈论开场）+ [docs/02-旁白稿.txt](docs/02-旁白稿.txt)（配音稿）
- [ ] **第 3 步 · 收集工具和资源**（进行中）：[docs/03-素材清单.md](docs/03-素材清单.md)、[docs/03-出图与视频提示词.md](docs/03-出图与视频提示词.md)
- [ ] **第 4 步 · 制作**：Remotion 搭建、渲染 1920×1080 成片

## 目录

- `docs/`：每一步的产出文档
- `scripts/truel_odds.py`：三人决斗生存概率的精确计算 + 蒙特卡洛验证（`python3 scripts/truel_odds.py`）
- `scripts/narration_timing.py`：按旁白稿估算每个镜头的配音时长
- `scripts/tts_seed_audio.py`：用豆包 seed-audio 生成每个镜头的旁白（密钥从环境变量读取）
- `public/`：图片、视频、旁白、音效、音乐素材
- `.claude/skills/remotion-best-practices`：Remotion 官方 agent skill（来自 remotion-dev/skills 4.0.532）
