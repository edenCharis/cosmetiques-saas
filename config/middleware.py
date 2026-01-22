from core.tenancy import set_current_tenant


class TenantMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_tenant(None)

        user = getattr(request, 'user', None)

        if user and user.is_authenticated and user.tenant:
            set_current_tenant(user.tenant)

        response = self.get_response(request)
        set_current_tenant(None)
        return response