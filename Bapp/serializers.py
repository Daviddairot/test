# serializers.py

from rest_framework import serializers

# Serializer for PDF to Word Conversion
class PDFToWordSerializer(serializers.Serializer):
    pdf_file = serializers.FileField()

# Serializer for Video to Audio Conversion
class VideoToAudioSerializer(serializers.Serializer):
    video_file = serializers.FileField()

# Serializer for Image Resize
class ImageResizeSerializer(serializers.Serializer):
    image_file = serializers.ImageField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()

# Serializer for QR Code Generation
class QRCodeSerializer(serializers.Serializer):
    data = serializers.CharField()

# Serializer for Video Transcription
class VideoTranscriberSerializer(serializers.Serializer):
    video_file = serializers.FileField()


# Serializer for Video Transcription
class VideoTranscriberSerializer(serializers.Serializer):
    video_file = serializers.FileField()

# class DownloadYouTubeVideoSerializer(serializers.Serializer):
#     video_url = serializers.CharField()