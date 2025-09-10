from django.shortcuts import render

# Create your views here.
def show_main(request):
    context = {
        'nama_apps' : 'Ini Sportstation',
        'npm' : '2406421970',
        'name': 'Faris Huda',
        'class': 'PBP E'
    }

    return render(request, "main.html", context)