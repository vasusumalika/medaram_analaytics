from django.db import models


# Create your models here.
class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    email = models.CharField(max_length=256, null=True, blank=True)
    password = models.CharField(max_length=256, null=True, blank=True)
    phone_number = models.CharField(max_length=256, null=True, blank=True)
    user_type = models.ForeignKey("UserType", on_delete=models.CASCADE, null=True)
    depot = models.ForeignKey("Depot", on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")


class UserType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_type_created_user', default="",
                                   null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_type_updated_user', null=True,
                                   blank=True, default="")


class Depot(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    depot_code = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='depot_created_user', default="",
                                   null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='depot_updated_user', null=True,
                                   blank=True, default="")


class Vehicle(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    vehicle_owner = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_created_user', default="",
                                   null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_updated_user', null=True,
                                   blank=True, default="")


class OperationType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opt_type_created_user', default="",
                                   null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opt_type_updated_user', null=True,
                                   blank=True, default="")


# bus_number means vechicle_no

class VehicleDetails(models.Model):
    id = models.AutoField(primary_key=True)
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name="vehicle_details_depot")
    bus_number = models.CharField(max_length=256, null=True, blank=True)
    opt_type = models.ForeignKey(OperationType, on_delete=models.CASCADE, related_name="vehicle_details_opt_type")
    vehicle_name = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="vehicle_details_vehicle")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    vehicle_owner = models.CharField(max_length=256, null=True, blank=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_details_created_user',
                                   default="", null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_details_updated_user',
                                   null=True, blank=True, default="")


# bus_type means operation_type
# bus_number means vechicle_no

class SpecialBusDataEntry(models.Model):
    id = models.AutoField(primary_key=True)
    special_bus_sending_depot = models.ForeignKey(Depot, on_delete=models.CASCADE,
                                                  related_name="special_bus_sending_depot")
    special_bus_reporting_depot = models.ForeignKey(Depot, on_delete=models.CASCADE,
                                                    related_name="special_bus_reporting_depot")
    bus_type = models.ForeignKey(OperationType, on_delete=models.CASCADE, related_name="special_bus_opt_type")
    bus_number = models.ForeignKey(VehicleDetails, on_delete=models.CASCADE, related_name="special_bus_vehicle")
    log_sheet_no = models.CharField(max_length=256, null=True, blank=True)
    driver1_name = models.CharField(max_length=256, null=True, blank=True)
    driver1_staff_no = models.CharField(max_length=256, null=True, blank=True)
    driver1_phone_number = models.CharField(max_length=256, null=True, blank=True)
    driver2_name = models.CharField(max_length=256, null=True, blank=True)
    driver2_staff_no = models.CharField(max_length=256, null=True, blank=True)
    driver2_phone_number = models.CharField(max_length=256, null=True, blank=True)
    incharge_name = models.CharField(max_length=256, null=True, blank=True)
    incharge_phone_number = models.CharField(max_length=256, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='special_bus_created_user',
                                   default="", null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='special_bus_updated_user',
                                   null=True, blank=True, default="")


class StatisticsDateEntry(models.Model):
    id = models.AutoField(primary_key=True)
    bus_unique_code = models.CharField(max_length=256, null=True, blank=True)
    total_ticket_amount = models.CharField(max_length=256, null=True, blank=True)
    total_adult_passengers = models.CharField(max_length=256, null=True, blank=True)
    total_child_passengers = models.CharField(max_length=256, null=True, blank=True)
    mhl_adult_passengers = models.CharField(max_length=256, null=True, blank=True)
    mhl_child_passengers = models.CharField(max_length=256, null=True, blank=True)
    mhl_adult_amount = models.CharField(max_length=256, null=True, blank=True)
    mhl_child_amount = models.CharField(max_length=256, null=True, blank=True)
    entry_type = models.CharField(max_length=256, null=True, blank=True)
    service_operated_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='statistics_data_entry_created_user', default="",
                                   null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='statistics_data_entry_updated_user', null=True,
                                   blank=True, default="")


class OutDepotVehicleReceive(models.Model):
    bus_number = models.ForeignKey(VehicleDetails, on_delete=models.CASCADE, related_name="out_depot_bus_vehicle")
    special_bus_data_entry = models.ForeignKey(SpecialBusDataEntry, on_delete=models.CASCADE,
                                               related_name="out_depot_special_bus")
    unique_no = models.IntegerField()
    new_log_sheet_no = models.IntegerField()
    hsd_top_oil_liters = models.IntegerField()
    mts_no = models.IntegerField()
    bus_reported_date = models.DateField()
    bus_reported_time = models.TimeField()
    status = models.IntegerField(help_text="0=active;1=inactive;2=delete")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='out_depot_vehicle_created_user',
                                   null=True, blank=True, default="")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='out_depot_vehicle_updated_user',
                                   null=True, blank=True, default="")
