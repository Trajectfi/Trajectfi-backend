from django.conf import settings
from rest_framework import exceptions as rest_exceptions
from rest_framework import generics, serializers

from . import exceptions, models
from .models import Listing
from .service import CoreService


class AcceptedNFTSerializer(serializers.ModelSerializer):
    """
    Serializer class for AcceptedNFT Model.
    Additionally return a number of listings that uses
    the nfts's contract address

    Fields:
        - name
        - contract_address
        - listing_count
    """

    listings_count = serializers.SerializerMethodField()

    class Meta:
        model = models.AcceptedNFT
        fields = ["name", "contract_address", "listings_count"]

    def get_listings_count(self, obj: models.AcceptedNFT) -> int:
        return models.Listing.objects.filter(
            nft_contract_address=obj.contract_address
        ).count()


class AcceptedTokenSerializer(serializers.ModelSerializer):
    """
    Serializer class for AcceptedToken Model.
    Additionally return a number of listings that uses
    the token's contract address

    Fields:
        - name
        - contract_address
        - listing_count
    """

    listings_count = serializers.SerializerMethodField()

    class Meta:
        model = models.AcceptedToken
        fields = ["name", "contract_address", "listings_count"]

    def get_listings_count(self, obj: models.AcceptedNFT) -> int:
        return models.Listing.objects.filter(
            token_contract_address=obj.contract_address
        ).count()


class UserSerializer(serializers.ModelSerializer):
    """
    Convert the user model class to dict-like data for json serialization.
    """

    class Meta:
        model = models.User
        fields = ["id", "public_key", "email"]


class SignInSerializer(serializers.Serializer):
    """
    Serializer class for the sign in request call.
    It validates the signstures to ensure it is the right user that is
    making the signin request.
    This is for signing in with the wallet (account).

    Data:
        signatures: A list of strings representing the signatures of
            the signed login message
        public_key: The public key of the signer
    """

    signatures = serializers.ListField(child=serializers.CharField())
    public_key = serializers.CharField()

    def validate(self, attrs: dict) -> dict:
        """
        Validate the request data
        """
        # The signature list length must be greater than or equals to 5
        # according to the starknet signature format.
        if len(attrs["signatures"]) < 5:
            raise exceptions.InvalidSignature

        # validate the signature
        check = CoreService.validate_login_request(
            attrs["signatures"], attrs["public_key"]
        )
        if not check:
            raise exceptions.LoginValidationFailed

        # prevent login if account is not active
        if models.User.objects.filter(
            public_key=attrs["public_key"], is_active=False
        ).exists():
            raise rest_exceptions.AuthenticationFailed

        return attrs

    def save(self) -> dict:
        """
        Create or get the user and generate an auth token data
        for requests authentications

        Returns:
            dict: Data of the user
        """
        public_key = self.validated_data["public_key"]
        user, is_new = CoreService.login_or_register_user(public_key)
        data = UserSerializer(user).data
        data["is_new"] = is_new
        token_info = CoreService.generate_auth_token_data(user)
        return {**data, **token_info}


class OfferSerializer(serializers.Serializer):
    class Meta:
        model = models.Offer
        fields = "__all__"


class SimpleOfferSerializer(serializers.Serializer):
    class Meta:
        model = models.Offer
        exclude = [
            "signature",
            "signature_expiry",
            "signature_chain_id",
            "signature_unique_id",
        ]


class MakeOfferSerializer(serializers.Serializer):
    listing = serializers.UUIDField()
    principal = serializers.IntegerField(min_value=1)
    repayment_amount = serializers.IntegerField(min_value=1)
    collateral_contract = serializers.CharField()
    collateral_id = serializers.IntegerField(min_value=1)
    token_contract = serializers.CharField()
    loan_duration = serializers.IntegerField(
        min_value=settings.MIN_LOAN_DURATION, max_value=settings.MAX_LOAN_DURATION
    )
    expiry = serializers.IntegerField()
    chain_id = serializers.CharField()
    unique_id = serializers.IntegerField()
    signatures = serializers.ListField(child=serializers.CharField())

    def validate(self, attrs):
        """
        Validate the request data
        """
        # Listing Validation
        try:
            listing = models.Listing.objects.get(id=attrs["listing"])
        except models.Listing.DoesNotExist:
            raise serializers.ValidationError({"detail": "Listing does not exist"})
        if listing.status != models.ListingStatus.OPEN:
            raise serializers.ValidationError({"detail": "Listing is not active"})
        # Collateral Contract Validation
        if listing.nft_contract_address != attrs["collateral_contract"]:
            raise serializers.ValidationError({"detail": "Invalid listing collateral"})

        # Principal and Repayment Validation
        if attrs["principal"] > attrs["repayment_amount"]:
            raise serializers.ValidationError(
                {"detail": "Principal should be less than Repayment amount"}
            )

        # validate offer token
        if not models.AcceptedToken.objects.filter(
            contract_address=attrs["token_contract"]
        ).exists():
            raise serializers.ValidationError({"detail": "Token not supported"})

        # verify the signature
        data = {
            "principal": attrs["prinicipal"],
            "repayment_amount": attrs["repayment_amount"],
            "collateral_contract": attrs["collateral_contract"],
            "collateral_id": attrs["collateral_id"],
            "token_contract": attrs["token_contract"],
            "loan_duration": attrs["loan_duration"],
            "expiry": attrs["expiry"],
            "chain_id": attrs["chain_id"],
            "unique_id": attrs["unique_id"],
        }
        user = self.context["user"]

        check = CoreService.validate_loan_offer_request(data, attrs["signatures"], user)
        if not check:
            raise serializers.ValidationError({"detail": "Invalid signature message"})

        # set the necessary contexts
        self.context["listing"] = listing

        return attrs

    def save(self, **kwargs):
        user = self.context["user"]
        listing = self.context["listing"]
        offer = CoreService.create_offer(
            user,
            listing,
            self.validated_data["principal"],
            self.validated_data["repayment_amount"],
            self.validated_data["duration"],
            self.validated_data["signature"],
            self.validated_data["expiry"],
            self.validated_data["chain_id"],
            self.validated_data["unique_id"],
        )
        data = OfferSerializer(offer).data

        return data


class CancelOfferSerializer(serializers.Serializer):
    offer = serializers.UUIDField

    def validate(self, attrs):
        user = self.context["user"]
        # check if the offer exist and it belongs
        # to the user requesting the action
        generics.get_object_or_404(models.Offer, id=attrs["offer"], user=user)
        return attrs

    def save(self):
        # delete the offer
        CoreService.cancel_offer(self.validated_data["offer_id"])


class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = [
            "id",
            "nft_contract_address",
            "nft_token_id",
            "user",
            "borrow_amount",
            "duration",
            "created_at",
            "status",
        ]


class UpdateEmailSerializer(serializers.Serializer):
    """
    Serializer for updating user email address.
    """

    email = serializers.EmailField()

    def validate_email(self, value):
        """
        Validate that the email is properly formatted.
        """

        return value.lower()

    def save(self):
        """
        Update the authenticated user's email address.
        """
        user = self.context["user"]
        user.email = self.validated_data["email"]
        user.save(update_fields=["email"])
        return user
