# PRODUCTION DEPLOYMENT CHECKLIST

**Quick Reference for Production Launch**

---

## Pre-Deployment (Run 48 hours before launch)

### Security
- [ ] All print() statements removed from backend
- [ ] No hardcoded secrets in any file
- [ ] Git history cleaned: `git log --all -S 'password'` returns nothing
- [ ] `.env.production` is in `.gitignore`
- [ ] All Stripe keys are `pk_live_*` and `sk_live_*` (not test)
- [ ] DATABASE_URL uses real production credentials
- [ ] SECRET_KEY is 32+ characters
- [ ] Bandit scan: `bandit -r backend/app` - 0 issues
- [ ] npm audit: `npm audit` - no high vulnerabilities

### Configuration
- [ ] ENVIRONMENT=production (not development)
- [ ] LOG_LEVEL=info (not debug)
- [ ] enable_https_redirect=true
- [ ] CORS origins set to production domains only
- [ ] Rate limiting enabled and tested
- [ ] Database pool_size=20, max_overflow=40
- [ ] Redis maxmemory=512mb
- [ ] Sentry DSN configured

### Database
- [ ] Database backups running and tested
- [ ] Migrations applied: `alembic upgrade head`
- [ ] Indexes created on frequently queried fields
- [ ] Test restore from backup
- [ ] Production database has < 100,000 rows (or scaled appropriately)
- [ ] Connection limit set to 100+

### Monitoring
- [ ] Sentry initialized and error alerts configured
- [ ] Uptime monitoring configured (UptimeRobot, StatusPage)
- [ ] Log aggregation set up (CloudWatch/ELK)
- [ ] Health check endpoint working: `/health`
- [ ] Readiness probe working: `/health/ready`

### Frontend
- [ ] Build succeeds: `npm run build`
- [ ] No console errors in production build
- [ ] Stripe public key is `pk_live_*`
- [ ] API_URL points to production backend (https)
- [ ] TypeScript strict mode enabled
- [ ] ESLint passing: `npm run lint`

### Testing
- [ ] Login flow tested end-to-end
- [ ] Payment flow tested end-to-end (test payment in Stripe test mode first)
- [ ] Prediction generation tested for all sports
- [ ] At least 10 concurrent users tested without errors
- [ ] Error handling tested (try 500 error scenarios)
- [ ] Rate limiting tested (verify 429 responses)

---

## Deployment Day

### Hour -1 (1 hour before launch)

**Communication**:
- [ ] Notify support/customer team of launch
- [ ] Prepare rollback plan (document it)
- [ ] Assign on-call person for monitoring
- [ ] Have Fly.io/deployment dashboard open

**Final Checks**:
- [ ] Staging environment tests passing
- [ ] No uncommitted changes in git
- [ ] All team members on standby
- [ ] Rollback procedure tested

### Hour 0 (Deployment)

```bash
# 1. Tag release in git
git tag -a v1.0.0-production -m "Production release"
git push origin v1.0.0-production

# 2. Set production secrets in Fly.io
flyctl secrets set \
  ENVIRONMENT=production \
  SECRET_KEY=<strong-key> \
  STRIPE_SECRET_KEY=sk_live_xxx \
  STRIPE_PUBLIC_KEY=pk_live_xxx \
  ODDS_API_KEY=xxx \
  DB_PASSWORD=xxx \
  SENTRY_DSN=xxx \
  LOG_LEVEL=info

# 3. Deploy
flyctl deploy --app signaledge-ai

# 4. Monitor deployment
flyctl logs -f --app signaledge-ai
```

**Deployment Checklist**:
- [ ] Build completes successfully
- [ ] Container image pushed to registry
- [ ] Deployment progresses without errors
- [ ] 0 errors in logs after deployment
- [ ] Health check `/health` returns 200
- [ ] `/health/ready` returns 200
- [ ] At least 5 backend instances running

### Hour +1 (Post-Deployment)

