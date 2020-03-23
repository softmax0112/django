from django.test import TestCase
from django.urls import reverse

# Create your tests here.
import datetime, bcrypt, pytz

from django.test import TestCase
from django.utils import timezone

from .models import *
from registration.models import *

# Create your tests here.
class AdministrationInitialTests(TestCase):
    def test_layout_rect_calculation(self):
        """
        Try to add a teacher and two customers to a class
        """
        t1 = Staff.create_staff('Peter','Griffin','peter@griffin.com', 'password', True)
        type1 = ServiceTypes.create_classtype(3,'Yoga','Core Power')
        location1 = Locations.create_location('Home Base')
        room1 = Rooms.create_room('Studio A',location1)
        layout1 = Layouts.create_rect_layout("Layout 1",room1,1,2,40,30,6,3,1)

        utc = pytz.utc
        day = datetime.datetime.today()
        dt = datetime.datetime(day.year,day.month,day.day,16,30,tzinfo=utc)
        dur = datetime.timedelta(hours=1)

        c1 = Service.create_class(type1,t1,dt,dur,layout1)
        layout_recall = c1.layout

        self.assertEqual(CustomerPlacement.objects.filter(layout=layout_recall).count(), 30)

    def test_layout_opt_ex_calculation(self):
        """
        Try to add a teacher and two customers to a class which uses our optimization code
        """
        t1 = Staff.create_staff('Peter','Griffin','peter@griffin.com', 'password', True)
        type1 = ServiceTypes.create_classtype(3,'Yoga','Core Power')
        location1 = Locations.create_location('Home Base')
        room1 = Rooms.create_room('Studio A',location1)
        layout1 = Layouts.create_opt_layout_ex("Layout 1",room1)

        utc = pytz.utc
        day = datetime.datetime.today()
        dt = datetime.datetime(day.year,day.month,day.day,16,30,tzinfo=utc)
        dur = datetime.timedelta(hours=1)

        c1 = Service.create_class(type1,t1,dt,dur,layout1)
        layout_recall = c1.layout

        customer_set = CustomerPlacement.objects.filter(layout=layout_recall)
        for customer in customer_set:
            print(customer.x)

        self.assertEqual(30, 30)

