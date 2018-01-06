# from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile, File

from tempfile import TemporaryFile
import numpy as np

from chera import preprocessing

from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly
)
from rest_framework_jwt.settings import api_settings
import json, jsonpickle

from .serializers import StudentDataSerializer, UserSerializer
from ..models import Teacher, Student, Department, StudentData


def get_jwt(user):
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    return token


class Register(APIView):

    permission_classes = (AllowAny,)
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        if not request.POST:
            return Response({'Error': "Please provide username/password", 'msg': 'failure'}, status=400)

        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        is_teacher = request.POST.get('isTeacher')

        is_teacher = not (is_teacher == 'False' or is_teacher == 'false' or is_teacher == 0 or is_teacher == '0')

        try:
            user = User.objects.create(email=email, username=username,
                                       first_name=first_name, last_name=last_name)
            user.set_password(password)
            user.save()

            if is_teacher:
                instance = Teacher(user=user)
                instance.save()
            else:
                uid = request.POST.get('uid')
                dept_id = request.POST.get('dept_id')
                dept_id = int(dept_id)
                department = Department.objects.get(dept_id=dept_id)
                instance = Student(user=user, uid=uid)
                instance.dept_id = department
                instance.save()

            return Response({'msg': 'success'})
        except Exception as e:
            print("Exception caught")
            user = User.objects.get(username=username)
            if user:
                user.delete()

            return Response(
                {
                    'msg': 'failure',
                    'Error': e.__str__()
                }, status=400
            )


class Login(APIView):

    permission_classes = (AllowAny,)
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        if not request.POST:
            return Response({'Error': "Please provide username/password", 'msg': 'failure'}, status=400)

        username = request.POST.get('username')
        password = request.POST.get('password')
        is_teacher = request.POST.get('isTeacher')

        is_teacher = not (is_teacher == 'False' or is_teacher == 'false' or is_teacher == 0 or is_teacher == '0')

        print(is_teacher)
        try:
            user = authenticate(username=username, password=password)

            if is_teacher:
                teacher = Teacher.objects.get(user=user)
                id = teacher.teacher_id
            else:
                student = Student.objects.get(user=user)
                id = student.student_id

        except Exception as e:
            print(e)
            try:
                User.objects.get(username=username).delete()
            except Exception as e:
                return Response({'msg': 'failure',
                                 'error': 'Invalid username or password'},
                                status=401)

            return Response({'msg': 'failure', 'error': e.__str__()}, status=401)

        token = get_jwt(user)
        return Response({'token': token, 'id': id,
                         'is_teacher': is_teacher,
                         'user': UserSerializer(user).data
                         }, status=200)


class StudentDataCreateAPIView(APIView):
    parser_classes = (MultiPartParser,)
    temp = 'temp'

    def post(self, request):
        video = request.data['video']
        path = default_storage.save(self.temp, ContentFile(video.read()))
        full_path = default_storage.path(path)

        dataset = preprocessing.generate_dataset(full_path)

        if not len(dataset):
            return Response({'msg': 'failure',
                             'error': 'No face found in the video'}, status=401)

        outfile = TemporaryFile()
        np.save(outfile, dataset)

        username = request.data['username']

        user = User.objects.filter(username=username).first()
        student = user.student

        f = File(outfile, '{0}.npy'.format(username))

        instance = StudentData(student_id=student, data=f)
        instance.save()

        default_storage.delete(path)

        return Response({'msg': 'success'})


class StudentDataUpdateAPIView(UpdateAPIView):
    serializer_class = StudentDataSerializer
    queryset = StudentData.objects.all()


class StudentDataGetListAPIView(ListAPIView):
    serializer_class = StudentDataSerializer

    def get_queryset(self, *args, **kwargs):
        student_id = self.request.GET['student_id']
        return StudentData.objects.filter(student_id=student_id)


class StudentDataDeleteAPIView(DestroyAPIView):
    serializer_class = StudentDataSerializer
    queryset = StudentData.objects.all()


'''
curl -X GET -H "Authorization: JWT <token>" -H "Content-Type:application/json" http://127.0.0.1:8000/api/course/get/?dept_id=2&teacher_id=1&name=Computer%20Networks&academic_yr=2017&year=3

'''