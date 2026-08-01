# Soft issue inspector

Local side-by-side viewer for `regression_report.json` **soft_issues**.

## Launch

From `pipelines/extraction-pipeline`:

```powershell
python scripts/soft_issue_viewer/app.py
```

Or:

```powershell
.\scripts\soft_issue_viewer\run.ps1
```

Open **http://127.0.0.1:8765/**

## How old vs new are located

| Role | Default path |
|------|----------------|
| **Report** | `work/cefr-companion-2020/metadata/regression_report.json` (only **soft** issues listed) |
| **Old (baseline)** | Prefer `work/.../baseline_pre_full_rerun/`, else `baseline_pre_rerun/`, else `versions/001/` |
| **New (current)** | `output/cefr-companion-2020/CEFR_Companion_Volume.md` |

The UI is aimed at the **remaining soft issues** after hard pins (section headers, p.47 order, span inventory). Hard issues block versioning and are not in the sidebar.

Override:

```powershell
python scripts/soft_issue_viewer/app.py --old PATH --new PATH --report PATH --port 8765
```

Requires Flask (`pip install flask` in the project venv).
