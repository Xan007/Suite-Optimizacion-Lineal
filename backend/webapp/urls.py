from django.urls import path
from . import views
from django.conf import settings

API_PREFIX = 'api/v1'

urlpatterns = [
    path('', views.home, name='home'),

    # Test endpoints
    path(f'{API_PREFIX}/test/', views.test, name='api-test'),
    path(f'{API_PREFIX}/test/health-check/', views.health_check, name='api-health-check'),

    # Analyze endpoints
    path(f'{API_PREFIX}/analyze/', views.analyze_problem, name='api-analyze'),
    path(f'{API_PREFIX}/analyze/validate-model', views.validate_model, name='api-validate-model'),
    path(f'{API_PREFIX}/analyze/get-representations', views.get_representations, name='api-get-representations'),
    path(f'{API_PREFIX}/analyze/analyze-image', views.analyze_problem_from_image, name='api-analyze-image'),
    path(f'{API_PREFIX}/analyze/solve', views.solve_model, name='api-solve'),
]
