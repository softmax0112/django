import json
import pendulum

from datetime import datetime
from time import strptime
import stripe


from django.shortcuts import render, redirect, reverse
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .forms import AuthorizationForm
from administration.core.loading import get_model
from payment.models import Order ,Payment

Profile = get_model("administration", "Profile")
Locations = get_model("administration", "Locations")
ServiceTypes = get_model("administration", "ServiceTypes")
Service = get_model("registration", "Service")
CustomerCheckin = get_model("registration", "CustomerCheckin")
Authorization = get_model("customer", "Authorization")


# ==========================
# Customer Account Template
# ==========================

class CustomerAccount(TemplateView):
    def get(self,request):
        return redirect('/customer/classes-schedule')


# =================================
# Customer Class Schedule Template
# =================================

class CustomerClassesSchedule(TemplateView):
    template_name = 'customer/classes_schedule.html'

    context = {
        "customer_area_expand": "true",
        "customer_class_show":"show",
        "customer_classes_schedule": "active",
    }

    def get(self, request):
        classes = Service.objects.filter(enrolled_customers=request.user).order_by('scheduled_time')
        profile = Profile.objects.filter(pk=request.user.id).first()
        self.context['object'] = profile

        if len(classes) > 0:
            next_classes_list = []
            upcoming_classes_list = []

            for cls in classes:
                if not cls.occurred():
                    if cls.get_next_upcoming_classes_remaining_hours() <= 2:
                        next_classes_list.append(cls)
                    else:
                        upcoming_classes_list.append(cls)

            if len(next_classes_list) > 0:
                self.context['next_classes'] = next_classes_list

            if len(upcoming_classes_list) > 0:
                self.context['upcoming_classes'] = upcoming_classes_list

        return render(request, self.template_name, self.context)

    def post(self, request):
        print(request.POST.get('class_id'))
        CustomerCheckin.objects.create(customer=Profile.objects.get(id=request.user.id),
                                      in_class=Service.objects.get(id=request.POST.get('class_id')),
                                      id_in_layout=0,       # TBD from client - what goes here
                                      cancelled=True)

        return render(request, self.template_name, self.context)

# ==========================
# Customer History Template
# ==========================

class CustomerHistory(TemplateView):
    template_name = 'customer/history.html'

    context = {
        "customer_area_expand": "true",
        "customer_class_show":"show",
        "customer_history": "active",
    }

    def get(self, request):
        customer_checkin = CustomerCheckin.objects.filter(in_class__enrolled_customers=request.user).order_by('in_class__scheduled_time')
        if len(customer_checkin) > 0:
            class_list = []

            for sc in customer_checkin:
                if sc.in_class.occurred():
                    class_list.append(sc)

            if len(class_list) > 0:
                self.context['customer_checkins'] = class_list

        return render(request, self.template_name, self.context)


# ============================
# Customer Purchases Template
# ============================
class CustomerPurchases(TemplateView):
    template_name = 'customer/purchases.html'
    model = Payment

    returnData = {
        "customer_area_expand": "true",
        "customer_class_show":"show",
        "customer_puchases": "active",
    }
  
    def get_context_data(self, **kwargs):
        context = super(CustomerPurchases,self).get_context_data(**kwargs)
        context['payment_list'] = Payment.objects.all().order_by('-transaction_date')
        context['customer_puchases']="active"
        return context
    # def get(self, request):
    #     return render(request, self.template_name, self.returnData,)


# =================================
# Customer Authorization Template
# =================================

class CustomerAuthorizations(TemplateView):
    template_name = 'customer/authorizations.html'
    context = {
        "customer_area_expand": "true",
        "customer_class_show":"show",
        "customer_authorizations": "active",
        "new_relationship_form": AuthorizationForm(),
        "relationship_choices": Authorization.RELATIONSHIP_CHOICES,
        "action_choices": Authorization.ACTION_CHOICES,
    }
    def get(self, request):
        authorization = Authorization.objects.filter(from_profile=request.user)
        recipient_auths = Authorization.objects.filter(to_profile=request.user)
        if len(authorization) > 0:
            authorization = authorization.exclude(id=request.user.id)
            self.context['my_authorizations'] = authorization

        if len(recipient_auths) > 0:
            self.context['shared_auths'] = recipient_auths

        return render(request, self.template_name, self.context)

    def post(self, request):
        if 'delete_auth' in request.POST:
            print("this is called")
            auth_obj = Authorization.objects.filter(id=int(request.POST.get('auth-id')))
            if auth_obj:
                auth_obj.delete()
                authorization = Authorization.objects.filter(from_profile=request.user)
                self.context['my_authorizations'] = authorization
                return render(request, self.template_name, self.context)
        elif 'update_auth' in request.POST:
            auth_id = request.POST.get('my_auth_id')
            my_auth = Authorization.objects.get(id=auth_id)
            my_auth.relationship = request.POST.get('relationship')
            my_auth.action = request.POST.get('action')
            my_auth.to_profile = Profile.objects.get(email=request.POST.get('email'))
            my_auth.save()
        else:
            form = AuthorizationForm(request.POST)
            if form.is_valid():
                form.save(request)
        return self.get(request)

