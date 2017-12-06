import os

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from djangoSite import settings
from .controller import handle_uploaded_file, render_image, load_image
from .forms import FileForm, UploadFileForm, FileDeletionForm
from .models import DataFile


def index(request):
    return HttpResponseRedirect(reverse('fuzzy_winner:plot'))


def upload_success(request, title):
    return render(request, 'fuzzy_winner/uploadSuccess.html', {'title': title})


def plot(request):
    def get_files():
        return DataFile.objects.all()

    file_form = FileForm(available_files=get_files())
    deletion_form = FileDeletionForm(available_files=get_files())
    upload_form = UploadFileForm()

    if request.method == 'POST':
        try:
            selected_file = get_object_or_404(DataFile, pk=request.POST['available_files'])
        except:
            return HttpResponseRedirect(reverse('fuzzy_winner:plot'))
        if "optimize_transaction" in request.POST:
            image_path = render_image(selected_file.get_path(), output_format="svg", optimize=True)
        else:
            image_path = render_image(selected_file.get_path(), output_format="svg")
        image_data = reverse('fuzzy_winner:show_image', args=[image_path])
        return render(request, 'fuzzy_winner/graph.html', {'file_form': file_form,
                                                           'deletion_form': deletion_form,
                                                           'upload_form': upload_form,
                                                           'image_data': image_data})
    return render(request, 'fuzzy_winner/graph.html', {'file_form': file_form,
                                                       'deletion_form': deletion_form,
                                                       'upload_form': upload_form,
                                                       'image_data': ''})


def show_image(request, file_path):
    image_binary = load_image(file_path)
    return HttpResponse(image_binary, 'image/svg+xml')


def delete_file(request):
    if request.method == 'POST':
        to_be_deleted = request.POST.getlist('to_be_deleted')
        print(to_be_deleted)
        for file_id in to_be_deleted:
            try:
                selected_file = get_object_or_404(DataFile, pk=file_id)
                DataFile.objects.filter(pk=file_id).delete()
                os.remove(os.path.join(settings.MEDIA_URL, selected_file.get_name()))
            except:
                pass
        return HttpResponseRedirect(reverse('fuzzy_winner:plot'))
    else:
        return HttpResponseRedirect(reverse('fuzzy_winner:plot'))


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            new_file = handle_uploaded_file(request.FILES['file_path'], request.POST['file_name'])
            return HttpResponseRedirect(reverse('fuzzy_winner:plot'))
    else:
        form = UploadFileForm()
        return render(request, 'fuzzy_winner/upload.html', {'form': form})


def contact(request):
    if request.method == 'POST':
        print(request.POST['name'] + " writes " + request.POST['message'])
    return HttpResponseRedirect(reverse('fuzzy_winner:plot'))
