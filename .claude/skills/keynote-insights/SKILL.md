---
name: keynote-insights
description: 把 Apple WWDC / Google I/O keynote 视频沉淀成"结论先行、画面为王"的深红+浅灰主题中文 PPT 报告。自动下载视频、对齐官方 transcript、按特性分段、用 ffmpeg 抽取高分辨率 UX 演示帧与 GIF、汇总外部分析师/自媒体观点，并渲染出每页一个特性的洞察 PPT。适用场景："把 WWDC 2025 keynote 做成 PPT"、"分析 I/O 2025 关键特性与行业影响"、"整理 keynote UX 演示截图"。
---

# Keynote Insights PPT Skill

把一场 keynote 变成一份"观点驱动、UX 大图打底"的 PPT 报告。

## 使用场景触发词

- "把 WWDC {YEAR} keynote 做成 PPT / 洞察报告"
- "分析 I/O {YEAR} 的关键特性对行业的影响"
- "整理 keynote 的 UX 演示截图"
- "汇总分析师对 {某 keynote 特性} 的评论"

## 两阶段工作流

### Stage A — Ingest & Segment（拉取 & 切段，产出候选清单）

对每个新的 keynote_id（如 `wwdc2025`）只跑一次：

1. 解析用户输入：`keynote_id` 或 YouTube URL 或 Apple URL。
2. 建工作目录 `workspace/<keynote_id>/`。
3. `scripts/fetch_video.sh <url> <workdir>` → 下载 1080p 视频、字幕、章节。
4. `scripts/fetch_apple_transcript.py <apple_url> <workdir>` → 官方带时间戳 transcript；失败则 fallback 到 YouTube 字幕。
5. `scripts/segment_features.py <workdir>` → 生成 `features_candidates.json`。
6. **停下来**把清单 pretty print 给用户，问他勾选哪些特性进 PPT（使用 `AskUserQuestion` 或终端交互）。

### Stage B — Research & Render（仅处理用户选中的特性）

1. 把用户选择写入 `features_selected.json`。
2. 对每个选中特性**并行**执行：
   - `scripts/extract_frames.py <workdir> <feature_id>` → `frames/<id>/*.png`（每 0.5s 一帧）。
   - `scripts/pick_best_frame.py <workdir> <feature_id>` → `frames/<id>/best_*.png`（1-3 张，Claude 视觉判断）。
   - `scripts/make_gif.py <workdir> <feature_id>` → `gifs/<id>.gif`（3-5 秒 UX 演示循环）。
   - `scripts/analyst_roundup.py <workdir> <feature_id>` → `commentary/<id>.md`（外部观点摘要 + 源链接）。
3. 每个特性综合 transcript + 媒体观点，产出：
   - **观点标题**：一句话结论（深红色标题字）。
   - **行业影响**：3 条 bullet（对手机软件品类 / 周边硬件 / 开发者生态）。
4. `scripts/build_ppt.py <workdir>` → `<keynote_id>_insights.pptx`。
5. `libreoffice --headless --convert-to pdf <pptx>` 出 PDF 预览。

## 色卡与版式（严格遵守）

详见 [`references/ppt_layout_spec.md`](references/ppt_layout_spec.md)。要点：

- 深红 `#8B1A1A` 主色、浅灰 `#F4F4F4` 背景、正文灰 `#4A4A4A`。
- 特性页：顶部导航条 4% → 大图/GIF 55% → 观点标题 12% → 行业影响 16% → 媒体引述 13%。
- 字体：中文 PingFang SC / Source Han Sans，西文 SF Pro / Helvetica Neue。

## 关键设计决策

### 为什么不用 Chrome 截图

Chrome 扩展截图只能拿到浏览器视口某一瞬间的画面，关键 UI 标签和动效都会错过。本 skill 改为：

1. `yt-dlp` 下载原始视频到本地。
2. 用 transcript 时间戳锚定特性出现的秒数区间。
3. `ffmpeg` 在该区间内每 0.5s 抽 1080p 帧 → 多张候选。
4. 把候选帧拼成雪碧图交给 Claude 视觉，选出 UI 最清晰的那张。

### Transcript 来源优先级

1. Apple 官方 transcript（`developer.apple.com/videos/play/...` 页内 JSON）— 最准确。
2. YouTube 自动字幕（`yt-dlp --write-auto-subs`）— 95% 准确。
3. Whisper 本地转录 — 仅兜底。

### 外部观点来源白名单

见 [`references/analyst_sources.md`](references/analyst_sources.md)，WebSearch 时通过 `allowed_domains` 限制。

## 调用示例

```
用户：帮我把 WWDC 2025 keynote 做成 PPT 报告
Claude：
  1) bash .claude/skills/keynote-insights/scripts/fetch_video.sh <url> workspace/wwdc2025
  2) python3 .claude/skills/keynote-insights/scripts/fetch_apple_transcript.py ...
  3) python3 .claude/skills/keynote-insights/scripts/segment_features.py workspace/wwdc2025
  4) 展示 features_candidates.json 给用户勾选
  5) 对所选特性并行跑 extract_frames / pick_best_frame / make_gif / analyst_roundup
  6) python3 .claude/skills/keynote-insights/scripts/build_ppt.py workspace/wwdc2025
  7) 交付 workspace/wwdc2025/wwdc2025_insights.pptx + PDF 预览
```

## 首次运行准备

```bash
bash .claude/skills/keynote-insights/install.sh
```

会检查依赖（ffmpeg、yt-dlp、python 包）并建立到 `~/.claude/skills/keynote-insights` 的软链。

## 相关文档

- [`references/ppt_layout_spec.md`](references/ppt_layout_spec.md) — PPT 布局尺寸与字号
- [`references/analyst_sources.md`](references/analyst_sources.md) — 分析师 / 自媒体白名单
- [`references/industry_impact_rubric.md`](references/industry_impact_rubric.md) — 行业影响分析框架
