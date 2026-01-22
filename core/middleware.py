# middleware.py
from core.tenancy import set_current_tenant, get_current_tenant


class TenantMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_tenant(None)

        user = getattr(request, 'user', None)

        # 🔍 DEBUG - Print to console
        print("\n" + "="*60)
        print("🔍 TENANT MIDDLEWARE DEBUG")
        print(f"1. User: {user}")
        print(f"2. Is authenticated? {user.is_authenticated if user else False}")
        print(f"3. Has tenant attribute? {hasattr(user, 'tenant') if user else False}")
        print(f"4. user.tenant = {user.tenant if (user and hasattr(user, 'tenant')) else 'N/A'}")
        
        if user and user.is_authenticated and user.tenant:
            set_current_tenant(user.tenant)
            print(f"5. ✅ TENANT SET TO: {user.tenant.name}")
        else:
            print(f"5. ❌ TENANT NOT SET - Reason:")
            if not user:
                print(f"   → user is None")
            elif not user.is_authenticated:
                print(f"   → user not authenticated (not logged in)")
            elif not user.tenant:
                print(f"   → user.tenant is None (USER HAS NO TENANT!)")
        
        print(f"6. get_current_tenant() = {get_current_tenant()}")
        print("="*60 + "\n")

        response = self.get_response(request)
        set_current_tenant(None)
        return response