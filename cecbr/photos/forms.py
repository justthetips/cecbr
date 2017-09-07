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
        fields = ['person_name','photos']

        files = MultiMediaField(min_num=1,media_type='image')


    def save(self, commit=True):
        instance = super(PersonForm, self).save(False)
        group_id = self.request.POST['groupid']
        group = Group.objects.get(pk=group_id)
        instance.group = group
        instance.save()
        for photo in self.cleaned_data['files']:
            tp = TrainingPhoto(person=instance, photo=photo).save()

        return instance

