from django.contrib.auth.models import User, Group
from django.db.models import F
from rest_framework import viewsets, generics, mixins,status
from rest_framework.views import APIView
from rest_framework.decorators import api_view

from api.serializers import UserSerializer, GroupSerializer,\
        HelplineUserSerializer, HelplineCaseSerializer,SmsSerializer,\
        MainCdrSerializer,LocationsSerializer,SafePalSerializer
from helpline.models import HelplineUser, Case, SMSCDR,MainCDR,Locations,SafePal
from rest_framework_csv import renderers as r
from rest_framework.response import Response

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

class CaseManagerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.filter(HelplineUser__hl_role='Casemanager').order_by('-date_joined')
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


class RegionsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    renderer_classes = [r.CSVRenderer] # + tuple(settings.DEFAULT_RENDERER_CLASSES)
    queryset = Locations.objects.all().values(level_name=F('region_name') ,level_uid=F('region_uid'),level_region=F('pk')).distinct('level_uid')

    # def get_queryset(self):
    #     level = self.request.query_params['level'] or None
    #     if not level == None:
    #         queryset = Locations.objects.filter(region_uid=level).values(level_name=F('region_name') ,level_uid=F('region_uid'),Region=F('id')).distinct('level_uid')        
    #     else:
    #         queryset = Locations.objects.all().values(level_name=F('region_name') ,level_uid=F('region_uid'),Region=F('id')).distinct('level_uid')
    #     return queryset

        # if level == 'district' and not level_value == None:
        #     queryset = Locations.objects.filter(region_uid=level_value).values(level_name=F('district_name') ,level_uid=F('district_uid')).distinct('level_uid')        
        #     return queryset
        # if level == 'ward' and not level_value == None:
        #     queryset = Locations.objects.filter(district_uid=level_value).values(level_name=F('district_name') ,level_uid=F('district_uid')).distinct('level_uid')        
        #     return queryset
        # if level == 'village' and not level_value == None:
        #     queryset = Locations.objects.filter(ward_uid=level_value).values(level_name=F('district_name') ,level_uid=F('district_uid')).distinct('level_uid')        
        #     return queryset

    serializer_class = LocationsSerializer
class DistrictsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    renderer_classes = [r.CSVRenderer] # + tuple(settings.DEFAULT_RENDERER_CLASSES)
    queryset = Locations.objects.all().values(level_name=F('district_name') ,level_uid=F('district_uid'),level_region=F('region_uid')).distinct('level_uid')
    serializer_class = LocationsSerializer

class WardsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    renderer_classes = [r.CSVRenderer] # + tuple(settings.DEFAULT_RENDERER_CLASSES)
    queryset = Locations.objects.all().values(level_name=F('ward_name') ,level_uid=F('ward_uid'),level_region=F('district_uid')).distinct('level_uid')
    serializer_class = LocationsSerializer

class VillagesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    renderer_classes = [r.CSVRenderer] # + tuple(settings.DEFAULT_RENDERER_CLASSES)
    queryset = Locations.objects.all().values(level_name=F('village_name') ,level_uid=F('village_uid'),level_region=F('ward_uid')).distinct('level_uid')
    serializer_class = LocationsSerializer

class SafePalViewSetx(viewsets.ModelViewSet):

    queryset = SafePal.objects.all()
    serializer_class = SafePalSerializer

    def create(self, request, format=None):
        serializer = SafePalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(chl_user_id=request.user.pk)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SafePalViewSet(mixins.ListModelMixin,mixins.CreateModelMixin,
                     viewsets.GenericViewSet):

    queryset = SafePal.objects.all()
    serializer_class = SafePalSerializer
    
    # def get(self, request, *args, **kwargs):
    #     return self.retrieve(request, *args, **kwargs)

    # def post(self, request, *args, **kwargs):
    #     print("Cheru: Wee")
    #     return self.create(request, *args, **kwargs)
    # def put(self, request, *args, **kwargs):
    #     return self.update(request, *args, **kwargs)

    # def delete(self, request, *args, **kwargs):
    #     return self.destroy(request, *args, **kwargs)


