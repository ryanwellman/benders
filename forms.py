from models import *
from django import forms
from django.forms import ModelForm, ModelChoiceField
from django.contrib.auth.models import User

# ******** This is where I left off.  Need to put the games in the form *******
class NewsForm(ModelForm):

    def __init__(self, *args, **kwargs):
	super(NewsForm, self).__init__(*args, **kwargs)

	self.fields['news'].widget.attrs['class'] = 'span8'
      	self.fields['photo'].label = "Add Photo for News"
	self.fields['title'].label = "Label for News"

    class Meta:
	model = News


SEASON_OPTION_QS = Season.objects.values_list('season', flat=True)
AWARDS_OPTION_QS = Awards.objects.values_list('award', flat=True)
#PLAYERS_OPTION_QS = Players.objects.list('first_name', 'last_name')

class AwardsForm(ModelForm):
    season = ModelChoiceField(queryset=SEASON_OPTION_QS, required=True)
    award = ModelChoiceField(queryset=AWARDS_OPTION_QS, required=True)
    #player = ModelChoiceField(queryset=PLAYERS_OPTION_QS, required=True)

    def __init__(self, *args, **kwargs):
	super(AwardsForm, self).__init__(*args, **kwargs)

    class Meta:
	model = HallOfFame


class CreateScheduleForm(ModelForm):

    def __init__(self, *args, **kwargs):
	super(CreateScheduleForm, self).__init__(*args, **kwargs)

	self.fields['when'].widget.attrs['class'] = 'bootstrap-datepicker'

    class Meta:
	model = Schedule


class CreateUserForm(forms.Form):
    username = forms.CharField(max_length=30, help_text='Max length is 30 characters')
    first_name = forms.CharField(label='First Name')
    last_name = forms.CharField(label='Last Name')
    password1 = forms.CharField(label='Password', max_length=30, widget=forms.PasswordInput(), help_text='Max length is 30 characters')
    password2 = forms.CharField(label='Confirm Password', max_length=30, widget=forms.PasswordInput())
    email = forms.EmailField(help_text='**Only used for BG related stuff')
    referred_by = forms.CharField(max_length=40, help_text='**Required for all new players')
    
    def __init__(self, *args, **kwargs):
	super(CreateUserForm, self).__init__(*args, **kwargs)

    def clean(self):
	password1 = self.cleaned_data.get('password1')
	password2 = self.cleaned_data.get('password2')

	if password1 and password1 != password2:
	    raise forms.ValidationError("Passwords don't match")

	return self.cleaned_data


class UpdateUserForm(forms.Form):
    email = forms.EmailField()
    old_password = forms.CharField(label='Current Password', max_length=30, widget=forms.PasswordInput(), required=False)
    new_password1 = forms.CharField(label='New Password', max_length=30, widget=forms.PasswordInput(), required=False)
    new_password2 = forms.CharField(label='Confirm Password', max_length=30, widget=forms.PasswordInput(), required=False)

    def __init__(self, *args, **kwargs):
	super(UpdateUserForm, self).__init__(*args, **kwargs)

    def clean(self):
	password1 = self.cleaned_data.get('new_password1')
	password2 = self.cleaned_data.get('new_password2')

   	if new_password1 and new_password1 != new_password2:
	    raise forms.ValidationError("New passwords don't match")

	return self.cleaned_data


class UserLogInForm(forms.Form):
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'placeholder': 'Username'}), max_length=30)
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder': 'Password'}), max_length=30)

    def __init__(self, *args, **kwargs):
        super(UserLogInForm, self).__init__(*args, **kwargs)


class UserRSVPForm(forms.Form):
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'placeholder': 'Username'}), max_length=30)
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder': 'Password'}), max_length=30)
    confirm_rsvp = forms.BooleanField(label='My RSVP means I will be there for sure', required=True)

    def __init__(self, *args, **kwargs):
	super(UserRSVPForm, self).__init__(*args, **kwargs)


class QuickRSVPForm(forms.Form):
    confirm_rsvp = forms.BooleanField(label='My RSVP means I will be there for sure', required=True)

    def __init__(self, *args, **kwargs):
        super(QuickRSVPForm, self).__init__(*args, **kwargs)


class UserProfileForm(ModelForm):

    def __init__(self, *args, **kwargs):
	super(UserProfileForm, self).__init__(*args, **kwargs)

	self.fields['playing_since'].label = "Playing poker since"
	self.fields['tour_seasons'].label = "Seasons at Bender's Garage"
   	self.fields['favorite_hand'].label = "Favorite Poker Hand"
	self.fields['best_memory'].label = "Best Poker Memory"
	self.fields['outside_activity'].label = "Favorite Activity Outside of Poker"
	self.fields['best_memory'].widget.attrs['class'] = 'span8'
	self.fields['photo'].label = "Upload Player Picture"

    class Meta:
	model = Players
	fields = ['nickname', 'playing_since', 'tour_seasons', 'favorite_hand', 'best_memory', 'outside_activity', 'photo']


class MessageForm(ModelForm):

    def __init__(self, *args, **kwargs):
	super(MessageForm, self).__init__(*args, **kwargs)

	self.fields['message'].widget.attrs['class'] = 'span8'

    class Meta:
	model = MessageBoard


class ImageUploadForm(forms.Form):
    image = forms.ImageField()
