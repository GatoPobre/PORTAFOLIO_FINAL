from django import forms
from .models import Producto, Categoria


class CategoriaForm(forms.ModelForm):
    """Formulario para el modelo Categoria."""
    class Meta:
        model = Categoria
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs['aria-describedby'] = "id_nombre_help id_nombre_error"
        self.fields['nombre'].widget.attrs['aria-required'] = 'true'


class ProductoForm(forms.ModelForm):
    """Formulario para el modelo Producto."""
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'descripcion_corta',
                  'caracteristicas', 'precio', 'stock', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descripcion_corta': forms.TextInput(attrs={'class': 'form-control'}),
            'caracteristicas': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field_id = f"id_{field_name}"
            field.widget.attrs['aria-describedby'] = f"{field_id}_help {field_id}_error"
            if field.required:
                field.widget.attrs['aria-required'] = 'true'

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is None or precio <= 0:
            raise forms.ValidationError(
                "El precio debe ser estrictamente mayor a 0.")
        return precio

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is None:
            raise forms.ValidationError("El stock es obligatorio.")

        if self.instance.pk is None:  # Si es un producto NUEVO
            if stock <= 5:
                raise forms.ValidationError(
                    "Al registrar un nuevo módulo, el stock inicial debe ser mayor a 5.")
        else:  # Si se está MODIFICANDO un producto existente
            if stock < 0:
                raise forms.ValidationError(
                    "El stock no puede ser un número negativo.")
        return stock
