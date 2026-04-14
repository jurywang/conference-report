# 外部观点来源白名单

`analyst_roundup.py` 通过 `WebSearch` 的 `allowed_domains` 参数限制只从这些域名取信息。顺序=优先级。

## 英文 · 分析师 / 专业媒体

- `bloomberg.com` — Mark Gurman 的产品前瞻与行业评论
- `theverge.com` — 新特性上手与行业视角
- `daringfireball.net` — John Gruber 的深度解读
- `stratechery.com` — Ben Thompson 战略分析
- `sixcolors.com` — Jason Snell 细节评述
- `techcrunch.com` — 行业影响与初创反应
- `arstechnica.com` — 技术深挖
- `wsj.com` — 商业 & 竞争格局
- `ft.com` — 欧洲 / 全球视角
- `nytimes.com` — 大众视角

## 英文 · 苹果 / 安卓社区

- `9to5mac.com` — WWDC 详细报道
- `macrumors.com` — 社区反应与改动清单
- `9to5google.com` — Google I/O 报道（用于 I/O 场景）
- `androidpolice.com` — Android 视角
- `appleinsider.com` — 深度与爆料
- `reddit.com` — 谨慎采用，仅作为"社区情绪"补充（注明非专业媒体）

## 中文 · 科技媒体

- `36kr.com` — 36 氪
- `ifanr.com` — 爱范儿
- `sspai.com` — 少数派
- `geekpark.net` — 极客公园
- `jiemian.com` — 界面新闻
- `pingwest.com` — 品玩
- `ithome.com` — IT 之家
- `leiphone.com` — 雷锋网
- `huxiu.com` — 虎嗅
- `tmtpost.com` — 钛媒体
- `cn.technode.com` — 动点科技

## 中文 · 视频 / 自媒体（二级引用，注明来源类型）

- `bilibili.com` — 评测类 UP 主（科技美学、何同学、小白测评等）
- `zhihu.com` — 深度问答
- `weixin.qq.com` — 公众号文章（通过 Bing / Google 间接搜索）

## 搜索查询模板

```
{feature_name_en} WWDC {year} review impact
{feature_name_en} vs {competitor_category}
{feature_name_zh} WWDC {year} 分析 影响
```

例如 AirPods Live Translation：
```
AirPods Live Translation WWDC 2025 review impact
AirPods Live Translation vs translator devices
AirPods 实时翻译 WWDC 2025 翻译机 行业
```

## 取舍原则

1. **每特性 3-6 条引述**：要多样（至少 1 条中文、1 条英文、1 条业内分析师）。
2. **拒绝纯转载**：如果多个来源复述同一段官方通稿，只保留一个。
3. **保留反向意见**：如果有批评 / 质疑声音，优先纳入（增加洞察密度）。
4. **保留原文引号**：媒体引述文字走 `" … "`，避免用自己的话复述成"假引用"。
5. **附 URL**：每条引述必须带可点击源链接，PPT 底部以超链接形式呈现。
