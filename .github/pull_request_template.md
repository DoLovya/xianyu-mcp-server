## Summary

- 

## CI/CD Checklist

- [ ] CI 通过（ci.yml）
- [ ] Release 通过（release.yml，如适用）

## Deliverables

**Workflows**

- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `.github/workflows/codeql.yml`（可选）

**Repo configs**

- `.github/dependabot.yml`（可选）
- Repository Variables：`UV_INDEX_URL`、`UV_EXTRA_INDEX_URL`、`PUBLISH_PYPI_ON_TAG`（可选）
- Secrets：`PYPI_API_TOKEN`（可选）

**Docs**

- `docs/ci-cd.md`
