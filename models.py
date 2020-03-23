import datetime, bcrypt, pytz
from uuid import uuid4
try:
    from .optimization.optimization import opt_example, room_optimization
    from . import ruoom_optimization
except:
    from . import ruoom_optimization
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import Group
import timeago
from phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError,PermissionDenied
from django.db.models.signals import pre_save


def waiver_directory_path(instance, filename):
    return 'files/waiver/%s/%s' % (str(instance.location_id), filename)


# Create your models here.
class StudioSettings(models.Model):
    name = models.CharField(max_length=200)
    customer_type = models.IntegerField() #0 - no setting, 1 - yoga mat, 2 - bike, 3 - table, 4 - bed, 5 - generic obstruction

    def __str__(self):
        return self.name

    #@receiver(pre_save, User)
    #def check_limits(sender, **kwargs):
    #    if sender.objects.count() > 1:      #There can only be one settings row
    #        raise PermissionDenied


class Locations(models.Model):
    name = models.CharField(max_length=200)
    street_address = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    ZIPcode = models.CharField(max_length=20)

    time_zone_string = models.CharField(default='UTC',max_length=50)
    #Rooms object cites this Locations object
    def time_zone(self):
        return pytz.timezone(self.time_zone_string)

    def __str__(self):
        return self.name

    @classmethod
    def create_location(cls,input_name):
        new_location = cls(name=input_name)
        new_location.save()
        return new_location


# creating separate to handle multiple uploads against one location
class Waiver(models.Model):
    location = models.ForeignKey(Locations, on_delete=models.CASCADE)
    waiver_file = models.FileField(upload_to=waiver_directory_path)


class Rooms(models.Model):
    name = models.CharField(max_length=200)
    location = models.ForeignKey(Locations, on_delete=models.CASCADE)
    obstruction = models.BooleanField(default=True)
    length = models.FloatField(default=None)       #Units Feet
    width = models.FloatField(default=None)       #Units Feet
    #Layouts object cites this Rooms object
    def __str__(self):
        return self.name

    @classmethod
    def create_room(cls,input_name,input_location,input_length,input_width):
        new_room = cls(name=input_name,location=input_location,length=input_length,width=input_width)
        new_room.save()
        return new_room


class CustomerPlacement(models.Model):
    x = models.FloatField()         #Units Feet
    y = models.FloatField()         #Units Feet
    size_x = models.FloatField(default=1)  # Units Feet
    size_y = models.FloatField(default=1)  # Units Feet

    alignment = models.FloatField() #1 = y aligned with room y
    layout = models.ForeignKey('Layouts', on_delete=models.CASCADE)
    id_in_layout = models.IntegerField(default=-1)
    uuid = models.CharField(max_length=50, null=True, blank=True) # to track changes and new shapes from front end.

    def __str__(self):
        return str(self.id_in_layout) + ' ' + str(self.x) + ' ' + str(self.y)

    @classmethod
    def create_customerplacement(cls, x_input, y_input, alignment_input, layout_input, id_input, uuid):
        new_customerplacement = cls(
            x=x_input, y=y_input, alignment=alignment_input, layout=layout_input,
            id_in_layout=id_input, uuid=uuid)
        new_customerplacement.save()
        return new_customerplacement


class Obstruction(models.Model):
    x = models.FloatField()         #Units Feet
    y = models.FloatField()         #Units Feet
    size_x = models.FloatField()         #Units Feet
    size_y = models.FloatField()         #Units Feet

    alignment = models.FloatField()  #1 = y aligned with room y
    layout = models.ForeignKey('Layouts', on_delete=models.CASCADE)
    id_in_layout = models.IntegerField(default=-1)
    uuid = models.CharField(max_length=50, null=True, blank=True)  # to track changes and new shapes from front end.

    is_instructor = models.BooleanField(default=False)  # Boolean value to identify a instructor obstruction in layout

    def __str__(self):
        return str(self.id_in_layout) + ' ' + str(self.x) + ' ' + str(self.y)

    @classmethod
    def create_obstruction(cls, x_input, y_input, size_x_input, size_y_input, alignment_input, layout_input, id_input, uuid):
        new_obstruction = cls(
            x=x_input,y=y_input, size_x=size_x_input, size_y=size_y_input,
            alignment=alignment_input, layout=layout_input, id_in_layout=id_input, uuid=uuid
        )
        new_obstruction.save()
        return new_obstruction


class Door(models.Model):
    x = models.FloatField()  # Units Feet
    y = models.FloatField()  # Units Feet
    size_x = models.FloatField(default=1)  # Units Feet
    size_y = models.FloatField(default=1)  # Units Feet

    alignment = models.FloatField()  # 1 = y aligned with room y
    layout = models.ForeignKey('Layouts', on_delete=models.CASCADE)
    id_in_layout = models.IntegerField(default=-1)
    uuid = models.CharField(max_length=50, null=True, blank=True)  # To track changes and new shapes from front end

    def __str__(self):
        return str(self.id_in_layout) + ' ' + str(self.x) + ' ' + str(self.y)

    @classmethod
    def create_door(cls, x_input, y_input, alignment_input, layout_input, id_input, uuid):
        new_door = cls(
            x=x_input, y=y_input, alignment=alignment_input, layout=layout_input,
            id_in_layout=id_input, uuid=uuid)
        new_door.save()
        return new_door


