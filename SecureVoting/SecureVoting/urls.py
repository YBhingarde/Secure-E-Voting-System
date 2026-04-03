from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from voting_app import views  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vote/', views.candidates_list, name='candidates_list'),
    path('vote/<int:candidate_id>/', views.vote_verify, name='vote_verify'),
    path('vote/thanks/', views.vote_thanks, name='vote_thanks'),
    path('results/', views.live_results, name='live_results'),
]

#photo and media file show
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)