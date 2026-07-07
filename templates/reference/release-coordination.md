# Release Coordination for Product Owners

Coordinate releases across teams to minimize chaos, catch bugs early, and maintain the ability to rollback quickly.

---

## Dependency Mapping

Before shipping any release, identify what blocks what.

### Build Dependency Chart

```
Feature A (Mobile checkout)
  ├─ Depends on: Backend API (Feature B)
  └─ Blocking: Feature C (Mobile payments)

Feature B (Backend API)
  ├─ Depends on: Infrastructure work (Feature D)
  └─ Blocking: Feature A, Feature C
```

### Sequencing Decision

- Ship Feature D first (no dependencies)
- Then Feature B (depends on D)
- Then Feature A (depends on B)
- Then Feature C (depends on A and B)

---

## Staging Gates (Feature Must Pass Each)

Every feature goes through multiple gates before reaching production.

### Gate 1: Feature Complete (Dev Team)
### Gate 2: Design Review (Product + Design)
### Gate 3: QA Gate (QA + PO)
### Gate 4: Product Approval (PO)

---

## Risk Sequencing

For any release with multiple features, sequence by risk.

**High-risk features** (ship early, have more time to test):
- New technology/architecture
- Affects many users
- Complex edge cases

**Low-risk features** (ship later, less testing needed):
- Bug fixes
- Minor UI improvements
- Isolated features

---

## Staged Rollout Strategy (Feature Flags)

Never ship features to 100% of users at once. Use feature flags.

### Phase 1: 1% of Users
### Phase 2: 10% of Users
### Phase 3: 100% of Users

---

## Launch Readiness Checklist

Before ANY production deployment, verify this checklist is complete.

---

## Cross-Team Release Sync

**Weekly During Release Window (1 hour)**

---

## Rollback Planning & Execution

Every release should have a tested rollback plan.

---

## Implementation Checklist

- [ ] Document dependencies before release
- [ ] Set up staging gates for all features
- [ ] Create feature flag configuration
- [ ] Complete launch readiness checklist
- [ ] Document rollback plan + test it
- [ ] Schedule weekly release sync
- [ ] Brief on-call team on feature
- [ ] Set up monitoring + alerts
- [ ] Create support documentation
- [ ] Draft customer communication
- [ ] Post-release: Monitor every 30 min for 48 hours
- [ ] Post-release: Schedule retrospective (what went well/poorly?)