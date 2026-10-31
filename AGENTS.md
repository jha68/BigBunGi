# BigBunGi workflow

The user wants every completed project change redeployed automatically.

- Use the existing checkout; do not create a worktree unless requested.
- After appropriate validation, commit and push the completed changes to `main`
  to trigger `.github/workflows/pages.yml`. Routine redeployment is authorized;
  do not ask for confirmation again.
- Check the deployment run and its public HTTPS verification before reporting
  that changes are live. Investigate failures and continue until deployment
  succeeds or a concrete external blocker remains.
- Production URL: https://bigbungi.junununseo.com/.
- Preserve unrelated user changes. Never commit credentials or generated caches.
