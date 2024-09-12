from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns =[
    path('pdf-to-word/', views.pdf_to_word, name='pdf_to_word'),
    path('video-to-audio/', views.video_to_audio, name='video_to_audio'),
    path('image-resize/', views.image_resize, name='image_resize'),
    path('remove-background/', views.remove_background, name='remove_background'),
    path('generate-qr-code/', views.generate_qr_code, name='generate_qr_code'),
    path('video-transcriber/', views.video_transcriber, name='video_transcriber'),
    # path('download-youtube/', views.download_youtube_video, name='download_youtube_video'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
