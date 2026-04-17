# Mailgun Email Integration Guide

## Overview
The platform now has full email integration powered by Mailgun. This supports:
- Daily/weekly digest emails
- Prediction result notifications
- Tier upgrade announcements
- Password reset emails
- Email verification
- Promotional campaigns
- Accuracy milestone celebrations

## Configuration

### 1. Add .env Variables
Your `.env` file now includes:
```env
MAILGUN_API_KEY=your-mailgun-api-key-here
MAILGUN_DOMAIN=mg.sportstats.com
MAILGUN_SENDER=noreply@sportstats.com
```

**Important**: Update `MAILGUN_DOMAIN` with your actual sending domain from Mailgun dashboard.

### 2. Install Dependencies
The `mailgun-sdk` package has been added to `requirements.txt`.

## API Endpoints

### Email Preferences
**Get user's email preferences:**
```
GET /api/email/preferences
```
Returns what types of emails user receives.

**Update email preferences:**
```
POST /api/email/preferences
Body: {
  "prediction_results": true,
  "daily_digest": true,
  "weekly_digest": true,
  "tier_updates": true,
  "promotional": false,
  "account_updates": true,
  "new_features": true,
  "accuracy_milestone": true
}
```

### Email Verification
**Send verification email:**
```
POST /api/email/verify-email
```

**Verify with token (called from email link):**
```
POST /api/email/verify-email/{token}
```

### Email Logs
**Get user's email history:**
```
GET /api/email/logs?limit=50&email_type=prediction_result
```

### Test Email
**Send test email (for development):**
```
POST /api/email/test?template_name=prediction_result
```

### Unsubscribe
**Unsubscribe from email type:**
```
POST /api/email/unsubscribe/{token}?email_type=promotional
```

## Email Types

### 1. Prediction Result Emails
Sent immediately when a prediction resolves.
- **Template**: `prediction_result`
- **Preference**: `prediction_results`
- **Trigger**: When PredictionRecord.outcome is updated

### 2. Daily Digest
Summary of picks from previous day.
- **Template**: `daily_digest`
- **Preference**: `daily_digest`
- **Schedule**: Daily at 6 AM UTC

### 3. Weekly Digest
Performance summary for the past week.
- **Template**: `weekly_digest`
- **Preference**: `weekly_digest`
- **Schedule**: Monday at 6 AM UTC

### 4. Tier Upgrade
Congratulations email for tier upgrades.
- **Template**: `tier_upgrade`
- **Preference**: `tier_updates`
- **Trigger**: On successful tier upgrade

### 5. Password Reset
Email with password reset link.
- **Template**: `password_reset`
- **Preference**: `account_updates`
- **Trigger**: On password reset request

### 6. Email Verification
Email with verification link for new accounts.
- **Template**: `email_verification`
- **Preference**: `account_updates`
- **Trigger**: On signup or verification request

### 7. Accuracy Milestone
Celebration email when hitting accuracy milestones.
- **Template**: `accuracy_milestone`
- **Preference**: `accuracy_milestone`
- **Schedule**: Every 6 hours (checks for new milestones)
- **Milestones**: 50%, 60%, 70%, 75%, 80%, 90%, 95%, 99%

## Integration Examples

### Integrate with Tier Upgrade Flow
```python
from app.services.email_integration_service import EmailIntegrationService
from app.services.mailgun_service import MailgunService

# In your tier upgrade endpoint:
mailgun = MailgunService(settings)
email_service = EmailIntegrationService(settings, mailgun)

await email_service.send_tier_upgrade_email(
    db=db,
    user_id=user_id,
    new_tier='pro_plus',
    features=['Unlimited picks', 'Advanced analysis', 'Premium support']
)
```

### Integrate with Password Reset
```python
await email_service.send_password_reset_email(
    db=db,
    user_id=user_id,
    reset_token=reset_token
)
```

### Integrate with Prediction Resolution
```python
# In your prediction resolution service:
await email_service.send_prediction_result_email(
    db=db,
    user_id=user_id,
    matchup='Lakers vs Celtics',
    prediction='Lakers Win',
    result='hit',
    confidence=0.75,
    sport='basketball_nba',
    resolved_at=datetime.utcnow()
)
```

### Send Promotional Campaign
```python
# Send promo to all users who want promotions
user_ids = []  # Get from database
result = await email_service.send_promotional_email(
    db=db,
    user_ids=user_ids,
    subject='Limited Time: 50% Off Pro Plus!',
    html_body='<h1>Special Offer</h1>...',
    text_body='Special Offer...'
)
```

## Email Templates

Templates are stored in the `email_templates` table and rendered using Jinja2 syntax. 

Available templates:
- `prediction_result` - Prediction resolve notification
- `daily_digest` - Daily picks summary
- `weekly_digest` - Weekly performance report
- `password_reset` - Password reset link
- `tier_upgrade` - New tier announcement
- `email_verification` - Email verification link
- `accuracy_milestone` - Milestone celebration

### Template Variables

**prediction_result:**
- `{{ user_name }}` - User's username
- `{{ matchup }}` - Game matchup
- `{{ prediction }}` - Prediction text
- `{{ sport }}` - Sport name
- `{{ result }}` - hit/miss/void/push
- `{{ result_label }}` - Formatted result
- `{{ confidence }}` - Confidence percentage
- `{{ dashboard_url }}` - Link to dashboard

