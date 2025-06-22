import time
import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import os
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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, 'sign_language_model.keras')
        self.model = tf.keras.models.load_model(model_path or 'sign_language_model.keras')
        
        # Make sure these labels match your model's output
        self.class_labels = [
            'A', 'B', 'C', 'D', 'DELETE', 'E', 'F', 'G', 'H', 'I',
            'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
            'Space', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
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
            
            # Reset confirmed sign at start of each frame
            self.confirmed_sign = None
            
            # Check if in cooldown period
            if current_time - self.last_sign_time < self.cooldown:
                ret, jpeg = cv2.imencode('.jpg', frame)
                return jpeg.tobytes(), None
            
            # Process hand landmarks if available
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Extract landmarks
                    landmarks = []
                    for lm in hand_landmarks.landmark:
                        landmarks.extend([lm.x, lm.y, lm.z])
                    
                    # Draw landmarks
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                    if len(landmarks) >= 63:
                        landmarks = landmarks[:63]
                        prediction = self.model.predict(np.array([landmarks]), verbose=0)
                        predicted_class = np.argmax(prediction)
                        confidence = np.max(prediction)
                        
                        if confidence > 0.85:
                            detected_sign = self.class_labels[predicted_class]
                            
                            # Handle space sign
                            if detected_sign == 'Space':
                                detected_sign = ' '
                            
                            # New sign detection
                            if self.current_sign != detected_sign:
                                self.current_sign = detected_sign
                                self.sign_start_time = current_time
                            # Sign held long enough
                            elif current_time - self.sign_start_time >= self.sign_hold:
                                self.confirmed_sign = detected_sign
                                self.last_sign_time = current_time
                                self.current_sign = None  # Reset for next sign

            # Add visual feedback
            if self.confirmed_sign:
                cv2.putText(frame, f"Sign: {self.confirmed_sign}", 
                           (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            elif current_time - self.last_sign_time < self.cooldown:
                remaining = self.cooldown - (current_time - self.last_sign_time)
                cv2.putText(frame, f"Wait: {remaining:.1f}s", 
                           (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            ret, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes(), self.confirmed_sign
            
        except Exception as e:
            print(f"Error processing frame: {str(e)}")
            return None, None