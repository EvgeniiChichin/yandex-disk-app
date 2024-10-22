from django import forms

class KeyForm(forms.Form):
    public_key = forms.URLField(
        label='Ключ опубликованного ресурса',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Введите публичный ключ'})
    )
    file_type = forms.ChoiceField(
        label='Тип файла',
        choices=[
            ('all', 'Все'),
            ('document', 'Документ'),
            ('image', 'Изображение'),
            ('video', 'Видео'),
            ('audio', 'Аудио'),
            ('archive', 'Архив'),
        ],
        initial='all',
    )