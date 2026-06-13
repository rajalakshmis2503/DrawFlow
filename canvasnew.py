import cv2 as cv
import numpy as np
import easyocr

class Canvas():
    def __init__(self, columns, rows):
        self.colors = {
                "BLUE": (255,0,0),
                "GREEN": (0,255,0),
                "RED": (0,0,255),
                }
        self.color = "BLUE" 
        self.lines = {} 
        self.currLine = None  
        self.grid = [[None] * columns for row in range(rows)] # pointers to the functions

    def draw_dashboard(self, frame, gesture = "HOVER", data = {}):
        frame_height, frame_width, _ = frame.shape

        # find index finger
        idx_finger = (-1, -1, -1) 
        if data.get('idx_finger') != None:
            idx_finger = data['idx_finger']
        _, c, r = idx_finger 

        # add clear_button
        clear_button_width = int(frame_width *.2) 
        clear_button_height = int(frame_height * .15)
        width_border = int(clear_button_width * .05) 
        height_border = int(clear_button_height * .05)

        frame = cv.rectangle(frame, (width_border, height_border), 
                            (clear_button_width - width_border,clear_button_height - height_border),
                            (122, 122, 122), -1)
        text = "CLEAR ALL"
        font = cv.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 1
        font_color = (255, 255, 255)
        line_type = cv.LINE_AA

        # Calculate text size
        text_size = cv.getTextSize(text, font, font_scale, font_thickness)[0]

        # Calculate text position
        text_x = int((clear_button_width - text_size[0]) / 2)  # Center horizontally
        text_y = int(clear_button_height * 0.5) + int(text_size[1] / 2)  # Center vertically

        # Put text on the frame
        cv.putText(frame, text, (text_x, text_y), font, font_scale, font_color, font_thickness, line_type)
        
        # clear output!
        if (width_border <= c <= clear_button_width - width_border and 
            height_border <= r <= clear_button_height):
            self.lines = {}
            self.grid = [[None] * len(self.grid[0]) for row in range(len(self.grid))]

        current_width  = frame_width - clear_button_width
        button_width = int(current_width / len(self.colors))
        button_height = clear_button_height
        width_border = int(button_width * .05)
        height_border = int(button_height *.05)

        x_dist = clear_button_width
        
        for name_color, color_arr in self.colors.items():
            frame = cv.rectangle(frame, 
                                (x_dist + width_border, height_border), 
                                (x_dist + button_width - width_border, button_height - height_border),
                                color_arr, 
                                -1)
            
            if gesture == "DRAW" and \
                (height_border <= r <= button_height - height_border and \
                x_dist + width_border <= c <= x_dist + button_width - width_border):
                self.end_line()
                self.color = name_color
            # highlight the color we've selected
            if name_color == self.color:
                frame = cv.rectangle(frame, 
                                    (x_dist + width_border, height_border), 
                                    (x_dist + button_width - width_border, button_height - height_border),
                                    (255, 255, 255),
                                    5)
            x_dist += button_width

        text = f"Mode: {gesture}"
        font = cv.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0  # Adjust this value to change the size of the text
        font_thickness = 3
        font_color = self.colors[self.color]
        line_type = cv.LINE_AA

        # Calculate text size
        text_size = cv.getTextSize(text, font, font_scale, font_thickness)[0]

        # Calculate text position
        text_x = width_border
        text_y = int(button_height * 2) + text_size[1]

        # Put text on the frame
        cv.putText(frame, text, (text_x, text_y), font, font_scale, font_color, font_thickness, line_type)
        
        # draw the ring if we're in the eraser mode
        if gesture == "ERASE":
            # get middle finger and radius of circle to draw
            distance = data['radius']
            _, mid_r, mid_c = data['mid_fing_tip']

            # put circle on the map, and add some opacity
            img = frame.copy()
            cv.circle(img, (mid_r, mid_c), int(distance*.5), (0,255,255), -1)
            alpha = 0.4
            frame = cv.addWeighted(frame, alpha, img, 1-alpha, 0)
        elif gesture == "TRANSLATE":
            distance = data['radius']
            _, c, r = data['idx_finger']

            # put circle on the map, and add some opacity
            img = frame.copy()
            cv.circle(img, (c, r), int(distance*.5), (255,255,255), -1)
            alpha = 0.4
            frame = cv.addWeighted(frame, alpha, img, 1-alpha, 0)
        return frame

    def push_point(self, point):
        
        # check for active line
        if len(self.lines) == 0 or self.currLine == None or self.lines[self.currLine.get_origin()].active == False:
            line = Line(self.color, point)
            self.currLine = line
            self.lines[point] = self.currLine
        else:
        # existing line
            self.currLine.points.append(point)

        row, col = point 
        
        self.grid[row][col] = self.currLine.get_origin()
        
    def end_line(self):
        
        if self.currLine != None and len(self.lines) > 0:
            self.lines[self.currLine.get_origin()].active = False

    def draw_lines(self, frame):
        
        for line in self.lines.values():
            for i, point in enumerate(line.points):
                if i == 0:
                    continue
                prev_y, prev_x = line.points[i-1]
                y, x = point
                cv.line(
                        frame, 
                        (prev_x, prev_y), 
                        (x, y), 
                        self.colors[line.color],
                        5
                        )
        return frame

    def translate_mode(self, position, radius, shift):
       
        r, c = position

        uniqueLines = set()

        for dr in range(
                max(0, r - radius), 
                min(r + radius, len(self.grid) - 1)):
            for dc in range(
                    max(0, c - radius), 
                    min(c + radius, len(self.grid[0]) - 1)):
                # if we have some point in the line
                if self.grid[dr][dc] != None:
                    # get the origin point of this line
                    uniqueLines.add(self.grid[dr][dc])
        

        for og_point in uniqueLines:
            line = self.lines.pop(og_point)
            for r, c in line.points:
                self.grid[r][c] = None

            translation = []
            for r, c in line.points:
                trans_r, trans_c = r + shift[0], c + shift[1]
                if (0 <= trans_r < len(self.grid)) and (0 <= trans_c < len(self.grid[0])):
                    translation.append((trans_r, trans_c))
                else:
                    break
            
            if len(translation) == len(line.points):
                line.points = translation


            for r, c in line.points:
                self.grid[r][c] = line.get_origin() # new points on the grid

            self.lines[line.get_origin()] = line

    def erase_mode(self, position, radius):
        
        dleft, dtop = position

        self.currLine = None
        for dr in range(max(0, dleft - radius), 
                min(dleft + radius, len(self.grid[0]))):
            for dc in range(
                            max(0, dtop - radius), 
                            min(dtop + radius, len(self.grid))):
                if self.grid[dc][dr] != None:
                    key = self.grid[dc][dr]
                    line = self.lines.pop(key)
                    for (r, c) in line.points:
                        self.grid[r][c] = None

    def take_screenshot(self, filename):

        def perform_ocr(image_path):
        # Initialize the OCR reader
            reader = easyocr.Reader(['en'])

        # Read the image
            image = cv.imread(image_path)

        # Perform OCR using easyocr
            result = reader.readtext(image)

        # Extract the text from the result
            text = ' '.join([res[1] for res in result])

            return text

        white_background = np.full((600, 800, 3), (255, 255, 255), dtype=np.uint8)
        canvas_image = self.draw_lines(white_background)

        cv.imwrite(filename, canvas_image)

        text = perform_ocr("drawing.jpg")

        print("OCR Result:")
        print(text)
        cv.waitKey(0)
        
        
        


class Line():
   
    def __init__(self, color, origin):
        self.color = color
        self.points = [origin]
        self.active = True

    def get_origin(self):
        return self.points[0]

    def __repr__(self):
        return f"\tcolor({self.color})\n \
                \tactive({self.active})\n \
                points({self.points[0]})"
def main():
    canvas = Canvas()
    line = Line("BLUE")
    line.points.append((10, 5))
    print(line)


if __name__ == '__main__':
    main()