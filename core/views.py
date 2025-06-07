# Create your views here.
from rest_framework import filters, status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import models, serializers
from .models import Listing, ListingStatus
from .serializers import ListingSerializer


class AcceptedNFTListAPIView(ListAPIView):
    queryset = models.AcceptedNFT.objects.all().order_by("name")
    serializer_class = serializers.AcceptedNFTSerializer


class AcceptedTokenListAPIView(ListAPIView):
    queryset = models.AcceptedToken.objects.all().order_by("name")
    serializer_class = serializers.AcceptedTokenSerializer


class SignInAPIView(GenericAPIView):
    serializer_class = serializers.SignInSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        return Response(data)


class OfferCreateAPIView(GenericAPIView):
    serializer_class = serializers.MakeOfferSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data, status=status.HTTP_201_CREATED)


class OfferCancelAPIView(GenericAPIView):
    serializer_class = serializers.CancelOfferSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListingPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ListingListAPIView(ListAPIView):
    serializer_class = ListingSerializer
    pagination_class = ListingPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["nft_contract_address", "user__public_key"]

    def get_queryset(self):
        queryset = Listing.objects.filter(status=ListingStatus.OPEN).order_by(
            "-created_at"
        )
        collateral_contract = self.request.query_params.get("collateral_contract")
        borrower_address = self.request.query_params.get("borrower_address")

        if collateral_contract:
            queryset = queryset.filter(nft_contract_address__iexact=collateral_contract)
        if borrower_address:
            queryset = queryset.filter(user__public_key__iexact=borrower_address)

        return queryset


class UpdateEmailAPIView(GenericAPIView):
    """
    API endpoint for authenticated users to update their email address.

    Requires authentication via Knox token.
    Validates email format and updates the user's email in the database.
    """

    serializer_class = serializers.UpdateEmailSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Update authenticated user's email address.

        Returns:
            200 OK: Email updated successfully
            400 Bad Request: Invalid email format
            401 Unauthorized: User not authenticated
        """
        serializer = self.serializer_class(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)

        updated_user = serializer.save()

        return Response(
            {"message": "Email updated successfully", "email": updated_user.email},
            status=status.HTTP_200_OK,
        )
