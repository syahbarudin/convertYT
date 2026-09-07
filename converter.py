import os
import shutil
import tempfile
import streamlit as st
import yt_dlp

# Deteksi FFmpeg sistem atau dari paket imageio-ffmpeg
ffmpeg_path = shutil.which("ffmpeg")
if not ffmpeg_path:
  try:
    import imageio_ffmpeg

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
  except ImportError:
    ffmpeg_path = None

st.set_page_config(
    page_title="YT Studio Audio Converter",
    page_icon="🎧",
    layout="centered",
)

st.title("🎧 YT Studio Audio Converter")
st.caption("Unduh dan konversi audio YouTube dengan kendali format & bitrate.")

# Input URL
url = st.text_input(
    "Tautan YouTube:",
    placeholder="https://www.youtube.com/watch?v=...",
)

# Panel Pilihan Format & Bitrate (Grid 2 Kolom)
col_fmt, col_bit = st.columns(2)

with col_fmt:
  format_pilihan = st.selectbox(
      "Format Output:",
      [
          "MP3 (Paling Populer)",
          "M4A (Bawaan YouTube / Cepat)",
          "WAV (Uncompressed / Lossless)",
          "OPUS (Format Modern)",
      ],
  )

with col_bit:
  bitrate_pilihan = st.select_slider(
      "Kualitas Bitrate:",
      options=["128 kbps", "192 kbps", "256 kbps", "320 kbps"],
      value="192 kbps",
      help="Semakin tinggi bitrate, semakin jernih suara (khusus MP3/OPUS).",
  )

# Ekstraksi kode ekstensi & angka bitrate
target_codec = {
    "MP3": "mp3",
    "M4A": "m4a",
    "WAV": "wav",
    "OPUS": "opus",
}[format_pilihan.split()[0]]

target_bitrate_num = bitrate_pilihan.split()[0]
target_mime = {
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "wav": "audio/wav",
    "opus": "audio/ogg",
}[target_codec]

st.write("")

if url:
  if st.button("⚡ Ekstrak & Konversi Audio", type="primary", use_container_width=True):
    with st.spinner("Mengambil informasi media..."):
      try:
        ydl_opts_info = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
          info = ydl.extract_info(url, download=False)
          title = info.get("title", "Audio")
          thumb = info.get("thumbnail", None)
          duration = info.get("duration", 0)
          channel = info.get("uploader", "Unknown Channel")

        # Kartu Informasi Video
        st.markdown("---")
        c1, c2 = st.columns([1, 2], vertical_alignment="center")
        if thumb:
          c1.image(thumb, use_container_width=True)
        with c2:
          st.subheader(title)
          st.caption(f"Saluran: **{channel}** • Durasi: **{duration // 60}m {duration % 60}s**")

        # Metric Badges (Biar Kelihatan Keren & Informatif)
        m1, m2, m3 = st.columns(3)
        m1.metric(label="Format Target", value=target_codec.upper())
        m2.metric(label="Bitrate Target", value=bitrate_pilihan)
        m3.metric(label="Mesin Audio", value="FFmpeg Pro" if ffmpeg_path else "Direct Stream")

        # Mulai Proses Download & Encode
        with st.spinner(f"Mengonversi ke {target_codec.upper()} ({bitrate_pilihan})..."):
          temp_dir = tempfile.mkdtemp()
          output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

          ydl_opts = {
              "format": "bestaudio/best",
              "outtmpl": output_template,
              "quiet": True,
              "no_warnings": True,
          }

          if ffmpeg_path:
            ydl_opts["ffmpeg_location"] = ffmpeg_path
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": target_codec,
                "preferredquality": target_bitrate_num,
            }]

          with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

          # Ambil hasil dari direktori sementara
          files = os.listdir(temp_dir)
          if files:
            file_path = os.path.join(temp_dir, files[0])
            file_name = files[0]
            file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)

            with open(file_path, "rb") as f:
              audio_bytes = f.read()

            st.success(f"🎉 Konversi tuntas! Ukuran file: **{file_size_mb} MB**")
            st.audio(audio_bytes, format=target_mime)

            st.download_button(
                label=f"⬇️ Simpan File ({target_codec.upper()} • {file_size_mb} MB)",
                data=audio_bytes,
                file_name=file_name,
                mime=target_mime,
                type="primary",
                use_container_width=True,
            )

            shutil.rmtree(temp_dir, ignore_errors=True)

      except Exception as e:
        st.error(f"Gagal memproses video: {e}")