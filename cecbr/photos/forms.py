from django import forms
from multiupload.fields import MultiMediaField

from .models import Group, Person, TrainingPhoto

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['group_name']



class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['groups','person_name','photos']

        files = MultiMediaField(min_num=1,media_type='image')


    def __init__(self, *args, **kwargs):
        super(PersonForm,self).__init__(*args, **kwargs)
        user = kwargs.pop('instance',None)
        qs = Group.objects.filter(user=user)
        self.fields['groups'].queryset = qs

    def save(self, commit=True):
        instance = super(PersonForm, self).save(commit)
        for photo in self.cleaned_data['files']:
            tp = TrainingPhoto(person=instance, photo=photo).save()

        return instance

