from dataclasses import dataclass
from typing import Dict, Iterable, List

from aios_orchestration_core.github.pm_gateway import PMGitHubGateway
from aios_orchestration_core.labels.pm_labels import PM_CANONICAL_LABEL_BY_STATE, PM_LEGACY_LABEL_BY_STATE, normalize_pm_state_from_labels


@dataclass
class CleanRunCounter:
    required_consecutive_clean_runs: int = 10
    current_streak: int = 0

    def record_run(self, had_conflict: bool) -> None:
        if had_conflict:
            self.current_streak = 0
        else:
            self.current_streak += 1

    @property
    def bridge_exit_ready(self) -> bool:
        return self.current_streak >= self.required_consecutive_clean_runs


def backfill_pm_canonical_labels_for_open_issues(gateway: PMGitHubGateway, issue_numbers: Iterable[int]) -> Dict[int, List[str]]:
    updated: Dict[int, List[str]] = {}
    for issue_number in issue_numbers:
        issue = gateway.get_issue(issue_number)
        if not issue.open:
            continue
        normalized = normalize_pm_state_from_labels(issue.labels)
        if normalized.state is None:
            continue

        canonical_label = PM_CANONICAL_LABEL_BY_STATE[normalized.state]
        if canonical_label not in issue.labels:
            gateway.add_labels(issue_number, [canonical_label])
            gateway.post_comment(
                issue_number,
                "PM label migration: added canonical state label "
                f"{canonical_label} from legacy aliases.",
            )
            updated[issue_number] = [canonical_label]
    return updated


def find_legacy_pm_saved_view_queries(queries: Iterable[str]) -> List[str]:
    legacy_labels = set(PM_LEGACY_LABEL_BY_STATE.values())
    flagged = []
    for query in queries:
        if any(label in query for label in legacy_labels):
            flagged.append(query)
    return flagged
