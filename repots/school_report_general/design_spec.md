---
template_id: school_report_general
kind: deck
category: scenario
summary: General school report and course presentation deck with a blue technical academic style.
keywords: [school-report, course-presentation, project-defense, blue-tech, general]
primary_color: "#0F6FC6"
canvas_format: banner
canvas_dimensions: "1920x1080"
replication_mode: standard
page_count: 10
page_types: [cover, toc, chapter, content, ending]
placeholders:
  01_cover: ["{{TITLE}}", "{{SUBTITLE}}", "{{AUTHOR}}", "{{DATE}}", "{{ORGANIZATION}}"]
  02_toc: ["{{TOC_ITEM_1_TITLE}}", "{{TOC_ITEM_1_DESC}}", "{{TOC_ITEM_2_TITLE}}", "{{TOC_ITEM_2_DESC}}", "{{TOC_ITEM_3_TITLE}}", "{{TOC_ITEM_3_DESC}}", "{{TOC_ITEM_4_TITLE}}", "{{TOC_ITEM_4_DESC}}"]
  02_chapter: ["{{CHAPTER_NUM}}", "{{CHAPTER_TITLE}}", "{{CHAPTER_DESC}}"]
  03a_content_overview: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{CONTENT_AREA}}", "{{PAGE_NUM}}"]
  03b_content_feature_grid: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{PAGE_NUM}}"]
  03c_content_technical_route: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{PAGE_NUM}}"]
  03d_content_image_text: ["{{PAGE_TITLE}}", "{{IMAGE}}", "{{CONTENT_AREA}}", "{{PAGE_NUM}}"]
  03e_content_architecture: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{PAGE_NUM}}"]
  03f_content_demo: ["{{PAGE_TITLE}}", "{{SCREENSHOT}}", "{{CONTENT_AREA}}", "{{PAGE_NUM}}"]
  04_ending: ["{{THANK_YOU}}", "{{ENDING_SUBTITLE}}", "{{CONTACT_INFO}}"]
---

# School Report General — Design Specification

## I. Template Overview
- Use cases: course reports, experiment summaries, project defenses, system design presentations, and staged academic progress reports.
- Theme mode: light.
- Visual identity: white content pages anchored by blue arrow-title ribbons, cyan accent circles, and restrained academic spacing. The source deck's MySQL-specific wording has been generalized into school-report placeholders while preserving the classroom-report feeling.

## II. Color Scheme
- Primary blue: `#0F6FC6` for section ribbons, key arrows, and active accents.
- Deep blue: `#17406D` for title emphasis and footer metadata.
- Cyan accent: `#009DD9` and `#0BD0D9` for progress dots, dividers, and light callouts.
- Soft background: `#F4F8FC` and `#EAF5FB` for panels.
- Body text: `#101820`; secondary text: `#5B6B7C`; white: `#FFFFFF`.

## III. Typography
- Chinese-first stack: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`.
- English emphasis: `Arial Black, Arial, sans-serif` for short labels and large numerals.
- Body baseline: 34 px on the 1920x1080 canvas.

## IV. Signature Design Elements
- Blue arrow ribbon: section and content pages use a left circular node plus a blue arrow tab with a black title inset.
- Academic cover band: the cover uses a broad blue center band and light grid arcs, adapted from the original course-report deck.
- Content chrome: content pages keep a compact top-left title ribbon and a small page-number footer, leaving the main body flexible.
- Generalized image slots: screenshot, diagram, and image-heavy pages use outlined placeholders instead of source-specific MySQL images.

## V. Page Roster
| File | Type | Description |
|---|---|---|
| `01_cover.svg` | cover | Course/project report cover with blue horizontal title band, subtitle, author, organization, and date slots. |
| `02_toc.svg` | toc | Four-item report outline page with numbered cyan nodes and title/description pairs. |
| `02_chapter.svg` | chapter | Full-bleed section divider using a centered arrow ribbon, chapter number, title, and short description. |
| `03a_content_overview.svg` | content | Overview page with key-message panel and a large flexible content area for paragraphs or bullets. |
| `03b_content_feature_grid.svg` | content | Six-card function or contribution overview grid for course reports and project summaries. |
| `03c_content_technical_route.svg` | content | Horizontal technical route / methodology flow with five stages. |
| `03d_content_image_text.svg` | content | Two-column image plus explanation page for experiment results, screenshots, or figures. |
| `03e_content_architecture.svg` | content | Architecture / process diagram canvas with layered blocks and connection arrows. |
| `03f_content_demo.svg` | content | Large screenshot-focused page with right-side interpretation notes. |
| `04_ending.svg` | ending | Closing thanks page with optional subtitle and contact information. |

## VI. Assets
- No external bitmap assets are required. Decorative elements are native SVG shapes so the template remains resolution-independent.

## VII. Placeholder Overrides
- This template declares explicit placeholders for each page stem because the standard roster includes several content variants with specialized image, screenshot, and architecture slots.
