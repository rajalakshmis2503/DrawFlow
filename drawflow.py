import numpy as np
import cv2 as cv
import mediapipe as mp
from handsv2 import HandDetector
from canvasnew import Canvas
# from handwriting_recognition import handwriting_recognition

def main():
    cap = cv.VideoCapture(0)
    
    # width and height for 2-D grid
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH) + 0.5)
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT) + 0.5)

    # set the default background mode (CAM/BLACK)
    background_mode = 'CAM'

    # initialize the canvas element and hand-detector program
    canvas = Canvas(800, 600)
    detector = HandDetector(background_mode)
    
    while True:
        # Reading the frame from the camera
        ret, frame = cap.read()
        frame = cv.flip(frame, 1)
        
        data = {}

        if background_mode == 'BLACK':
            black_frame = np.zeros((height, width, 3), dtype="uint8")  # Create a black frame
            request = detector.determine_gesture(frame, black_frame)
            frame = black_frame
        else:
            request = detector.determine_gesture(frame, frame)

        gesture = request.get('gesture')
        # if we have a gesture, deal with it
        if gesture is not None:
            idx_finger = request['idx_fing_tip'] # coordinates of tip of index fing
            _, c, r = idx_finger
    
            data = {'idx_finger': idx_finger}
            rows, cols, _ = frame.shape

            # check the radius of concern 
            if (0 < c < cols and 0 < r < rows):
                if gesture == "DRAW":
                    canvas.push_point((r, c))
                elif gesture == "ERASE":
                    # stop current line
                    canvas.end_line()

                    radius = request['idx_mid_radius']

                    _, mid_r, mid_c = request['mid_fing_tip']
                    canvas.erase_mode((mid_r, mid_c), int(radius*0.5))

                    # add features for the drawing phase
                    data['mid_fing_tip'] = request['mid_fing_tip']
                    data['radius'] = radius

                elif gesture == "HOVER":
                    canvas.end_line()

                elif gesture == "READ":
                    canvas.end_line()
                    canvas.take_screenshot("drawing.jpg")

                    gesture = "HOVER"

                elif gesture == "TRANSLATE":
                    canvas.end_line()

                    idx_position = (r,c)

                    shift = request['shift']
                    radius = request['idx_pinky_radius']
                    radius = int(radius*.8)

                    canvas.translate_mode(idx_position, int(radius*.5), shift)

                    data['radius'] = radius
            frame = canvas.draw_dashboard(frame, gesture, data = data)

        else:
            frame = canvas.draw_dashboard(frame)
            canvas.end_line
                
        frame = canvas.draw_lines(frame)
        cv.imshow("DrawFlow", frame)
    
        stroke = cv.waitKey(1) & 0xff  

        if stroke == ord('b'): # press 'b' to switch backgrounds 
            background_mode = "BLACK" if background_mode == 'CAM' else "CAM"
            detector.background_mode = background_mode

        if stroke == ord('q') or stroke == 27: # press 'q' to quit
            break

    cap.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()



