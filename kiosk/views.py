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
sys.path.append('/home')
from lab12.face import face_compare, face_detection
from lab11.Object_Detection import server


def upload_img(now, image, img_type):
    url = 'https://f8rhqudog3.execute-api.us-west-2.amazonaws.com/v2/image'
    image_name = f'{now.tm_year}{now.tm_mon}{now.tm_mday}{now.tm_hour}{now.tm_min}'
    name_img = image_name + f'{img_type}.jpeg'
    files = {'image': (name_img, image, 'multipart/form-data')}
    response = requests.post(url, files=files)
    return response


def get_image(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img = img.convert("RGB")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    img_str = base64.b64encode(buffer.getvalue())
    return img, img_str


@api_view(['POST'])
def register(request):
    # 모든 일행이 나온 사진을 제공받음
    group_img_data = request.data['file'].replace('data:image/jpeg;base64', "")
    group_img = base64.b64decode(group_img_data)
    now = time.localtime()

    # decode하고 난 이미지를 API Gateway를 통해 lambda함수를 불러 s3버킷에 저장하고 이미지 url을 return
    upload_response = upload_img(now, group_img, 'group_img')
    group_img_url = upload_response.json()[0]['file_url']
    group = CustomerGroup.objects.create(group_img_url=group_img_url)

    # 얼굴 인식 ai 모델에 단체 사진 url 변수를 주고 각 멤버의 객체(얼굴) 사진을 업로드 한 후 url을 return 해준다.
    data = face_detection.FindFaces(group_img_url)
    # 리턴 받은 데이터 형식:
    # {'image#': object_img_url}

    # 얼굴인식 + 객체 프로그램을 돌려 얼굴 사진, 객체, 가족사진을 매칭시킨다.
    for i in range(1, len(data) + 1):
        # 객체(얼굴)
        object_img_url = data[f'image{i}']
        # Customer 생성
        Customer.objects.create(object_img_url=object_img_url, group=group)
    return Response({'result': 'success!'})


@api_view(['POST'])
def face_recognition(request):
    url = 'https://f8rhqudog3.execute-api.us-west-2.amazonaws.com/v2/image'

    # 키오스크에서 찍은 얼굴 사진 이미지로 디코드
    img_data = request.data['file'].replace('data:image/jpeg;base64', "")
    img = base64.b64decode(img_data)
    files = {'image': ('face_to_compare.jpeg', img, 'multipart/form-data')}
    object_to_compare_url = requests.post(url, files=files).json()[0]['file_url']

    # DB에 저장되어 있는 모든 인물들과 얼굴을 대조하기 위해 모든 url을 dictionary에 넣어준다.
    all_object_img_url = {}
    for i in Customer.objects.all():
        all_object_img_url[i.object_img_url] = i.id

    # 얼굴 비교 ai 돌려서 받은 id 값을 data에 저장
    customer_id = face_compare.testCompare(all_object_img_url, object_to_compare_url)
    customer = Customer.objects.get(id=customer_id)
    object_url = customer.object_img_url

    # 해당 객체(얼굴) 이미지 불러온다.
    upload = get_image(object_url)
    img_str = upload[1]

    """
    person = Customer.objects.get(
        object_img_url='https://team3-cctv-bucket.s3.us-west-2.amazonaws.com/cctv/2/2021129_18:26_object1.jpeg')

    response = requests.get(person.object_img_url)
    image = Image.open(BytesIO(response.content))
    image = image.convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    img_str = base64.b64encode(buffer.getvalue())
    return Response({"image": img_str, "id": person.id})
    """

    # 해당하는 객체 이미지와 Customer_id를 프론트에 리턴한다.
    return Response({"image": img_str, "id": customer_id})


@api_view(['GET'])
def get_group(request, pk):
    # 제공 받은 pk(id)에 상응하는 고객 정보 불러와서 직렬화
    customer = Customer.objects.get(id=pk)
    s_customer = CustomerSerializer(customer)

    # 유저가 속한 그룹 id를 받아와 해당 그룹과 그룹 멤버를 불러옴
    group_id = s_customer.data['group']['id']
    group_members = Customer.objects.filter(group=group_id)
    s_group_members = CustomerSerializer(group_members, many=True)
    group = CustomerGroup.objects.get(id=group_id)
    members = []

    # 본인을 제외한 일행들을 members 변수에 저장
    for i in s_group_members.data:
        response = requests.get(i['object_img_url'])
        member_object_img = Image.open(BytesIO(response.content))
        member_object_img = member_object_img.convert("RGB")
        buffer = BytesIO()
        member_object_img.save(buffer, format="JPEG")
        member_object_img_str = base64.b64encode(buffer.getvalue())
        if i['id'] == pk:
            pass
        else:
            members.append({'member_id': i['id'], 'member_face': member_object_img_str})

    image = get_image(group.group_img_url)
    group_img_str = image[1]

    data = {
        "group_img": group_img_str,
        "members": members,
    }

    return Response(data)


@api_view(['GET'])
def get_member_location(request, pk):
    member = Customer.objects.get(id=pk)
    member_object_img_url = member.object_img_url

    # ai 객체 인식 함수를 돌린다 -> 리턴값은 없고 요청시마다 이미지가 s3에 같은 이름으로 덮어씌워진다..
    server.pack(member_object_img_url)

    result_url = {}
    result_object_url = {}

    all_camera = Camera.objects.all()

    # s3에 같은 이름으로 덮어 씌워지기 때문에 객체 매칭으로 찾은 일행원으로 가능성이 높은 카메라 수만큼의 이미지들을
    # 얼굴비교를 통해 정확성을 높인다. result 이미지의 번호는 카메라 번호
    for i in range(1, len(all_camera)+1):
        result_url[i] = f'https://team3-cctv-bucket.s3.us-west-2.amazonaws.com/results/result${i}.jpeg'
        result_object_url[
            f'https://team3-cctv-bucket.s3.us-west-2.amazonaws.com/objects/object${i}.jpeg'] = i

    result_num = face_compare.testCompare(result_object_url, member_object_img_url)

    image = get_image(result_url[result_num])
    result_image_str = image[1]

    cam = Camera.objects.get(id=result_num)
    location = cam.location
    """
    response = requests.get('https://team3-cctv-bucket.s3.us-west-2.amazonaws.com/cctv/2/12-09-2021_20-18-45_CCTV1_picture.jpg')
    location_img = Image.open(BytesIO(response.content))
    location_img = location_img.convert("RGB")
    buffer = BytesIO()
    location_img.save(buffer, format="JPEG")
    location_img_str = base64.b64encode(buffer.getvalue())
    camera = Camera.objects.get(id=1)
    
    return Response({"location": camera.location, "location_img": location_img_str})
   """
    return Response({"location_img": result_image_str, "location": location})

