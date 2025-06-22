import time
import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf

class SignDetector:
    def __init__(self, model_path=None):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Load model
        self.model = tf.keras.models.load_model(model_path or 'sign_language_model.keras')
        
        self.class_labels = [
            'A', 'B', 'C', 'D', 'DELETE', 'E', 'F', 'G', 'H', 'I',
            'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
            'Space', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'CLEAR', 'SPEAK'
        ]
        
        # State tracking
        self.last_sign_time = 0
        self.current_sign = None
        self.confirmed_sign = None
        self.cooldown = 2.0  # seconds between signs
        self.sign_hold = 0.5  # seconds to hold sign before confirmation

    def process_frame(self, frame):
        try:
            current_time = time.time()
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            # Visual feedback variables
            sign_confirmed = False
            show_cooldown = False
            
            # Check if in cooldown period
            if current_time - self.last_sign_time < self.cooldown:
                show_cooldown = True
            else:
                # Process hand landmarks
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        landmarks = []
                        for lm in hand_landmarks.landmark:
                            landmarks.extend([lm.x, lm.y, lm.z])
                        mp.solutions.drawing_utils.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        if len(landmarks) >= 63:
                            landmarks = landmarks[:63]
                            prediction = self.model.predict(np.array([landmarks]), verbose=0)
                            predicted_class = np.argmax(prediction)
                            confidence = np.max(prediction)
                            
                            if confidence > 0.85:
                                detected_sign = self.class_labels[predicted_class]
                                
                                # Handle special signs
                                if detected_sign == 'Space':
                                    detected_sign = ' '
                                
                                # New sign detection
                                if self.current_sign != detected_sign:
                                    self.current_sign = detected_sign
                                    self.sign_start_time = current_time
                                # Sign held long enough
                                elif current_time - self.sign_start_time >= self.sign_hold:
                                    if not self.confirmed_sign:
                                        self.confirmed_sign = detected_sign
                                        self.last_sign_time = current_time
                                        sign_confirmed = True
            
            # Visual feedback
            if sign_confirmed:
                cv2.putText(frame, f"Confirmed: {self.confirmed_sign}", 
                           (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            elif show_cooldown:
                remaining = self.cooldown - (current_time - self.last_sign_time)
                cv2.putText(frame, f"Cooldown: {remaining:.1f}s", 
                           (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Reset confirmed sign after showing it
            if sign_confirmed:
                return_sign = self.confirmed_sign
                self.confirmed_sign = None
            else:
                return_sign = None
            
            ret, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes(), return_sign
            
        except Exception as e:
            print(f"Error processing frame: {str(e)}")
            return None, None