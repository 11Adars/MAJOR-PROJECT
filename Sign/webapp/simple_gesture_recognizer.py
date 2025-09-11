"""
Simple gesture recognition without complex training
Uses basic pattern matching and mock predictions for testing
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

class SimpleGestureRecognizer:
    """Simple gesture recognizer for testing"""
    
    def __init__(self):
        self.gestures = ["block_mad", "hello", "thank_you"]
        self.current_gesture = None
        self.confidence = 0.0
        
        # Create mapping
        self.mapping = {gesture: idx for idx, gesture in enumerate(self.gestures)}
        
        # Save mapping file
        with open("simple_custom_mapping.json", 'w') as f:
            json.dump(self.mapping, f, indent=2)
        
        print(f"✅ Simple recognizer initialized with gestures: {self.gestures}")
    
    def predict_gesture(self, landmarks_data):
        """Simple prediction based on hand position patterns"""
        try:
            if not landmarks_data:
                return "no_action", 0.95
            
            # Simple pattern recognition
            hand_positions = []
            for frame_data in landmarks_data:
                frame_df = pd.DataFrame(frame_data)
                if not frame_df.empty:
                    right_hand = frame_df[frame_df['type'] == 'right_hand'][['x', 'y']].values
                    left_hand = frame_df[frame_df['type'] == 'left_hand'][['x', 'y']].values
                    
                    if len(right_hand) > 0:
                        hand_positions.append(np.mean(right_hand, axis=0))
            
            if len(hand_positions) < 3:
                return "no_action", 0.95
            
            # Simple pattern analysis
            positions = np.array(hand_positions)
            
            # Calculate movement patterns
            y_movement = np.ptp(positions[:, 1])  # Y-axis range
            x_movement = np.ptp(positions[:, 0])  # X-axis range
            
            # Simple gesture classification
            if y_movement > 0.15:  # Vertical movement
                if np.mean(positions[:, 1]) < 0.5:  # Upper area
                    return "hello", 0.85
                else:
                    return "thank_you", 0.80
            elif x_movement > 0.2:  # Horizontal movement
                return "block_mad", 0.75
            else:
                return "no_action", 0.90
                
        except Exception as e:
            print(f"Prediction error: {e}")
            return "no_action", 0.50

def test_simple_recognizer():
    """Test the simple recognizer"""
    recognizer = SimpleGestureRecognizer()
    
    # Create test data
    test_landmarks = []
    for i in range(10):
        frame_data = [
            {'type': 'right_hand', 'x': 0.5 + i*0.02, 'y': 0.3 + i*0.01, 'z': 0},
            {'type': 'left_hand', 'x': 0.3, 'y': 0.4, 'z': 0}
        ]
        test_landmarks.append(frame_data)
    
    gesture, confidence = recognizer.predict_gesture(test_landmarks)
    print(f"Test prediction: {gesture} (confidence: {confidence:.3f})")
    
    return True

if __name__ == "__main__":
    test_simple_recognizer()
