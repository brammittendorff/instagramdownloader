 
import argparse
import sys
import os
import threading
import math
import glob
import shutil
import cv2 as cv
import math
import time
import argparse

def getFaceBox(net, frame, conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    blob = cv.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)

    net.setInput(blob)
    detections = net.forward()
    bboxes = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * frameWidth)
            y1 = int(detections[0, 0, i, 4] * frameHeight)
            x2 = int(detections[0, 0, i, 5] * frameWidth)
            y2 = int(detections[0, 0, i, 6] * frameHeight)
            bboxes.append([x1, y1, x2, y2])
            cv.rectangle(frameOpencvDnn, (x1, y1), (x2, y2), (0, 255, 0), int(round(frameHeight/150)), 8)
    return frameOpencvDnn, bboxes

def classify_image(current_image):
    retval = os.getcwd()

    # Location of models and protos
    faceProto = 'models/opencv_face_detector.pbtxt'
    faceModel = 'models/opencv_face_detector_uint8.pb'
    ageProto = 'models/age_deploy.prototxt'
    ageModel = 'models/age_net.caffemodel'
    genderProto = 'models/gender_deploy.prototxt'
    genderModel = 'models/gender_net.caffemodel'

    # Load network
    ageNet = cv.dnn.readNet(ageModel, ageProto)
    genderNet = cv.dnn.readNet(genderModel, genderProto)
    faceNet = cv.dnn.readNet(faceModel, faceProto)

    # Load values adjusted to the model
    MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
    # ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
    ageList = [1, 2, 3, 4, 5, 6, 7, 8]
    # genderList = ['Male', 'Female']
    genderList = [1, 2]
    padding = 20

    frame = cv.imread(current_image, 1)

    # Create a face box to classify gender and age
    frameFace, bboxes = getFaceBox(faceNet, frame)

    if not bboxes:
        return False
    else:
        faces = {}
        for bbox in bboxes:
            # Load face with padding
            face = frame[max(0,bbox[1]-padding):min(bbox[3]+padding,frame.shape[0]-1),max(0,bbox[0]-padding):min(bbox[2]+padding, frame.shape[1]-1)]

            blob = cv.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)

            # Classify Gender
            genderNet.setInput(blob)
            genderPreds = genderNet.forward()
            gender = genderList[genderPreds[0].argmax()]
            # print('Gender : {}, conf = {:.3f}'.format(gender, genderPreds[0].max()))
            faces['gender'] = gender
            faces['genderprediction'] = genderPreds[0].max()

            #Classify Age
            ageNet.setInput(blob)
            agePreds = ageNet.forward()
            age = ageList[agePreds[0].argmax()]
            # print('Age : {}, conf = {:.3f}'.format(age, agePreds[0].max()))
            faces['age'] = age
            faces['ageprediction'] = agePreds[0].max()
        return faces