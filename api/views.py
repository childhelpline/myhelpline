from django.contrib.auth.models import User, Group
from rest_framework import viewsets

from api.serializers import UserSerializer, GroupSerializer,\
        HelplineUserSerializer, HelplineCaseSerializer,SmsSerializer
from helpline.models import HelplineUser, Case, SMSCDR

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
class SmsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
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

class HelplineCaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows helpline cases to be viewed or edited.
    """
    queryset = Case.objects.all()
    serializer_class = HelplineCaseSerializer