class Layouts(models.Model):
    name = models.CharField(max_length=200)
    room = models.ForeignKey(Rooms, on_delete=models.CASCADE)
    capacity = models.IntegerField(default=0)
    x = models.FloatField(null=True, blank=True, default=None)
    y = models.FloatField(null=True, blank=True, default=None)
    # Customer dimensions
    customer_x = models.IntegerField(default=1)
    customer_y = models.IntegerField(default=1)

    def __str__(self):
        return self.name
        # return self.name + ' ' + str(self.id)

    @classmethod
    def create_layout(cls, input_name, input_room, x_input, y_input, customer_x=1, customer_y=1):
        new_layout = cls(name=input_name,room=input_room, x=x_input, y=y_input, customer_x=customer_x, customer_y=customer_y)
        new_layout.save()
        return new_layout

    @classmethod
    def create_rect_layout(cls,input_name,input_room,space_between_mats,space_from_wall,ruoom_length,ruoom_width,mat_length,mat_width,orientation, customer_x, customer_y):
        new_layout = cls(name=input_name,room=input_room, x=ruoom_width, y=ruoom_length, customer_x=customer_x, customer_y=customer_y)
        new_layout.save()
        new_placements, count = ruoom_optimization.rect_layout(space_between_mats,space_from_wall,ruoom_length,ruoom_width,mat_length,mat_width,orientation)
        for i in range(count):
            new_placement=CustomerPlacement.create_customerplacement(new_placements[i].x,new_placements[i].y,new_placements[i].alignment,new_layout,i+1, uuid4())
        new_layout.capacity = count
        new_layout.save()
        return new_layout

    @classmethod
    def create_opt_layout_ex(cls,input_name,input_room):
        new_layout = cls(name=input_name,room=input_room, x=30, y=40)
        new_layout.save()
        new_placements = opt_example()
        count = len(new_placements)
        for i in range(count):
            new_placement=CustomerPlacement.create_customerplacement(new_placements[i][0],new_placements[i][1],1,new_layout,i+1)
        new_layout.capacity = count
        new_layout.save()
        return new_layout

    @classmethod
    def create_opt_layout(cls, input_name, input_room, space_between, space_from_wall, customer_x, customer_y, orientation, teacher, shape_x, shape_y, shape_pos_x, shape_pos_y, scale):
        new_layout = cls(name=input_name,room=input_room, x=shape_x[0], y=shape_y[0])
        new_layout.save()
        new_placements = room_optimization(space_between,space_from_wall,customer_x,customer_y,orientation,teacher,shape_x,shape_y,shape_pos_x,shape_pos_y,scale)
        count = len(new_placements)
        for i in range(count):
            new_placement=CustomerPlacement.create_customerplacement(new_placements[i][0],new_placements[i][1],1,new_layout,i+1)
        new_layout.capacity = count
        new_layout.save()
        return new_layout


