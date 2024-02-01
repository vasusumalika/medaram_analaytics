from django.db import models


# Create your models here.
class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    email = models.CharField(max_length=256)
    password = models.CharField(max_length=256)
    phone_number = models.CharField(max_length=256)
    user_type = models.ForeignKey("UserType", on_delete=models.CASCADE, null=True)
    depot = models.ForeignKey("Depot", on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")


class UserType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_type_created_user", null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_type_updated_user", null=True)


class Depot(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    depot_code = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="depot_created_user", null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="depot_updated_user", null=True)


class Vehicle(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vehicle_created_user")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vehicle_updated_user")


class OperationType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="opt_type_created_user")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="opt_type_updated_user")


class VehicleDetails(models.Model):
    id = models.AutoField(primary_key=True)
    depot_id = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="vehicle_details_depot")
    bus_number = models.CharField(max_length=256)
    opt_type = models.ForeignKey(OperationType, on_delete=models.CASCADE, related_name="vehicle_details_opt_type")
    vehicle_name = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="vehicle_details_vehicle")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vehicle_details_created_user")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vehicle_details_updated_user")


class SpecialBusDataEntry(models.Model):
    id = models.AutoField(primary_key=True)
    special_bus_sending_depot = models.ForeignKey(Depot, on_delete=models.CASCADE,
                                                  related_name="special_bus_sending_depot")
    special_bus_reporting_depot = models.ForeignKey(Depot, on_delete=models.CASCADE,
                                                    related_name="special_bus_reporting_depot")
    bus_type = models.ForeignKey(OperationType, on_delete=models.CASCADE, related_name="special_bus_opt_type")
    bus_number = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="special_bus_vehicle")
    log_sheet_no = models.CharField(max_length=256)
    driver1_name = models.CharField(max_length=256)
    drive1_staff_name = models.CharField(max_length=256)
    driver1_phone_number = models.CharField(max_length=256)
    driver2_name = models.CharField(max_length=256)
    drive2_staff_name = models.CharField(max_length=256)
    drive2_phone_number = models.CharField(max_length=256)
    incharge_name = models.CharField(max_length=256)
    incharge_phone_number = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="special_bus_created_user")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="special_bus_updated_user")
