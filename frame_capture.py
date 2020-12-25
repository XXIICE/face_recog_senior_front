import json
import trio
from datetime import datetime
import time

import cv2
import PySimpleGUI as gui
import requests


student_list = {}

# Room is fixed.
room = "CB2312"

# # Required query
course_code = ""
section_name = ""
section_id = ""
class_timeend = None

# Loading models
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe(
    "data/models/deploy.prototxt.txt",
    "data/models/res10_300x300_ssd_iter_140000.caffemodel")
print("[INFO] model loaded.")

# Specifying camera
cam = cv2.VideoCapture(0)


async def capture_frame():
    frameNo = 0

    while cam.isOpened():
        hasNextFrame, frame = cam.read()
        if(hasNextFrame):
            hasFace, confidences = detect_face(frame)
        else:
            break

        if hasFace:
            print("[INFO] Face detected with frame number:", frameNo, confidences)
            success, encoded_image = cv2.imencode('.jpg', frame)
            await identify_face(encoded_image)
            frameNo += 1

        await trio.sleep(0)

def detect_face(image):
    hasFace = False

    # Resize and convert image to blob
    blob = cv2.dnn.blobFromImage(
        cv2.resize(image, (300, 300)),
        1.0,
        (300, 300),
        (104.0, 177.0, 123.0))

    # Pass blob through the network
    # Obtain the detections and predictions
    net.setInput(blob)
    detections = net.forward()
    confidences = []

    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > 0.8:
            confidences.append(confidence)
            hasFace = True

    return (hasFace, confidences)

async def identify_face(image):
    url = "https://frrsca-backend.khanysorn.me/api/v1/class/attendance/check_student"
    # url = "http://0.0.0.0:8001/api/v1/class/attendance/check_student"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = url + "/" + course_code + "/" + section_name + "/" + section_id + "/" + timestamp

    payload = {
        'image': ('image.jpg', image, 'image/jpeg')
    }

    response = requests.post(path, files=payload)

    if response.ok:
        result = response.json()

        if len(result) > 0:
            for student in result:
                student_id = student['student_id']
                print(student_id)

                if student_id not in student_list:
                    student_list[student_id] = student
        
    await trio.sleep(3)

async def main():     
    student_list_column = [
        [
            gui.Text("Course", font='Courier 16', key = "-COURSECODE-")
        ],
        [
            gui.Text(text = datetime.now().strftime("%Y-%m-%d %H:%M:%S"), key = "-DATETIME-", font='Courier 16')
        ],
        [
            gui.Listbox(
                values=[],
                enable_events=True,
                size=(60, 30),
                key="-STUDENT LIST-",
                font='Courier 20'
            ),
        ]
    ]

    layout = [
        [
            gui.Column(student_list_column)
        ]
    ]

    window = gui.Window(title="FRRSCA | " + room, layout = layout, margins=(200, 100))

    while True:
        event, values = window.read(timeout=1000)

        if event == "EXIT" or event == gui.WIN_CLOSED:
            break
        
        window["-COURSECODE-"].update(course_code)
        window["-DATETIME-"].update(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        window["-STUDENT LIST-"].update(student_list)

        await trio.sleep(0)

    cam.release()
    cv2.destroyAllWindows()
    window.close()

async def check_absent_student():
    url = "https://frrsca-backend.khanysorn.me/api/v1/class/attendance/check_absent_student"
    # url = "http://0.0.0.0:8001/api/v1/class/attendance/check_absent_student"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = url + "/" + section_id + "/" + timestamp
    
    requests.post(path)

    print("[INFO] Checking absent student completed.")

async def check_timetable():
    '''
        # 1. query course_code, section_number, class_timeend (if time_end > current_time)
        # 2. countdown to class_time_end
        # 3. check_absent_student
        # Redo
    '''
    global course_code
    global section_name
    global section_id
    global class_timeend
    
    url = "https://frrsca-backend.khanysorn.me/api/v1/class/attendance/timetable/check"
    # url = "http://0.0.0.0:8001/api/v1/class/attendance/timetable/check"
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = url + '/' + room + '/' + current_datetime
    
    response = requests.post(path)

    if response.ok and response.json():
        student_list.clear()
        class_result = response.json()
        print(class_result)

        course_code = class_result['course_code']
        section_name = str(class_result['section_name'])
        section_id = str(class_result['section_id'])
        class_timeend = datetime.strptime(class_result['class_timeend'], '%Y-%m-%dT%H:%M:%S')

        current_time = datetime.strptime(current_datetime, "%Y-%m-%d %H:%M:%S")
        current_seconds = (current_time.hour * 60 * 60) + (current_time.minute * 60) + (current_time.second)
    
        deadline_seconds = (class_timeend.hour * 60 * 60) + (class_timeend.minute * 60) + (class_timeend.second)

        sleep_seconds = (deadline_seconds - current_seconds) + 1

        await trio.sleep(sleep_seconds)
        await check_absent_student()
        await check_timetable()

    else:
        print("End process ...")

async def parent() -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(main)
        nursery.start_soon(check_timetable)
        nursery.start_soon(capture_frame)

if cam.isOpened():
    trio.run(parent)
else:
    print("Unable to open camera.")
