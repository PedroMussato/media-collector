import json
import base64
import subprocess
import re
import mimetypes

from pathlib import Path

from mutagen.id3 import (
    ID3,
    APIC,
    TIT2,
    TPE1,
    TPE2,
    TALB,
    TRCK
)


ROOT = Path("Music")


def clean_name(value):
    """
    Remove caracteres inválidos para filesystem.
    Evita criar subdiretórios acidentais.
    """

    value = str(value)

    value = re.sub(
        r'[\\/:*?"<>|]',
        '',
        value
    )

    value = value.strip()

    return value or "Unknown"



def save_cover(base64_data, output):

    if not base64_data:
        return None

    try:

        if "," in base64_data:
            _, data = base64_data.split(",", 1)
        else:
            data = base64_data

        image_bytes = base64.b64decode(data)

        img = Image.open(BytesIO(image_bytes))

        # Corrige orientação (EXIF)
        img = ImageOps.exif_transpose(img)

        # RGB
        img = img.convert("RGB")

        # Mantém proporção e gera exatamente 600x600
        img = ImageOps.fit(
            img,
            (600, 600),
            method=Image.Resampling.LANCZOS
        )

        img.save(
            output,
            format="JPEG",
            quality=92,
            optimize=True,
            progressive=False
        )

        return output

    except Exception as e:

        print(f"Cover error: {e}")

        return None



def download_mp3(url, output):

    if output.exists():
        print(
            f"Already exists: {output}"
        )
        return output


    temp = output.parent / "%(title)s.%(ext)s"


    command = [
        "yt-dlp",

        "--cookies-from-browser",
        "firefox",

        "-x",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",

        "-o",
        str(temp),

        url
    ]


    subprocess.run(
        command,
        check=True
    )


    downloaded = list(
        output.parent.glob("*.mp3")
    )


    if not downloaded:
        raise Exception(
            "MP3 not generated"
        )


    latest = max(
        downloaded,
        key=lambda x: x.stat().st_mtime
    )


    latest.rename(output)


    return output



def add_metadata(
    file,
    artist,
    album,
    title,
    track,
    cover
):

    tags = ID3()


    tags.add(
        TPE1(
            encoding=3,
            text=artist
        )
    )


    tags.add(
        TPE2(
            encoding=3,
            text=artist
        )
    )


    tags.add(
        TALB(
            encoding=3,
            text=album
        )
    )


    tags.add(
        TIT2(
            encoding=3,
            text=title
        )
    )


    if track:

        tags.add(
            TRCK(
                encoding=3,
                text=str(track)
            )
        )


    if cover and cover.exists():

        mime, _ = mimetypes.guess_type(
            cover
        )

        tags.add(
            APIC(
                encoding=3,
                mime=mime or "image/jpeg",
                type=3,
                desc="Cover",
                data=cover.read_bytes()
            )
        )


    tags.save(file)



def process_library(config):

    ROOT.mkdir(
        exist_ok=True
    )


    for band, albums in config.items():


        if not isinstance(albums, dict):
            continue


        band_name = clean_name(
            band
        )


        band_dir = ROOT / band_name

        band_dir.mkdir(
            exist_ok=True
        )


        for album, data in albums.items():


            if not isinstance(data, dict):
                continue


            musics = data.get(
                "musics",
                {}
            )


            if not musics:
                continue


            album_name = clean_name(
                album
            )


            album_dir = (
                band_dir /
                album_name
            )


            album_dir.mkdir(
                exist_ok=True
            )


            cover = None


            if data.get("cover"):

                cover = save_cover(
                    data["cover"],
                    album_dir / "cover.jpg"
                )


            for music_name, music in musics.items():


                if not isinstance(music, dict):
                    continue


                url = music.get(
                    "yt_url"
                )


                if not url:
                    print(
                        f"Missing URL: {music_name}"
                    )
                    continue



                title = clean_name(
                    music_name
                )


                track = music.get(
                    "track"
                )


                if track:

                    filename = (
                        f"{int(track):02d} - {title}.mp3"
                    )

                else:

                    filename = (
                        f"{title}.mp3"
                    )


                output = (
                    album_dir /
                    filename
                )


                try:

                    print(
                        f"\nDownloading:"
                        f"\n{band} - {album}"
                        f"\n{filename}"
                    )


                    download_mp3(
                        url,
                        output
                    )


                    add_metadata(
                        output,
                        band_name,
                        album_name,
                        title,
                        track,
                        cover
                    )


                    print(
                        "OK"
                    )


                except Exception as e:

                    print(
                        f"ERROR {filename}"
                    )

                    print(e)




def main():

    with open(
        "music.json",
        encoding="utf-8"
    ) as file:

        config = json.load(
            file
        )


    process_library(
        config
    )



if __name__ == "__main__":
    main()