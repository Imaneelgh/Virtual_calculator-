from flask import Flask, render_template, Response
import cv2
import mediapipe as mp
import numpy as np
import math

app = Flask(__name__)

camera = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.5, max_num_hands=1)

class Button:
    def __init__(self, pos, width, height, value):
        self.pos = pos
        self.width = width
        self.height = height
        self.value = value

    def draw(self, img, is_active=False):
        shadow_color = (30, 30, 30)
        highlight_color = (255, 255, 255)
        color = (50, 50, 50) if not is_active else (100, 100, 255)

        cv2.rectangle(img, (self.pos[0] + 5, self.pos[1] + 5),
                      (self.pos[0] + self.width + 5, self.pos[1] + self.height + 5),
                      shadow_color, -1)

        cv2.rectangle(img, self.pos,
                      (self.pos[0] + self.width, self.pos[1] + self.height),
                      color, -1)

        cv2.line(img, self.pos, (self.pos[0] + self.width, self.pos[1]), highlight_color, 2)
        cv2.line(img, self.pos, (self.pos[0], self.pos[1] + self.height), highlight_color, 2)

        cv2.putText(img, self.value, (self.pos[0] + 20, self.pos[1] + 60),
                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)

    def checkClick(self, x, y):
        return self.pos[0] < x < self.pos[0] + self.width and self.pos[1] < y < self.pos[1] + self.height

def findDistance(x, y, a, b):
    return int(((x - a) ** 2 + (y - b) ** 2) ** 0.5)

scientificButtonValues = [
    ["7", "8", "9", "/", "sin", "cos", "tan"],
    ["4", "5",  "6", "*", "log", "ln", "sqrt"],
    ["1", "2", "3", "-", "(", ")", "^"],
    ["0", ".", "=", "+", "C", "<-", "pi"]
]

def createButtons():
    buttonList = []
    values = scientificButtonValues
    for y, row in enumerate(values):
        for x, value in enumerate(row):
            xpos = x * 80 + 50
            ypos = y * 80 + 170
            buttonList.append(Button((xpos, ypos), 80, 80, value))
    return buttonList

myEquation = ""
delayCounter = 0
buttonList = createButtons()

def gen_frames():
    global myEquation, delayCounter, buttonList

    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            frame = cv2.flip(frame, 1)
            imageHeight, imageWidth, _ = frame.shape

            imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(imgRGB)

            display_area_color = (50, 50, 50)
            cv2.rectangle(frame, (50, 50), (imageWidth - 50, 120), display_area_color, -1)
            cv2.line(frame, (50, 50), (imageWidth - 50, 50), (255, 255, 255), 2)
            cv2.line(frame, (50, 50), (50, 120), (255, 255, 255), 2)
            cv2.line(frame, (50, 120), (imageWidth - 50, 120), (30, 30, 30), 2)
            cv2.line(frame, (imageWidth - 50, 50), (imageWidth - 50, 120), (30, 30, 30), 2)

            for button in buttonList:
                button.draw(frame)

            distance = float('inf')
            index_x, index_y = None, None
            middle_x, middle_y = None, None

            if results.multi_hand_landmarks:
                for handLandmarks in results.multi_hand_landmarks:
                    for point in mp_hands.HandLandmark:
                        normalizedLandmark = handLandmarks.landmark[point]
                        pixelCoordinatesLandmark = mp_drawing._normalized_to_pixel_coordinates(
                            normalizedLandmark.x, normalizedLandmark.y, imageWidth, imageHeight
                        )

                        if point == mp_hands.HandLandmark.INDEX_FINGER_TIP:
                            if pixelCoordinatesLandmark is not None:
                                index_x, index_y = pixelCoordinatesLandmark

                        if point == mp_hands.HandLandmark.MIDDLE_FINGER_TIP:
                            if pixelCoordinatesLandmark is not None:
                                middle_x, middle_y = pixelCoordinatesLandmark
                            break

                if index_x is not None and middle_x is not None:
                    frame = cv2.circle(frame, (index_x, index_y), radius=3, color=(0, 0, 255), thickness=5)
                    distance = findDistance(index_x, index_y, middle_x, middle_y)

                    if distance < 35:
                        for button in buttonList:
                            if button.checkClick(index_x, index_y) and delayCounter == 0:
                                myValue = button.value

                                if myValue == "=":
                                    try:
                                        myEquation = str(eval(myEquation.replace('pi', str(np.pi)).replace('sqrt', 'np.sqrt').replace('log', 'np.log10').replace('ln', 'np.log').replace('^', '**').replace('sin', 'np.sin').replace('cos', 'np.cos').replace('tan', 'np.tan')))
                                    except:
                                        myEquation = "Error"
                                elif myValue == "C":
                                    myEquation = ""
                                elif myValue == "<-":
                                    myEquation = myEquation[:-1]
                                else:
                                    myEquation += myValue

                                delayCounter = 1

            if delayCounter != 0:
                delayCounter += 1
                if delayCounter > 10:
                    delayCounter = 0

            cv2.putText(frame, myEquation, (60, 110), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)