from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import User, Vendor


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["username"] = user.username
        token["email"] = user.email
        token["phone_number"] = user.phone_number
        token["gstin"] = user.gstin
        token["user_role"] = user.user_role
        token["is_superuser"] = user.is_superuser
        # ...
        return token


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    password1 = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    password2 = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password1": "Password fields don't match."}
            )

        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")

        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data["password1"])
        instance.save()

        return instance


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        user = User.objects.filter(email=value).first()
        if not user:
            raise serializers.ValidationError("User with this email ID doesn't exist.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    confirm_password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    def validate(self, value):
        if value["password"] != value["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Password fields don't match."}
            )
        return value


class ProcurementOfficerRegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    password2 = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "gstin",
            "password1",
            "password2",
        )

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password1": "Password fields don't match."}
            )

        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data["email"],
            phone_number=validated_data["phone_number"],
            gstin=validated_data["gstin"],
            password=validated_data["password1"],
            user_role="procurement_officer",
        )

        return user


class VendorInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = (
            "vendor_name",
            "address",
            "vendor_certified",
            "vendor_type",
        )


class VendorRegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    password2 = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    vendor_info = VendorInfoSerializer(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "gstin",
            "password1",
            "password2",
            "vendor_info",
        )

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password1": "Password fields don't match."}
            )

        return attrs

    def create(self, validated_data):
        vendor_data = validated_data.pop("vendor_info", None)
        password1 = validated_data.pop("password1", None)
        password2 = validated_data.pop("password2", None)
        user = User.objects.create_user(
            user_role="vendor", password=password1, **validated_data
        )

        if vendor_data:
            Vendor.objects.create(user=user, **vendor_data)

        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "gstin",
        )

    def update(self, instance, validated_data):
        # Update user fields
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.phone_number = validated_data.get(
            "phone_number", instance.phone_number
        )
        instance.gstin = validated_data.get("gstin", instance.gstin)
        instance.save()

        # Check if the user role is 'vendor' and update vendor info
        if instance.user_role == "vendor":
            vendor_data = self.validated_data.get("vendor", {})
            vendor = instance.vendor
            vendor.vendor_name = vendor_data.get("vendor_name", vendor.vendor_name)
            vendor.address = vendor_data.get("address", vendor.address)
            vendor.vendor_certified = vendor_data.get(
                "vendor_certified", vendor.vendor_certified
            )
            vendor.vendor_type = vendor_data.get("vendor_type", vendor.vendor_type)
            vendor.save()

        return instance

    def to_representation(self, instance):
        # Get user fields
        representation = super().to_representation(instance)

        # Check if the user role is 'vendor' and include vendor info
        if instance.user_role == "vendor":
            vendor_data = {
                "vendor_name": instance.vendor.vendor_name,
                "address": instance.vendor.address,
                "vendor_certified": instance.vendor.vendor_certified,
                "vendor_type": instance.vendor.vendor_type,
            }
            representation["vendor"] = vendor_data

        return representation


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"
