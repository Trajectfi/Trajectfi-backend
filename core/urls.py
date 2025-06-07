from django.urls import path

from . import views

urlpatterns = [
    path(
        "accepted-nfts/",
        views.AcceptedNFTListAPIView.as_view(),
        name="accepted-nfts-list-view",
    ),
    path(
        "accepted-tokens/",
        views.AcceptedTokenListAPIView.as_view(),
        name="accepted-tokens-list-view",
    ),
    path(
        "sigin/",
        views.SignInAPIView.as_view(),
        name="signin",
    ),
    path(
        "listings/",
        views.ListingListAPIView.as_view(),
        name="listing-list",
    ),
    path("offer/create/", views.OfferCreateAPIView.as_view(), name="create-offer"),
    path("offer/cancel/", views.OfferCancelAPIView.as_view(), name="cancel-offer"),
    path(
        "account/update-email/",
        views.UpdateEmailAPIView.as_view(),
        name="update-email",
    ),
]
