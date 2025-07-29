from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


def validate_production_year(value):
    """Walidator roku produkcji pojazdu"""
    current_year = timezone.now().year
    if value < 1885 or value > current_year + 1:
        raise ValidationError(
            f"Rok produkcji musi być między 1885 a {current_year + 1}"
        )


class Image(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nazwa pliku")
    image = models.ImageField(upload_to="images/", verbose_name="Plik zdjęcia")
    uploaded_at = models.DateTimeField(
        default=timezone.now, verbose_name="Data dodania"
    )

    class Meta:
        verbose_name = "Zdjęcie"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.image.name
        super().save(*args, **kwargs)


class Vehicle(models.Model):
    class Category(models.TextChoices):
        MOTORCYCLE = "motocykl", "Motocykl"
        CAR = "osobowe", "Osobowy"
        TRUCK = "ciezarowy", "Ciężarowy"

    class FuelType(models.TextChoices):
        PETROL = "benzyna", "Benzyna"
        DIESEL = "diesel", "Diesel"
        LPG = "lpg", "Benzyna+LPG"

    title = models.CharField(max_length=200, verbose_name="Tytuł ogłoszenia")
    description = models.TextField(verbose_name="Opis")
    category = models.CharField(
        max_length=15, choices=Category.choices, verbose_name="Kategoria"
    )
    manufacturer = models.CharField(max_length=100, verbose_name="Marka")
    model = models.CharField(max_length=100, verbose_name="Model")
    make_year = models.IntegerField(
        verbose_name="Rok produkcji", validators=[validate_production_year]
    )
    mileage = models.IntegerField(
        verbose_name="Przebieg", validators=[MinValueValidator(0)]
    )
    cubic_capacity = models.IntegerField(
        verbose_name="Pojemność silnika", validators=[MinValueValidator(0)]
    )
    power = models.IntegerField(
        verbose_name="Moc (KM)", validators=[MinValueValidator(0)]
    )
    fuel_type = models.CharField(
        max_length=20, choices=FuelType.choices, verbose_name="Rodzaj paliwa"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Użytkownik")

    photo = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Zdjęcie główne",
        related_name="vehicle_photo",
    )

    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    publication_date = models.DateTimeField(
        verbose_name="Data publikacji", blank=True, null=True
    )

    class Meta:
        verbose_name = "Pojazd"
        verbose_name_plural = "Pojazdy"
        ordering = ["-date_added"]

    def __str__(self):
        return f"{self.manufacturer} {self.model} ({self.make_year})"

    def is_published(self):
        return (
            self.publication_date is not None
            and self.publication_date <= timezone.now()
        )


class Gallery(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    image = models.ForeignKey(
        Image, on_delete=models.CASCADE, related_name="gallery_images"
    )

    class Meta:
        verbose_name = "Zdjęcie w galerii"
        verbose_name_plural = "Zdjęcia w galerii"
        constraints = [
            models.UniqueConstraint(
                fields=["vehicle", "image"], name="unique_image_per_vehicle_gallery"
            )
        ]

    def __str__(self):
        return f"Zdjęcie '{self.image.name}' w galerii dla '{self.vehicle.title}'"
