from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login

from .models import Vehicle, Image, Gallery
from .forms import VehicleForm, CustomUserCreationForm, GalleryUploadForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Rejestracja zakończona sukcesem. Jesteś zalogowany.")
            return redirect('vehicles:public_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def vehicle_list_published(request):
    vehicles = Vehicle.objects.filter(
        publication_date__isnull=False,
        publication_date__lte=timezone.now(),
        is_deleted=False
    ).select_related("user", "photo").order_by("-publication_date")
    context = {"vehicles": vehicles, "title": "Ostatnio dodane ogłoszenia"}
    return render(request, "MotoSell/vehicle_list.html", context)


def vehicle_detail(request, pk):
    vehicle = get_object_or_404(
        Vehicle, pk=pk, is_deleted=False, publication_date__isnull=False
    )
    gallery_images = vehicle.gallery_images.all().select_related('image')
    context = {
        'vehicle': vehicle,
        'gallery_images': gallery_images
    }
    return render(request, 'MotoSell/vehicle_detail.html', context)


@login_required
def vehicle_list_user(request):
    vehicles = Vehicle.objects.filter(user=request.user, is_deleted=False).select_related("photo").order_by("-date_added")
    context = {"vehicles": vehicles, "title": "Moje ogłoszenia"}
    return render(request, "MotoSell/vehicle_list.html", context)


@login_required
def vehicle_create(request):
    if request.method == "POST":
        vehicle_form = VehicleForm(request.POST, request.FILES)
        if vehicle_form.is_valid():
            uploaded_file = vehicle_form.cleaned_data.get('main_photo')
            new_image = None
            if uploaded_file:
                new_image = Image.objects.create(
                    name=uploaded_file.name,
                    image=uploaded_file
                )

            vehicle = vehicle_form.save(commit=False)
            vehicle.user = request.user

            if new_image:
                vehicle.photo = new_image
            vehicle.save()

            messages.success(
                request, "Twoje ogłoszenie zostało dodane. Możesz je teraz opublikować lub dodać więcej zdjęć w edycji."
            )
            return redirect("vehicles:update", pk=vehicle.pk)
    else:
        vehicle_form = VehicleForm()

    context = {"vehicle_form": vehicle_form, "title": "Dodaj nowe ogłoszenie"}
    return render(request, "MotoSell/vehicle_form.html", context)



@login_required
def vehicle_update(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, is_deleted=False)
    if vehicle.user != request.user:
        return HttpResponseForbidden("Nie masz uprawnień do edycji tego ogłoszenia.")

    if request.method == "POST":
        vehicle_form = VehicleForm(request.POST, request.FILES, instance=vehicle)
        gallery_form = GalleryUploadForm(request.POST, request.FILES)

        if vehicle_form.is_valid():
            uploaded_file = vehicle_form.cleaned_data.get('main_photo_upload')
            if uploaded_file:
                new_image = Image.objects.create(name=uploaded_file.name, image=uploaded_file)
                vehicle.photo = new_image

            vehicle_form.save()
            messages.success(request, "Ogłoszenie zostało zaktualizowane.")

        if gallery_form.is_valid():
            images = request.FILES.getlist('images')
            for img in images:
                image_instance = Image.objects.create(name=img.name, image=img)
                Gallery.objects.create(vehicle=vehicle, image=image_instance)
            if images:
                messages.success(request, f"Dodano {len(images)} zdjęć do galerii.")

        return redirect("vehicles:update", pk=vehicle.pk)
    else:
        vehicle_form = VehicleForm(instance=vehicle)
        gallery_form = GalleryUploadForm()

    context = {
        "vehicle_form": vehicle_form,
        "gallery_form": gallery_form,
        "vehicle": vehicle,
        "title": f"Edytuj ogłoszenie: {vehicle.title}"
    }
    return render(request, "MotoSell/vehicle_form.html", context)


@login_required
@require_POST
def vehicle_publish(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, user=request.user, is_deleted=False)
    if vehicle.publication_date is None:
        vehicle.publication_date = timezone.now()
        vehicle.save()
        messages.success(request, "Twoje ogłoszenie zostało opublikowane!")
    else:
        messages.info(request, "To ogłoszenie jest już opublikowane.")
    return redirect("vehicles:user_list")


@login_required
@require_POST
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, user=request.user)
    if not vehicle.is_deleted:
        vehicle.is_deleted = True
        vehicle.save()
        messages.success(request, "Ogłoszenie zostało usunięte.")
    return redirect("vehicles:user_list")
