# Fitness Thresholds

This file defines deterministic thresholds for architecture fitness functions.

## Thresholds

### dependency_rule_violations
- PASS: 0 violations
- WARN: 1-3 violations
- FAIL_CRITICAL: >=4 violations or violation in protected boundary

### complexity_hotspots
- PASS: no module exceeds agreed complexity threshold
- WARN: 1-2 modules exceed threshold by <=20%
- FAIL_CRITICAL: >2 modules exceed threshold or any module exceeds by >50%

### duplication_trend
- PASS: stable or decreasing duplication
- WARN: increase <=5% over review window
- FAIL_CRITICAL: increase >5% over review window

### test_flakiness_rate
- PASS: <2%
- WARN: 2%-5%
- FAIL_CRITICAL: >5%

### performance_budget_regression
- PASS: <=5%
- WARN: >5% and <=10%
- FAIL_CRITICAL: >10%

### security_static_findings
- PASS: no high/critical findings
- WARN: low/medium findings only
- FAIL_CRITICAL: any critical finding
