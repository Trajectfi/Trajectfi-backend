"""
URL configuration for trajectfi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.db.models import Count
from rest_framework import serializers, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.urls import path
from core.tests.models import AcceptedToken, Listing  # type: ignore


# Serializer
class AcceptedTokenSerializer(serializers.ModelSerializer):
    listing_count = serializers.SerializerMethodField()

    class Meta:
        model = AcceptedToken
        fields = ["contract_address", "name", "listing_count"]

    def get_listing_count(self, obj):
        return obj.listing_count


# View
class AcceptedTokenListView(generics.ListAPIView):
    queryset = AcceptedToken.objects.annotate(listing_count=Count("listing"))
    serializer_class = AcceptedTokenSerializer


# URL Configuration
urlpatterns = [
    path(
        "api/accepted-tokens/",
        AcceptedTokenListView.as_view(),
        name="accepted-token-list",
    ),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
]
