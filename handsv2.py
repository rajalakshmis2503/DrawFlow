import cv2 as cv
import mediapipe as mp
import numpy as np


class HandDetector():
    

    def __init__(self, background_mode, mode = False, max_hands = 1):
        # setup
        self.max_hands = max_hands
        self.background_mode=background_mode
        self.mode = mode
        # hand drawing stuff
        self.hands = mp.solutions.hands.Hands(self.mode, self.max_hands)
        self.drawing = mp.solutions.drawing_utils
        # will be used for translation
        self.prev_position = None

    def detect_hands(self, img, bg, draw=True):
        
        img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB) # I think we need RGB
        self.results = self.hands.process(img_rgb)

        if self.background_mode == "BLACK": 
           img = bg

        if self.results.multi_hand_landmarks and draw:
            for hand_landmark in self.results.multi_hand_landmarks:
                self.drawing.draw_landmarks(img, hand_landmark,
                        mp.solutions.hands.HAND_CONNECTIONS)
        return img


    def detect_landmarks(self, shape: tuple):
        
        landmarks = []
        if self.results.multi_hand_landmarks:
            my_hand = self.results.multi_hand_landmarks[0] # should only be one
            for idx, landmark in enumerate(my_hand.landmark):
                height, width, _ = shape
                x, y = int(landmark.x * width), int(landmark.y * height)
                landmarks.append([idx, x, y])

        return landmarks
    
    def detect_gesture(self, landmarks, threshhold=0.70, debug=False):
       
        _, r, c = landmarks[5]

        vectorize = lambda u, v: [v[i] - u[i] for i in range(len(v))]

        vector_magnitude = lambda vector: sum(dim**2 for dim in vector)**0.5

        cos_angle = lambda u, v: np.dot(u, v) / (vector_magnitude(u) * vector_magnitude(v))

        # Calculate palm vectors
        palm_index_vector = vectorize(landmarks[0], landmarks[5])
        palm_mid_vector = vectorize(landmarks[0], landmarks[9])
        palm_ring_vector = vectorize(landmarks[0], landmarks[13])
        palm_pinky_vector = vectorize(landmarks[0], landmarks[17])

        # Calculate finger vectors
        index_vector = vectorize(landmarks[6], landmarks[8])
        middle_vector = vectorize(landmarks[10], landmarks[12])
        ring_vector = vectorize(landmarks[14], landmarks[16])
        pinky_vector = vectorize(landmarks[18], landmarks[20])

        # Define gesture conditions
        if debug:
            return cos_angle(index_vector, palm_index_vector)

        # Index finger pointing out, other fingers tucked
        if (cos_angle(palm_index_vector, index_vector) > threshhold and
                cos_angle(index_vector, middle_vector) < 0 and
                cos_angle(index_vector, ring_vector) < 0 and
                cos_angle(index_vector, pinky_vector) < 0):
            return "DRAW"

        # Index and middle finger pointing out, other fingers tucked
        if (cos_angle(palm_index_vector, index_vector) > threshhold and
                cos_angle(palm_mid_vector, middle_vector) > threshhold and
                cos_angle(index_vector, ring_vector) < 0 and
                cos_angle(index_vector, pinky_vector) < 0):
            return "HOVER"

        # Index, middle, and ring finger pointing out, pinky finger tucked
        if (cos_angle(palm_index_vector, index_vector) > threshhold and
                cos_angle(index_vector, middle_vector) > 0.90 and
                cos_angle(index_vector, ring_vector) > 0.90 and
                cos_angle(palm_pinky_vector, pinky_vector) < 0):
            return "ERASE"

        # Index and pinky finger pointing out, other fingers tucked
        if (cos_angle(palm_index_vector, index_vector) > threshhold and
                cos_angle(palm_pinky_vector, pinky_vector) > threshhold and
                cos_angle(index_vector, middle_vector) < 0 and
                cos_angle(index_vector, ring_vector) < 0):
            return "TRANSLATE"

        if (cos_angle(palm_index_vector, index_vector) < threshhold and
            cos_angle(palm_mid_vector, middle_vector) < threshhold and
            cos_angle(palm_ring_vector, ring_vector) < threshhold and
            cos_angle(palm_pinky_vector, pinky_vector) > threshhold):
            return "READ"
       
        return "HOVER"
    
    def determine_gesture(self, frame, background):
        

        frame = self.detect_hands(frame, background)
        landmark_list = self.detect_landmarks(frame.shape)
        gesture = None 

        if len(landmark_list) != 0:
            gesture = self.detect_gesture(landmark_list)
        else:
            # no hand detected
            return {}


        # writing in finger info
        idx_finger = landmark_list[8] # coordinates of tip of index fing
        mid_fing = landmark_list[12]
        pinky_finger = landmark_list[20]

        euclidean_dist = lambda a1, a2: sum([(x-y)**2 for x, y in zip(a1, a2)])**.5

        post = {"gesture": gesture, "idx_fing_tip": idx_finger}
        
        if gesture == "ERASE":
            # add the radius distance
            distance = euclidean_dist(idx_finger[1:], mid_fing[1:])
            post['mid_fing_tip'] = mid_fing
            post['idx_mid_radius'] = distance

        # add additonal info
        elif gesture == "TRANSLATE":
            # find the midpoint
            distance = euclidean_dist(idx_finger[1:], pinky_finger[1:])
            post['idx_pinky_radius'] = distance

            _, c, r = idx_finger
            # call function with previous point
            if self.prev_position == None:
                self.prev_position = (r, c)
            
            # calculate and store the shift
            shift = (r - self.prev_position[0], c - self.prev_position[1])
            post['shift'] = shift

 
        # update previous position position with current point
        _, c, r = idx_finger
        self.prev_position = (r, c)

        return post
    
def determine_gesture(self, frame, background): # type: ignore
    

    frame = self.detect_hands(frame, background)
    landmark_list = self.detect_landmarks(frame.shape)
    gesture_info = {}
    
    if len(landmark_list) != 0:
        gesture_info = self.detect_gesture(landmark_list)
    else:
        return {}

    # Update the gesture_info dictionary with the index finger tip coordinates
    if gesture_info.get('gesture') == "TRANSLATE":
        idx_finger = landmark_list[8]  # Coordinates of tip of index finger
        gesture_info['idx_fing_tip'] = idx_finger

    # Update previous position with current point
    _, c, r = idx_finger
    self.prev_position = (r, c)

    return gesture_info



def main():

    cap = cv.VideoCapture(0)
    detector = HandDetector()

    while True:
        _, img = cap.read()
        img = cv.flip(img, 1)
        img = detector.detect_hands(img)

        landmark_list = detector.detect_landmarks(img.shape)
        if len(landmark_list) != 0:
            val = detector.detect_gesture(landmark_list, threshhold=0.9,)
            cv.putText(img, f"Mode: {val}", (50, 50),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv.LINE_AA)

        cv.imshow('Camera', img)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()