**Immediate Validation**:
- [ ] Frontend loads without JS errors
- [ ] Login works with test account
- [ ] Can create prediction without errors
- [ ] Predictions have confidence scores
- [ ] No 500 errors in logs
- [ ] Sentry shows 0 unresolved issues
- [ ] Response times < 1 second (p95)

**User Communication**:
- [ ] Status page shows "Operational"
- [ ] Support team notified of successful launch
- [ ] Customer notification (if applicable)

---

## Post-Launch Monitoring (First 24 hours)

### Every Hour:
- [ ] [ ] Check Sentry for errors (should be near 0)
- [ ] [ ] Check uptime monitoring (should be 100%)
- [ ] [ ] Check error rate (should be < 0.1%)
- [ ] [ ] Check response times (p95 < 1s, p99 < 2s)

### Every 4 Hours:
- [ ] [ ] Review logs for warnings
- [ ] [ ] Check database connection pool health
- [ ] [ ] Check Redis memory usage
- [ ] [ ] Test critical workflows (login, payment)

### Daily (First 7 Days):
- [ ] [ ] Database size within expected bounds
- [ ] [ ] No memory leaks (instance memory stable)
- [ ] [ ] All scheduled jobs running (training pipeline)
- [ ] [ ] Backup jobs completing successfully

---

## Rollback Procedure (If Needed)

```bash
# 1. Assess severity
#    - If error rate > 5%: Rollback immediately
#    - If specific feature broken: Deploy hotfix (don't rollback)
#    - If data loss risk: Rollback AND investigate

# 2. Rollback to previous version
git checkout v<previous-version-tag>
flyctl deploy --app signaledge-ai

# 3. Verify rollback succeeded
flyctl logs -f --app signaledge-ai
# Should see no errors after deployment

# 4. Notify team
# - Document what failed
# - Schedule post-mortem
# - Create bug tickets for issues found
```

---

## Success Criteria (Launch is successful if...)

✅ **First 24 hours**:
- Error rate < 0.5%
- 99th percentile response time < 2 seconds
- Zero data loss incidents
- All core features working (login, payments, predictions)

✅ **First 7 days**:
- Error rate < 0.1%
- No critical issues unresolved
- Daily active users > 10
- All payment transactions successful

✅ **First 30 days**:
- System running stably
- < 1 incident per week
- User feedback positive
- Ready to scale

---

## Emergency Contacts

| Role | Name | Phone | Slack |
|------|------|-------|-------|
| DevOps Lead | - | - | @devops |
| Backend Lead | - | - | @backend |
| Frontend Lead | - | - | @frontend |
| CEO | - | - | @ceo |

**Escalation Path**:
- Minor issue (< 100 users affected) → Tech Lead
- Major issue (100-1000 users affected) → CTO
- Critical issue (> 1000 users affected) → CEO

---

## Post-Mortem Template (If Issues Found)

```
Date: [Date]
Severity: [Critical/High/Medium]
Duration: [Start] - [End]
Users Affected: [Number]

What Happened:
[Description]

Root Cause:
[Investigation findings]

Fix Applied:
[What was done]

Prevention:
[How to prevent in future]

Follow-up Items:
- [ ] Item 1
- [ ] Item 2

Assigned To: [Name]
```

---

## After Launch: Week 1 Action Items

- [ ] Schedule post-launch review meeting
- [ ] Document any issues found and fixes applied
- [ ] Create tickets for any bugs discovered
- [ ] Evaluate performance against targets
- [ ] Gather user feedback
- [ ] Plan improvements for Week 2

---

## References

- [PRODUCTION_REVIEW.md](PRODUCTION_REVIEW.md) - Full production review
- [PRODUCTION_ACTION_PLAN.md](PRODUCTION_ACTION_PLAN.md) - Detailed implementation plan
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Original deployment checklist
- [Fly.io Docs](https://fly.io/docs/)
- [FastAPI Security](https://fastapi.tiangolo.com/advanced/security/)

---

**Last Updated**: May 3, 2026  
**Status**: 🟡 READY FOR IMPLEMENTATION
