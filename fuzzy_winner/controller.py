import logging
import os
import secrets

import graphviz
from django.utils import timezone

from .bin.processModule import compute_transactions_network, optimize_transactions_network
from .models import DataFile

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_file_extension(filename):
    return ".xlsx"


def handle_uploaded_file(f, filename):
    temp_code = secrets.token_urlsafe(16) + get_file_extension(filename)
    dest = os.path.join('temp', temp_code)
    with open(dest, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
        new_file = DataFile()
        new_file.filename = filename
        new_file.tempCode = temp_code
        new_file.date = timezone.now()
        new_file.save()
        return temp_code


def render_image(input_file_path, output_format="svg", optimize=False):
    if not optimize:
        dot_data = compute_transactions_network(input_file_path)
    else:
        dot_data = optimize_transactions_network(input_file_path)

    output_file_path = os.path.join("temp", secrets.token_urlsafe(16) + "." + output_format)
    outputfile_name, extension = os.path.splitext(output_file_path)
    graphviz.Source(dot_data.to_string(), filename=outputfile_name, format=output_format).render()
    return output_file_path


def load_image(file_path):
    with open(file_path, "rb") as f:
        byte = f.read()
    return byte
