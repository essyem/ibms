# portal/widgets.py
from django.forms import TextInput

class IconPickerWidget(TextInput):
    template_name = 'portal/widgets/icon_picker.html'

    class Media:
        css = {
            'all': [
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
                'css/icon-picker.css'
            ]
        }
        js = [
            'js/icon-picker.js'
        ]