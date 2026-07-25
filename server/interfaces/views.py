from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Band, Album, Music
from django.shortcuts import HttpResponseRedirect
import base64
import mimetypes
import json


@login_required(login_url='/auth_app/login/')
def home(request):
    return render(request, 'interfaces/home.html', context={"bands":Band.objects.filter(owner=request.user)})

@login_required(login_url='/auth_app/login/')
def create_band(request):

    if request.method == "POST":
        band = Band()
        band.owner = request.user
        band.name = request.POST["name"]
        band.save()
        return HttpResponseRedirect('/')

    return render(request, 'interfaces/create_band.html')

@login_required(login_url='/auth_app/login/')
def band(request, uuid):
    band = Band.objects.get(uuid=uuid)

    if request.method == "POST":
        band.name = request.POST["name"]
        band.save()
        return HttpResponseRedirect('/')

    return render(request, 'interfaces/band.html', context={"band":band,"albums":Album.objects.filter(band=band)})

@login_required(login_url='/auth_app/login/')
def create_album(request, uuid):

    if request.method == "POST":
        album = Album()
        album.band = Band.objects.get(uuid=uuid)
        album.name = request.POST["name"]
        album.cover = request.FILES.get("cover")
        album.save()
        return HttpResponseRedirect(f'/band/{uuid}')

    return render(request, 'interfaces/create_album.html', context={"band":Band.objects.get(uuid=uuid)})

@login_required(login_url='/auth_app/login/')
def album(request, uuid):
    album = Album.objects.get(uuid=uuid)
    musics = Music.objects.filter(album=album).order_by("track")
    
    if request.method == "POST":
        album.name = request.POST["name"]
        if request.FILES.get("cover"):
            album.cover = request.FILES.get("cover")
        album.save()
        return HttpResponseRedirect(f'/band/{album.band.uuid}')
    
    return render(request, 'interfaces/album.html', context={"album":album, "musics":musics})

@login_required(login_url='/auth_app/login/')
def create_music(request, uuid):

    if request.method == "POST":
        music = Music()
        music.album = Album.objects.get(uuid=uuid)
        music.name = request.POST["name"]
        music.track = request.POST["track"]
        music.yt_url = request.POST["yt_url"]
        music.save()
        return HttpResponseRedirect(f'/album/{uuid}')

    return render(request, 'interfaces/create_music.html', context={"album":Album.objects.get(uuid=uuid)})

@login_required(login_url='/auth_app/login/')
def music(request, uuid):

    music = Music.objects.get(uuid=uuid)

    if request.method == "POST":
        music.name = request.POST["name"]
        music.track = request.POST["track"]
        music.yt_url = request.POST["yt_url"]
        music.save()
        return HttpResponseRedirect(f'/album/{music.album.uuid}')

    return render(request, 'interfaces/music.html', context={"music":music})

@login_required(login_url='/auth_app/login/')
def delete_music(request, uuid):
    music = Music.objects.get(uuid=uuid)

    if request.method == "POST":
        music.delete()
        return HttpResponseRedirect(f'/album/{music.album.uuid}')

    return render(request, 'interfaces/delete_music.html', context={"music":music})

@login_required(login_url='/auth_app/login/')
def delete_album(request, uuid):
    album = Album.objects.get(uuid=uuid)

    if request.method == "POST":
        album.delete()
        return HttpResponseRedirect(f'/band/{album.band.uuid}')

    return render(request, 'interfaces/delete_music.html', context={"album":album})


@login_required(login_url='/auth_app/login/')
def delete_band(request, uuid):
    band = Band.objects.get(uuid=uuid)

    if request.method == "POST":
        band.delete()
        return HttpResponseRedirect('/')

    return render(request, 'interfaces/delete_band.html', context={"band":band})

def image_to_base64(image_field):
    if not image_field:
        return None

    file_path = image_field.path

    mime_type, _ = mimetypes.guess_type(file_path)

    with open(file_path, "rb") as image:
        encoded = base64.b64encode(image.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"

@login_required(login_url='/auth_app/login/')
def generate_conf_file_main(request):
    conf = {}

    bands = Band.objects.filter(owner=request.user)

    for band in bands:
        conf[band.name] = {}

        albums = Album.objects.filter(band=band)

        for album in albums:
            conf[band.name][album.name] = {
                "cover": image_to_base64(album.cover) if album.cover else None,
                "musics": {}
            }

            musics = Music.objects.filter(album=album)

            for music in musics:
                conf[band.name][album.name]["musics"][music.name] = {
                    "track": music.track,
                    "yt_url": music.yt_url
                }

    return render(request, 'interfaces/conf.html', {
        "conf": json.dumps(conf, indent=4, ensure_ascii=False)
    })


@login_required(login_url='/auth_app/login/')
def generate_conf_file_band(request,uuid):
    conf = {}

    band = Band.objects.get(uuid=uuid)

    conf[band.name] = {}

    albums = Album.objects.filter(band=band)

    for album in albums:

        conf[band.name][album.name] = {
            "cover": image_to_base64(album.cover) if album.cover else None,
            "musics": {}
        }

        musics = Music.objects.filter(album=album)

        for music in musics:
            conf[band.name][album.name]["musics"][music.name] = {
                "track": music.track,
                "yt_url": music.yt_url
            }

    return render(request, 'interfaces/conf.html', {
        "conf": json.dumps(conf, indent=4, ensure_ascii=False)
    })


@login_required(login_url='/auth_app/login/')
def generate_conf_file_album(request,uuid):
    conf = {}

    album = Album.objects.get(uuid=uuid)

    conf[album.band.name] = {}

    conf[album.band.name][album.name] = {
        "cover": image_to_base64(album.cover) if album.cover else None,
        "musics": {}
    }

    musics = Music.objects.filter(album=album)
    
    for music in musics:
        conf[album.band.name][album.name]["musics"][music.name] = {
            "track": music.track,
            "yt_url": music.yt_url
        }

    return render(request, 'interfaces/conf.html', {
        "conf": json.dumps(conf, indent=4, ensure_ascii=False)
    })


