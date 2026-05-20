from __future__ import annotations

from frying_pan.normalized.rules import RuleAction, SecurityRule
from frying_pan.policy.audit.audit_engine import PolicyAuditEngine
from frying_pan.policy.audit.findings import FindingType


def test_policy_audit_flags_broad_allow_scaffold() -> None:
    findings = PolicyAuditEngine().audit(
        "source-1",
        "shared/security",
        [SecurityRule(name="allow-any", scope_path="shared", action=RuleAction.ALLOW)],
    )

    assert findings
    assert findings[0].finding_type == FindingType.BROAD_ALLOW
