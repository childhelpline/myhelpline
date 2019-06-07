from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework.views import APIView

from api.serializers import UserSerializer, GroupSerializer,\
        HelplineUserSerializer, HelplineCaseSerializer,SmsSerializer,MainCdrSerializer
from helpline.models import HelplineUser, Case, SMSCDR,MainCDR

"""class SupervisorViewSet(viewsets.ModelViewSet):
    ""
    API endpoint that allows users to be viewed or edited.
    ""
    def get(self,request):
        emp_profile = HelplineUser.objects.filter(hl_role='Supervisor').order_by('-hl_time')
        serializer = HelplineUserSerializer(emp_profile)
        return Response(serializer.data)

class CaseworkerViewSet(viewsets.ModelViewSet):
    ""
    API endpoint that allows users to be viewed or edited.
    ""
    queryset = HelplineUser.objects.filter(hl_role='Caseworker').order_by('-hl_time')
    serializer_class = HelplineUserSerializer
"""
class MainCdrViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows SMS to be viewed or edited.
    """
    queryset = MainCDR.objects.filter()
    serializer_class = MainCdrSerializer

    def get(self, request, format=None):
        cdrs = MainCdr.objects.all()
        serializer = MainCdrSerializer(cdrs, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = MainCdrSerializer()
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # queryset = MainCDR.objects.filter()
    # serializer_class = MainCdrSerializer
    
class SmsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows SMS to be viewed or edited.
    """
    queryset = SMSCDR.objects.filter(sms_type='OUTBOX')
    serializer_class = SmsSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

class CaseWorkerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.filter(HelplineUser__hl_role='Caseworker').order_by('-date_joined')
    serializer_class = UserSerializer

class SupervisorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.filter(HelplineUser__hl_role='Supervisor').order_by('-date_joined')
    serializer_class = UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class HelplineUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows helpline users to be viewed or edited.
    """
    queryset = HelplineUser.objects.all()
    serializer_class = HelplineUserSerializer
    def perform_update(self, serializer):
        game = self.request.data
        _ = serializer.save(game=game)
        return Response(_)

class HelplineCaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows helpline cases to be viewed or edited.
    """
    queryset = Case.objects.all()
    serializer_class = HelplineCaseSerializer
