import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON
import time

# Configura aquí el directorio raíz de tus MP3
ROOT_DIR = "/Volumes/My Passport/Dj compilation 2025/DMS/DMS 80s"

# Género por defecto si está vacío
GENERO_POR_DEFECTO = "Unknown"

def limpiar_texto(texto):
    if not texto:
        return ""
    return " ".join(texto.strip().title().split())

def forzar_actualizacion_fisica(ruta_archivo):
    """Fuerza la actualización física del archivo tocando el archivo."""
    with open(ruta_archivo, 'a'):
        os.utime(ruta_archivo, None)

def limpiar_metadatos_mp3(ruta_archivo):
    try:
        audio = MP3(ruta_archivo, ID3=ID3)
        tags = audio.tags

        cambios = False

        # Título
        if TIT2 in tags:
            original = tags[TIT2].text[0]
            limpio = limpiar_texto(original)
            if limpio != original:
                tags[TIT2].text[0] = limpio
                cambios = True

        # Artista
        if TPE1 in tags:
            original = tags[TPE1].text[0]
            limpio = limpiar_texto(original)
            if limpio != original:
                tags[TPE1].text[0] = limpio
                cambios = True

        # Álbum
        if TALB in tags:
            original = tags[TALB].text[0]
            limpio = limpiar_texto(original)
            if limpio != original:
                tags[TALB].text[0] = limpio
                cambios = True

        # Género
        if TCON in tags:
            original = tags[TCON].text[0]
            limpio = limpiar_texto(original) or GENERO_POR_DEFECTO
            if limpio != original:
                tags[TCON].text[0] = limpio
                cambios = True
        else:
            # Si no hay género, lo agrega
            tags.add(TCON(encoding=3, text=[GENERO_POR_DEFECTO]))
            cambios = True

        # Guardar siempre para forzar actualización física
        audio.save()
        forzar_actualizacion_fisica(ruta_archivo)
        print(f"Procesado y forzado update: {ruta_archivo}")

    except Exception as e:
        print(f"Error procesando {ruta_archivo}: {e}")

def procesar_directorio(raiz):
    for root, _, files in os.walk(raiz):
        for file in files:
            if file.lower().endswith(".mp3"):
                limpiar_metadatos_mp3(os.path.join(root, file))

if __name__ == "__main__":
    procesar_directorio(ROOT_DIR) 