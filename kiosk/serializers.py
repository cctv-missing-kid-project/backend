from kiosk.models import Customer, CustomerGroup, Camera
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer


class CustomerGroupSerializer(ModelSerializer):
    group_img_url = serializers.CharField(max_length=200)

    class Meta:
        model = CustomerGroup
        fields = ['id', 'group_img_url']


class CustomerSerializer(ModelSerializer):
    object_img_url = serializers.CharField(max_length=200)
    group = CustomerGroupSerializer(many=False, read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'object_img_url', 'group']


class CameraSerializer(ModelSerializer):
    location = serializers.CharField(max_length=200)

    class Meta:
        model = Camera
        fields = ['id', 'location']
