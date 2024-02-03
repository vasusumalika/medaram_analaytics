from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    user_email_phone = serializers.CharField(required=True)
    user_password = serializers.CharField(required=True)

class DepotVehicleSerializer(serializers.Serializer):
    special_bus_sending_depot = serializers.IntegerField(required=True)

class GetSplBusDataEntrySerializer(serializers.Serializer):
    special_bus_data_id = serializers.IntegerField(required=True)

class SplBusEntrySerializer(serializers.Serializer):
    bus_sending_depot = serializers.IntegerField(required=True)
    bus_reporting_depot = serializers.IntegerField(required=True)
    bus_type = serializers.IntegerField(required=True)
    bus_number = serializers.IntegerField(required=True)
    log_sheet_no = serializers.CharField(required=True)
    driver1_name = serializers.CharField(required=True)
    driver1_staff_no = serializers.CharField(required=True)
    driver1_phone_number = serializers.CharField(required=True)
    driver2_name = serializers.CharField(required=True)
    driver2_staff_no = serializers.CharField(required=True)
    driver2_phone_number = serializers.CharField(required=True)
    incharge_name = serializers.CharField(required=True)
    incharge_phone_no = serializers.CharField(required=True)