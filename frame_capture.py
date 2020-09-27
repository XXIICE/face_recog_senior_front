import json
import trio
from datetime import datetime

import cv2
import PySimpleGUI as gui
import requests

student_list = {}
# Load models
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe(
    "data/models/deploy.prototxt.txt",
    "data/models/res10_300x300_ssd_iter_140000.caffemodel")
print("[INFO] model loaded.")

cam = cv2.VideoCapture(1)

# def capture_frame(sec_period):
async def capture_frame():
    # cam = cv2.VideoCapture(1)
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

        if cv2.waitKey(30) & 0xff == ord('`'):
            break

        await trio.sleep(0)
        print(f"Exit at {datetime.now()}")

    # cam.release()
    # cv2.destroyAllWindows()


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
    # print(detections)

    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > 0.8:
            # print(confidence * 100)
            confidences.append(confidence)
            hasFace = True

    return (hasFace, confidences)


def draw_face_box():
    pass


async def identify_face(image):
    print(f"Enter {identify_face=} function at {datetime.now()}.")
    url = "https://frrsca-backend.khanysorn.me/api/v1/class/attendance/check_student"
    # url = "http://0.0.0.0:8001/api/v1/class/attendance/check_student"
    # url = "http://0.0.0.0:8002/api/v1/face/recognition/identify"
    room = "CB2301"
    course_code = "INT402"
    section_number = "1"
    timestamp = "2020-09-24 13:30:00"
    # timestamp = datetime.now().strftime("%Y-%m-%d% %H:%M:%S")
    path = url + "/" + room + "/" + course_code + "/" + section_number + "/" + timestamp

    payload = {
        'image': ('image.jpg', image, 'image/jpeg')
    }

    # payload = {
    #     'file': ('image.jpg', image, 'image/jpeg')
    # }

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

    # cam = cv2.VideoCapture(1)
    # frameNo = 0


    while True:
        event, values = window.read(timeout=1000)

        if event == "EXIT" or event == gui.WIN_CLOSED:
            break
        
        window["-DATETIME-"].update(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        window["-STUDENT LIST-"].update(student_list)

        # hasNextFrame, frame = cam.read()
        # if(hasNextFrame):
        #     # cv2.imshow('Frame', frame)
        #     hasFace, confidences = detect_face(frame)
        # else:
        #     break

        # if hasFace:
        #     print("[INFO] Face detected with frame number:", frameNo)
        #     print(confidences)
        #     success, encoded_image = cv2.imencode('.jpg', frame)
        #     await identify_face(encoded_image)
        #     frameNo += 1

        await trio.sleep(0)

    cam.release()
    cv2.destroyAllWindows()
    window.close()

# async def func() -> None:
#     print(f"Enter {func=} function at {datetime.now()}.")
#     await trio.sleep(5)
#     print(f"Exit at {datetime.now()}")

async def parent() -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(main)
        nursery.start_soon(capture_frame)
        # nursery.start_soon(
        #     identify_face, 
        #     open("/Users/iMac/Documents/images/Group/60130500008_Test_2.jpeg", 'rb').read()
        # )
        # nursery.start_soon(
        #     identify_face, 
        #     open("/Users/iMac/Documents/images/Group/60130500138_20.png", 'rb').read()
        # )
        # nursery.start_soon(
        #     identify_face, 
        #     open("/Users/iMac/Documents/images/Group/60130500008_Test_2.jpeg", 'rb').read()
        # )
        print(f"{parent=} here.")
    print(f"{parent=} exit.")

trio.run(parent)


# def is_valid_section(section):
#     sec = section.strip().lower()
#     return sec == 'morning' or sec == 'afternoon'


# async def main():
#     await show_student_list()
#     await identify_face(open("/Users/iMac/Documents/images/Group/60130500008_Test_2.jpeg", 'rb').read())
#     await identify_face(open("/Users/iMac/Documents/images/Group/60130500138_20.png", 'rb').read())
#     await identify_face(open("/Users/iMac/Documents/images/Group/60130500008_Test_2.jpeg", 'rb').read())


# asyncio.run(main())

# if __name__ == "__main__":
#     # Load models
#     print("[INFO] loading model...")
#     net = cv2.dnn.readNetFromCaffe(
#         "data/models/deploy.prototxt.txt",
#         "data/models/res10_300x300_ssd_iter_140000.caffemodel")
#     print("[INFO] model loaded.")

    # section = input("Section (morning/afternoon)? ")
    # if(is_valid_section(section)):
        # print("[INFO] Section {} started capturing...".format(section))
        # capture_frame(section)
    # else:
    #     print("[INFO] Invalid section")

    # capture_frame()

    # identify_face(open("/Users/iMac/Documents/images/Group/60130500008_Test_2.jpeg", 'rb').read())
    # identify_face(open("/Users/iMac/Documents/images/Group/60130500138_20.png", 'rb').read())
    # identify_face(open("/Users/iMac/Documents/images/Group/60130500008_Test_2.jpeg", 'rb').read())
