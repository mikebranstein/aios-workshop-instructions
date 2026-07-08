# Metrics & Experimentation for Product Owners

Use data to make backlog decisions, not opinion. This guide covers AARRR framework, funnel analysis, cohort analysis, and A/B testing.

---

## AARRR Framework: Identify What's Broken First

Before shipping new features, identify which metric is broken. Then prioritize fixes to that metric.

### The Five Metrics

**Acquisition:** Are new users arriving?
- Measure: New users per month, CAC (cost per acquisition)
- Target: Growing at target rate (e.g., +10% month-over-month)
- If broken: Improve marketing, sales, or awareness

**Activation:** Do new users complete onboarding?
- Measure: % of new users who [complete onboarding / sign up / try first feature]
- Target: 40-60% (varies by product)
- If broken: Improve onboarding flow, reduce friction

**Retention:** Do users come back?
- Measure: % of users active after 7 days, 30 days, 90 days
- Target: 50%+ at day 7, 30%+ at day 30
- If broken: Improve core product, add engagement features

**Referral:** Do users invite others?
- Measure: % of users who refer someone, viral coefficient
- Target: 10-20% viral (depends on business model)
- If broken: Improve referral mechanics, incentives

**Revenue:** Are users generating revenue?
- Measure: Total ARR, ARPU (average revenue per user), LTV:CAC ratio
- Target: LTV > 3x CAC
- If broken: Improve pricing, upsell, reduce churn

---

## Implementation Checklist

- [ ] Define AARRR metrics for your product
- [ ] Identify which metric is broken first
- [ ] Document pre-launch success metrics (primary + secondary)
- [ ] Analyze current funnel (identify biggest drop-offs)
- [ ] Analyze cohorts (are recent users better/worse?)
- [ ] Set up dashboards for all metrics
- [ ] Create alerts for regression
- [ ] Plan weekly metrics review cadence (Monday standup)
- [ ] For high-risk features, plan A/B test
- [ ] Document adoption tracking plan
- [ ] Set kill-decision criteria (if adoption <X% after Y days)
- [ ] Post-launch: Review metrics weekly
- [ ] Month 3: Cohort review (Phase 2 or de-prioritize?)