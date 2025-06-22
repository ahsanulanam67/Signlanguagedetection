from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('get_sentence/', views.get_sentence, name='get_sentence'),
    path('speak_sentence/', views.speak_sentence, name='speak_sentence'),
    path('clear_sentence/', views.clear_sentence, name='clear_sentence'),
    path('sign_status/', views.sign_status, name='sign_status'),  # Add this line
]