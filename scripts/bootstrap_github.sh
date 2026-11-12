#!/usr/bin/env bash
# One-time GitHub setup: labels, milestones, branch protection and lecturer invitation.
# Requires the GitHub CLI logged in (`gh auth login`) with admin rights on the repo.
#
#   ./scripts/bootstrap_github.sh OWNER/REPO
#
# Safe to run twice: existing labels/milestones are skipped.
set -uo pipefail

REPO="${1:?usage: $0 OWNER/REPO}"
OWNER="${REPO%%/*}"
LECTURER_EMAIL="jordi.pascual@urv.cat"

echo "== Labels"
while IFS='|' read -r name color desc; do
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" 2>/dev/null \
    && echo "  + $name" || echo "  = $name (exists)"
done <<'EOF'
report|1d76db|Task reports and slides
flow|5319e7|Flow and router (main.py)
crews|0e8a16|Agents, tasks and crews
tools|fbca04|Custom tools (conflict detection, ...)
data|c5def5|Input scenarios
tests|bfd4f2|Tests
docs|0075ca|README and documentation
infra|ededed|CI, bots, repository setup
meeting|d4c5f9|Meeting agenda / minutes
wip|cccccc|Work in progress, ignored by the stale bot
EOF

echo "== Milestones"
create_milestone() {
  local title="$1" due="$2" desc="$3"
  if gh api "repos/$REPO/milestones?state=all" --jq '.[].title' | grep -qxF "$title"; then
    echo "  = $title (exists)"
  else
    gh api "repos/$REPO/milestones" -f title="$title" -f due_on="$due" -f description="$desc" \
      --silent && echo "  + $title"
  fi
}
create_milestone "Task 1 - Design" "2026-11-22T22:55:00Z" "PDF report + 8-10 slides (15%)"
create_milestone "Task 2 - Flow skeleton" "2026-12-16T22:55:00Z" "ZIP with CrewAI flow project and flow plot (5%)"
create_milestone "Final delivery" "2027-01-10T22:55:00Z" "Code ZIP + final report + 10-12 slides (35%)"

echo "== Branch protection on main (CI 'test' must pass, no direct pushes)"
gh api -X PUT "repos/$REPO/branches/main/protection" --input - <<'EOF' >/dev/null \
  && echo "  ok" \
  || echo "  ! failed (private repos on free plans do not support it: make the repo public or use GitHub Education/Team)"
{
  "required_status_checks": {"strict": true, "contexts": ["test"]},
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF

echo "== Lecturer access ($LECTURER_EMAIL)"
if [ "$(gh api "users/$OWNER" --jq .type)" = "Organization" ]; then
  gh api -X POST "orgs/$OWNER/invitations" -f email="$LECTURER_EMAIL" -f role=direct_member \
    --silent && echo "  invitation sent to the organization" \
    || echo "  ! could not invite by email; add him manually in the org People settings"
else
  echo "  Personal repo: Settings > Collaborators > Add people > search '$LECTURER_EMAIL'"
fi

echo "Done. Remember: every member runs 'uv sync && uv run pre-commit install'."
