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
          
            return '3/day'
        else: 
            return '1/day'