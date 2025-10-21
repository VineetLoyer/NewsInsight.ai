# NewsInsight.ai — Visual UI Guide

## 🎨 UI Layout Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  📰 NEWSINSIGHT                                                      │
│  Verified News Insights & Deep Analysis                             │
│                                                                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  🔍 Search                                    🗞️ Top 3 Verified      │
│  ┌────────────────────────────┐              News Insights           │
│  │ Topic or keyword...        │              for "technology"       │
│  └────────────────────────────┘                                      │
│                                              ┌──────────────────────┐│
│  📌 Suggested topics                         │ OpenAI Announces     ││
│  ┌─────┐ ┌─────────┐ ┌──────────┐          │ GPT-5                ││
│  │Tech │ │Business │ │Politics  │          │ [Positive]           ││
│  └─────┘ └─────────┘ └──────────┘          │                      ││
│  ┌─────┐ ┌─────────┐ ┌──────────┐          │ 2 hrs · TechCrunch   ││
│  │World│ │Science  │ │Markets   │          │                      ││
│  └─────┘ └─────────┘ └──────────┘          │ OpenAI has           ││
│                                             │ announced GPT-5…     ││
│  🔧 Debug Info                              │                      ││
│  Region: us-west-2                          │ [🔗 Orig] [💡 Expl]  ││
│  Table: news_metadata                       │ [AI] [Reasoning]     ││
│                                              │                      ││
│                                              │ ▼ Detailed Analysis  ││
│                                              │ ▼ Chat About This    ││
│                                              └──────────────────────┘│
│                                                                      │
│                                              ┌──────────────────────┐│
│                                              │ Fed Signals Rate     ││
│                                              │ Pause                ││
│                                              │ [Neutral]            ││
│                                              │                      ││
│                                              │ 4 hrs · Bloomberg    ││
│                                              │ ...                  ││
│                                              └──────────────────────┘│
│                                                                      │
│                                              ┌──────────────────────┐│
│                                              │ EU Approves AI       ││
│                                              │ Regulation           ││
│                                              │ [Neutral]            ││
│                                              │                      ││
│                                              │ 6 hrs · Euractiv     ││
│                                              │ ...                  ││
│                                              └──────────────────────┘│
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## 📋 Article Card Anatomy

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  EB Garamond 1.6rem, font-weight: 700                  │
│  Headline: OpenAI Announces GPT-5 [Positive] ───┐    │
│                                            sentiment   │
│  ───────────────────────────────────────────────┐      │
│  2 hrs · TechCrunch                            │      │
│  (meta info below headline)                     │      │
│  ───────────────────────────────────────────────┘      │
│                                                         │
│  Lora 1.05rem, italic                                 │
│  OpenAI has announced GPT-5, their latest language... │
│  (teaser text, truncated at ~180 chars)              │
│                                                         │
│  ──────────────────────────────────────────────────   │
│                                                         │
│  [🔗 Orig]  [💡 Explain]    [AI] [Reasoning]...      │
│  (action buttons + entity tags)                       │
│                                                         │
│  ▼ Detailed Analysis                                  │
│    (expander - hidden by default)                     │
│                                                         │
│  ▼ Chat About This Article                            │
│    (expander - hidden by default)                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 🎨 Color Palette

### Sentiment Chips

```
Positive: ███████ bg: #f1fdf3 (light green), text: #0d5c0d ███
Neutral:  ███████ bg: #f9f9f9 (light gray),  text: #5a5a5a ███
Negative: ███████ bg: #fef3f3 (light red),   text: #a41e1e ███
```

### Text Colors

```
Accent (headlines):    #1a1a1a (dark gray)
Body text:             #2c3e50 (medium gray)
Secondary text:        #6b7280 (light gray)
Borders:               #d9d9d9 (light gray)
```

## 🔤 Typography Hierarchy

