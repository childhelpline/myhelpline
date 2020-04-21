from django.conf.urls import url, include
from rest_framework import routers
from api import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'sms', views.SmsViewSet)
router.register(r'helplineusers', views.HelplineUserViewSet)
router.register(r'helplinecases', views.HelplineCaseViewSet)
router.register(r'caseworkers', views.CaseWorkerViewSet)
router.register(r'casemanagers', views.CaseManagerViewSet)
router.register(r'supervisors', views.SupervisorViewSet)
router.register(r'regions', views.RegionsViewSet)
router.register(r'districts', views.DistrictsViewSet)
router.register(r'wards', views.WardsViewSet)
router.register(r'villages', views.VillagesViewSet)
router.register(r'safepal', views.SafePalViewSet,base_name="safepal_cases")
router.register(r'cdrlist',views.MainCdrViewSet, base_name='MainCdr')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
