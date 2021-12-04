import base64
import requests
import time
#이미지 관련
from PIL import Image
from io import BytesIO, StringIO
# from django.shortcuts import render
#django rest 관련
from rest_framework.decorators import api_view
from rest_framework.response import Response
#모델, serializer
from kiosk.models import Customer, CustomerGroup, Camera
from kiosk.serializers import CustomerSerializer, CustomerGroupSerializer, CameraSerializer


@api_view(['POST'])
def face_save(request):
    url = 'https://f8rhqudog3.execute-api.us-west-2.amazonaws.com/v2/image'
    print(request.data)
    # face_image = request.data['face']
    # face_image = base64.b64decode(face_image)
    # object_image = request.data['object']
    # object_image = base64.b64decode(object_image)
    #
    # now = time.localtime()
    # image_name = f'{now.tm_year}_{now.tm_mon}_{now.tm_mday}_{now.tm_hour}:{now.tm_min}_'
    #
    # file1 = {'image': (image_name+'face.jpeg', face_image, 'multipart/form-data')}
    # with requests.Session() as s:
    #     resp = s.post(url, files=file1)
    #     face_url = resp.json()[0]['file_url']
    #
    # file2 = {'image': (image_name+'object.jpeg', object_image, 'multipart/form-data')}
    # with requests.Session() as s:
    #     resp = s.post(url, files=file2)
    #     object_url = resp.json()[0]['file_url']
    #
    # data = {'face_img_url': face_url, 'object_img_url': object_url}
    return Response({'result': 'success!'})


@api_view(['POST'])
def face_recognition(request):
    img_data = request.data['file'].replace('data:image/jpeg;base64', "")
    img = base64.b64decode(img_data)
    filename = 'image.jpeg'
    created_image = open(filename, 'wb')
    created_image.write(img)
    created_image.close()

    response = requests.get('https://team3-cctv-bucket.s3.us-west-2.amazonaws.com/top-10-greatest-leonardo-dicaprio-movies.jpg')
    image2 = Image.open(BytesIO(response.content))
    image2 = image2.convert("RGB")
    buffer = BytesIO()
    image2.save(buffer, format="JPEG")
    img2_str = base64.b64encode(buffer.getvalue())


    #얼굴인식을 통해 모든 db의 모든 사진과 대조하여 일치하는 id를 보낸다?
    return Response({"image": img2_str, "id": 1})


@api_view(['GET'])
def get_group(request, pk):
    #제공 받은 pk(id)에 상응하는 고객 정보 불러와서 serializer로 직렬화
    customer = Customer.objects.get(id=pk)
    s_customer = CustomerSerializer(customer)

    #유저가 속한 그룹 id를 받아와 해당 그룹과 그룹 멤버를 불러옴
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

    response = requests.get(member_object_img_url)
    member_object_img = Image.open(BytesIO(response.content))
    member_object_img = member_object_img.convert("RGB")
    buffer = BytesIO()
    member_object_img.save(buffer, format="JPEG")
    #member_object_img를 이용해서 ai모델을 돌려서 이미지 주소를 리턴 받고 리퀘스트해서 스트링화 한 이미지를 프론트에 리턴해준다
    #일단은 그냥 오브젝트 이미지를 전달하는 걸로 구현합시다
    member_object_img = base64.b64encode(buffer.getvalue())

    return Response({"location": member_object_img})

