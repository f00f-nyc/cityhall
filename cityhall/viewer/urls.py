from django.conf.urls import patterns, url
from viewer.views import CityHallViewer


urlpatterns = patterns(
    "",
    url(r"^$",CityHallViewer.as_view(), name="viewer_home"),
)
