from django.conf.urls import include, url
from . import views, api

urlpatterns = [
    url(r'^$', views.page_dashboard),
    url(r'^user/login', views.user_login),
    url(r'^user/logout', views.user_logout),
    url(r'^page/perfil/$', views.page_perfil),
    url(r'^page/dashboard/$', views.page_dashboard),
    url(r'^page/issues/$', views.page_issues),
    url(r'^page/treatments/$', views.page_treatments),
    url(r'^page/treatment/(?P<treatment_id>\w+)/$', views.page_treatment),

    url(r'^page/admin/groups/$', views.page_admin_groups),
    url(r'^page/admin/settings/$', views.page_admin_settings),

    url(r'^page/manager/users/$', views.page_manager_users),
    url(r'^page/manager/statistics/$', views.page_manager_statistics),

    url(r'^api/dashboard/$', api.dashboard),
    url(r'^api/issues/$', api.issues),
    url(r'^api/manager/users/$', api.manager_users),
    url(r'^api/manager/user/$', api.manager_user),
    url(r'^api/manager/user/(?P<user_id>\w+)/$', api.manager_user),
    url(r'^api/manager/treatments/$', api.manager_treatments),
    url(r'^api/admin/groups/$', api.admin_groups),
    url(r'^api/admin/group/$', api.admin_group),
    url(r'^api/admin/group/(?P<group_id>\w+)/$', api.admin_group),
    url(r'^api/user/perfil/$', api.user_perfil),
    url(r'^api/user/pass/$', api.user_pass),
    url(r'^api/volunteer/new/$', api.volunteer_new),
]
