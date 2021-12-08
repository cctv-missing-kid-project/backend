import base64
import requests
import time
# 이미지 관련
from PIL import Image
from io import BytesIO, StringIO
# from django.shortcuts import render
# django rest 관련
from rest_framework.decorators import api_view
from rest_framework.response import Response
# 모델, serializer
from kiosk.models import Customer, CustomerGroup, Camera
from kiosk.serializers import CustomerSerializer, CustomerGroupSerializer, CameraSerializer
import sys
sys.path.append('home')
from lab12 import face_detection, face_recognition
from lab11.Object_Detection import server


def upload_img(now, image, img_type):
    url = 'https://f8rhqudog3.execute-api.us-west-2.amazonaws.com/v2/image'

    image_name = f'{now.tm_year}{now.tm_mon}{now.tm_mday}_{now.tm_hour}:{now.tm_min}_'
    name_img = image_name + f'{img_type}.jpeg'
    files = {'image': (name_img, image, 'multipart/form-data')}
    response = requests.post(url, files=files)
    return response


@api_view(['POST'])
def register(request):
    # 모든 일행이 나온 사진을 제공받음
    group_img_data = request.data['file'].replace('data:image/jpeg;base64', "")
    group_img = base64.b64decode(group_img_data)
    now = time.localtime()

    upload_response = upload_img(now, group_img, 'group_img')
    group_img_url = upload_response.json()[0]['file_url']
    group = CustomerGroup.objects.create(group_img_url=group_img_url)

    # 가족 이미지 주고 개별 이미지 획득
    data = face_detection.FindFaces(group_img_url)

    # 얼굴인식 + 객체 프로그램을 돌려 얼굴 사진, 객체, 가족사진을 매칭시킨다.
    # group.id는 커스토머 추가할 때 필요한 데이터(하나의 그룹으로 묶기 위한)
    for i in range(1, len(data) + 1):
        # 얼굴
        object_image_str = data[f'image{i}']
        object_image = base64.b64decode(face_image_str)
        object_response = upload_img(now, face_image, 'face_img')
        object_img_url = face_response.json()[0]['file_url']
        # Customer 생성
        Customer.objects.create(object_img_url=object_img_url, group=group.id)

    return Response({'result': 'success!'})


@api_view(['POST'])
def face_recognition(request):
    url = 'https://f8rhqudog3.execute-api.us-west-2.amazonaws.com/v2/image'

    # 키오스크에서 찍은 얼굴 사진 이미지로
    img_data = request.data['file'].replace('data:image/jpeg;base64', "")
    img = base64.b64decode(img_data)
    files = {'image': ('face_to_compare.jpeg', img, 'multipart/form-data')}
    face_to_compare_url = requests.post(url, files=files).json()[0]['file_url']

    all_face_img_url = []
    for i in Customer.objects.all():
        all_face_img_url.append(i.face_img_url)
    # print(all_face_img_url)
    # # 얼굴 비교 ai 돌려서 받은 id 값을 data에 저장
    customer_id = face_recognition.CompareFace(face_to_compare_url, all_face_img_url)

    customer = Customer.objects.get(id=customer_id)
    face_url = customer.face_img_url

    # 해당 얼굴 이미지 불러온다.
    response = requests.get(face_url)
    # response = requests.get(
    #     'https://team3-cctv-bucket.s3.us-west-2.amazonaws.com/top-10-greatest-leonardo-dicaprio-movies.jpg')
    image2 = Image.open(BytesIO(response.content))
    image2 = image2.convert("RGB")
    buffer = BytesIO()
    image2.save(buffer, format="JPEG")
    img2_str = base64.b64encode(buffer.getvalue())

    # 얼굴인식을 통해 모든 db의 모든 사진과 대조하여 일치하는 id를 보낸다?
    # return Response({"image": img2_str, "id": 1})
    # 얼굴 비교 후 맞는 아이디와 해당 이미지를 전송해준다
    return Response({"image": img2_str, "id": id})


@api_view(['GET'])
def get_group(request, pk):
    # 제공 받은 pk(id)에 상응하는 고객 정보 불러와서 serializer로 직렬화
    customer = Customer.objects.get(id=pk)
    s_customer = CustomerSerializer(customer)

    # 유저가 속한 그룹 id를 받아와 해당 그룹과 그룹 멤버를 불러옴
    group_id = s_customer.data['group']['id']
    group_members = Customer.objects.filter(group=group_id)
    s_group_members = CustomerSerializer(group_members, many=True)
    group = CustomerGroup.objects.get(id=group_id)
    members = []

    for i in s_group_members.data:
        response = requests.get(i['face_img_url'])
        member_face_img = Image.open(BytesIO(response.content))
        member_face_img = member_face_img.convert("RGB")
        buffer = BytesIO()
        member_face_img.save(buffer, format="JPEG")
        member_face_img_str = base64.b64encode(buffer.getvalue())
        members.append({'member_id': i['id'], 'member_face': member_face_img_str})

    response = requests.get(group.group_img_url)
    group_img = Image.open(BytesIO(response.content))
    group_img = group_img.convert("RGB")
    buffer = BytesIO()
    group_img.save(buffer, format="JPEG")
    group_img_str = base64.b64encode(buffer.getvalue())

    data = {
        "group_img": group_img_str,
        "members": members,
    }

    return Response(data)


@api_view(['GET'])
def get_member_location(request, pk):
    member = Customer.objects.get(id=pk)
    member_object_img_url = member.object_img_url

    # ai 객체 인식 함수를 돌려서 이미지 주소를 리턴받는다. 올린 후에
    server.pack(member_object_img_url)
    # response = requests.get(member_object_img_url)
    # member_object_img = Image.open(BytesIO(response.content))
    # member_object_img = member_object_img.convert("RGB")
    # buffer = BytesIO()
    # member_object_img.save(buffer, format="JPEG")
    # member_object_img = base64.b64encode(buffer.getvalue())

    result_url = []
    result_object_url = []

    all_camera = Camera.objects.all()

    for i in range(1, len(all_camera)+1):
        result_url.append({i: f'https://team3-cctv-bucket.s3.us-west-2.amazonaws.com/result${i}.jpeg'})
        result_object_url.append(f'https://team3-cctv-bucket.s3.us-west-2.amazonaws.com/object${i}.jpeg')

    result_num = face_recognition.CompareFace(member_object_img_url, result_object_url)
    cam = Camera.objects.get(id=result_num)
    location = cam.location

    return Response({"location_img": result_url[result_num], "location": location})
