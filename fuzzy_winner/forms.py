from django import forms


class UploadFileForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.title = kwargs.pop("title") if kwargs.get("title") is not None else "Add new file"
        self.desc = kwargs.pop("desc") if kwargs.get(
            "desc") is not None else "Choose the file to upload:"
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.fields['file_name'] = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'uploadForm'}))
        self.fields['file_path'] = file = forms.FileField()


class FileForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.title = kwargs.pop("title") if kwargs.get("title") is not None else "Visualize graph data"
        self.desc = kwargs.pop("desc") if kwargs.get("desc") is not None else "Select the file to plot from"
        available_files = kwargs.pop('available_files')
        super(FileForm, self).__init__(*args, **kwargs)
        choices = ((file.id, file.filename,) for file in available_files)

        self.fields['available_files'] = forms.ChoiceField(required=False, widget=forms.RadioSelect, choices=choices)


class FileDeletionForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.title = kwargs.pop("title") if kwargs.get("title") is not None else "Delete file from database"
        self.desc = kwargs.pop("desc") if kwargs.get("desc") is not None else "Select the file you want to delete"
        available_files = kwargs.pop('available_files')
        super(FileDeletionForm, self).__init__(*args, **kwargs)
        choices = ((file.id, file.filename,) for file in available_files)
        self.fields['to_be_deleted'] = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple,
            choices=choices,
        )
