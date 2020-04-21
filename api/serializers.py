from django.contrib.auth.models import User, Group
from rest_framework import serializers

from helpline.models import HelplineUser, Case, SMSCDR,MainCDR,Locations,SafePal
from helpdesk.models import Ticket
from django.utils import timezone
from datetime import datetime

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


class TimestampField(serializers.DateTimeField):
    """
    Convert a django datetime to/from timestamp.
    """
    # def to_representation(self, value):
    #     """
    #     Convert the field to its internal representation (aka timestamp)
    #     :param value: the DateTime value
    #     :return: a UTC timestamp integer
    #     """
    #     result = super(TimestampField, self).to_representation(value)
    #     return result.timestamp()

    def to_internal_value(self, value):
        """
        deserialize a timestamp to a DateTime value
        :param value: the timestamp value
        :return: a django DateTime value
        """
        converted = datetime.fromtimestamp(float('%s' % float(value)))
        return super(TimestampField, self).to_representation(converted)

class SafePalSerializer(serializers.HyperlinkedModelSerializer):
    survivor_date_of_birth = serializers.DateField(format="%Y-%m-%d",read_only=True)
    incident_date_and_time = TimestampField()
    date_of_interview_with_cso = TimestampField()

    class Meta:
        model = SafePal
        fields = ('incident_report_id','survivor_name','survivor_gender','survivor_contact_phone_number','survivor_contact_email',\
            'survivor_date_of_birth','unique_case_number','incident_location','incident_date_and_time','incident_type',\
            'incident_description','incident_reported_by','number_of_perpetrators','perpetrator_name','perpetrator_gender',\
            'perpetrator_estimated_age','perpetrator_relationship','perpetrator_location','date_of_interview_with_cso')


class LocationsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="level_uid")
    label = serializers.CharField(source="level_name")  
    region = serializers.CharField(source="level_region")         

    class Meta:
        model = Locations
        fields = ('label','name','region')

class SmsSerializer(serializers.HyperlinkedModelSerializer):
    
    class Meta:
        model = SMSCDR
        fields = ('from_phone','msg','time','sms_time')
