from django.urls import include, path
from .views import CitysViewSet
from rest_framework.routers import SimpleRouter

router = SimpleRouter()


router.register("citys", CitysViewSet, basename="citys")


urlpatterns = [path("", include(router.urls))]