```
Page Title (h1)
├─ Font: EB Garamond, 3.5rem, bold
├─ Color: #1a1a1a
└─ Border-bottom: 3px solid #1a1a1a

Section Header (h2)
├─ Font: EB Garamond, 2rem, bold
└─ Color: #1a1a1a

Card Headline (h3)
├─ Font: EB Garamond, 1.6rem, bold
└─ Color: #1a1a1a

Card Meta
├─ Font: Lora, 0.95rem, normal
└─ Color: #6b7280

Card Teaser
├─ Font: Lora, 1.05rem, italic
└─ Color: #2c3e50

Body Text
├─ Font: Lora, 1rem, normal
└─ Color: #2c3e50

Small Text
├─ Font: Lora, 0.9rem, normal
└─ Color: #6b7280
```

## 🔘 Button States

```
Primary Button:
├─ Normal:  white bg, #1a1a1a text, 1px border
├─ Hover:   gray bg, darker text
└─ Disabled: #d9d9d9 bg, gray text

Link Button:
├─ Normal:  #1a1a1a text, 1px underline
├─ Hover:   #666 text, darker underline
└─ Style:   underline on hover
```

## 📱 Responsive Behavior

```
Wide Layout (>1200px):
├─ Sidebar: 350px fixed
├─ Main: full width cards
└─ Cards: full width

Medium Layout (800-1200px):
├─ Sidebar: 300px
├─ Main: full width cards
└─ Cards: full width

Narrow Layout (<800px):
├─ Sidebar: hidden/collapsible
├─ Main: full width
└─ Cards: stack vertically
```

## 🎯 Feature Flow Diagrams

### Search Flow

```
User Input:
  └─ Types "technology"
     └─ autocomplete suggestions
        └─ Hit Enter
           └─ DDB scan + filter
              └─ Return top 3 articles
                 └─ Display in cards
                    └─ User can interact
```

### Suggested Topic Flow

```
User Click:
  └─ Click "Technology" button
     └─ Set topic = "Technology"
        └─ Auto-search triggered
           └─ DDB scan + filter
              └─ Return top 3
                 └─ Cards update
```

### Explain Flow

```
User Action:
  └─ Click "Explain" button
     └─ Spinner appears
        └─ bedrock_explain() called
           └─ Article summary sent to Claude
              └─ Claude generates analysis
                 └─ Store in session_state
                    └─ Expander opens with analysis
```

### Chat Flow

```
User Action:
  └─ Expand "Chat About This Article"
     └─ Enter question
        └─ Click "Send"
           └─ bedrock_chat() called
              └─ Question + article sent to Claude
                 └─ Claude generates answer
                    └─ Add to chat history
                       └─ Rerun app
                          └─ Chat history displayed
```

## 📊 Sentiment Chip Appearance

### Positive

```
┌─────────────┐
│ Positive 💚 │  ← Green chip
└─────────────┘
bg: #f1fdf3
text: #0d5c0d
```

### Neutral

```
┌─────────────┐
│ Neutral ⚪ │  ← Gray chip
└─────────────┘
bg: #f9f9f9
text: #5a5a5a
```

### Negative

```
┌─────────────┐
│ Negative ❌ │  ← Red chip
└─────────────┘
bg: #fef3f3
text: #a41e1e
```

## 🏷️ Entity Tags

```
Individual Tags:
┌─────────┐ ┌──────────┐ ┌─────────┐
│ OpenAI  │ │ AI       │ │ Models  │
└─────────┘ └──────────┘ └─────────┘

Styling:
├─ Padding: 6px 12px
├─ Border-radius: 20px
├─ Border: 1px solid #d9d9d9
├─ Background: white
├─ Font-size: 0.85rem
└─ Font-weight: 500
```

## 🔍 Search Box Styling

```
┌────────────────────────────────────────┐
│ Topic or keyword                   [🔍] │ ← Placeholder text
│                                         │
│ Styling:                                │
│ ├─ Height: 40px                        │
│ ├─ Border: 1px solid #d9d9d9           │
│ ├─ Border-radius: 4px                  │
│ ├─ Padding: 8px 12px                   │
│ ├─ Font: Lora 1rem                     │
│ └─ Background: white                   │
│                                         │
│ Focus:                                  │
│ ├─ Border-color: #1a1a1a               │
│ └─ Outline: 2px solid #1a1a1a          │
└────────────────────────────────────────┘
```

