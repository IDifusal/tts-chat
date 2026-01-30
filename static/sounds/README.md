# Sound Effects

This directory contains sound effects for the bot.

## Required Files

### Event Sounds (Auto-play)
- `subscription.mp3` - Plays when someone subscribes
- `follow.mp3` - Plays when someone follows

### Command Sounds (Manual with !command)
- `carcrashing.mp3` - Example: !carcrashing
- Add more sounds here...

## Adding Sounds

1. Add `.mp3` file to this directory
2. For commands: Users can trigger with `!filename` (without .mp3)
3. For events: Reference in event handler

## Format

- **Format:** MP3
- **Sample Rate:** 44100 Hz recommended
- **Channels:** Stereo or Mono
- **Bitrate:** 128-192 kbps recommended

## Free Sound Resources

- [Freesound.org](https://freesound.org/)
- [Zapsplat.com](https://www.zapsplat.com/)
- [Pixabay Sounds](https://pixabay.com/sound-effects/)

## Notes

- Keep files under 1MB for fast loading
- Short sounds (1-3 seconds) work best for events
- Longer sounds OK for commands
