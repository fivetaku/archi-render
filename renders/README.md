# renders/ — AI render revisions (git-ignored, LFS-out)

Layout: `renders/<project>/<shot>/R00..Rnn/` with `render.png|jpg`, `prompt.txt`, `meta.json`
(+ `mask_internal.png`, `mask_grok.png` for fix revisions). `R` numbers auto-increment; nothing is overwritten.

Policy (design P8, clm_008):
- This folder is in `.gitignore` and is **not** put in git LFS either. Rendered pixels are cheap to
  regenerate (prompt + pack + input hash are in `meta.json`) and heavy to version.
- Long-term storage: sync `renders/` to external storage (NAS / cloud drive) with `rsync -a renders/ <dest>/`.
- What *is* tracked: `assets/captures/` (inputs), `assets/stylepacks/` (recipes), `40-reports/approvals.md`
  (stage history) and `50-output/<project>/contact_sheet_*.jpg` (deliverables).
- Vendor image URLs (imgen.x.ai) are temporary; `render.py` downloads immediately and never stores the URL.