class Profile(User):


    GENDER_TYPE_MALE = "male"
    GENDER_TYPE_FEMALE = "female"

    USER_TYPE_CUSTOMER = "customer"
    USER_TYPE_STAFF = "staff"

    USER_TYPE_CHOICES = (
        (USER_TYPE_CUSTOMER, "customer"),
        (USER_TYPE_STAFF, "staff"),
    )

    # Add any more genders here.
    GENDER_TYPE_CHOICES = (
        (GENDER_TYPE_FEMALE, "Female"),
        (GENDER_TYPE_MALE, "Male"),
    )

    user_type = models.CharField(max_length=10,
                                 choices=USER_TYPE_CHOICES,
                                 null=True,
                                 blank=True)

    phone = PhoneNumberField(blank=True)
    notes = models.CharField(max_length=5000, null=True, blank=True)

    gender = models.CharField(max_length=20,
                              choices=GENDER_TYPE_CHOICES,
                              null=True,
                              blank=True)
    date_of_birth = models.DateField(blank=True, verbose_name='Date of birth', null=True)


    street_address = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)

    #Service object cites this Staff object
    emgcy_cont_name = models.CharField(verbose_name="Emergency Contact Name", max_length=400, null=True)
    emgcy_cont_relation = models.CharField(verbose_name="Emergency Contact Relationship", max_length=400, null=True)
    emgcy_cont_num = PhoneNumberField(verbose_name="Emergency Contact Number", blank=True, null=True)

    is_teacher = models.BooleanField(verbose_name="Is Instructor?",default=False)
    balance=models.FloatField(blank=True, null=True, verbose_name='Account Balance', default=0)


    #pagepermissions = models.CharField(max_length=200) #CHANGE THIS ENTRY FOR PAGE PERMISSION INFORMATION

    def first_last(self):
        return self.first_name + ' ' + self.last_name
    
    def first_last_user(self):
        return self.first_name + ' ' + self.last_name + ' ' + '('+str(self.user_type) + ')'

    def last_first(self):
        return self.last_name + ', ' + self.first_name

    def is_customeruser(self):
        return "Customer" in self.groups.values_list('name', flat=True)

    def is_staffuser(self):
        return "Staff" in self.groups.values_list('name', flat=True)

    def __str__(self):
        return self.first_last()

    @classmethod
    def create_staff(cls,input_first,input_last,input_email,input_password, input_teacher):
        pw_hash = bcrypt.hashpw(str.encode(input_password), bcrypt.gensalt()).decode()
        new_staff = cls(first_name = input_first,last_name = input_last,email = input_email, password = pw_hash, is_teacher = input_teacher, user_type=Profile.USER_TYPE_STAFF)
        new_staff.save()
        group = Group.objects.filter(name="Staff")
        if group:
            new_staff.groups.add(group.first())
        new_staff.save()
        return new_staff

    @classmethod
    def create_customer(cls, input_first, input_last, input_email, input_password):
        pw_hash = bcrypt.hashpw(str.encode(
            input_password), bcrypt.gensalt()).decode()
        new_customer = cls(first_name=input_first, last_name=input_last,
                          email=input_email, password=pw_hash, user_type=Profile.USER_TYPE_CUSTOMER)
        new_customer.save()
        group = Group.objects.filter(name="Customer")
        if group:
            new_customer.groups.add(group.first())
        new_customer.save()
        return new_customer

    def save(self, *args, **kwargs):
        # currently model is inherited from 'User' model therefore 'username' property cannot be ignore and MUST be unique
        # in our forms we are making sure that emails are unique and thus can be stored for 'username'
        # DELETE THIS login when auth user model is changed.
        self.username = self.email
        super(Profile, self).save(*args, **kwargs)

    @classmethod
    def get_count(cls, **kwargs):
        return cls.objects.filter(**kwargs).count()

    class Meta:
        verbose_name = 'Profile'


class Shifts(models.Model):
    notes = models.CharField(max_length=1000)
    staff_member = models.ForeignKey(Profile,
                                     on_delete=models.CASCADE,
                                     limit_choices_to={'is_staff': True})

    scheduled_time = models.DateTimeField()
    duration = models.DurationField()

    @classmethod
    def create_shift(cls,input_name,input_staff,input_time, input_duration):
        new_shift = cls(name=input_name, staff_member=input_staff, scheduled_time=input_time, duration=input_duration)
        new_shift.save()
        return new_shift

    def __str__(self):
        return self.name


class ServiceTypes(models.Model):
    level = models.IntegerField()
    workout = models.CharField(max_length=200)
    name = models.CharField(max_length=200)

    def __str__(self):
        return str(self.level)+' | '+self.name

    @classmethod
    def create_classtype(cls,input_level,input_workout,input_name):
        new_classtype = cls(level=input_level,workout=input_workout,name=input_name)
        new_classtype.save()
        return new_classtype

# class ShopItem(models.Model):
#    name = models.CharField(max_length=200)
#    price = models.DecimalField(decimal_places=2)
#    quantity = models.IntegerField(default=-1)
#    info = models.CharField(max_length=1000)

#    def __str__(self):
#        return self.name


class Note(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(Profile, related_name='read_by')
    delete_by = models.ManyToManyField(Profile, related_name='delete_by')

    def __str__(self):
        return self.title

    @property
    def creation_date(self):
        return self.creation_time.strftime('%Y-%m-%d')

    @property
    def time_passed(self):
        return timeago.format(timezone.now() - self.creation_time)

    def short_description(self):
        if len(self.description) > 25:
            short_description = self.description[0:25] + '...'
        else:
            short_description = self.description + '.'
        return short_description


class StatusChoices:
    NOT_STARTED = 'Not Started'
    IN_PROGRESS = 'In Progress'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'

    CHOICES = (
        (NOT_STARTED, NOT_STARTED),
        (IN_PROGRESS, IN_PROGRESS),
        (COMPLETED, COMPLETED),
        (CANCELLED, CANCELLED)
    )

    COLOURS = {
        NOT_STARTED: 'muted',
        IN_PROGRESS: 'warning',
        COMPLETED: 'success',
        CANCELLED: 'danger'
    }


class Task(models.Model):
    goal = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default=StatusChoices.NOT_STARTED, choices=StatusChoices.CHOICES)
    due_date = models.DateField()
    assignee = models.ForeignKey(Profile, related_name='task', on_delete=models.CASCADE)
    notes = models.CharField(max_length=255)

    def __str__(self):
        return "{} | {} | {}".format(self.goal, self.status, self.assignee)

    @property
    def date_due(self):
        return self.due_date.strftime('%Y-%m-%d')

    def status_color(self):
        return StatusChoices.COLOURS[self.status]
