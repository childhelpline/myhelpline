from django.contrib.auth.models import User, Group
from rest_framework import serializers

from helpline.models import HelplineUser, Case, SMSCDR,MainCDR
from helpdesk.models import Ticket

class UserSerializer(serializers.HyperlinkedModelSerializer):

    name = serializers.CharField(source='username')
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

class Hl_UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = HelplineUser
        fields = ('hl_auth', 'hl_exten','hl_status')

class HelplineCaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Case
        fields = ('url', 'hl_time', 'priority', 'hl_data', 'hl_popup')

class MainCdrSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MainCDR
        fields = ('hl_phone','hl_start','hl_answer','hl_stop','hl_queue','hl_status','hl_type','hl_chan','hl_agent','hl_transfer','hl_record','hl_case','hl_wrapup','hl_bargein','hl_voicemail','hl_disposition','hl_pid')

class SmsSerializer(serializers.HyperlinkedModelSerializer):
    
    class Meta:
        model = SMSCDR
        fields = ('from_phone','msg','time','sms_time')
        # extra_kwargs = {'contact': {'required': False}}
        # def create(self,validated_data):
        #     sms = model.objects.create(
        #         contact=validated_data['contact'],
        #         msg=validated_data['msg'],
        #         time= timezone.now(), # validated_data['sent_timestamp'],
        #         sms_time=timezone.now()
        #     )
        #     sms.save()
        #     return sms
