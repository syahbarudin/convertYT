import os
import shutil
import tempfile
import streamlit as st
import yt_dlp

# Cek ketersediaan FFmpeg
ffmpeg_path = shutil.which("ffmpeg")
if not ffmpeg_path:
  try:
    import imageio_ffmpeg

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
  except ImportError:
    ffmpeg_path = None

st.set_page_config(
    page_title="YT Studio Audio Converter",
    page_icon="mp4.png",
    layout="centered",
)

st.title("🎧 YT Studio Audio Converter")
st.caption("Unduh dan konversi audio YouTube dengan kendali format & bitrate.")

# Input URL
url = st.text_input(
    "Tautan YouTube:",
    placeholder="https://www.youtube.com/watch?v=...",
)

# Pilihan Format & Pengaturan Bitrate Dinamis
col_fmt, col_bit = st.columns(2, vertical_alignment="bottom")

with col_fmt:
  format_pilihan = st.selectbox(
      "Format Audio:",
      [
          "MP3 (Audio Universal)",
          "M4A (Audio Asli AAC YouTube)",
          "WAV (Studio Lossless)",
      ],
  )

# Penyesuaian bitrate berdasarkan format yang dipilih
if "MP3" in format_pilihan:
  target_codec = "mp3"
  target_mime = "audio/mpeg"
  with col_bit:
    bitrate_val = st.selectbox(
        "Kualitas Bitrate:",
        ["320 kbps (Ultra High)", "256 kbps (High)", "192 kbps (Standard)", "128 kbps (Hemat)"],
        index=2,
    )
    target_bitrate_num = bitrate_val.split()[0]

elif "M4A" in format_pilihan:
  target_codec = "m4a"
  target_mime = "audio/mp4"
  target_bitrate_num = "160"
  with col_bit:
    st.info("💡 **Bitrate:** ~160 kbps (Stream Asli YouTube)")

elif "WAV" in format_pilihan:
  target_codec = "wav"
  target_mime = "audio/wav"
  target_bitrate_num = "1411"
  with col_bit:
    st.info("💡 **Bitrate:** 1411 kbps (Lossless 16-bit PCM)")

st.write("")

# Tombol Proses & Unduh
if url:
  if st.button("⚡ Ekstrak & Konversi Audio", type="primary", use_container_width=True):
    with st.spinner("Mengambil metadata video..."):
      try:
        ydl_opts_info = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
          info = ydl.extract_info(url, download=False)
          title = info.get("title", "Audio")
          thumb = info.get("thumbnail", None)
          duration = info.get("duration", 0)
          channel = info.get("uploader", "Unknown Channel")

        st.markdown("---")
        c1, c2 = st.columns([1, 2], vertical_alignment="center")
        if thumb:
          c1.image(thumb, use_container_width=True)
        with c2:
          st.subheader(title)
          st.caption(f"Saluran: **{channel}** • Durasi: **{duration // 60}m {duration % 60}s**")

        # Metric Badges Informatif
        m1, m2, m3 = st.columns(3)
        m1.metric(label="Format Target", value=target_codec.upper())
        m2.metric(label="Bitrate Audio", value=f"{target_bitrate_num} kbps")
        m3.metric(label="Mesin Konversi", value="FFmpeg Pro" if ffmpeg_path else "Direct")

        with st.spinner(f"Memproses {target_codec.upper()} ({target_bitrate_num} kbps)..."):
          temp_dir = tempfile.mkdtemp()
          output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

          ydl_opts = {
              "format": "bestaudio/best",
              "outtmpl": output_template,
              "quiet": True,
              "no_warnings": True,
          }

          if target_codec != "m4a" and ffmpeg_path:
            ydl_opts["ffmpeg_location"] = ffmpeg_path
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": target_codec,
                "preferredquality": target_bitrate_num,
            }]

          with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

          files = os.listdir(temp_dir)
          if files:
            file_path = os.path.join(temp_dir, files[0])
            file_name = files[0]
            file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)

            with open(file_path, "rb") as f:
              audio_bytes = f.read()

            st.success(f"🎉 Selesai! Ukuran berkas: **{file_size_mb} MB**")
            st.audio(audio_bytes, format=target_mime)

            st.download_button(
                label=f"⬇️ Simpan {target_codec.upper()} ({file_size_mb} MB)",
                data=audio_bytes,
                file_name=file_name,
                mime=target_mime,
                type="primary",
                use_container_width=True,
            )

            shutil.rmtree(temp_dir, ignore_errors=True)

      except Exception as e:
        st.error(f"Gagal memproses berkas: {e}")

# --- WATERMARK KREDIT CREATOR ---
st.markdown(
    """
    <div style="margin-top: 80px; padding-top: 20px; border-top: 1px dashed rgba(255, 255, 255, 0.2); text-align: center;">
      <p style="font-size: 12px; color: #888; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 1px;">Project created by</p>
      <p style="font-size: 15px; font-weight: 700; color: #f1f1f1; margin: 0;">Syahbarudin Abdillah</p>
    </div>
    """,
    unsafe_allow_html=True,
)
