# Foundation Models API — 外部观点

> _生成时间：2026-04；来源：WebSearch。_

## 要点汇总

- WWDC 2025 首次把 Apple Intelligence 背后的端侧大模型开放给第三方开发者；免费、离线、隐私合规、随 Swift 原生集成。
- Framework 提供 guided generation / tool calling 等能力；支持文本生成与 Image Playground 联动的图像生成。
- iOS 26 发布后数周，已有教育类（笔记转测验）、户外类（自然语言离线搜索）App 采用；是继 Core ML 以来最显著的 Apple AI 平台开放动作。

## 分析师 / 自媒体引述

> "Apple announced the Foundation Models Framework, a new API allowing third-party developers to leverage the large language models at the heart of Apple Intelligence and build it into their apps." — MacRumors, [macrumors.com](https://www.macrumors.com/2025/06/09/foundation-models-framework/), 2025-06-09

> "The framework allows developers to integrate Apple's on-device models directly into apps, enabling AI-powered features that work offline, protect privacy, and incur no inference costs." — TechCrunch, [techcrunch.com](https://techcrunch.com/2025/06/09/apple-lets-developers-tap-into-its-offline-ai-models/), 2025-06-09

> "The framework includes built-in features like guided generation and tool calling for easy integration of generative capabilities into existing apps." — AppleInsider, [appleinsider.com](https://appleinsider.com/articles/25/06/09/apple-intelligence-opened-up-to-all-developers-with-foundation-models-framework), 2025-06-09

## 反方 / 风险视角

> "Apple's initial rollout gives developers access to the on-device, smaller-scale versions of its AI models." — 9to5Mac benchmark, [9to5mac.com](https://9to5mac.com/2025/06/11/how-do-apple-new-local-models-compare/), 2025-06-11

(含义：参数规模较小 → 长上下文 / 复杂推理仍需云端大模型；与 GPT-4o / Gemini 1.5 Pro 拉开差距。)

## 行业影响判断（Claude 综合）

1. **对云端 LLM 定价**：中小 iOS App 的日常 AI 调用（摘要、分类、翻译）从按 token 付费的 OpenAI / Anthropic / Gemini 迁移到免费端侧；云端 API 面临结构性"低端用例流失"。
2. **对创业公司产品策略**：AI wrapper 类 App 失去"直接调 GPT"的护城河；差异化要靠垂直数据、workflow 设计、跨平台一致性，而不是"谁调用最便宜的 API"。
3. **对 Android 生态**：Google 的 Gemini Nano + Android AICore 进入直接竞争；中国侧 OPPO / 小米 / 荣耀的端侧模型也会被迫加速开放 SDK。
