from django.db import models

def material_directory_path(instance, filename):
    return "materials/{0}/{1}".format(instance.author, filename)

class Material(models.Model):
    author = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to=material_directory_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.author} book'