# ====================================
# Customer Accounts Settings Template
# ====================================

class CustomerAccountSettings(TemplateView):
    template_name = 'customer/account_settings.html'

    context = {
        "customer_area_expand": "true",
        "customer_class_show": "show",
        "customer_account_settings": "active",
    }

    def get(self, request):
        profile = Profile.objects.filter(pk=request.user.id).first()
        if profile:
            self.context['object'] = profile

            if profile.first_name and profile.last_name and profile.gender and profile.date_of_birth:
                self.context['profile_info_updated'] = True
            else:
                self.context['profile_info_updated'] = False

            if profile.street_address and profile.city and profile.state and profile.emgcy_cont_name and profile.emgcy_cont_num and profile.emgcy_cont_relation:
                print("if part is called")
                self.context['contact_info_updated'] = True
            else:
                print("else part is called")
                self.context['contact_info_updated'] = False

            if profile.email:
                self.context['account_info_updated'] = True
            else:
                self.context['account_info_updated'] = False
        self.context['gender_type_choices'] = Profile.GENDER_TYPE_CHOICES

        return render(request, self.template_name, self.context)

    def post(self, request):

        if 'personal_info' in request.POST:
            profile = Profile.objects.get(pk=request.user.id)
            profile.first_name = request.POST.get('first_name')
            profile.last_name = request.POST.get('last_name')
            profile.gender = request.POST.get('gender')
            profile.date_of_birth = request.POST.get('date_of_birth')
            profile.save()

            return self.get(request)

        elif 'contact_info' in request.POST:
            profile = Profile.objects.get(pk=request.user.id)
            profile.street_address = request.POST.get('street_address')
            profile.city = request.POST.get('city')
            profile.state = request.POST.get('state')
            profile.phone = request.POST.get('phone')
            profile.emgcy_cont_name = request.POST.get('emgcy_cont_name')
            profile.emgcy_cont_relation = request.POST.get('emgcy_cont_relation')
            profile.emgcy_cont_num = request.POST.get('emgcy_cont_num')
            profile.save()

            return self.get(request)

        elif 'account_info' in request.POST:
            profile = Profile.objects.get(pk=request.user.id)
            profile.email = request.POST.get('email')
            if request.POST.get('password'):
                profile.set_password(request.POST.get('password'))
            profile.save()

            return self.get(request)

        return redirect("customer:customer-account-settings")


# =====================
# Customer Booking View
# =====================

class CustomerBookingView(TemplateView):
    template_name = "customer/booking.html"

    context = {
        "customer_area_expand": "true",
        "customer_class_show": "show",
        "customer_account_settings": "active",
    }

    @staticmethod
    def get_week_date_and_month_list(date):
        today = date

        week_start_date = today.start_of('week').date().day
        week_end_date = today.end_of('week').date().day

        month_number = today.date().month
        week_start_date_month = today.start_of('week').date().month
        week_end_date_month = today.end_of('week').date().month
        week_date_list = []

        if week_start_date < week_end_date:
            week_date_list = [(month_number, date) for date in range(week_start_date, week_end_date+1)]
        else:
            month_end_date = today.start_of('week').date().end_of('month').day
            week_date_list = [(week_start_date_month, date) for date in range(week_start_date, month_end_date+1)]
            for date in range(1, week_end_date+1):
                week_date_list.append((week_end_date_month, date))

        return week_date_list

    @staticmethod
    def get_timings_range():
        ante_meridiem_start = 9     # 9 am
        post_meridiem_end = 9       # 9 pm

        time_list = [(item, " AM") for item in range(ante_meridiem_start, 12+1)]
        for item in range(1, post_meridiem_end+1):
            time_list.append((item , " PM"))

        return time_list

    @staticmethod
    def get_current_week_day_date_dictionary(date):
        """
        *** no params ***
        :return: Dictionary {}
            This method returns a dictionary containing `days` as keys and `month + date` as values.
            i.e {'Monday': 'Sep 2','Tuesday': 'Sep 3', 'Wednesday': 'Sep 4', 'Thursday': 'Sep 5', 'Friday': 'Sep 6', 'Saturday': 'Sep 7', 'Sunday': 'Sep 8'}
            Note: Date is system dependent.
        """

        today = date
        day_date_dict = {}
        week_date_list = []
        week_day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        week_start_date = today.start_of('week').date().day
        week_end_date = today.end_of('week').date().day
        month_end_date = today.end_of('month').date().day
        week_start_date_month_name = today.start_of('week').date().format('MMM')
        week_end_date_month_name = today.end_of('week').date().format('MMM')

        if week_start_date < week_end_date:
            week_date_list = [week_start_date_month_name + " " + str(date) for date in range(week_start_date, week_end_date+1)]
        else:
            week_date_list = [week_start_date_month_name + " " + str(date) for date in range(week_start_date, month_end_date+1)]
            for date in range(1, week_end_date+1):
                week_date_list.append(week_end_date_month_name + " " + str(date))

        for index in range(0, len(week_date_list)):
            day_date_dict[week_day_list[index]] = week_date_list[index]

        return day_date_dict

    def get(self, request):
        locations = Locations.objects.all()
        classes = Service.objects.all()
        class_types = ServiceTypes.objects.all()
        instructors = Profile.objects.filter(user_type=Profile.USER_TYPE_STAFF, is_teacher=True)

        day_date_dict = CustomerBookingView.get_current_week_day_date_dictionary(pendulum.now())
        time_list = CustomerBookingView.get_timings_range()
        week_day_list = CustomerBookingView.get_week_date_and_month_list(pendulum.now())

        if len(locations) > 0:
            self.context['locations'] = locations
        if len(classes) > 0:
            self.context['classes'] = classes
        if len(class_types) > 0:
            self.context['class_types'] = class_types
        if len(instructors) > 0:
            self.context['instructors'] = instructors
        if day_date_dict:
            self.context['day_date_dict'] = day_date_dict
        if time_list:
            self.context['time_list'] = time_list
        if week_day_list:
            self.context['week_day_list'] = week_day_list
        return render(request, self.template_name, self.context)


