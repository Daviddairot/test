import base64
import json
import os
import io
import time
from django.http import HttpResponse, JsonResponse
from PIL import Image
from pdf2docx import Converter
from moviepy.editor import VideoFileClip
import qrcode
from rembg import remove
# from rembg import remove
import io
from moviepy.editor import VideoFileClip
import speech_recognition as sr
from pdf2docx import Converter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import tempfile
import shutil
import logging
from pytube import YouTube
# from .serializers import DownloadYouTubeVideoSerializer
import yt_dlp



# 1. PDF to Word Converter
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['POST'])
def pdf_to_word(request):
    if request.method == 'POST':
        try:
            # Parse the JSON request
            data = json.loads(request.body)
            file_name = data['file_name']
            file_data = data['file_data']  # Base64 encoded file content

            # Decode base64 file data
            decoded_file = base64.b64decode(file_data)

            # Write the decoded file to a temporary location
            temp_pdf_path = f'media/temp_{file_name}'
            with open(temp_pdf_path, 'wb') as f:
                f.write(decoded_file)

            # Convert the PDF to Word using pdf2docx
            word_file_path = 'media/converted.docx'
            cv = Converter(temp_pdf_path)
            cv.convert(word_file_path)
            cv.close()

            # Remove the temporary PDF file after conversion
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

            # Return the Word file as a download
            with open(word_file_path, 'rb') as word_file:
                response = HttpResponse(word_file.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                response['Content-Disposition'] = f'attachment; filename="converted_{file_name}.docx"'
                return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=400)


# 2. Video to Audio Converter
@api_view(['POST'])
def video_to_audio(request):
    if 'video_file' in request.FILES:
        try:
            video_file = request.FILES['video_file']
            # Save the video to a temporary file
            temp_video_path = "media/temp_video.mp4"
            with open(temp_video_path, 'wb') as f:
                f.write(video_file.read())

            # Convert video to audio
            video = VideoFileClip(temp_video_path)
            audio_path = "media/converted_audio.mp3"
            video.audio.write_audiofile(audio_path)

            # Return audio file as download
            with open(audio_path, 'rb') as audio_file:
                response = HttpResponse(audio_file.read(), content_type='audio/mp3')
                response['Content-Disposition'] = 'attachment; filename="converted_audio.mp3"'
                return response

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    return Response({"error": "Invalid request or missing file."}, status=400)



# 3. Image Resizer
@api_view(['POST'])
def image_resize(request):
    try:
        # Check if file and dimensions are provided
        if 'image_file' not in request.FILES or 'width' not in request.data or 'height' not in request.data:
            return Response({"error": "Invalid request or missing file/parameters."}, status=400)

        image_file = request.FILES['image_file']
        width = int(request.data['width'])
        height = int(request.data['height'])

        # Open the image and resize
        img = Image.open(image_file)
        img = img.resize((width, height))
        
        # Save the image to a BytesIO object instead of disk
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)  # Go to the beginning of the file

        # Send the resized image as a response
        return HttpResponse(img_io, content_type='image/jpeg', headers={
            'Content-Disposition': 'attachment; filename="resized_image.jpg"'
        })

    except Exception as e:
        # Log the error and return a 500 response
        print(f"Error resizing image: {str(e)}")
        return Response({"error": str(e)}, status=500)
    return Response({"error": "Invalid request or missing file/parameters."}, status=status.HTTP_400_BAD_REQUEST)



# 4. Image Background Removal
@api_view(['POST'])
def remove_background(request):
    if 'image_file' in request.FILES:
        try:
            image_file = request.FILES['image_file']

            # Convert the InMemoryUploadedFile to bytes
            image_bytes = image_file.read()

            # Remove background using rembg
            output = remove(image_bytes)

            # Return the image with the background removed
            return HttpResponse(output, content_type='image/png')

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"error": "Invalid request or missing file."}, status=status.HTTP_400_BAD_REQUEST)




# 5. QR Code Generator
@api_view(['POST'])
def generate_qr_code(request):
    data = request.data.get('data')
    if data:
        qr = qrcode.make(data)
        qr_path = 'media/qr_code.png'
        qr.save(qr_path)

        # Return QR code as download
        with open(qr_path, 'rb') as qr_file:
            response = HttpResponse(qr_file.read(), content_type='image/png')
            response['Content-Disposition'] = 'attachment; filename="qr_code.png"'
            return response
    return Response({"error": "Invalid request or missing data."}, status=status.HTTP_400_BAD_REQUEST)




