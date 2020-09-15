import cv2
# import httpx
import json
# from PIL import Image


def capture_frame():
    cam = cv2.VideoCapture(1)
    frameNo = 0

    while True:
        hasNextFrame, frame = cam.read()
        cv2.imshow('Frame', frame)

        hasFace, confidences = detect_face(frame)
        print(confidences)

        # print(type(Image.fromarray(frame)))
        # frame = Image.fromarray(frame)

        if hasFace:
            cv2.imwrite("data/images/" + str(frameNo) + ".png", frame)
            print("[INFO] Face detected with frame number:", frameNo)
            # identify_face(open("data/images/" + str(frameNo) + ".png", 'rb').read())
            frameNo += 1

        if cv2.waitKey(30) & 0xff == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()


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

        if confidence > 0.6:
            # print(confidence * 100)
            confidences.append(confidence)
            hasFace = True

    return (hasFace, confidences)


def draw_face_box():
    pass


# def identify_face(image):
def identify_face():
    # ENDPOINT = "http://0.0.0.0:5001/"
    # response = httpx.post(url=ENDPOINT, data=open("data/images/sample/S__5144578.jpg"))
    # print(response.text)
    import requests

    url = "http://localhost:8002/api/v1/face/identify"

    payload = {
        'file': ('filename.png', open("data/images/0.png", 'rb').read(), 'multipart/form-data')
    }
    # payload = image
    headers = {
        'Content-Type': 'multipart/form-data'
    }

    response = requests.post(url, files=payload)

    print(response.text.encode('utf8'))


if __name__ == "__main__":
    # Load models
    # print("[INFO] loading model...")
    # net = cv2.dnn.readNetFromCaffe(
    #     "data/models/deploy.prototxt.txt",
    #     "data/models/res10_300x300_ssd_iter_140000.caffemodel")

    # capture_frame()

    identify_face()

    # frameNo = 0
    # cv2.imwrite("data/images/" + str(frameNo) + ".png", cv2.imread("data/images/sample/S__5144578.jpg"))
    # print(detect_face(cv2.imread("data/images/sample/S__5144578.jpg")))
