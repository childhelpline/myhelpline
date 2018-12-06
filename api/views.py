from django.contrib.auth.models import User, Group
from rest_framework import viewsets

from api.serializers import UserSerializer, GroupSerializer,\
        HelplineUserSerializer, HelplineCaseSerializer
from helpline.models import HelplineUser, Case

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
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
