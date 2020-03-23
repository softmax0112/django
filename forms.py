from django import forms

from administration.core.loading import get_model

Authorization = get_model('customer', 'Authorization')
Profile = get_model('administration', 'Profile')


class AuthorizationForm(forms.ModelForm):
    class Meta:
        model = Authorization
        fields = ['action', 'split_service', 'relationship']

    def save(self, request):
        email = request.POST.get('email')
        relationship = request.POST.get('relationship')
        action = request.POST.get('action')
        from_user = Profile.objects.get(email=email)
        requested_user = Profile.objects.get(id=request.user.id)

        # SPLIT action is still to be configured here. Services models is not clear
        Authorization.objects.create(from_profile=requested_user,
                                     to_profile=from_user,
                                     relationship=relationship,
                                     action=action)