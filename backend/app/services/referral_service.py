





+""
Referral System for Monetization
Reward users for referring new customers
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import secrets

logger = logging.getLogger(__name__)


class ReferralService:
    """
    Handle referral rewards and tracking.
    Implements tier-based referral rewards.
    """
    
    # Referral rewards configuration
    REFERRAL_REWARDS = {
        'free_to_paid': {
            'referrer': {
                'tier_extension_days': 30,
                'tier': 'pro'  # Upgrade referrer to Pro for 30 days
            },
            'referred': {
                'discount_percent': 50,
                'discount_months': 1
            }
        },
        'paid_to_paid': {
            'referrer': {
                'tier_extension_days': 30,
                'tier': 'same'  # Extend same tier
            },
            'referred': {
                'discount_percent': 25,
                'discount_months': 1
            }
        }
    }
    
    # Bonus for referring multiple users
    BONUS_THRESHOLDS = {
        5: {'bonus_days': 7, 'description': '5 referrals bonus'},
        10: {'bonus_days': 15, 'description': '10 referrals bonus'},
        25: {'bonus_days': 30, 'description': '25 referrals bonus'},
        50: {'bonus_days': 60, 'description': '50 referrals bonus'}
    }
    
    def __init__(self, db=None):
        """
        Initialize referral service.
        
        Args:
            db: Database connection (optional - can work without for simple tracking)
        """
        self.db = db
        self.referral_codes: Dict[str, Dict] = {}
        self.referrals: List[Dict] = []
    
    def generate_referral_code(self, user_id: int, username: str) -> str:
        """
        Generate unique referral code for user.
        
        Args:
            user_id: User's ID
            username: User's username for personalization
            
        Returns:
            Unique referral code
        """
        # Create personalized code: first 4 chars of username + random
        prefix = username[:4].upper() if username else 'REF'
        code = f"{prefix}{secrets.token_hex(3).upper()}"
        
        # Ensure uniqueness
        if code in self.referral_codes:
            code = f"{prefix}{secrets.token_hex(4).upper()}"
        
        self.referral_codes[code] = {
            'user_id': user_id,
            'code': code,
            'created_at': datetime.utcnow(),
            'uses': 0,
            'active': True
        }
        
        logger.info(f"Generated referral code {code} for user {user_id}")
        return code
    
    def get_referral_code(self, user_id: int) -> Optional[str]:
        """Get existing referral code for user"""
        for code, data in self.referral_codes.items():
            if data['user_id'] == user_id and data['active']:
                return code
        return None
    
    def validate_referral_code(self, code: str) -> Dict:
        """
        Validate a referral code.
        
        Returns:
            Dict with validity status and referrer info
        """
        code = code.upper().strip()
        
        if code not in self.referral_codes:
            return {
                'valid': False,
                'reason': 'Invalid referral code'
            }
        
        referrer_data = self.referral_codes[code]
        
        if not referrer_data['active']:
            return {
                'valid': False,
                'reason': 'This referral code has been deactivated'
            }
        
        return {
            'valid': True,
            'referrer_id': referrer_data['user_id'],
            'code': code,
            'uses': referrer_data['uses']
        }
    
    async def process_referral(
        self,
        referrer_id: int,
        referred_id: int,
        referrer_tier: str = 'free',
        referred_tier: str = 'free'
    ) -> Dict:
        """
        Process referral and apply rewards.
        
        Args:
            referrer_id: ID of user who referred
            referred_id: ID of new user
            referrer_tier: Current tier of referrer
            referred_tier: Initial tier of referred user
            
        Returns:
            Dict with reward details
        """
        # Determine reward type
        if referrer_tier == 'free' and referred_tier != 'free':
            reward_type = 'free_to_paid'
        elif referrer_tier != 'free' and referred_tier != 'free':
            reward_type = 'paid_to_paid'
        else:
            reward_type = None
        
        if not reward_type:
            logger.info(f"No referral reward applicable: referrer={referrer_tier}, referred={referred_tier}")
            return {
                'success': False,
                'message': 'Referral does not qualify for rewards'
            }
        
        rewards = self.REFERRAL_REWARDS[reward_type]
        
        # Record referral
        referral_record = {
            'referrer_id': referrer_id,
            'referred_id': referred_id,
            'reward_type': reward_type,
            'referrer_reward_days': rewards['referrer']['tier_extension_days'],
            'referred_discount_percent': rewards['referred']['discount_percent'],
            'created_at': datetime.utcnow(),
            'claimed': False
        }
        
        self.referrals.append(referral_record)
        
        # Update referrer code usage
        code = self.get_referral_code(referrer_id)
        if code and code in self.referral_codes:
            self.referral_codes[code]['uses'] += 1
            
            # Check for bonus thresholds
            total_referrals = self.get_referral_count(referrer_id)
            bonus = self._check_bonus_threshold(total_referrals)
            if bonus:
                referral_record['bonus_days'] = bonus['bonus_days']
        
        logger.info(
            f"Processed referral: referrer={referrer_id}, referred={referred_id}, "
            f"reward_type={reward_type}"
        )
        
        return {
            'success': True,
            'reward_type': reward_type,
            'referrer_reward': {
                'tier_extension_days': rewards['referrer']['tier_extension_days'],
                'tier': rewards['referrer']['tier']
            },
            'referred_reward': {
                'discount_percent': rewards['referred']['discount_percent'],
                'discount_months': rewards['referred']['discount_months']
            },
            'message': f'Referral successful! You both receive rewards.'
        }
    
    def _check_bonus_threshold(self, total_referrals: int) -> Optional[Dict]:
        """Check if referral count triggers a bonus"""
        for threshold, bonus in sorted(self.BONUS_THRESHOLDS.items()):
            if total_referrals >= threshold:
                continue  # Keep checking for higher threshold
            return bonus
        return None
    
    def get_referral_count(self, user_id: int) -> int:
        """Get total number of successful referrals for a user"""
        return sum(1 for r in self.referrals if r['referrer_id'] == user_id)
    
    def get_referral_stats(self, user_id: int) -> Dict:
        """
        Get referral statistics for a user.
        
        Returns:
            Dict with referral counts, pending rewards, etc.
        """
        user_referrals = [r for r in self.referrals if r['referrer_id'] == user_id]
        
        total_referrals = len(user_referrals)
        claimed_referrals = sum(1 for r in user_referrals if r['claimed'])
        pending_referrals = total_referrals - claimed_referrals
        
        # Calculate total days earned
        total_days = sum(r.get('referrer_reward_days', 0) for r in user_referrals)
        bonus_days = sum(r.get('bonus_days', 0) for r in user_referrals)
        
        # Check next bonus threshold
        next_bonus = None
        for threshold, bonus in sorted(self.BONUS_THRESHOLDS.items()):
            if total_referrals < threshold:
                next_bonus = {
                    'threshold': threshold,
                    'current': total_referrals,
                    'needed': threshold - total_referrals,
                    'bonus': bonus
                }
                break
        
        return {
            'total_referrals': total_referrals,
            'claimed_referrals': claimed_referrals,
            'pending_referrals': pending_referrals,
            'total_reward_days': total_days,
            'bonus_days': bonus_days,
            'next_bonus': next_bonus,
            'referral_code': self.get_referral_code(user_id)
        }
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        Get top referrers leaderboard.
        
        Returns:
            List of top referrers with stats
        """
        # Count referrals per user
        referrer_counts: Dict[int, int] = {}
        for r in self.referrals:
            rid = r['referrer_id']
            referrer_counts[rid] = referrer_counts.get(rid, 0) + 1
        
        # Sort by count
        sorted_referrers = sorted(
            referrer_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        leaderboard = []
        for i, (user_id, count) in enumerate(sorted_referrers[:limit], 1):
            # Get tier info if available
            tier = 'Unknown'
            days_earned = sum(
                r.get('referrer_reward_days', 0)
                for r in self.referrals
                if r['referrer_id'] == user_id
            )
            
            leaderboard.append({
                'rank': i,
                'user_id': user_id,
                'referral_count': count,
                'total_reward_days': days_earned,
                'tier': tier
            })
        
        return leaderboard
    
    async def claim_referral_reward(self, referral_id: int, user_id: int) -> Dict:
        """
        Claim pending referral reward.
        
        Args:
            referral_id: ID of referral to claim
            user_id: User claiming the reward
            
        Returns:
            Dict with claim result
        """
        # Find referral
        referral = None
        for r in self.referrals:
            if r['referred_id'] == referral_id and r['referrer_id'] == user_id:
                referral = r
                break
        
        if not referral:
            return {
                'success': False,
                'message': 'Referral not found'
            }
        
        if referral['claimed']:
            return {
                'success': False,
                'message': 'Reward already claimed'
            }
        
        # Mark as claimed
        referral['claimed'] = True
        referral['claimed_at'] = datetime.utcnow()
        
        logger.info(f"Referral reward claimed: referral_id={referral_id}, user_id={user_id}")
        
        return {
            'success': True,
            'reward_days': referral.get('referrer_reward_days', 0),
            'bonus_days': referral.get('bonus_days', 0),
            'message': f'Congratulations! You received {referral.get("referrer_reward_days", 0)} days of Pro tier!'
        }


# Global instance
referral_service = ReferralService()
