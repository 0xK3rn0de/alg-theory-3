from django import forms

from .models import MemeTemplate


class MemeTemplateForm(forms.ModelForm):
    class Meta:
        model = MemeTemplate
        fields = ["title", "category", "top_text", "bottom_text", "image"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Например, Понедельник"}),
            "category": forms.TextInput(attrs={"placeholder": "Например, Работа"}),
            "top_text": forms.TextInput(attrs={"placeholder": "Верхняя подпись"}),
            "bottom_text": forms.TextInput(attrs={"placeholder": "Нижняя подпись"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("top_text", "").strip() and not cleaned_data.get("bottom_text", "").strip() and not cleaned_data.get("image"):
            raise forms.ValidationError("Добавьте хотя бы одну подпись или изображение.")
        image = cleaned_data.get("image")
        if image and image.size > 5 * 1024 * 1024:
            self.add_error("image", "Размер изображения не должен превышать 5 МБ.")
        return cleaned_data