**daily_digest:**
- `{{ user_name }}`
- `{{ date }}` - Date of digest
- `{{ picks_count }}` - Number of picks
- `{{ win_rate }}` - Win rate percentage
- `{{ tier }}` - User's tier
- `{{ picks }}` - List of picks with {matchup, prediction, confidence, sport}
- `{{ dashboard_url }}`

**weekly_digest:**
- `{{ user_name }}`
- `{{ week_of }}` - Start date of week
- `{{ total_picks }}`
- `{{ hits }}` - Number of hits
- `{{ misses }}` - Number of misses
- `{{ win_rate }}`
- `{{ avg_confidence }}` - Average confidence
- `{{ top_sports }}` - List of {name, picks, win_rate}
- `{{ dashboard_url }}`

**Other templates:**
See templates in `email_templates_service.py` for full variable lists.

## Background Tasks

### Daily Digest Task
- **Time**: 6 AM UTC daily
- **Action**: Sends daily summary to users who:
  - Have `daily_digest` preference enabled
  - Have verified email
  - Made predictions yesterday

### Weekly Digest Task
- **Time**: Monday 6 AM UTC
- **Action**: Sends weekly summary (same criteria as daily)

### Milestone Task
- **Time**: Every 6 hours
- **Action**: Checks if users hit accuracy milestones and sends celebration emails

### Custom Schedule
To change times, modify `app/tasks/email_tasks.py`:
```python
# In run_email_task_loop()
if hour == 6 and now.minute < 5:  # Change 6 to desired hour (0-23 UTC)
    await send_daily_digest(db)
```

## Database Models

### EmailPreferences
Stores user's email subscription settings:
- `prediction_results` - Get emails when predictions resolve
- `daily_digest` - Get daily pick summary
- `weekly_digest` - Get weekly performance
- `tier_updates` - Get notified on tier upgrades
- `promotional` - Get marketing emails
- `account_updates` - Get password resets, alerts
- `new_features` - Get notified of new features
- `accuracy_milestone` - Get milestone celebrations
- `verified` - Email address verified
- `unsubscribe_token` - One-click unsubscribe token

### EmailLog
Tracks all emails sent:
- `mailgun_message_id` - Mailgun tracking ID
- `status` - sent/bounced/complained/opened/clicked/failed
- `sent_at` - When email was sent
- `opened_at` - When user opened (if tracked)
- `context_data` - Data used in email

### EmailTemplate
Email template definitions:
- `name` - Template name (unique)
- `subject` - Email subject with {{ variables }}
- `html_body` - HTML template
- `text_body` - Plain text alternative
- `is_active` - Whether template is active

## Mailgun Webhook Integration (Optional)

Mailgun can send webhooks for email events (opens, clicks, bounces, etc).

To enable:
1. Go to Mailgun Dashboard → Webhooks
2. Add webhook for your domain
3. Configure callback URL: `https://your-domain.com/api/email/webhooks/mailgun`
4. Implement webhook handler in `app/routes/email.py`

Example webhook handler:
```python
@router.post("/webhooks/mailgun")
async def mailgun_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Mailgun email events"""
    payload = await request.json()
    
    event = payload.get('event')
    mailgun_id = payload['message']['headers']['message-id']
    
    # Update email log
    log = await db.execute(
        select(EmailLog).where(EmailLog.mailgun_message_id == mailgun_id)
    )
    email_log = log.scalar_one_or_none()
    
    if email_log:
        email_log.status = event
        if event == 'opened':
            email_log.opened_at = datetime.utcnow()
        await db.commit()
    
    return {"status": "processed"}
```

## Testing

### Send Test Email
```bash
curl -X POST http://localhost:8000/api/email/test?template_name=prediction_result \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### View Email Logs
```bash
curl -X GET http://localhost:8000/api/email/logs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Check Mailgun Configuration
```bash
# Test API key directly
curl --user api:YOUR_API_KEY \
  https://api.mailgun.net/v3/mg.sportstats.com/messages
```

## Common Issues

### Emails Not Sending
1. **Check Mailgun configuration**: Verify API key and domain in `.env`
2. **Check user preferences**: User may have disabled email type
3. **Check logs**: Look at backend logs for errors
4. **Test email**: Use `/api/email/test` endpoint
5. **Mailgun status**: Check if domain/API key is valid on Mailgun dashboard

### Wrong Sender Name
Update `MAILGUN_SENDER` in `.env` to change sender email address.

### Template Rendering Errors
Check template syntax in `email_templates_service.py`. Use `{{ }}` for variables, not `{ }`.

### Emails Going to Spam
- Warm up domain (send gradually increasing volumes)
- Set up SPF, DKIM, DMARC records on your domain
- Use professional sender domain (not @gmail.com)
- Avoid spam trigger words in subject/content

## Production Checklist

- [ ] Update `MAILGUN_DOMAIN` to your actual sending domain
- [ ] Verify domain in Mailgun (SPF, DKIM, DMARC)
- [ ] Update email sender from noreply@sportstats.com to your domain
- [ ] Test all email templates with real user data
- [ ] Set up Mailgun webhooks for bounce/complaint handling
- [ ] Configure email preference defaults
- [ ] Test with Gmail, Outlook, Apple Mail
- [ ] Set up monitoring for failed sends
- [ ] Create unsubscribe header in templates
- [ ] Document tier upgrade/password reset flows

## Additional Resources

- [Mailgun Documentation](https://documentation.mailgun.com/)
- [Email Marketing Best Practices](https://mailgun.com/blog/)
- [Jinja2 Template Syntax](https://jinja.palletsprojects.com/)
