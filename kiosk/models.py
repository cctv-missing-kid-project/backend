from django.db import models


# Create your models here.
class CustomerGroups(models.Model):
    group_img_url = models.CharField(max_length=200)


class Customers(models.Model):
    face_img_url = models.CharField(max_length=200)
    object_img_url = models.CharField(max_length=200)
    group = models.ForeignKey(CustomerGroups, on_delete=models.CASCADE)


class Camera(models.Model):
    location = models.CharField(max_length=200)


# 실시간에 근접하게 찾는 기능만을 위해서는 굳이 당장은 필요 없지만 추후 과거의 데이터까지 사용하려면 저장해도 된다.
# class Found(models.Model):
#     found_img_url = models.CharField(max_length=200)
#     camera = models.ForeignKey(max_length=10)
