# Release checklist — {{REPO_NAME}} {{VERSION}}

**Target commit / branch:** `________________`  
**Cut date:** `YYYY-MM-DD`  
**Release owner:** `________________`

## Gates (automate first)

- [ ] `git status` clean on release commit
- [ ] CI green for the commit to be tagged
- [ ] Tests / lint (project-specific): `________________`
- [ ] Version bumped everywhere required (single source of truth + mirrors)
- [ ] Changelog / release notes entry for this version

## Ship

- [ ] Release commit merged or pushed to release line
- [ ] Tag created (`________________`) and pushed
- [ ] GitHub Release (or equivalent) with correct notes
- [ ] Registry publish (PyPI / npm / crates / images) if applicable

## Post-release

- [ ] Artifact visible (release page, registry tag, docs version)
- [ ] Smoke install or binary run from published artifact
- [ ] Hotfix / backport policy noted if needed

---

_Fill `{{REPO_NAME}}` / `{{VERSION}}` or delete placeholders. Adapt command lines to your stack._
