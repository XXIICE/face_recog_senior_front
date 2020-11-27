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
class_timeend = None

# Loading models
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe(
    "data/models/deploy.prototxt.txt",
    "data/models/res10_300x300_ssd_iter_140000.caffemodel")
print("[INFO] model loaded.")

# Finding camera
camera_index = input("Specify camera driver index (starting from 0): ")
cam = cv2.VideoCapture(int(camera_index))


async def capture_frame():
    frameNo = 0

    while cam.isOpened():
        print(f"Enter {capture_frame=} function at {datetime.now()}.")
        hasNextFrame, frame = cam.read()
        if(hasNextFrame):
            # cv2.imshow('Frame', frame)
            hasFace, confidences = detect_face(frame)
        else:
            break

        if hasFace:
            print("[INFO] Face detected with frame number:", frameNo)
            print(confidences)
            success, encoded_image = cv2.imencode('.jpg', frame)
            await identify_face(encoded_image)
            # cv2.imwrite("data/images/section_" + sec_period + "/" + str(frameNo) + ".jpg", frame)
            # identify_face(open("data/images/section_" + sec_period + "/" + str(frameNo) + ".jpg", 'rb').read())
            frameNo += 1

        await trio.sleep(0)
        print(f"Exit at {datetime.now()}")

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
    print(f"Enter {identify_face=} function at {datetime.now()}.")
    url = "https://frrsca-backend.khanysorn.me/api/v1/class/attendance/check_student"
    # url = "http://0.0.0.0:8001/api/v1/class/attendance/check_student"
    # url = "http://0.0.0.0:8002/api/v1/face/recognition/identify"
    course_code = "INT450"
    section_number = "1"
    # timestamp = "2020-01-30 13:30:00"
    timestamp = datetime.now().strftime("%Y-%m-%d% %H:%M:%S")
    path = url + "/" + room + "/" + course_code + "/" + section_number + "/" + timestamp

    payload = {
        'image': ('image.jpg', image, 'image/jpeg')
    }

    # response = requests.post(url, files=payload)
    response = requests.post(path, files=payload)

    if response.ok:
        result = response.json()

        if len(result) > 0:
            for student in result:
                student_id = student['student_id']
                # student_id = student['person_id']
                print(student_id)

                if student_id not in student_list:
                    student_list[student_id] = student
            
            print(json.dumps(student_list, indent=2))
    # print(response.text.encode('utf8'))
    await trio.sleep(3)
    print(f"Exit at {datetime.now()}")

async def main():     
    student_list_column = [
        [
            gui.Text("INT402", font='Courier 16')
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

    window = gui.Window(title="Hello CB2301", layout = layout, margins=(200, 100))

    while True:
        event, values = window.read(timeout=1000)

        if event == "EXIT" or event == gui.WIN_CLOSED:
            break
        
        window["-DATETIME-"].update(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        window["-STUDENT LIST-"].update(student_list)

        await trio.sleep(0)

    cam.release()
    cv2.destroyAllWindows()
    window.close()

async def check_present_student():
    pass

async def check_absent_student():
    print("Checking absent students is complete.")
    pass

async def check_timetable():
    '''
        # 1. query course_code, section_number, class_timeend (if time_end > current_time)
        # 2. countdown to class_time_end
        # 3. check_absent_student
        # Redo
    '''
    global course_code
    global section_name
    global class_timeend
    
    # url = "https://frrsca-backend.khanysorn.me/api/v1/class/attendance/timetable/check"
    url = "http://0.0.0.0:8001/api/v1/class/attendance/timetable/check"
    current_datetime = datetime.now().strftime("%Y-%m-%d% %H:%M:%S")
    # print(current_datetime)
    # current_datetime = "2020-11-30 11:59:30"
    path = url + '/' + room + '/' + current_datetime
    response = requests.post(path)
    print(response.json())

    if response.ok and response.json():
        class_result = response.json()
        print(class_result)

        course_code = class_result['course_code']
        section_name = str(class_result['section_name'])
        class_timeend = datetime.strptime(class_result['class_timeend'], '%Y-%m-%dT%H:%M:%S')
    
        # print(course_code)
        # print(section_name)
        # print(class_timeend)

        current_time = datetime.strptime(current_datetime, "%Y-%m-%d %H:%M:%S")
        current_seconds = (current_time.hour * 60 * 60) + (current_time.minute * 60) + (current_time.second)
        print(current_seconds)
    
        # global check_timetable_schedule
        # deadline_seconds = (check_timetable_schedule.hour * 60 * 60) + (check_timetable_schedule.minute * 60) + (check_timetable_schedule.second)
        deadline_seconds = (class_timeend.hour * 60 * 60) + (class_timeend.minute * 60) + (class_timeend.second)
        print(deadline_seconds)

        sleep_seconds = (deadline_seconds - current_seconds) + 1
        print("current - deadline = ", sleep_seconds)

        await trio.sleep(sleep_seconds)
        await check_absent_student()
        await check_timetable()

    else:
        print("End process ...")

async def parent() -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(main)
        nursery.start_soon(capture_frame)
        print(f"{parent=} here.")
    print(f"{parent=} exit.")

if cam.isOpened():
    trio.run(parent)
else:
    print("Unable to open camera.")
