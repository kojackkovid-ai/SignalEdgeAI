"""
Email Templates Service
Handles email template definitions and rendering
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.email_models import EmailTemplate

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service for managing and rendering email templates"""
    
    def __init__(self):
        self.templates = {
            'prediction_result': {
                'subject': 'Your Prediction Result - {{ sport }}',
                'name': 'prediction_result',
                'html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Prediction Result 📊</h2>
    <p>Hi {{ user_name }},</p>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h3>{{ matchup }}</h3>
        <p><strong>Prediction:</strong> {{ prediction }}</p>
        <p><strong>Sport:</strong> {{ sport }}</p>
        <p><strong>Result:</strong> <span style="color: {% if result == 'hit' %}green{% elif result == 'miss' %}red{% else %}gray{% endif %}; font-weight: bold;">{{ result_label }}</span></p>
        <p><strong>Confidence:</strong> {{ confidence }}%</p>
    </div>
    
    <p><a href="{{ dashboard_url }}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Dashboard</a></p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
    <p style="font-size: 12px; color: #666;">You received this email because you have prediction result emails enabled.</p>
</div>
''',
                'text': '''Prediction Result
Hi {{ user_name }},

Matchup: {{ matchup }}
Prediction: {{ prediction }}
Sport: {{ sport }}
Result: {{ result_label }}
Confidence: {{ confidence }}%

View your full dashboard: {{ dashboard_url }}
'''
            },
            
            'daily_digest': {
                'subject': 'Your Daily Picks Summary - {{ date }}',
                'name': 'daily_digest',
                'html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Daily Picks Summary 🎯</h2>
    <p>Hi {{ user_name }},</p>
    
    <p>Here's your daily picks summary for {{ date }}:</p>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <p><strong>Picks Made:</strong> {{ picks_count }}</p>
        <p><strong>Win Rate Today:</strong> {{ win_rate }}%</p>
        <p><strong>Your Tier:</strong> {{ tier }}</p>
    </div>
    
    <h3>today's Picks:</h3>
    {% for pick in picks %}
    <div style="border-left: 3px solid #007bff; padding-left: 15px; margin: 15px 0;">
        <p><strong>{{ pick.matchup }}</strong></p>
        <p>Prediction: {{ pick.prediction }}</p>
        <p>Confidence: {{ pick.confidence }}%</p>
        <p>Sport: {{ pick.sport }}</p>
    </div>
    {% endfor %}
    
    <p><a href="{{ dashboard_url }}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Full Dashboard</a></p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
    <p style="font-size: 12px; color: #666;">You received this email because you have daily digest emails enabled.</p>
</div>
''',
                'text': '''Daily Picks Summary
Hi {{ user_name }},

Date: {{ date }}
Picks Made: {{ picks_count }}
Win Rate: {{ win_rate }}%
Your Tier: {{ tier }}

Today's Picks:
{% for pick in picks %}
- {{ pick.matchup }}: {{ pick.prediction }} ({{ pick.confidence }}% confidence)
{% endfor %}

View your full dashboard: {{ dashboard_url }}
'''
            },
            
            'weekly_digest': {
                'subject': 'Your Weekly Performance Report',
                'name': 'weekly_digest',
                'html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Weekly Performance Report 📈</h2>
    <p>Hi {{ user_name }},</p>
    
    <p>Here's your performance summary for the week of {{ week_of }}:</p>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <p><strong>Total Picks:</strong> {{ total_picks }}</p>
        <p><strong>Hits:</strong> <span style="color: green;">{{ hits }}</span></p>
        <p><strong>Misses:</strong> <span style="color: red;">{{ misses }}</span></p>
        <p><strong>Win Rate:</strong> {{ win_rate }}%</p>
        <p><strong>Avg Confidence:</strong> {{ avg_confidence }}%</p>
    </div>
    
    <h3>Top Sports This Week:</h3>
    {% for sport in top_sports %}
    <p>{{ sport.name }}: {{ sport.picks }} picks ({{ sport.win_rate }}% WR)</p>
    {% endfor %}
    
    <p style="margin-top: 20px;">
        {% if win_rate >= 50 %}
        🎉 Great week! Keep up the momentum!
        {% elif win_rate >= 40 %}
        📊 Solid performance! You're improving!
        {% else %}
        💪 Keep learning and improving!
        {% endif %}
    </p>
    
    <p><a href="{{ dashboard_url }}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Detailed Stats</a></p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
    <p style="font-size: 12px; color: #666;">You received this email because you have weekly digest emails enabled.</p>
</div>
''',
                'text': '''Weekly Performance Report
Hi {{ user_name }},

Week of: {{ week_of }}
Total Picks: {{ total_picks }}
Hits: {{ hits }}
Misses: {{ misses }}
Win Rate: {{ win_rate }}%
Avg Confidence: {{ avg_confidence }}%

Top Sports This Week:
{% for sport in top_sports %}
- {{ sport.name }}: {{ sport.picks }} picks ({{ sport.win_rate }}% WR)
{% endfor %}

View your full stats: {{ dashboard_url }}
'''
            },
            
            'password_reset': {
                'subject': 'Reset Your Password',
                'name': 'password_reset',
                'html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Password Reset Request</h2>
    <p>Hi {{ user_name }},</p>
    
    <p>We received a request to reset your password. Click the link below to create a new password:</p>
    
    <p style="margin: 20px 0;">
        <a href="{{ reset_url }}" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
    </p>
    
    <p style="color: #666; font-size: 12px;">This link will expire in 1 hour.</p>
    
    <p>If you didn't request this, you can ignore this email. Your password won't change until you create a new one.</p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
    <p style="font-size: 12px; color: #666;">© 2026 Sports Prediction Platform. All rights reserved.</p>
</div>
''',
                'text': '''Password Reset Request
Hi {{ user_name }},

Click this link to reset your password:
{{ reset_url }}

This link will expire in 1 hour.

If you didn't request this, you can ignore this email.
'''
            },
            
            'tier_upgrade': {
                'subject': 'Welcome to {{ new_tier }}! 🎉',
                'name': 'tier_upgrade',
                'html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Welcome to {{ new_tier }}! 🎉</h2>
    <p>Hi {{ user_name }},</p>
    
    <p>Congratulations! You've successfully upgraded to <strong>{{ new_tier }}</strong>.</p>
    
    <div style="background: #e8f4f8; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h3>Your New Features:</h3>
        {% for feature in features %}
        <p>✓ {{ feature }}</p>
        {% endfor %}
    </div>
    
    <p>You can now:</p>
    <ul>
        <li>Unlock up to {{ daily_limit }} picks per day</li>
        <li>Access premium analysis and insights</li>
        <li>Use advanced filters and search</li>
    </ul>
    
    <p><a href="{{ dashboard_url }}" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Start Exploring</a></p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
    <p style="font-size: 12px; color: #666;">Thank you for supporting the platform!</p>
</div>
''',
                'text': '''Welcome to {{ new_tier }}!
Hi {{ user_name }},

Congratulations! You've upgraded to {{ new_tier }}.

Your New Features:
{% for feature in features %}
- {{ feature }}
{% endfor %}

Daily Limit: {{ daily_limit }} picks
Premium Features: Yes
Advanced Analysis: Yes

Start exploring: {{ dashboard_url }}
'''
            },
            
            'email_verification': {
                'subject': 'Verify Your Email Address',
                'name': 'email_verification',
                'html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Verify Your Email</h2>
    <p>Hi {{ user_name }},</p>
    
    <p>Click the link below to verify your email address:</p>
    
    <p style="margin: 20px 0;">
        <a href="{{ verification_url }}" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Verify Email</a>
    </p>
    
    <p style="color: #666; font-size: 12px;">This link will expire in 24 hours.</p>
    
    <p>If you didn't create this account, you can ignore this email.</p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
    <p style="font-size: 12px; color: #666;">© 2026 Sports Prediction Platform. All rights reserved.</p>
</div>
''',
                'text': '''Verify Your Email
Hi {{ user_name }},

Click this link to verify your email:
{{ verification_url }}

This link will expire in 24 hours.
'''
            },
            
            'accuracy_milestone': {
                'subject': 'Congratulations! You Hit {{ milestone }}% Win Rate! 🎯',
                'name': 'accuracy_milestone',
                'html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>🎯 Milestone Achievement!</h2>
    <p>Hi {{ user_name }},</p>
    
    <p>Congratulations! You've reached a <strong>{{ milestone }}% win rate</strong>!</p>
    
    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
        <p style="font-size: 18px; font-weight: bold;">{{ milestone }}%</p>
        <p>You're in the top {{ percentile }}% of predictors!</p>
    </div>
    
    <p>Keep up the great work! Your consistent performance is impressive.</p>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h3>Your Stats</h3>
        <p><strong>Total Picks:</strong> {{ total_picks }}</p>
        <p><strong>Hits:</strong> {{ hits }}</p>
        <p><strong>Misses:</strong> {{ misses }}</p>
        <p><strong>Avg Confidence:</strong> {{ avg_confidence }}%</p>
    </div>
    
    <p><a href="{{ dashboard_url }}" style="background: #ffc107; color: black; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Your Profile</a></p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
    <p style="font-size: 12px; color: #666;">Keep pushing for even higher win rates!</p>
</div>
''',
                'text': '''Congratulations! {{ milestone }}% Win Rate!
Hi {{ user_name }},

You've reached a {{ milestone }}% win rate!
You're in the top {{ percentile }}% of predictors!

Your Stats:
Total Picks: {{ total_picks }}
Hits: {{ hits }}
Misses: {{ misses }}
Avg Confidence: {{ avg_confidence }}%

View your profile: {{ dashboard_url }}
'''
            }
        }
    
    async def create_default_templates(self, db: AsyncSession):
        """Create default email templates in database"""
        try:
            for template_name, template_data in self.templates.items():
                # Check if template exists
                result = await db.execute(
                    select(EmailTemplate).where(
                        EmailTemplate.name == template_name
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    template = EmailTemplate(
                        name=template_name,
                        subject=template_data['subject'],
                        html_body=template_data['html'],
                        text_body=template_data.get('text'),
                        is_active=True
                    )
                    db.add(template)
            
            await db.commit()
            logger.info("✅ Email templates created/verified")
        except Exception as e:
            logger.warning(f"Error creating templates: {e}")
            await db.rollback()
