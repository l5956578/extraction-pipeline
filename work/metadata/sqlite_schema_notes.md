# SQLite / Website Import Notes

## Recommended schema

```sql
CREATE TABLE content_nodes (
  id TEXT PRIMARY KEY,
  parent_id TEXT REFERENCES content_nodes(id),
  title TEXT NOT NULL,
  anchor TEXT,
  page_start INTEGER,
  page_end INTEGER,
  node_type TEXT  -- chapter | section | prose
);

CREATE TABLE artifacts (
  id TEXT PRIMARY KEY,
  display_caption TEXT NOT NULL,  -- "Display Name | artifact_id"
  artifact_type TEXT,             -- descriptor_scale | table | figure | section_block
  page_start INTEGER,
  page_end INTEGER,
  anchor TEXT,
  asset_path TEXT
);

CREATE TABLE artifact_product_tiers (
  artifact_id TEXT REFERENCES artifacts(id),
  product_tier TEXT  -- base | assessment_action | detailed | context
);

CREATE TABLE scale_rows (
  artifact_id TEXT REFERENCES artifacts(id),
  cefr_level TEXT,
  descriptor_text TEXT,
  sort_order INTEGER
);

CREATE TABLE figure_assets (
  artifact_id TEXT REFERENCES artifacts(id),
  file_path TEXT,
  mime_type TEXT,
  blob BLOB
);

CREATE TABLE products (
  id TEXT PRIMARY KEY,
  name TEXT,
  description TEXT,
  product_tier TEXT
);
```

## Import workflow

1. Load `output/db_import_registry.json` → `artifacts` + `artifact_product_tiers`
2. Parse `<!-- db:id=... -->` comments in `CEFR_Companion_Volume.md` for prose blocks → `content_nodes`
3. Split pipe tables under each artifact heading into `scale_rows` (CEFR level = first column when A1–C2)
4. Copy `output/assets/` into web root; store paths in `figure_assets` (BLOB optional for portability)

## Product mapping (your offerings)

| Product | `product_tier` | Key artifact |
|---------|----------------|--------------|
| Base self-assessment | `base` | `table_self_assessment_grid` (pages 177–181) |
| Assessment + action plan | `assessment_action` | All Ch 3–6 descriptor scales |
| Detailed à-la-carte scales | `detailed` | Individual `scale_*` artifacts |
| Coaching / context prose | `context` | Chapters, methodology, figures |

## UI pattern

- **Sidebar:** `manifest.json` → `navigation` tree
- **Deep links:** `anchor` field per artifact (e.g. `#table_self_assessment_grid`)
- **Search:** `display_caption` format `Name | id` enables `LIKE '%| scale_vocabulary_control'`

## Coaching sessions

Keep `sessions` table separate from content — link sessions to user assessment results and `product_tier`, not to PDF page numbers.