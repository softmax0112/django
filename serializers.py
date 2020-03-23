from rest_framework import serializers

from administration.core.loading import get_model

Profile = get_model("administration", "Profile")
Service = get_model("registration", "Service")


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'email', 'phone', 'street_address', 'city', 'state', 'country',
                  'emgcy_cont_name', 'emgcy_cont_num']

    def create(self, validated_data):
        """
        Create and return a new `Profile` instance, given the validated data.
        """
        return Profile.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Profile` instance, given the validated data.
        """
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.street_address = validated_data.get('street_address', instance.street_address)
        instance.city = validated_data.get('city', instance.city)
        instance.state = validated_data.get('state', instance.state)
        instance.country = validated_data.get('country', instance.country)
        instance.emgcy_cont_name = validated_data.get('emgcy_cont_name', instance.emgcy_cont_name)
        instance.emgcy_cont_num = validated_data.get('emgcy_cont_num', instance.emgcy_cont_num)
        instance.save()
        return instance


class ServiceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Service
        fields = ['class_type', 'teacher', 'layout', 'enrolled_customers', 'capacity']

    def create(self, validated_data):
        """
        Create and return a new `Services` instance, given the validated data.
        """
        return Service.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Services` instance, given the validated data.
        """
        instance.class_type = validated_data.get('class_type', instance.first_name)
        instance.teacher = validated_data.get('teacher', instance.last_name)
        instance.layout = validated_data.get('layout', instance.email)
        instance.enrolled_customers = validated_data.get('enrolled_customers', instance.phone)
        instance.capacity = validated_data.get('capacity', instance.street_address)
        instance.save()
        return instance