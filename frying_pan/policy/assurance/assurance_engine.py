from __future__ import annotations

from frying_pan.policy.assurance.behavior_diff import BehaviorDiff
from frying_pan.policy.assurance.behavior_snapshot import BehaviorSnapshot


class PolicyAssuranceEngine:
    def compare(self, before: BehaviorSnapshot, after: BehaviorSnapshot) -> BehaviorDiff:
        changed = (
            before.action != after.action or before.matched_rule_name != after.matched_rule_name
        )
        warnings: list[str] = []
        if changed:
            warnings.append(
                "Policy behavior changed for this test case; operator review is required."
            )
        return BehaviorDiff(before=before, after=after, behavior_changed=changed, warnings=warnings)
