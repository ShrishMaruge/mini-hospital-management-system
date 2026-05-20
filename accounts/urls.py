from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),

    path("login/<str:role>/", views.user_login, name="login"),
    path("register/<str:role>/", views.register, name="register"),

    path("verify-otp/<str:role>/<str:email>/", views.verify_otp, name="verify_otp"),
    path("resend-otp/<str:role>/<str:email>/", views.resend_otp, name="resend_otp"),

    path("logout/", views.logout_view, name="logout"),
    path("google/connect/", views.google_connect, name="google_connect"),
    path("google/callback/", views.google_callback, name="google_callback"),

]