# Set up logging
logger = logging.getLogger(__name__)

# Function to format timestamp into SRT format
def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


logger = logging.getLogger(__name__)

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

@api_view(['POST'])
def video_transcriber(request):
    if 'video_file' in request.FILES:
        try:
            video_file = request.FILES['video_file']

            # Step 1: Save the uploaded video file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video_file:
                for chunk in video_file.chunks():
                    temp_video_file.write(chunk)
                temp_video_path = temp_video_file.name  # Store the temp file path

            # Ensure the temp file is properly closed
            temp_video_file.close()

            # Move the file to a stable location
            stable_video_path = 'media/temp_video.mp4'
            shutil.move(temp_video_path, stable_video_path)

            # Step 2: Extract Audio from the Video
            video = VideoFileClip(stable_video_path)
            audio_path = "media/temp_audio.wav"
            video.audio.write_audiofile(audio_path)

            # Step 3: Use Speech Recognition to transcribe the audio in chunks
            recognizer = sr.Recognizer()
            audio_file = sr.AudioFile(audio_path)

            srt_content = ""
            chunk_duration = 10  # Split the audio into 10-second chunks
            total_duration = video.duration  # Total video duration in seconds
            current_time = 0

            with audio_file as source:
                while current_time < total_duration:
                    end_time = min(current_time + chunk_duration, total_duration)
                    chunk = recognizer.record(source, duration=chunk_duration)

                    try:
                        text = recognizer.recognize_google(chunk, show_all=True)

                        if text and isinstance(text, dict) and 'alternative' in text:
                            segments = text['alternative']
                            for idx, segment in enumerate(segments):
                                transcript = segment.get('transcript', '')
                                if transcript:
                                    srt_content += f"{idx + 1}\n"
                                    srt_content += f"{format_timestamp(current_time)} --> {format_timestamp(end_time)}\n"
                                    srt_content += transcript + "\n\n"

                    except sr.UnknownValueError:
                        srt_content += f"{format_timestamp(current_time)} --> {format_timestamp(end_time)}\n"
                        srt_content += "Could not understand audio.\n\n"
                    except sr.RequestError as e:
                        srt_content += f"{format_timestamp(current_time)} --> {format_timestamp(end_time)}\n"
                        srt_content += f"Could not request results from service; {e}\n\n"

                    current_time = end_time

            # Step 4: Save the transcription as an SRT file
            srt_path = "media/transcription.srt"
            with open(srt_path, 'w') as srt_file:
                srt_file.write(srt_content)

            # time.sleep(2)
            # # Clean up temporary files
            # if os.path.exists(audio_path):
            #     os.remove(audio_path)
            # if os.path.exists(stable_video_path):
            #     os.remove(stable_video_path)

            with open(srt_path, 'rb') as srt_file:
                response = HttpResponse(srt_file.read(), content_type='text/plain')
                response['Content-Disposition'] = 'attachment; filename= "transcription.srt"'
                return response

        except Exception as e:
            logger.error(f"Error during video transcription: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'error': 'Invalid request. POST method and video_file required.'}, status=status.HTTP_400_BAD_REQUEST)





# import yt_dlp as youtube_dl
# import os


# @api_view(['POST'])
# def download_youtube_video(request):
#     video_url = request.data.get('video_url')
    
#     if not video_url:
#         return Response({'error': 'video_url is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
#     try:
#         # Set options for yt-dlp
#         ydl_opts = {
#             'format': 'best',
#             'outtmpl': 'media/downloaded_video.mp4',
#             'noplaylist': True,
#             'no_resume': True,  # Disable resuming of partial downloads
#             'quiet': True,
#         }

#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.download([video_url])

#         video_path = 'media/downloaded_video.mp4'
        
#         if not os.path.exists(video_path):
#             return Response({'error': 'Video file not found.'}, status=status.HTTP_404_NOT_FOUND)

#         # Return the video file as a response
#         with open(video_path, 'rb') as video_file:
#             response = HttpResponse(video_file.read(), content_type='video/mp4')
#             response['Content-Disposition'] = 'attachment; filename="downloaded_video.mp4"'
#             return response

#     except yt_dlp.DownloadError as e:
#         return Response({'error': f'Download error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     except yt_dlp.utils.ExtractorError as e:
#         return Response({'error': f'Extractor error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     except yt_dlp.utils.PostProcessingError as e:
#         return Response({'error': f'Post processing error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#     except Exception as e:
#         return Response({'error': f'An unexpected error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
