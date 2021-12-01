from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from PIL import Image
from io import BytesIO
from kiosk.models import Customers, CustomerGroups, Camera
import base64
import requests


@api_view(['POST'])
def face_save(request):
    img_data = request.data['file'].replace('data:image/jpeg;base64', "")
    img = base64.b64decode(img_data)
    #############AI 얼굴인식 모듈 불러와서 전송 받은 얼굴 데이터에 적용시킨 결과값을 데이터베이스에 저장##########
    #############리턴 값은 그냥 success messege로 충분할 수가 있다.

    return Response({'result': 'success!'})


@api_view(['POST'])
def face_recognition(request):
    img_data = request.data['file'].replace('data:image/jpeg;base64', "")
    img = base64.b64decode(img_data)
    filename = 'image.jpeg'
    created_image = open(filename, 'wb')
    created_image.write(img)
    created_image.close()

    response = requests.get('https://team3-cctv-bucket.s3.us-west-2.amazonaws.com/testingpic1.PNG')
    image2 = Image.open(BytesIO(response.content))
    image2 = image2.convert("RGB")
    buffer = BytesIO()
    image2.save(buffer, format="JPEG")
    img2_str = base64.b64encode(buffer.getvalue())


    #얼굴인식을 통해 모든 db의 모든 사진과 대조하여 일치하는 id를 보낸다?
    return Response({"image": img2_str, "id": 1})
