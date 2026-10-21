from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Topic, Entry


class UserRegistrationForm(forms.ModelForm):
    """Registration form requiring username, email, password, and confirmation."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com',
            'autocomplete': 'email',
        }),
        help_text="A valid email address is required for account identification."
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password',
            'autocomplete': 'new-password',
        }),
        help_text="Password must contain at least 8 characters and cannot be entirely numeric."
    )
    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
        }),
        help_text="Re-type your password for verification."
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a unique username',
                'autocomplete': 'username',
            }),
        }
        help_texts = {
            'username': "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', "Passwords do not match.")
            else:
                # Run Django's standard password validators
                try:
                    validate_password(password)
                except ValidationError as err:
                    self.add_error('password', err)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class TopicForm(forms.ModelForm):
    """Form for creating and editing learning topics."""
    class Meta:
        model = Topic
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Django Web Framework, Data Structures, Machine Learning',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what you plan to learn, key resources, or general scope of this topic...',
            }),
        }
        labels = {
            'title': 'Topic Title',
            'description': 'Description (Optional)',
        }


class EntryForm(forms.ModelForm):
    """Form for creating and editing an entry under a known topic."""
    class Meta:
        model = Entry
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Setting up Class-Based Views and Generic Mixins',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Write your learning notes, key takeaways, snippets, and reflections here...',
            }),
        }
        labels = {
            'title': 'Entry Title',
            'content': 'Notes & Content',
        }


class QuickEntryForm(forms.ModelForm):
    """Form for creating an entry from the global 'Add Entry' action with topic selection."""
    class Meta:
        model = Entry
        fields = ['topic', 'title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Asynchronous Task Queues with Celery',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Write your learning notes, key takeaways, snippets, and reflections here...',
            }),
        }
        labels = {
            'topic': 'Select Topic',
            'title': 'Entry Title',
            'content': 'Notes & Content',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['topic'].queryset = Topic.objects.filter(user=user)
            self.fields['topic'].empty_label = "-- Choose one of your topics --"
            self.fields['topic'].widget.attrs.update({'class': 'form-select'})
