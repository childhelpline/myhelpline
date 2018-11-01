from django.contrib.auth.models import User, Group
from rest_framework import serializers

from helpline.models import HelplineUser, Case
from helpdesk.models import Ticket

class UserSerializer(serializers.HyperlinkedModelSerializer):

    name = serializers.IntegerField(source='pk')
    label = serializers.CharField(source='username')
    class Meta:
        model = User
        fields = ('label','name')

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

class HelplineUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = HelplineUser
        fields = ('url', 'user', 'hl_auth', 'hl_exten', 'case', 'hl_status')

class HelplineCaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Case
        fields = ('url', 'hl_time', 'priority', 'hl_data', 'hl_popup')
