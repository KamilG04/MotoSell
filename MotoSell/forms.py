import datetime
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Vehicle, Image


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class VehicleForm(forms.ModelForm):
    main_photo_upload = forms.ImageField(
        label="Prześlij/zmień zdjęcie główne",
        required=False,
        help_text="Wybierz główne zdjęcie pojazdu"
    )

    class Meta:
        model = Vehicle
        fields = [
            'title', 'description', 'category', 'manufacturer', 'model',
            'make_year', 'mileage', 'cubic_capacity', 'power', 'fuel_type',
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Opisz swój pojazd...'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Np. Sprzedam BMW X5 w doskonałym stanie'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        current_year = datetime.date.today().year
        year_choices = [('', 'Wybierz rok')] + [
            (year, str(year)) for year in range(current_year + 1, 1884, -1)
        ]
        self.fields['make_year'] = forms.ChoiceField(
            choices=year_choices, 
            label="Rok produkcji"
        )
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        
        self.fields['mileage'].widget.attrs.update({
            'placeholder': 'Podaj przebieg w km'
        })
        self.fields['power'].widget.attrs.update({
            'placeholder': 'Moc w KM'
        })
        self.fields['cubic_capacity'].widget.attrs.update({
            'placeholder': 'Pojemność w cm³'
        })

    def clean_make_year(self):
        year = self.cleaned_data.get('make_year')
        if year:
            year = int(year)
            current_year = datetime.date.today().year
            if year < 1885 or year > current_year + 1:
                raise forms.ValidationError(
                    f"Rok produkcji musi być między 1885 a {current_year + 1}"
                )
        return year

    def clean_mileage(self):
        mileage = self.cleaned_data.get('mileage')
        if mileage and mileage < 0:
            raise forms.ValidationError("Przebieg nie może być ujemny")
        return mileage


class GalleryUploadForm(forms.Form):
    images = MultipleFileField(
        label="Dodaj zdjęcia do galerii",
        required=False,
        help_text="Możesz wybrać wiele zdjęć jednocześnie"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['images'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
        })

    def clean_images(self):
        images = self.cleaned_data.get('images')
        if images:
            if not isinstance(images, list):
                images = [images]
            
            for image in images:
                if image:
                    if image.size > 5 * 1024 * 1024:
                        raise forms.ValidationError(
                            f"Plik {image.name} jest za duży. Maksymalny rozmiar: 5MB"
                        )
                    
                    # Sprawdź typ pliku
                    if not image.content_type.startswith('image/'):
                        raise forms.ValidationError(
                            f"Plik {image.name} nie jest obrazem"
                        )
        
        return images


class CustomUserCreationForm(UserCreationForm):
    """Rozszerzony formularz rejestracji użytkownika"""
    email = forms.EmailField(
        required=True,
        label="Adres email",
        help_text="Wymagany. Podaj poprawny adres email."
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label="Imię"
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label="Nazwisko"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Polskie etykiety
        self.fields['username'].label = "Nazwa użytkownika"
        self.fields['password1'].label = "Hasło"
        self.fields['password2'].label = "Potwierdź hasło"
        
    
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        

        self.fields['username'].widget.attrs.update({
            'placeholder': 'Wybierz unikalną nazwę użytkownika'
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'twoj@email.com'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ten adres email jest już używany.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
        return user