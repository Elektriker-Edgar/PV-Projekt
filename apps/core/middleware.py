"""
Custom Middleware für EDGARD PV-Service

Enthält Middleware für Admin-Login-Weiterleitung
"""
from django.shortcuts import redirect
from django.urls import resolve


class AdminLoginRedirectMiddleware:
    """
    Middleware zum Weiterleiten vom Django Admin zum Dashboard nach Login
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Prüfe, ob der Benutzer gerade auf /admin/ zugreift (Admin-Index)
        # und authentifiziert ist
        if (request.path == '/admin/' and
            request.user.is_authenticated and
            request.method == 'GET'):
            # Leite zum Dashboard weiter
            return redirect('/dashboard/')

        return response
