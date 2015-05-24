from django.conf.urls import patterns, url
from .views import (Info, Create)
from .views_auth import Authenticate, CreateEnvironment, CreateUser, GrantRights
from .views_env import EnvCreate, EnvView


urlpatterns = patterns("",  # noqa
    url(r"^info/$", Info.as_view(), name="info_home"),
    url(r"^create_default/$", Create.as_view(), name="create_def"),

    url(r"^auth/$", Authenticate.as_view(), name="authenticate"),
    url(r"^auth/create/env/$", CreateEnvironment.as_view(), name="create_env"),
    url(r"^auth/create/user/$", CreateUser.as_view(), name="create_user"),
    url(r"^auth/grant/$", GrantRights.as_view(), name="grant_rights"),

    url(r"^env/create/", EnvCreate.as_view(), name="create_values"),
    url(
        r"^env/view/(?P<env_path>.*)$",
        EnvView.as_view(),
        name="view_values"
    ),
)