
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import NodeID3 from "node-id3";
import sharp from "sharp";

const execFileAsync = promisify(execFile);

const ROOT = path.resolve("Music");

// Remove invalid filesystem characters and accidental path separators.
function cleanName(value) {
  const cleaned = String(value)
    .replace(/[\\/:*?"<>|]/g, "")
    .trim();

  return cleaned || "Unknown";
}

// Convert a base64 image into an oriented, square 600x600 JPEG.
async function saveCover(base64Data, output) {
  if (!base64Data) {
    return null;
  }

  try {
    const data = base64Data.includes(",")
      ? base64Data.slice(base64Data.indexOf(",") + 1)
      : base64Data;

    const imageBytes = Buffer.from(data, "base64");

    await sharp(imageBytes)
      .rotate() // Automatically correct EXIF orientation.
      .resize(600, 600, {
        fit: "cover",
        position: "centre",
        kernel: sharp.kernel.lanczos3,
      })
      .flatten({ background: "#ffffff" })
      .jpeg({
        quality: 92,
        mozjpeg: true,
        progressive: false,
      })
      .toFile(output);

    return output;
  } catch (error) {
    console.error(`Cover error: ${error.message}`);
    return null;
  }
}

// Download and convert a YouTube video to MP3.
async function downloadMp3(url, output) {
  try {
    await fs.access(output);
    console.log(`Already exists: ${output}`);
    return output;
  } catch {
    // The output does not exist, so download it.
  }

  // Isolate this download to avoid accidentally renaming another MP3.
  const tempDir = await fs.mkdtemp(
    path.join(os.tmpdir(), "music-download-")
  );

  try {
    const template = path.join(tempDir, "%(title)s.%(ext)s");

    const args = [
      "--cookies-from-browser",
      "firefox",
      "-x",
      "--audio-format",
      "mp3",
      "--audio-quality",
      "0",
      "-o",
      template,
      url,
    ];

    await execFileAsync("yt-dlp", args, {
      maxBuffer: 10 * 1024 * 1024,
    });

    const files = await fs.readdir(tempDir);

    const mp3Files = files.filter(
      (file) => path.extname(file).toLowerCase() === ".mp3"
    );

    if (mp3Files.length === 0) {
      throw new Error("MP3 not generated");
    }

    // Normally there is one result; use the newest if there are several.
    const candidates = await Promise.all(
      mp3Files.map(async (file) => {
        const fullPath = path.join(tempDir, file);
        const stat = await fs.stat(fullPath);

        return {
          fullPath,
          modified: stat.mtimeMs,
        };
      })
    );

    candidates.sort((a, b) => b.modified - a.modified);

    await fs.mkdir(path.dirname(output), { recursive: true });

    await fs.rename(candidates[0].fullPath, output);

    return output;
  } finally {
    // Remove temporary files even when the download fails.
    await fs.rm(tempDir, { recursive: true, force: true });
  }
}

// Write ID3 metadata and embed the album cover.
async function addMetadata(
  file,
  artist,
  album,
  title,
  track,
  cover
) {
  const tags = {
    artist,
    performerInfo: artist,
    album,
    title,
  };

  if (track) {
    tags.trackNumber = String(track);
  }

  if (cover) {
    try {
      const imageBuffer = await fs.readFile(cover);

      tags.image = {
        mime: "image/jpeg",
        type: {
          id: 3,
          name: "front cover",
        },
        description: "Cover",
        imageBuffer,
      };
    } catch (error) {
      console.error(`Could not read cover: ${error.message}`);
    }
  }

  const success = NodeID3.write(tags, file);

  if (!success) {
    throw new Error(`Could not write ID3 tags: ${file}`);
  }
}

// Process the entire music library.
async function processLibrary(config) {
  await fs.mkdir(ROOT, { recursive: true });

  for (const [band, albums] of Object.entries(config)) {
    if (
      !albums ||
      typeof albums !== "object" ||
      Array.isArray(albums)
    ) {
      continue;
    }

    const bandName = cleanName(band);
    const bandDir = path.join(ROOT, bandName);

    await fs.mkdir(bandDir, { recursive: true });

    for (const [album, data] of Object.entries(albums)) {
      if (
        !data ||
        typeof data !== "object" ||
        Array.isArray(data)
      ) {
        continue;
      }

      const musics = data.musics ?? {};

      if (
        !musics ||
        typeof musics !== "object" ||
        Array.isArray(musics) ||
        Object.keys(musics).length === 0
      ) {
        continue;
      }

      const albumName = cleanName(album);
      const albumDir = path.join(bandDir, albumName);

      await fs.mkdir(albumDir, { recursive: true });

      let cover = null;

      if (data.cover) {
        cover = await saveCover(
          data.cover,
          path.join(albumDir, "cover.jpg")
        );
      }

      for (const [musicName, music] of Object.entries(musics)) {
        if (
          !music ||
          typeof music !== "object" ||
          Array.isArray(music)
        ) {
          continue;
        }

        const url = music.yt_url;

        if (!url) {
          console.log(`Missing URL: ${musicName}`);
          continue;
        }

        const title = cleanName(musicName);
        const track = music.track;

        let filename;

        if (track) {
          const trackNumber = Number.parseInt(track, 10);

          if (!Number.isFinite(trackNumber)) {
            throw new Error(`Invalid track number: ${track}`);
          }

          filename =
            `${String(trackNumber).padStart(2, "0")} - ${title}.mp3`;
        } else {
          filename = `${title}.mp3`;
        }

        const output = path.join(albumDir, filename);

        try {
          console.log(
            `\nDownloading:\n${band} - ${album}\n${filename}`
          );

          await downloadMp3(url, output);

          await addMetadata(
            output,
            bandName,
            albumName,
            title,
            track,
            cover
          );

          console.log("OK");
        } catch (error) {
          console.error(`ERROR ${filename}`);
          console.error(error.message);
        }
      }
    }
  }
}

// Entry point.
async function main() {
  try {
    const content = await fs.readFile("music.json", "utf8");
    const config = JSON.parse(content);

    await processLibrary(config);
  } catch (error) {
    console.error(`Fatal error: ${error.message}`);
    process.exitCode = 1;
  }
}

main();
