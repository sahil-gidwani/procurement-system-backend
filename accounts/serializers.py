from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import User, Vendor


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token["username"] = user.username
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
            "company_name",
            "address",
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
        password1 = validated_data.pop("password1", None)
        password2 = validated_data.pop("password2", None)
        user = User.objects.create_user(
            **validated_data,
            password=password1,
            user_role="procurement_officer",
        )

        return user


class VendorInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = (
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
            "company_name",
            "address",
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
    vendor = VendorInfoSerializer(write_only=True, required=False, allow_null=True)
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "gstin",
            "company_name",
            "address",
            "vendor",
        )
    
    def __init__(self, *args, **kwargs):
        super(ProfileSerializer, self).__init__(*args, **kwargs)

        # Adjust the 'required' attribute of the 'vendor' field based on user role
        if 'context' in kwargs and 'request' in kwargs['context']:
            user = kwargs['context']['request'].user
            if user.is_authenticated:  # Ensure user is authenticated
                user_role = user.user_role
                if user_role == 'procurement_officer':
                    self.fields['vendor'].required = False

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
        instance.company_name = validated_data.get("company_name", instance.company_name)
        instance.address = validated_data.get("address", instance.address)
        instance.save()

        # Check if the user role is 'vendor' and update vendor info
        if instance.user_role == "vendor":
            print(validated_data)
            vendor_data = validated_data.get("vendor", {})
            vendor = instance.vendor
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
                "vendor_certified": instance.vendor.vendor_certified,
                "vendor_type": instance.vendor.vendor_type,
                "contract_expiry_date": instance.vendor.contract_expiry_date,
                "vendor_rating": instance.vendor.vendor_rating,
            }
            representation["vendor"] = vendor_data

        return representation


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"