## 📐 Card Layout Dimensions

```
Card Padding:        24px
Card Border:         1px solid #d9d9d9
Card Border-radius:  8px
Card Shadow:         0 2px 4px rgba(0,0,0,0.04)
Card Margin-bottom:  20px

Headline Margin:     -0.5em top, 0.5em bottom
Meta Border:         1px solid #d9d9d9
Meta Padding:        0.5em bottom
Teaser Margin:       1.2em bottom

Button Container:    Flex, gap: 8px
```

## 🎬 Interactive Elements

### Expanders

```
Closed State:
┌──────────────────────────────────┐
│ ▶ Detailed Analysis              │
└──────────────────────────────────┘

Open State:
┌──────────────────────────────────┐
│ ▼ Detailed Analysis              │
│                                  │
│ [Analysis content here...]       │
│                                  │
└──────────────────────────────────┘
```

### Text Input (Chat)

```
┌─────────────────────────────┬──────────┐
│ Ask a question...           │  [Send]  │
└─────────────────────────────┴──────────┘

Focus behavior:
├─ Border becomes #1a1a1a
└─ Shadow appears
```

## 🌐 Typography Imports

```css
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500;700;800&family=Lora:wght@400;500;600;700&display=swap');

Fonts Used:
├─ EB Garamond
│  └─ Weights: 400, 500, 700, 800 (for headlines)
│
└─ Lora
   └─ Weights: 400, 500, 600, 700 (for body)
```

## 🎯 Accessibility

```
Contrast Ratios:
├─ Headlines (#1a1a1a on white): 19:1 ✓
├─ Body text (#2c3e50 on white): 9:1 ✓
├─ Secondary (#6b7280 on white): 6:1 ✓
└─ Sentiment text on bg: 7:1+ ✓

Fonts:
├─ Serif fonts improve readability
├─ 1rem+ base font size
├─ 1.6+ line height
└─ Sufficient spacing

Buttons:
├─ Min height: 40px (touch target)
├─ Clear labels
└─ Disabled state visible
```

## 📸 Screenshots Examples

### Example 1: Search Results

```
📰 NewsInsight
Verified News Insights & Deep Analysis

🔍 Search              🗞️ Top 3 Verified News Insights
┌────────────────────┐ for "technology"
│ Topic or keyword...│
└────────────────────┘ ┌─────────────────────────────────┐
                        │ OpenAI Announces GPT-5  [GREEN]  │
📌 Suggested          │ 2 hrs · TechCrunch              │
[Tech] [Business]     │                                 │
[Pol.] [Markets]      │ OpenAI has announced GPT-5…     │
                        │                                 │
                        │ [🔗] [💡] [AI][Model]          │
                        │ ▼ Analysis  ▼ Chat              │
                        └─────────────────────────────────┘
```

### Example 2: Explain Panel Open

```
┌─────────────────────────────────┐
│ Article Headline [GREEN]        │
├─────────────────────────────────┤
│ ▼ Detailed Analysis (EXPANDED)  │
│                                 │
│ 1) What happened:               │
│    - GPT-5 announced            │
│    - 40% better accuracy        │
│                                 │
│ 2) Why it matters:              │
│    - Significant AI milestone   │
│    - Improved reasoning         │
│                                 │
│ 3) What to watch:               │
│    - Availability date          │
│    - Real-world applications    │
│                                 │
└─────────────────────────────────┘
```

### Example 3: Chat Open

```
┌─────────────────────────────────┐
│ Article Headline                │
│                                 │
│ ▼ Chat About This Article       │
│                                 │
│ You: What does this mean for    │
│ my AI startup?                  │
│                                 │
│ Claude: GPT-5 represents...     │
│                                 │
│ ┌──────────────────────┬────┐   │
│ │ Ask a question...    │Send│   │
│ └──────────────────────┴────┘   │
│                                 │
└─────────────────────────────────┘
```

---

This visual guide helps with:
✅ Understanding the layout
✅ Customizing colors & fonts
✅ Adding new features
✅ Maintaining design consistency
✅ Accessibility compliance