# ==========
# AJAX CALLS
# ==========

def ajax_for_get_profile_results(request):
    email = request.GET.get('email', None)
    profile = Profile.objects.filter(email=email)
    if len(profile) > 0:
        context = {
            'first_name': profile.first().first_name,
            'last_name': profile.first().last_name,
        }
    else:
        context = {
            'first_name': None,
            'last_name': None,
        }
    return JsonResponse(context)


def ajax_for_class_info(request):

    class_id = request.GET.get('class_id', None)
    clas = Service.objects.filter(id=class_id)
    week_day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    if len(clas) > 0:
        clas = clas.first()
        day_of_class = week_day_list[clas.scheduled_time.date().weekday()]
        slots = clas.capacity - clas.enrolled_customers.all().count()
        if slots < 0:
            slots = 0
        context = {
            'class_id': clas.id,
            'class_name': clas.class_type.name,
            'day_of_class': day_of_class,
            'date_of_class': clas.scheduled_time.date().strftime('%b %d'),
            'time_of_class': clas.scheduled_time.time(),
            'duration_of_class': clas.duration.total_seconds() / 60,
            'slots_remaining_of_class': slots,
            'location_of_class': None,
            'instructor_of_class': clas.teacher.first_name + " " + clas.teacher.last_name,
            'description_of_class': 'This is a dummy description',
        }
    else:
        context = {
            'first_name': None,
            'last_name': None,
        }
    return JsonResponse(context)


def ajax_get_class_context(request):
    week_type = request.GET.get('week_type', None)
    first_date = request.GET.get('first_date', None)
    first_date_month = strptime(first_date.split(" ")[0],'%b').tm_mon
    current_date = pendulum.datetime(pendulum.now().year, int(first_date_month), int(first_date.split(" ")[1]))
    day_date_dict = {}
    week_day_list = []
    time_list = []
    context = {}

    if week_type == 'prev':
        previous_to_current = current_date.previous()
        day_date_dict = CustomerBookingView.get_current_week_day_date_dictionary(previous_to_current)
        week_day_list = CustomerBookingView.get_week_date_and_month_list(previous_to_current)

    elif week_type == 'next':
        next_to_current = current_date.next()
        day_date_dict = CustomerBookingView.get_current_week_day_date_dictionary(next_to_current)
        week_day_list = CustomerBookingView.get_week_date_and_month_list(next_to_current)

    time_list = CustomerBookingView.get_timings_range()

    template_name = "customer/schedule_table.html"
    if day_date_dict:
        context['day_date_dict'] = day_date_dict
    if time_list:
        context['time_list'] = time_list
    if week_day_list:
        context['week_day_list'] = week_day_list
    return render(request, template_name, context=context)


def ajax_for_manage_booking(request):
    class_id = request.GET.get('class_id')
    user_id = request.GET.get('user_id')

    class_obj = Service.objects.get(id=class_id)
    user_obj = Profile.objects.get(id=user_id)

    # Check if Customer already Register in Class
    if class_obj.enrolled_customers.filter(pk=user_obj.pk).exists():
        response = {
            'message': 'You are already Registered for this class',
            'status': 'duplicate',
            'ok': True
        }
    else:
        class_obj.register(user_obj)
        response = {
            'message': 'You have Registered Successfully in class: {}'.format(user_obj.first_last(),
                                                                           class_obj.class_type),
            'status': 'registered',
            'ok': True
        }
    return JsonResponse(response)
