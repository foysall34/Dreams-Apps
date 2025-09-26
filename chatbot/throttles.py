# your_app/throttles.py

from rest_framework.throttling import UserRateThrottle
from .models import Subscription

class DreamInterpretationRateThrottle(UserRateThrottle):
    scope = 'dream_interpretation'

    def get_rate(self):
        try:
            subscription = Subscription.objects.get(user=self.request.user)
            plan = subscription.plan
        except Subscription.DoesNotExist:
            plan = 'free'

        if plan == 'premium':
            return '3/day'
        elif plan == 'platinum':
            # Assuming "up to three" means per day for simplicity here.
            # You might need more complex logic for consecutive nights.
            return '3/day'
        else: # Free plan
            return '1/day'