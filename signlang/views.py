from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators import gzip
from .utils.sign_detector import SignDetector
import threading
import cv2
import time
from .utils.speech import text_to_speech

# Initialize sign detector
detector = SignDetector()
current_sentence = []
sentence_lock = threading.Lock()

@gzip.gzip_page
def video_feed(request):
    def generate():
        cap = cv2.VideoCapture(0)
        while True:
            success, frame = cap.read()
            if not success:
                break
                
            frame_bytes, sign = detector.process_frame(frame)
            
            if sign:  # Only returns a sign when confirmed
                with sentence_lock:
                    if sign == ' ':  # Space
                        current_sentence.append(' ')
                    elif sign == 'DELETE':
                        if current_sentence:
                            current_sentence.pop()
                    elif sign == 'CLEAR':
                        current_sentence.clear()
                    elif sign == 'SPEAK':
                        if current_sentence:
                            sentence = ''.join(current_sentence)
                            text_to_speech(sentence)
                    elif sign not in ['DELETE', 'SPEAK', 'CLEAR']:
                        current_sentence.append(sign)
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    return StreamingHttpResponse(generate(), content_type='multipart/x-mixed-replace; boundary=frame')

def index(request):
    return render(request, 'signlang/index.html')

def get_sentence(request):
    with sentence_lock:
        return JsonResponse({
            'sentence': ''.join(current_sentence),
            'status': 'success'
        })

def speak_sentence(request):
    with sentence_lock:
        if current_sentence:
            sentence = ''.join(current_sentence)
            text_to_speech(sentence)  # Check if this function executes
            return JsonResponse({'status': 'spoken'})
        return JsonResponse({'status': 'empty'})

def clear_sentence(request):
    with sentence_lock:
        current_sentence.clear()
        print('Saboj Vai is checking if this function executes')
        return JsonResponse({'status': 'cleared'})  # Ensure this matches frontend

def sign_status(request):
    current_time = time.time()
    in_cooldown = current_time - detector.last_sign_time < detector.cooldown
    return JsonResponse({
        'confirmed_sign': detector.confirmed_sign,
        'in_cooldown': in_cooldown,
        'cooldown_remaining': max(0, detector.cooldown - (current_time - detector.last_sign_time))
    })