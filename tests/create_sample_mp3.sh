#!/bin/bash
# Create a 1-second silent MP3 file with ID3 tags
ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 1 \
  -metadata title="Test Song" \
  -metadata artist="Test Artist" \
  -metadata genre="Rock" \
  tests/resources/sample.mp3
